"""Recovery event replay tests."""

from __future__ import annotations

from toolobs.analysis.recovery_events import replay_recovery_events
from toolobs.infer.parse_output import parse_decision, signature_hash, signature_json
from toolobs.schemas import LedgerRow


def _row(prefix: str, arm: str, step: int, text: str) -> LedgerRow:
    parsed = parse_decision(text)
    return LedgerRow(
        run_id="t",
        model_id="m0",
        prefix_id=prefix,
        arm=arm,
        step=step,
        prompt_hash="p",
        output_text=text,
        parsed=parsed.parsed,
        latency_ms=1.0,
        cost_usd=0.0,
        timestamp_utc="2026-11-15T00:00:00+00:00",
        parser_status=parsed.status,
        signature_hash=signature_hash(parsed) if parsed.parsed else "",
        decision_json=signature_json(parsed) if parsed.parsed else "",
    )


TOOL = '{"tool": "get_order_details", "arguments": {"order_id": "#W1"}}'
OTHER = '{"tool": "cancel_order", "arguments": {"order_id": "#W1"}}'


def test_replay_covers_r1_r2_censored_and_final_answer() -> None:
    rows = [
        # p0: step 2 flags -> R2 at step 2
        _row("p0", "s3", 1, OTHER),
        _row("p0", "s3", 2, '{"final_answer": "There is a discrepancy in this observation."}'),
        # p1: step 1 matches the reference signature -> R1 at step 1
        _row("p1", "s3", 1, TOOL),
        # p2: unparsed step -> censored
        _row("p2", "s3", 1, "not json"),
        # p3: final answer without recovery -> censored
        _row("p3", "s3", 1, '{"final_answer": "All done."}'),
    ]
    reference_hashes = {
        "p1": signature_hash(parse_decision(TOOL)),
        "p0": "different",
        "p2": "different",
        "p3": "different",
    }
    events = replay_recovery_events(
        rows,
        reference_hashes,
        model_id="m0",
        regime="persistent",
        state_hashes={("p0", 3): "state-hash-p0"},
    )
    by_prefix = {event.prefix_id: event for event in events}
    assert (by_prefix["p0"].recovered_step, by_prefix["p0"].endpoint) == (2, "R2")
    assert (by_prefix["p1"].recovered_step, by_prefix["p1"].endpoint) == (1, "R1")
    assert by_prefix["p2"].censored is True
    assert by_prefix["p3"].censored is True
    assert by_prefix["p0"].state_hash == "state-hash-p0"
    assert by_prefix["p1"].state_hash == ""
