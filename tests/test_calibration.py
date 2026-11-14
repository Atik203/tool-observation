"""Calibration gate tests."""

from __future__ import annotations

from toolobs.infer.calibration import evaluate_all_models, evaluate_calibration
from toolobs.schemas import LedgerRow


def _row(
    prefix: str,
    arm: str,
    *,
    model: str = "qwen",
    parsed: bool = True,
    status: str = "ok",
    signature: str = "v",
) -> LedgerRow:
    return LedgerRow(
        run_id="cal",
        model_id=model,
        prefix_id=prefix,
        arm=arm,
        step=0,
        prompt_hash="p",
        output_text="{}",
        parsed=parsed,
        latency_ms=1.0,
        cost_usd=0.0,
        timestamp_utc="2026-11-15T00:00:00+00:00",
        stage="calibration",
        parser_status=status,
        signature_hash=signature,
    )


def _frame(prefixes: int = 10, s0_signature: str = "v", s3_switches: int = 5):
    rows = []
    for index in range(prefixes):
        prefix = f"p{index}"
        s3_signature = "x" if index < s3_switches else "v"
        rows.extend(
            [
                _row(prefix, "V", signature="v"),
                _row(prefix, "s0", signature=s0_signature),
                _row(prefix, "s1", signature="v"),
                _row(prefix, "s2", signature="x"),
                _row(prefix, "s3", signature=s3_signature),
            ]
        )
    return rows


def test_calibration_passes_when_gates_met() -> None:
    result = evaluate_calibration(_frame(), "qwen")
    assert result.passed is True
    assert result.parse_rate == 1.0
    assert result.placebo_jitter == 0.0
    assert result.s3_switch_rate == 0.5
    assert result.missing == []


def test_calibration_fails_on_low_parse_rate() -> None:
    rows = _frame()
    for row in rows[:10]:
        row.parsed = False
        row.parser_status = "parse_error"
        row.signature_hash = ""
    result = evaluate_calibration(rows, "qwen")
    assert result.passed is False
    assert result.gates["parse_rate"] is False


def test_calibration_fails_on_high_placebo_jitter() -> None:
    result = evaluate_calibration(_frame(s0_signature="x"), "qwen")
    assert result.placebo_jitter == 1.0
    assert result.gates["placebo_jitter"] is False


def test_calibration_fails_when_s3_is_a_floor() -> None:
    result = evaluate_calibration(_frame(s3_switches=0), "qwen")
    assert result.s3_switch_rate == 0.0
    assert result.gates["s3_switch_min"] is False


def test_calibration_fails_on_refusal_rate() -> None:
    rows = _frame()
    for row in rows[:3]:
        row.parsed = False
        row.parser_status = "refusal"
        row.signature_hash = ""
    result = evaluate_calibration(rows, "qwen")
    assert result.refusal_rate > 0.05
    assert result.gates["refusal_rate"] is False


def test_missing_reference_arm_fails_completeness() -> None:
    rows = [row for row in _frame() if not (row.prefix_id == "p0" and row.arm == "V")]
    result = evaluate_calibration(rows, "qwen")
    assert "p0:V" in result.missing
    assert result.gates["complete"] is False


def test_evaluate_all_models_requires_every_model() -> None:
    rows = _frame()
    for index in range(10):
        prefix = f"q{index}"
        rows.extend(
            [
                _row(prefix, "V", model="mistral", signature="v"),
                _row(prefix, "s0", model="mistral", signature="v"),
                _row(prefix, "s1", model="mistral", signature="v"),
                _row(prefix, "s2", model="mistral", signature="x"),
                _row(prefix, "s3", model="mistral", signature="x" if index < 5 else "v"),
            ]
        )
    report = evaluate_all_models(rows, ["qwen", "mistral"])
    assert report["passed"] is True
    assert len(report["models"]) == 2
