"""Recovery estimation: discrete-time exponential, Kaplan-Meier, RMST, Weibull.

The primary recovery endpoint is the transient s=3 risk set. The exponential
fit is the preregistered model; Kaplan-Meier and RMST are reported regardless.
The Weibull shape test is a grid-search likelihood-ratio check, adequate for the
four-step horizon and independent of optional survival packages.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

from ..schemas import RecoveryEvent


@dataclass(slots=True)
class ExponentialFit:
    """Discrete-time constant-hazard fit."""

    n: int
    events: int
    censored: int
    exposure: float
    hazard: float
    mu: float
    half_life: float | None

    def as_dict(self) -> dict[str, float | int | None]:
        return {
            "n": self.n,
            "events": self.events,
            "censored": self.censored,
            "exposure": self.exposure,
            "hazard": self.hazard,
            "mu": self.mu,
            "half_life": self.half_life,
        }


def fit_exponential(events: Iterable[RecoveryEvent], *, horizon: int = 4) -> ExponentialFit:
    """Fit the constant per-step hazard by maximum likelihood."""
    materialized = list(events)
    event_count = sum(1 for event in materialized if not event.censored)
    censored = len(materialized) - event_count
    exposure = sum(
        event.recovered_step if not event.censored and event.recovered_step is not None else horizon
        for event in materialized
    )
    hazard = (event_count / exposure) if exposure > 0 else 0.0
    if hazard <= 0.0:
        mu = 0.0
        half_life = None
    else:
        clipped = min(hazard, 1.0 - 1e-9)
        mu = -math.log(1.0 - clipped)
        half_life = math.log(2.0) / mu if mu > 0 else None
    return ExponentialFit(
        n=len(materialized),
        events=event_count,
        censored=censored,
        exposure=exposure,
        hazard=hazard,
        mu=mu,
        half_life=half_life,
    )


def kaplan_meier(events: Iterable[RecoveryEvent], *, horizon: int = 4) -> list[dict[str, float | int]]:
    """Discrete Kaplan-Meier survival at steps 1..horizon."""
    materialized = list(events)
    survival = 1.0
    rows: list[dict[str, float | int]] = []
    for step in range(1, horizon + 1):
        at_risk = 0
        observed = 0
        for event in materialized:
            end = event.recovered_step if not event.censored else horizon
            if end is None:
                end = horizon
            if end >= step:
                at_risk += 1
            if not event.censored and event.recovered_step == step:
                observed += 1
        if at_risk:
            survival *= 1.0 - observed / at_risk
        rows.append(
            {
                "step": step,
                "at_risk": at_risk,
                "events": observed,
                "survival": survival,
            }
        )
    return rows


def rmst(events: Iterable[RecoveryEvent], *, horizon: int = 4) -> float:
    """Restricted mean survival time over the discrete horizon."""
    return sum(float(row["survival"]) for row in kaplan_meier(events, horizon=horizon))


def _weibull_loglik(
    times: list[float],
    censored: list[bool],
    shape: float,
    scale: float,
) -> float:
    total = 0.0
    for time, is_censored in zip(times, censored, strict=True):
        ratio = time / scale
        if not is_censored:
            total += math.log(shape) - math.log(scale) + (shape - 1.0) * math.log(ratio)
        total -= ratio**shape
    return total


def weibull_lrt(events: Iterable[RecoveryEvent], *, horizon: int = 4) -> dict[str, float]:
    """Grid-search Weibull shape and test shape=1 by likelihood ratio."""
    materialized = list(events)
    times = [
        float(event.recovered_step if not event.censored and event.recovered_step else horizon)
        for event in materialized
    ]
    censored = [event.censored for event in materialized]
    if not times:
        return {"shape": 1.0, "scale": 1.0, "lrt": 0.0, "p_value": 1.0}
    best = (-math.inf, 1.0, 1.0)
    for shape_index in range(4, 61):  # 0.2 .. 3.0
        shape = shape_index / 20.0
        for scale_index in range(5, 201):  # 0.5 .. 20.0
            scale = scale_index / 10.0
            value = _weibull_loglik(times, censored, shape, scale)
            if value > best[0]:
                best = (value, shape, scale)
    null = max(
        _weibull_loglik(times, censored, 1.0, scale_index / 10.0)
        for scale_index in range(5, 201)
    )
    lrt = max(0.0, 2.0 * (best[0] - null))
    p_value = math.erfc(math.sqrt(lrt / 2.0))
    return {
        "shape": best[1],
        "scale": best[2],
        "loglik": best[0],
        "null_loglik": null,
        "lrt": lrt,
        "p_value": p_value,
    }


def recovery_report(events: Iterable[RecoveryEvent], *, horizon: int = 4) -> dict[str, object]:
    """Full recovery summary for one endpoint."""
    materialized = list(events)
    return {
        "n": len(materialized),
        "exponential": fit_exponential(materialized, horizon=horizon).as_dict(),
        "kaplan_meier": kaplan_meier(materialized, horizon=horizon),
        "rmst": rmst(materialized, horizon=horizon),
        "weibull": weibull_lrt(materialized, horizon=horizon),
    }
