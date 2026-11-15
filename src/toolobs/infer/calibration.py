"""G1 calibration gate evaluation.

The calibration run is a harness test, not a result. Per model, it checks parse
rate, placebo jitter (s=0 vs V), s=3 switch rate, and format refusal.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from ..schemas import LedgerRow

DEFAULT_GATES = {
    "parse_rate_min": 0.95,
    "placebo_jitter_max": 0.20,
    "negative_control_jitter_max": 0.20,
    "s3_switch_min": 0.10,
    "s3_switch_max": 0.80,
    "refusal_rate_max": 0.05,
}


@dataclass(slots=True)
class CalibrationResult:
    """Per-model calibration statistics and gate outcome."""

    model_id: str
    total: int
    parsed: int
    parse_rate: float
    refusal_rate: float
    placebo_jitter: float | None
    negative_control_jitter: float | None
    s3_switch_rate: float | None
    gates: dict[str, bool]
    passed: bool
    missing: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "total": self.total,
            "parsed": self.parsed,
            "parse_rate": self.parse_rate,
            "refusal_rate": self.refusal_rate,
            "placebo_jitter": self.placebo_jitter,
            "negative_control_jitter": self.negative_control_jitter,
            "s3_switch_rate": self.s3_switch_rate,
            "gates": self.gates,
            "passed": self.passed,
            "missing": self.missing,
        }


def _rate(numerator: int, denominator: int) -> float | None:
    return (numerator / denominator) if denominator else None


def evaluate_calibration(
    rows: Iterable[LedgerRow],
    model_id: str,
    *,
    gates: dict[str, float] | None = None,
) -> CalibrationResult:
    """Evaluate one model's calibration ledger against the G1 gates."""
    thresholds = dict(DEFAULT_GATES)
    thresholds.update(gates or {})
    model_rows = [row for row in rows if row.model_id == model_id]
    total = len(model_rows)
    parsed = sum(1 for row in model_rows if row.parsed)
    refusals = sum(1 for row in model_rows if row.parser_status == "refusal")
    parse_rate = _rate(parsed, total) or 0.0
    refusal_rate = _rate(refusals, total) or 0.0

    by_prefix: dict[str, dict[str, LedgerRow]] = defaultdict(dict)
    for row in model_rows:
        by_prefix[row.prefix_id][row.arm] = row

    placebo: list[bool] = []
    negative: list[bool] = []
    s3: list[bool] = []
    missing: list[str] = []
    for prefix_id, arms in sorted(by_prefix.items()):
        reference = arms.get("V")
        if reference is None or not reference.parsed or not reference.signature_hash:
            missing.append(f"{prefix_id}:V")
            continue
        for arm, bucket in (("s0", placebo), ("s3", s3)):
            row = arms.get(arm)
            if row is None or not row.parsed or not row.signature_hash:
                missing.append(f"{prefix_id}:{arm}")
                continue
            bucket.append(row.signature_hash != reference.signature_hash)
        s0_row = arms.get("s0")
        s1_row = arms.get("s1")
        if (
            s0_row is not None
            and s1_row is not None
            and s0_row.parsed
            and s1_row.parsed
            and s0_row.signature_hash
            and s1_row.signature_hash
        ):
            negative.append(s1_row.signature_hash != s0_row.signature_hash)

    placebo_jitter = _rate(sum(placebo), len(placebo))
    negative_control_jitter = _rate(sum(negative), len(negative))
    s3_switch = _rate(sum(s3), len(s3))
    checks = {
        "parse_rate": parse_rate >= thresholds["parse_rate_min"],
        "placebo_jitter": placebo_jitter is not None
        and placebo_jitter <= thresholds["placebo_jitter_max"],
        "negative_control_jitter": negative_control_jitter is not None
        and negative_control_jitter <= thresholds["negative_control_jitter_max"],
        "s3_switch_min": s3_switch is not None
        and s3_switch >= thresholds["s3_switch_min"],
        "s3_switch_max": s3_switch is not None
        and s3_switch <= thresholds["s3_switch_max"],
        "refusal_rate": refusal_rate < thresholds["refusal_rate_max"],
        "complete": not missing,
    }
    # Completeness is diagnostic. The format-controlled negative control (s0 vs
    # s1) is the placebo gate; V vs s0 is reported as format sensitivity.
    gate_keys = (
        "parse_rate",
        "negative_control_jitter",
        "s3_switch_min",
        "s3_switch_max",
        "refusal_rate",
    )
    return CalibrationResult(
        model_id=model_id,
        total=total,
        parsed=parsed,
        parse_rate=parse_rate,
        refusal_rate=refusal_rate,
        placebo_jitter=placebo_jitter,
        negative_control_jitter=negative_control_jitter,
        s3_switch_rate=s3_switch,
        gates=checks,
        passed=all(checks[key] for key in gate_keys),
        missing=missing[:20],
    )


def evaluate_all_models(
    rows: Iterable[LedgerRow],
    model_ids: Iterable[str],
    *,
    gates: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Evaluate every model and return a JSON-ready report."""
    materialized = list(rows)
    results = [
        evaluate_calibration(materialized, model_id, gates=gates)
        for model_id in model_ids
    ]
    by_arm = Counter((row.model_id, row.arm) for row in materialized)
    return {
        "models": [result.as_dict() for result in results],
        "passed": all(result.passed for result in results),
        "by_arm": {
            f"{model}|{arm}": count for (model, arm), count in sorted(by_arm.items())
        },
    }
