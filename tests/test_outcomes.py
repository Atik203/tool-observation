"""Automatic outcome-label tests."""

from __future__ import annotations

from toolobs.analysis.outcomes import (
    compute_outcomes,
    flag_detected,
    outcome_counts,
)
from toolobs.schemas import LedgerRow, PerturbationRecord


def _row(
    arm: str,
    *,
    prefix: str = "p1",
    signature: str = "v",
    tool: str = "get_order_details",
    arguments: dict | None = None,
    output: str = "{}",
    parsed: bool = True,
) -> LedgerRow:
    return LedgerRow(
        run_id="run",
        model_id="qwen",
        prefix_id=prefix,
        arm=arm,
        step=0,
        prompt_hash="p",
        output_text=output,
        parsed=parsed,
        latency_ms=1.0,
        cost_usd=0.0,
        timestamp_utc="2026-11-15T00:00:00+00:00",
        stage="main",
        parser_status="ok" if parsed else "parse_error",
        signature_hash=signature,
        decision_json=__import__("json").dumps(
            {"tool": tool, "arguments": arguments or {"order_id": "#w1"}}
        ),
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


def test_silent_propagation_when_false_value_appears_without_action_or_flag() -> None:
    rows = [
        _row("V"),
        _row("s2", output="The order is pending.", signature="v"),
    ]
    labels = compute_outcomes(rows, [_perturbation("s2", "pending", 2)])
    label = labels[0]
    assert label.y_any is False
    assert label.y_action is False
    assert label.y_flag is False
    assert label.y_silent is True


def test_flag_blocks_silent_propagation() -> None:
    rows = [
        _row("V"),
        _row("s2", output="The order is pending; that looks inconsistent.", signature="v"),
    ]
    label = compute_outcomes(rows, [_perturbation("s2", "pending", 2)])[0]
    assert label.y_flag is True
    assert label.y_silent is False


def test_action_switch() -> None:
    rows = [
        _row("V"),
        _row(
            "s2",
            tool="cancel_pending_order",
            arguments={"order_id": "#w1"},
            signature="a",
            output="Cancelling the order.",
        ),
    ]
    label = compute_outcomes(rows, [_perturbation("s2", "pending", 2)])[0]
    assert label.y_action is True
    assert label.y_any is True
    assert label.y_silent is False


def test_s1_is_not_scored_for_silent_propagation() -> None:
    rows = [
        _row("V"),
        _row("s1", output="The note says fragile.", signature="v"),
    ]
    label = compute_outcomes(rows, [_perturbation("s1", "fragile", 1)])[0]
    assert label.y_silent is False


def test_outcome_counts() -> None:
    rows = [
        _row("V"),
        _row("s2", output="pending", signature="v"),
        _row("s3", tool="cancel_pending_order", signature="a"),
    ]
    labels = compute_outcomes(
        rows,
        [
            _perturbation("s2", "pending", 2),
            _perturbation("s3", "pending", 3),
        ],
    )
    counts = outcome_counts(labels)
    assert counts["qwen|s2"]["silent"] == 1
    assert counts["qwen|s3"]["action"] == 1
