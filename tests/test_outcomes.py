"""Automatic outcome-label tests."""

from __future__ import annotations

import json

from toolobs.analysis.outcomes import (
    compute_outcomes,
    flag_detected,
    outcome_counts,
)
from toolobs.infer.parse_output import (
    parse_decision,
    signature_from_json,
    signature_hash,
    signature_json,
    signatures_differ,
)
from toolobs.schemas import DecisionSignature, LedgerRow, PerturbationRecord


def _sig(text: str) -> DecisionSignature:
    parsed = parse_decision(text)
    assert parsed.parsed, text
    return signature_from_json(signature_json(parsed))


def _row(
    arm: str,
    *,
    prefix: str = "p1",
    text: str = '{"tool": "get_order_details", "arguments": {"order_id": "#W1"}}',
    parsed: bool = True,
) -> LedgerRow:
    if parsed:
        decision = parse_decision(text)
        signature = signature_hash(decision)
        decision_json = signature_json(decision)
        status = decision.status
    else:
        signature = ""
        decision_json = ""
        status = "parse_error"
    return LedgerRow(
        run_id="run",
        model_id="qwen",
        prefix_id=prefix,
        arm=arm,
        step=0,
        prompt_hash="p",
        output_text=text,
        parsed=parsed,
        latency_ms=1.0,
        cost_usd=0.0,
        timestamp_utc="2026-11-15T00:00:00+00:00",
        stage="main",
        parser_status=status,
        signature_hash=signature,
        decision_json=decision_json,
    )


def _perturbation(arm: str, false_value, severity: int) -> PerturbationRecord:
    return PerturbationRecord(
        prefix_id="p1",
        arm=arm,
        severity=severity,
        json_path="$.status",
        true_value="delivered",
        false_value=false_value,
        criticality="critical" if severity >= 2 else "noncritical",
        expected_action_change=severity >= 2,
        renderer_version="toolresult-prose-v1",
    )


def test_flag_detection() -> None:
    assert flag_detected("The price looks inconsistent; let me verify.")
    assert not flag_detected("The order is delivered.")


def test_silent_propagation_of_an_argument_value() -> None:
    """Same action, corrupted value carried into the decision -> silent propagation."""
    rows = [
        _row("V", text='{"tool": "refund_order", "arguments": {"amount": 990}}'),
        _row("s2", text='{"tool": "refund_order", "arguments": {"amount": 1138}}'),
    ]
    labels = compute_outcomes(rows, [_perturbation("s2", 1138, 2)])
    label = labels[0]
    assert label.y_any is True
    assert label.y_action is False
    assert label.y_flag is False
    assert label.y_silent is True


def test_identical_decision_is_not_silent_propagation() -> None:
    """The audit's PPV defect: YU=1 on outputs identical to the reference must be impossible."""
    text = '{"tool": "search_direct_flight", "arguments": {"date": "2024-05-20", "origin": "DTW"}}'
    rows = [_row("V", text=text), _row("s2", text=text)]
    label = compute_outcomes(rows, [_perturbation("s2", 20, 2)])[0]
    assert label.y_any is False
    assert label.y_silent is False


def test_numeric_false_value_must_match_typed_not_substring() -> None:
    """False value 20 must not match inside the date 2024-05-20."""
    ref = '{"tool": "search_direct_flight", "arguments": {"date": "2024-05-20", "origin": "DTW"}}'
    model = '{"tool": "search_direct_flight", "arguments": {"date": "2024-05-20", "origin": "PHL"}}'
    rows = [_row("V", text=ref), _row("s2", text=model)]
    label = compute_outcomes(rows, [_perturbation("s2", 20, 2)])[0]
    assert label.y_any is True  # origin really differs
    assert label.y_silent is False  # but not because of "20" inside a date


def test_false_value_present_in_reference_is_not_propagation() -> None:
    """A value that legitimately appears in the reference cannot be attributed to the corruption."""
    ref = '{"final_answer": "Refunded to your payment card ending in payment_abc."}'
    model = '{"final_answer": "Refunded to your payment card ending in payment_abc."}'
    rows = [_row("V", text=ref), _row("s3", text=model)]
    label = compute_outcomes(rows, [_perturbation("s3", "payment", 3)])[0]
    assert label.y_any is False
    assert label.y_silent is False


def test_status_claim_propagation_is_silent() -> None:
    rows = [
        _row("V", text='{"final_answer": "The order is delivered."}'),
        _row("s2", text='{"final_answer": "The order is pending."}'),
    ]
    label = compute_outcomes(rows, [_perturbation("s2", "pending", 2)])[0]
    assert label.y_any is True
    assert label.y_action is False
    assert label.y_silent is True


def test_final_answer_value_conflict_is_a_decision_change() -> None:
    """The audit's missed-Y defect: a different refund amount is a decision change."""
    rows = [
        _row("V", text='{"final_answer": "Your refund is $990.00."}'),
        _row("s3", text='{"final_answer": "Your refund is $1138.00."}'),
    ]
    label = compute_outcomes(rows, [_perturbation("s3", 1138, 3)])[0]
    assert label.y_any is True
    assert label.y_action is False
    assert label.y_silent is True


def test_missing_value_on_one_side_is_paraphrase() -> None:
    """Omitting a detail amount is not a decision change (audit: OUT-085 style)."""
    rows = [
        _row("V", text='{"final_answer": "The return was initiated. The refund of $2895.55 is on its way."}'),
        _row("s2", text='{"final_answer": "The return was initiated. The refund is on its way."}'),
    ]
    label = compute_outcomes(rows, [_perturbation("s2", 2895.55, 2)])[0]
    assert label.y_any is False
    assert label.y_silent is False


def test_flag_blocks_silent_propagation() -> None:
    rows = [
        _row("V", text='{"tool": "refund_order", "arguments": {"amount": 990}}'),
        _row(
            "s2",
            text='{"tool": "refund_order", "arguments": {"amount": 1138}} The price looks inconsistent; verify.',
        ),
    ]
    label = compute_outcomes(rows, [_perturbation("s2", 1138, 2)])[0]
    assert label.y_flag is True
    assert label.y_silent is False


def test_action_switch_blocks_silent_propagation() -> None:
    rows = [
        _row("V", text='{"tool": "get_order_details", "arguments": {"order_id": "#W1"}}'),
        _row("s2", text='{"tool": "cancel_pending_order", "arguments": {"order_id": "#W1"}}'),
    ]
    label = compute_outcomes(rows, [_perturbation("s2", "cancel", 2)])[0]
    assert label.y_action is True
    assert label.y_any is True
    assert label.y_silent is False


def test_s1_is_not_scored_for_silent_propagation() -> None:
    rows = [
        _row("V", text='{"final_answer": "The note says nothing."}'),
        _row("s1", text='{"final_answer": "The note says fragile."}'),
    ]
    label = compute_outcomes(rows, [_perturbation("s1", "fragile", 1)])[0]
    assert label.y_silent is False


def test_prose_tool_argument_is_not_a_decision_slot() -> None:
    """transfer_to_human_agents summaries differ in prose only -> same decision (audit items)."""
    ref = '{"tool": "transfer_to_human_agents", "arguments": {"summary": "User wants to cancel insurance, but cannot be done through the system"}}'
    model = '{"tool": "transfer_to_human_agents", "arguments": {"summary": "User wants to cancel insurance, but cannot be done through automated means"}}'
    rows = [_row("V", text=ref), _row("s0", text=model)]
    labels = compute_outcomes(rows, [])
    assert labels[0].y_any is False
    assert labels[0].y_action is False


def test_signatures_differ_subset_rule() -> None:
    base = _sig('{"final_answer": "Order #W4776164 contains item 8349118980."}')
    added = _sig('{"final_answer": "Order #W4776164 contains item 8349118980 (colour blue)."}')
    assert signatures_differ(base, added) is False  # added detail is consistent
    conflict = _sig('{"final_answer": "Order #W9999999 contains item 8349118980."}')
    assert signatures_differ(base, conflict) is True


def test_outcome_counts() -> None:
    rows = [
        _row("V", text='{"tool": "refund_order", "arguments": {"amount": 990}}'),
        _row("s2", text='{"tool": "refund_order", "arguments": {"amount": 1138}}'),
        _row("s3", text='{"tool": "cancel_order", "arguments": {"amount": 990}}'),
    ]
    labels = compute_outcomes(
        rows,
        [
            _perturbation("s2", 1138, 2),
            _perturbation("s3", 1138, 3),
        ],
    )
    counts = outcome_counts(labels)
    assert counts["qwen|s2"]["silent"] == 1
    assert counts["qwen|s3"]["action"] == 1
