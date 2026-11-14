"""Conditional-logistic severity slope with prefix-cluster inference.

The implementation is pure Python so the analysis does not depend on a
particular statsmodels/scipy build. A stratum contributes the conditional
likelihood of its observed outcome set given the number of events; with four
severity rows per prefix the subset enumeration is exact.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations

SEVERITY = {"s0": 0, "s1": 1, "s2": 2, "s3": 3}


@dataclass(frozen=True, slots=True)
class SlopeRow:
    """One severity observation in a conditional-logit stratum."""

    group_id: str
    cluster_id: str
    model_id: str
    severity: int
    y: int


@dataclass(slots=True)
class SlopeResult:
    """Point estimate and inference for one slope."""

    beta: float
    se_model: float
    se_cluster: float
    z: float
    p_value: float
    n_groups: int
    n_rows: int
    converged: bool

    def as_dict(self) -> dict[str, float | int | bool]:
        return {
            "beta": self.beta,
            "se_model": self.se_model,
            "se_cluster": self.se_cluster,
            "z": self.z,
            "p_value": self.p_value,
            "n_groups": self.n_groups,
            "n_rows": self.n_rows,
            "converged": self.converged,
        }


@dataclass(frozen=True, slots=True)
class _Group:
    cluster_id: str
    s_values: tuple[float, ...]
    event_sum: float
    subset_sums: tuple[float, ...]


def _logsumexp(values: list[float]) -> float:
    maximum = max(values)
    return maximum + math.log(sum(math.exp(value - maximum) for value in values))


def _prepare(rows: Iterable[SlopeRow]) -> list[_Group]:
    grouped: dict[str, list[SlopeRow]] = defaultdict(list)
    for row in rows:
        grouped[row.group_id].append(row)
    groups: list[_Group] = []
    for group_rows in grouped.values():
        events = [row for row in group_rows if row.y == 1]
        if not events or len(events) == len(group_rows):
            continue
        s_values = tuple(float(row.severity) for row in group_rows)
        event_indices = tuple(index for index, row in enumerate(group_rows) if row.y == 1)
        event_sum = sum(s_values[index] for index in event_indices)
        subset_sums = tuple(
            sum(s_values[index] for index in subset)
            for subset in combinations(range(len(group_rows)), len(event_indices))
        )
        groups.append(
            _Group(
                cluster_id=group_rows[0].cluster_id,
                s_values=s_values,
                event_sum=event_sum,
                subset_sums=subset_sums,
            )
        )
    return groups


def _fit(groups: list[_Group], *, max_iter: int = 100, tol: float = 1e-8) -> SlopeResult:
    if not groups:
        return SlopeResult(0.0, math.inf, math.inf, 0.0, 1.0, 0, 0, False)
    beta = 0.0
    converged = False
    for _ in range(max_iter):
        gradient = 0.0
        hessian = 0.0
        for group in groups:
            values = [beta * value for value in group.subset_sums]
            log_z = _logsumexp(values)
            probabilities = [math.exp(value - log_z) for value in values]
            expectation = sum(prob * value for prob, value in zip(probabilities, group.subset_sums, strict=True))
            variance = sum(
                prob * (value - expectation) ** 2
                for prob, value in zip(probabilities, group.subset_sums, strict=True)
            )
            gradient += group.event_sum - expectation
            hessian -= variance
        if abs(hessian) < 1e-12:
            break
        step = gradient / (-hessian)
        beta += step
        if abs(step) < tol:
            converged = True
            break

    gradient = 0.0
    hessian = 0.0
    cluster_scores: dict[str, float] = defaultdict(float)
    for group in groups:
        values = [beta * value for value in group.subset_sums]
        log_z = _logsumexp(values)
        probabilities = [math.exp(value - log_z) for value in values]
        expectation = sum(prob * value for prob, value in zip(probabilities, group.subset_sums, strict=True))
        variance = sum(
            prob * (value - expectation) ** 2
            for prob, value in zip(probabilities, group.subset_sums, strict=True)
        )
        score = group.event_sum - expectation
        gradient += score
        hessian -= variance
        cluster_scores[group.cluster_id] += score
    information = -hessian
    if information <= 0:
        return SlopeResult(beta, math.inf, math.inf, 0.0, 1.0, len(groups), sum(len(g.s_values) for g in groups), False)
    se_model = math.sqrt(1.0 / information)
    se_cluster = math.sqrt(sum(score * score for score in cluster_scores.values())) / information
    se = se_cluster if se_cluster > 0 else se_model
    z = beta / se if se > 0 else 0.0
    p_value = math.erfc(abs(z) / math.sqrt(2.0))
    return SlopeResult(
        beta=beta,
        se_model=se_model,
        se_cluster=se_cluster,
        z=z,
        p_value=p_value,
        n_groups=len(groups),
        n_rows=sum(len(group.s_values) for group in groups),
        converged=converged or abs(gradient) < 1e-6,
    )


def conditional_logit(rows: Iterable[SlopeRow]) -> SlopeResult:
    """Fit the severity slope with prefix-cluster standard errors."""
    return _fit(_prepare(rows))


def rows_from_outcomes(labels: Iterable[object]) -> list[SlopeRow]:
    """Build slope rows from OutcomeLabels-like objects."""
    rows: list[SlopeRow] = []
    for label in labels:
        arm = label.arm
        if arm not in SEVERITY:
            continue
        prefix_id = str(label.prefix_id)
        model_id = str(label.model_id)
        rows.append(
            SlopeRow(
                group_id=f"{prefix_id}|{model_id}",
                cluster_id=prefix_id,
                model_id=model_id,
                severity=SEVERITY[arm],
                y=int(bool(label.y_any)),
            )
        )
    return rows


def per_model_slopes(rows: Iterable[SlopeRow]) -> dict[str, SlopeResult]:
    """Fit one slope per model, clustering by prefix."""
    materialized = list(rows)
    models = sorted({row.model_id for row in materialized})
    results: dict[str, SlopeResult] = {}
    for model in models:
        model_rows = [
            SlopeRow(
                group_id=row.cluster_id,
                cluster_id=row.cluster_id,
                model_id=row.model_id,
                severity=row.severity,
                y=row.y,
            )
            for row in materialized
            if row.model_id == model
        ]
        results[model] = _fit(_prepare(model_rows))
    return results


def pooled_slope(rows: Iterable[SlopeRow]) -> SlopeResult:
    """Fit the pooled slope, stratifying by prefix x model and clustering by prefix."""
    return _fit(_prepare(list(rows)))


@dataclass(slots=True)
class BootstrapResult:
    """Prefix-cluster bootstrap summary."""

    beta_mean: float
    ci_low: float
    ci_high: float
    p_one_sided: float
    p_two_sided: float
    replicates: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "beta_mean": self.beta_mean,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "p_one_sided": self.p_one_sided,
            "p_two_sided": self.p_two_sided,
            "replicates": self.replicates,
        }


def bootstrap_slope(
    rows: Iterable[SlopeRow],
    *,
    replicates: int = 2000,
    seed: int = 20261108,
    pooled: bool = True,
) -> BootstrapResult:
    """Percentile bootstrap clustered by prefix."""
    materialized = list(rows)
    clusters: dict[str, list[SlopeRow]] = defaultdict(list)
    for row in materialized:
        clusters[row.cluster_id].append(row)
    keys = sorted(clusters)
    if not keys:
        return BootstrapResult(0.0, 0.0, 0.0, 1.0, 1.0, 0)
    rng = random.Random(seed)
    estimates: list[float] = []
    for replicate in range(replicates):
        sampled = [rng.choice(keys) for _ in keys]
        resampled: list[SlopeRow] = []
        for index, key in enumerate(sampled):
            for row in clusters[key]:
                resampled.append(
                    SlopeRow(
                        group_id=f"{row.group_id}|b{replicate}|{index}",
                        cluster_id=f"{row.cluster_id}|b{replicate}|{index}",
                        model_id=row.model_id,
                        severity=row.severity,
                        y=row.y,
                    )
                )
        result = _fit(_prepare(resampled)) if pooled else _fit(_prepare(resampled))
        if math.isfinite(result.beta):
            estimates.append(result.beta)
    if not estimates:
        return BootstrapResult(0.0, 0.0, 0.0, 1.0, 1.0, 0)
    estimates.sort()
    low = estimates[max(0, int(0.025 * len(estimates)) - 1)]
    high = estimates[min(len(estimates) - 1, int(0.975 * len(estimates)))]
    p_one = (1 + sum(value <= 0 for value in estimates)) / (len(estimates) + 1)
    p_two = min(1.0, 2.0 * min(p_one, 1.0 - p_one + 1.0 / (len(estimates) + 1)))
    return BootstrapResult(
        beta_mean=sum(estimates) / len(estimates),
        ci_low=low,
        ci_high=high,
        p_one_sided=p_one,
        p_two_sided=p_two,
        replicates=len(estimates),
    )


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjustment across a family."""
    ordered = sorted(p_values.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, (key, value) in enumerate(ordered):
        candidate = min(1.0, value * (total - index))
        running = max(running, candidate)
        adjusted[key] = running
    return adjusted
