"""Recovery estimator tests."""

from __future__ import annotations

from toolobs.analysis.recovery import (
    fit_exponential,
    kaplan_meier,
    recovery_report,
    rmst,
    weibull_lrt,
)
from toolobs.schemas import RecoveryEvent


def _event(step: int | None, censored: bool = False, last_step: int = 0) -> RecoveryEvent:
    return RecoveryEvent(
        prefix_id="p",
        model_id="qwen",
        regime="transient",
        severity=3,
        horizon=4,
        recovered_step=step,
        endpoint="R1",
        censored=censored,
        last_step=last_step,
    )


def test_exponential_fit_with_recoveries() -> None:
    events = [_event(1), _event(2), _event(3), _event(4), _event(None, censored=True)]
    fit = fit_exponential(events)
    assert fit.n == 5
    assert fit.events == 4
    assert fit.censored == 1
    assert fit.hazard > 0
    assert fit.half_life is not None and fit.half_life > 0


def test_exponential_fit_all_censored() -> None:
    fit = fit_exponential([_event(None, censored=True), _event(None, censored=True)])
    assert fit.events == 0
    assert fit.hazard == 0.0
    assert fit.half_life is None


def test_kaplan_meier_is_monotone() -> None:
    rows = kaplan_meier([_event(1), _event(2), _event(3), _event(4)])
    survival = [row["survival"] for row in rows]
    assert survival == sorted(survival, reverse=True)
    assert 0.0 <= survival[-1] <= 1.0


def test_censoring_uses_last_follow_up() -> None:
    """A sequence that ends early must leave the risk set at its last observed step."""
    events = [
        _event(1),
        _event(None, censored=True, last_step=1),
        _event(None, censored=True, last_step=4),
    ]
    rows = kaplan_meier(events)
    assert rows[0]["at_risk"] == 3
    assert rows[1]["at_risk"] == 1  # early terminator is no longer at risk
    assert rows[1]["survival"] == rows[0]["survival"]
    fit = fit_exponential(events)
    assert fit.exposure == 1 + 1 + 4


def test_rmst_is_finite() -> None:
    value = rmst([_event(1), _event(2), _event(None, censored=True)])
    assert 0.0 <= value <= 4.0


def test_weibull_lrt_returns_valid_p_value() -> None:
    result = weibull_lrt([_event(1), _event(2), _event(3), _event(4), _event(None, censored=True)])
    assert 0.0 <= result["p_value"] <= 1.0
    assert result["shape"] > 0
    assert result["scale"] > 0


def test_recovery_report_shape() -> None:
    report = recovery_report([_event(1), _event(2)])
    assert set(report) == {"n", "exponential", "kaplan_meier", "rmst", "weibull"}
    assert report["n"] == 2
