#!/usr/bin/env python
"""Stage 19 - P6.3 row-level refits from the local main ledgers.

The Q1 panel register (V4/V5, correction C1) asked for row-level answers to
three point-only or asymptotically justified analyses.  All inputs are already
on this machine under ``data/runs/main`` (13,200 step-0 rows, recovery step
ledgers, recovery events); nothing is generated and no GPU is used.

What this script computes:

- severity functional form: exact conditional-logit LRTs for the quadratic and
  categorical severity terms, with a prefix-cluster null parametric bootstrap
  (the 800 prefixes are the resampling unit, all three model groups travel
  together) and a cluster-robust Wald companion; Holm over the six per-model
  tests with an explicit dependence note;
- severity reclassification: audited-only and rate-extrapolated refits that
  move donor-unused critical rows to s=0, with Rubin intervals from multiple
  imputation (replaces the old point-only dilution table);
- missingness: decomposition of the 525/9,600 missing cells, logistic IPW for
  arm rates and risk differences, a task x model x arm post-stratified check,
  a weighted conditional-logit slope, and Manski bounds (including extreme
  imputations for the slope);
- recovery: Aalen-Johansen cumulative incidence on the v2 semantic risk set
  with terminal non-recovery as a competing event, plus exact paired McNemar
  tests (transient s2 vs s3 and pairwise model comparisons).

Every input file is hashed (SHA-256) into the artifact so P6.5 can publish the
provenance.  Output is regenerable and gitignored, like every analysis JSON.

CPU-only, stdlib-only beyond the ``toolobs`` package.  Runtime target is about
two minutes on the local machine.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, replace
from itertools import combinations
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.analysis.outcomes import compute_outcomes, flag_detected  # noqa: E402
from toolobs.analysis.recovery import kaplan_meier  # noqa: E402
from toolobs.analysis.slope import holm_adjust  # noqa: E402
from toolobs.config import load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl_dicts  # noqa: E402
from toolobs.infer.ledger import read_ledger  # noqa: E402
from toolobs.infer.parse_output import signature_from_json, signatures_differ  # noqa: E402
from toolobs.paths import (  # noqa: E402
    ANALYSIS_DIR,
    AUDIT_DIR,
    MANIFEST_DIR,
    RUNS_DIR,
    resolve_repo_path,
)
from toolobs.provenance import git_commit, repo_relative, utc_now, write_json  # noqa: E402
from toolobs.schemas import PerturbationRecord, RecoveryEvent  # noqa: E402

PROVENANCE = "multi-role agent panel, author-overseen"
SEED = 20261108
Z95 = 1.96
HORIZON = 4
ARMS = ("s0", "s1", "s2", "s3")
SEVERITY = {"s0": 0, "s1": 1, "s2": 2, "s3": 3}
S2S3 = ("s2", "s3")
LINEAR, QUADRATIC, CATEGORICAL, REALIZED = 0, 1, 2, 3
PARAMS = {LINEAR: 1, QUADRATIC: 2, CATEGORICAL: 3, REALIZED: 4}

# Runtime-bounded bootstrap budgets.  The pooled test is the primary; the six
# per-model tests are the multiplicity family.
BOOT_POOLED_DEFAULT = 150
BOOT_MODEL_DEFAULT = 40
MI_DEFAULT = 40
IPW_SLOPE_BOOT_DEFAULT = 50
IPW_RATE_BOOT_DEFAULT = 500
RECOVERY_BOOT_DEFAULT = 2000


# ---------------------------------------------------------------------------
# Exact conditional-logit engine
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Group:
    """One conditional-logit stratum with precomputed subset sums."""

    key: str
    cluster: str
    severity: tuple[int, ...]
    y: tuple[int, ...]
    subsets: tuple[tuple[int, ...], ...]
    obs: int
    s: tuple[float, ...]
    s2: tuple[float, ...]
    c1: tuple[float, ...]
    c2: tuple[float, ...]
    c3: tuple[float, ...]
    c4: tuple[float, ...]
    ev_s: float
    ev_s2: float
    ev_c1: float
    ev_c2: float
    ev_c3: float
    ev_c4: float


def make_group(
    key: str, cluster: str, severity: Iterable[int], y: Iterable[int]
) -> Group | None:
    """Build one stratum; return None when the outcome has no variation."""
    sev = tuple(int(value) for value in severity)
    outcomes = tuple(int(value) for value in y)
    k = sum(outcomes)
    if k == 0 or k == len(outcomes):
        return None
    subsets = tuple(combinations(range(len(outcomes)), k))
    s = tuple(float(sum(sev[i] for i in subset)) for subset in subsets)
    s2 = tuple(float(sum(sev[i] * sev[i] for i in subset)) for subset in subsets)
    c1 = tuple(float(sum(1 for i in subset if sev[i] == 1)) for subset in subsets)
    c2 = tuple(float(sum(1 for i in subset if sev[i] == 2)) for subset in subsets)
    c3 = tuple(float(sum(1 for i in subset if sev[i] == 3)) for subset in subsets)
    c4 = tuple(float(sum(1 for i in subset if sev[i] == 4)) for subset in subsets)
    observed = tuple(i for i, value in enumerate(outcomes) if value)
    obs = subsets.index(observed)
    return Group(
        key=key,
        cluster=cluster,
        severity=sev,
        y=outcomes,
        subsets=subsets,
        obs=obs,
        s=s,
        s2=s2,
        c1=c1,
        c2=c2,
        c3=c3,
        c4=c4,
        ev_s=s[obs],
        ev_s2=s2[obs],
        ev_c1=c1[obs],
        ev_c2=c2[obs],
        ev_c3=c3[obs],
        ev_c4=c4[obs],
    )


def groups_from_records(
    records: Iterable[tuple[str, str, str, int, int]],
) -> list[Group]:
    """Build groups from (prefix, model, arm, severity, y) records."""
    grouped: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    for prefix, model, _arm, severity, y in records:
        grouped[(prefix, model)].append((severity, y))
    groups: list[Group] = []
    for (prefix, model) in sorted(grouped):
        values = grouped[(prefix, model)]
        group = make_group(
            f"{prefix}|{model}",
            prefix,
            [v[0] for v in values],
            [v[1] for v in values],
        )
        if group is not None:
            groups.append(group)
    return groups


def groups_by_prefix(groups: Iterable[Group], prefixes: Iterable[str]) -> dict[str, list[Group]]:
    """Bucket groups by prefix, keeping empty buckets for the full design."""
    buckets: dict[str, list[Group]] = {prefix: [] for prefix in prefixes}
    for group in groups:
        buckets.setdefault(group.cluster, []).append(group)
    return buckets


def _logsumexp(values: list[float]) -> float:
    maximum = max(values)
    return maximum + math.log(sum(math.exp(value - maximum) for value in values))


def _solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting for tiny systems."""
    n = len(vector)
    work = [matrix[i][:] + [vector[i]] for i in range(n)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) < 1e-14:
            work[column][column] += 1e-10
            pivot = column
        work[column], work[pivot] = work[pivot], work[column]
        divisor = work[column][column]
        for j in range(column, n + 1):
            work[column][j] /= divisor
        for row in range(n):
            if row == column:
                continue
            factor = work[row][column]
            if factor:
                for j in range(column, n + 1):
                    work[row][j] -= factor * work[column][j]
    return [work[i][n] for i in range(n)]


def _inverse(matrix: list[list[float]]) -> list[list[float]]:
    """Gauss-Jordan inverse for the 1x1 to 3x3 matrices used here."""
    n = len(matrix)
    work = [
        matrix[i][:] + [1.0 if i == j else 0.0 for j in range(n)]
        for i in range(n)
    ]
    for column in range(n):
        pivot = max(range(column, n), key=lambda row: abs(work[row][column]))
        if abs(work[pivot][column]) < 1e-14:
            work[column][column] += 1e-10
            pivot = column
        work[column], work[pivot] = work[pivot], work[column]
        divisor = work[column][column]
        for j in range(2 * n):
            work[column][j] /= divisor
        for row in range(n):
            if row == column:
                continue
            factor = work[row][column]
            if factor:
                for j in range(2 * n):
                    work[row][j] -= factor * work[column][j]
    return [row[n:] for row in work]


def fit_conditional(
    groups: list[Group],
    kind: int,
    *,
    warm: Iterable[float] | None = None,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Fit one exact conditional logit with prefix-cluster covariance.

    ``kind`` is LINEAR (one slope), QUADRATIC (s and s^2), or CATEGORICAL
    (indicators for s=1,2,3 against s=0).  ``weights`` supplies group-level
    inverse-probability weights; with weights the reported likelihood is a
    weighted pseudo-likelihood (used only for the IPW sensitivity, never for a
    reported LRT).
    """
    params = PARAMS[kind]
    beta = list(warm) if warm is not None else [0.0] * params

    def evaluate(current: list[float], need_hessian: bool = True):
        ll = 0.0
        grad = [0.0] * params
        hessian = [[0.0] * params for _ in range(params)]
        if kind == LINEAR:
            slope = current[0]
            for group in groups:
                weight = weights.get(group.key, 1.0) if weights else 1.0
                values = [slope * value for value in group.s]
                log_z = _logsumexp(values)
                probs = [math.exp(value - log_z) for value in values]
                ll += weight * (values[group.obs] - log_z)
                expected = sum(prob * value for prob, value in zip(probs, group.s, strict=True))
                grad[0] += weight * (group.ev_s - expected)
                if need_hessian:
                    variance = sum(
                        prob * (value - expected) ** 2
                        for prob, value in zip(probs, group.s, strict=True)
                    )
                    hessian[0][0] -= weight * variance
        elif kind == QUADRATIC:
            b0, b1 = current
            for group in groups:
                weight = weights.get(group.key, 1.0) if weights else 1.0
                values = [b0 * a + b1 * b for a, b in zip(group.s, group.s2, strict=True)]
                log_z = _logsumexp(values)
                probs = [math.exp(value - log_z) for value in values]
                ll += weight * (values[group.obs] - log_z)
                ex0 = ex1 = 0.0
                for prob, a, b in zip(probs, group.s, group.s2, strict=True):
                    ex0 += prob * a
                    ex1 += prob * b
                grad[0] += weight * (group.ev_s - ex0)
                grad[1] += weight * (group.ev_s2 - ex1)
                if need_hessian:
                    h00 = h01 = h11 = 0.0
                    for prob, a, b in zip(probs, group.s, group.s2, strict=True):
                        d0 = a - ex0
                        d1 = b - ex1
                        h00 += prob * d0 * d0
                        h01 += prob * d0 * d1
                        h11 += prob * d1 * d1
                    hessian[0][0] -= weight * h00
                    hessian[0][1] -= weight * h01
                    hessian[1][0] -= weight * h01
                    hessian[1][1] -= weight * h11
        elif kind == CATEGORICAL:
            b0, b1, b2 = current
            for group in groups:
                weight = weights.get(group.key, 1.0) if weights else 1.0
                values = [
                    b0 * a + b1 * b + b2 * c
                    for a, b, c in zip(group.c1, group.c2, group.c3, strict=True)
                ]
                log_z = _logsumexp(values)
                probs = [math.exp(value - log_z) for value in values]
                ll += weight * (values[group.obs] - log_z)
                ex0 = ex1 = ex2 = 0.0
                for prob, a, b, c in zip(probs, group.c1, group.c2, group.c3, strict=True):
                    ex0 += prob * a
                    ex1 += prob * b
                    ex2 += prob * c
                grad[0] += weight * (group.ev_c1 - ex0)
                grad[1] += weight * (group.ev_c2 - ex1)
                grad[2] += weight * (group.ev_c3 - ex2)
                if need_hessian:
                    h00 = h01 = h02 = h11 = h12 = h22 = 0.0
                    for prob, a, b, c in zip(
                        probs, group.c1, group.c2, group.c3, strict=True
                    ):
                        d0 = a - ex0
                        d1 = b - ex1
                        d2 = c - ex2
                        h00 += prob * d0 * d0
                        h01 += prob * d0 * d1
                        h02 += prob * d0 * d2
                        h11 += prob * d1 * d1
                        h12 += prob * d1 * d2
                        h22 += prob * d2 * d2
                    hessian[0][0] -= weight * h00
                    hessian[0][1] -= weight * h01
                    hessian[0][2] -= weight * h02
                    hessian[1][0] -= weight * h01
                    hessian[1][1] -= weight * h11
                    hessian[1][2] -= weight * h12
                    hessian[2][0] -= weight * h02
                    hessian[2][1] -= weight * h12
                    hessian[2][2] -= weight * h22
        else:
            b0, b1, b2, b3 = current
            for group in groups:
                weight = weights.get(group.key, 1.0) if weights else 1.0
                values = [
                    b0 * a + b1 * b + b2 * c + b3 * d
                    for a, b, c, d in zip(
                        group.c1, group.c2, group.c3, group.c4, strict=True
                    )
                ]
                log_z = _logsumexp(values)
                probs = [math.exp(value - log_z) for value in values]
                ll += weight * (values[group.obs] - log_z)
                ex0 = ex1 = ex2 = ex3 = 0.0
                for prob, a, b, c, d in zip(
                    probs, group.c1, group.c2, group.c3, group.c4, strict=True
                ):
                    ex0 += prob * a
                    ex1 += prob * b
                    ex2 += prob * c
                    ex3 += prob * d
                grad[0] += weight * (group.ev_c1 - ex0)
                grad[1] += weight * (group.ev_c2 - ex1)
                grad[2] += weight * (group.ev_c3 - ex2)
                grad[3] += weight * (group.ev_c4 - ex3)
                if need_hessian:
                    h = [[0.0] * 4 for _ in range(4)]
                    for prob, a, b, c, d in zip(
                        probs, group.c1, group.c2, group.c3, group.c4, strict=True
                    ):
                        delta = (a - ex0, b - ex1, c - ex2, d - ex3)
                        for j in range(4):
                            for k in range(j, 4):
                                value = prob * delta[j] * delta[k]
                                h[j][k] += value
                                if k != j:
                                    h[k][j] += value
                    for j in range(4):
                        for k in range(4):
                            hessian[j][k] -= weight * h[j][k]
        return ll, grad, hessian

    if not groups:
        return {
            "beta": [0.0] * params,
            "loglik": 0.0,
            "cov": [[0.0] * params for _ in range(params)],
            "se_cluster": [math.inf] * params,
            "se_model": [math.inf] * params,
            "n_groups": 0,
            "n_rows": 0,
            "converged": False,
        }

    loglik, gradient, hessian = evaluate(beta)
    converged = False
    for _ in range(100):
        if max(abs(value) for value in gradient) < 1e-9:
            converged = True
            break
        information = [[-hessian[j][k] for k in range(params)] for j in range(params)]
        delta = _solve(information, gradient)
        step = 1.0
        for _ in range(30):
            candidate = [beta[j] + step * delta[j] for j in range(params)]
            candidate_ll = evaluate(candidate, need_hessian=False)[0]
            if candidate_ll >= loglik - 1e-12:
                break
            step *= 0.5
        beta = [beta[j] + step * delta[j] for j in range(params)]
        loglik, gradient, hessian = evaluate(beta)
        if max(abs(step * value) for value in delta) < 1e-11:
            converged = True
            break

    loglik, gradient, hessian = evaluate(beta)
    information = [[-hessian[j][k] for k in range(params)] for j in range(params)]
    inverse = _inverse(information)

    cluster_scores: dict[str, list[float]] = defaultdict(lambda: [0.0] * params)
    for group in groups:
        weight = weights.get(group.key, 1.0) if weights else 1.0
        if kind == LINEAR:
            values = [beta[0] * value for value in group.s]
        elif kind == QUADRATIC:
            values = [
                beta[0] * a + beta[1] * b
                for a, b in zip(group.s, group.s2, strict=True)
            ]
        elif kind == CATEGORICAL:
            values = [
                beta[0] * a + beta[1] * b + beta[2] * c
                for a, b, c in zip(group.c1, group.c2, group.c3, strict=True)
            ]
        else:
            values = [
                beta[0] * a + beta[1] * b + beta[2] * c + beta[3] * d
                for a, b, c, d in zip(
                    group.c1, group.c2, group.c3, group.c4, strict=True
                )
            ]
        log_z = _logsumexp(values)
        probs = [math.exp(value - log_z) for value in values]
        expected = [0.0] * params
        if kind == LINEAR:
            for prob, value in zip(probs, group.s, strict=True):
                expected[0] += prob * value
            observed = [group.ev_s]
        elif kind == QUADRATIC:
            for prob, a, b in zip(probs, group.s, group.s2, strict=True):
                expected[0] += prob * a
                expected[1] += prob * b
            observed = [group.ev_s, group.ev_s2]
        elif kind == CATEGORICAL:
            for prob, a, b, c in zip(
                probs, group.c1, group.c2, group.c3, strict=True
            ):
                expected[0] += prob * a
                expected[1] += prob * b
                expected[2] += prob * c
            observed = [group.ev_c1, group.ev_c2, group.ev_c3]
        else:
            for prob, a, b, c, d in zip(
                probs, group.c1, group.c2, group.c3, group.c4, strict=True
            ):
                expected[0] += prob * a
                expected[1] += prob * b
                expected[2] += prob * c
                expected[3] += prob * d
            observed = [group.ev_c1, group.ev_c2, group.ev_c3, group.ev_c4]
        for j in range(params):
            cluster_scores[group.cluster][j] += weight * (observed[j] - expected[j])

    meat = [
        [sum(score[j] * score[k] for score in cluster_scores.values()) for k in range(params)]
        for j in range(params)
    ]
    middle = [
        [sum(inverse[j][k] * meat[k][col] for k in range(params)) for col in range(params)]
        for j in range(params)
    ]
    covariance = [
        [sum(middle[j][k] * inverse[k][col] for k in range(params)) for col in range(params)]
        for j in range(params)
    ]
    se_cluster = [math.sqrt(max(covariance[j][j], 0.0)) for j in range(params)]
    se_model = [math.sqrt(max(inverse[j][j], 0.0)) for j in range(params)]
    return {
        "beta": beta,
        "loglik": loglik,
        "cov": covariance,
        "cov_model": inverse,
        "se_cluster": se_cluster,
        "se_model": se_model,
        "n_groups": len(groups),
        "n_rows": sum(len(group.severity) for group in groups),
        "converged": converged,
        "gradient_inf": max(abs(value) for value in gradient),
    }


def fit_designs(
    groups: list[Group], *, warm: dict[str, list[float]] | None = None
) -> dict[str, Any]:
    """Fit the three nested severity specifications and both LRTs."""
    warm = warm or {}
    linear = fit_conditional(groups, LINEAR, warm=warm.get("linear"))
    quadratic = fit_conditional(groups, QUADRATIC, warm=warm.get("quadratic"))
    categorical = fit_conditional(groups, CATEGORICAL, warm=warm.get("categorical"))
    return {
        "linear": linear,
        "quadratic": quadratic,
        "categorical": categorical,
        "lrt_categorical_vs_linear": 2.0 * (categorical["loglik"] - linear["loglik"]),
        "lrt_quadratic_vs_linear": 2.0 * (quadratic["loglik"] - linear["loglik"]),
    }


def simulate_groups(groups: list[Group], beta: float, rng: random.Random) -> list[Group]:
    """Draw one outcome set per stratum from the fitted linear model."""
    simulated: list[Group] = []
    for group in groups:
        values = [beta * value for value in group.s]
        maximum = max(values)
        weights = [math.exp(value - maximum) for value in values]
        chosen = rng.choices(range(len(weights)), weights=weights, k=1)[0]
        outcomes = tuple(
            1 if i in group.subsets[chosen] else 0 for i in range(len(group.severity))
        )
        simulated.append(
            replace(
                group,
                y=outcomes,
                obs=chosen,
                ev_s=group.s[chosen],
                ev_s2=group.s2[chosen],
                ev_c1=group.c1[chosen],
                ev_c2=group.c2[chosen],
                ev_c3=group.c3[chosen],
                ev_c4=group.c4[chosen],
            )
        )
    return simulated


def _quantile(values: list[float], probability: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(probability * len(ordered))))
    return ordered[index]


def bootstrap_lrt(
    prefix_groups: dict[str, list[Group]],
    observed: dict[str, Any],
    *,
    reps: int,
    seed: int,
    label: str,
) -> dict[str, Any]:
    """Prefix-cluster null parametric bootstrap for both severity LRTs."""
    keys = sorted(prefix_groups)
    if not keys or reps <= 0:
        return {
            "label": label,
            "reps_requested": 0,
            "reps_valid": 0,
            "bootstrap_p_categorical_vs_linear": 1.0,
            "bootstrap_p_quadratic_vs_linear": 1.0,
        }
    rng = random.Random(seed)
    null_cat: list[float] = []
    null_quad: list[float] = []
    for replicate in range(reps):
        draws = rng.choices(keys, k=len(keys))
        resampled: list[Group] = []
        for index, key in enumerate(draws):
            for group in prefix_groups[key]:
                resampled.append(
                    replace(group, cluster=f"{group.cluster}|b{replicate}|{index}")
                )
        if not resampled:
            continue
        simulated = simulate_groups(resampled, observed["linear"]["beta"][0], rng)
        linear = fit_conditional(simulated, LINEAR, warm=observed["linear"]["beta"])
        quadratic = fit_conditional(simulated, QUADRATIC, warm=observed["quadratic"]["beta"])
        categorical = fit_conditional(
            simulated, CATEGORICAL, warm=observed["categorical"]["beta"]
        )
        if not (linear["converged"] and quadratic["converged"] and categorical["converged"]):
            continue
        null_cat.append(2.0 * (categorical["loglik"] - linear["loglik"]))
        null_quad.append(2.0 * (quadratic["loglik"] - linear["loglik"]))
    observed_cat = observed["lrt_categorical_vs_linear"]
    observed_quad = observed["lrt_quadratic_vs_linear"]
    p_cat = (1.0 + sum(value >= observed_cat for value in null_cat)) / (1.0 + len(null_cat))
    p_quad = (1.0 + sum(value >= observed_quad for value in null_quad)) / (1.0 + len(null_quad))
    return {
        "label": label,
        "reps_requested": reps,
        "reps_valid": len(null_cat),
        "observed_lrt_categorical_vs_linear": observed_cat,
        "bootstrap_p_categorical_vs_linear": p_cat,
        "null_categorical_mean": sum(null_cat) / len(null_cat) if null_cat else math.nan,
        "null_categorical_q95": _quantile(null_cat, 0.95),
        "observed_lrt_quadratic_vs_linear": observed_quad,
        "bootstrap_p_quadratic_vs_linear": p_quad,
        "null_quadratic_mean": sum(null_quad) / len(null_quad) if null_quad else math.nan,
        "null_quadratic_q95": _quantile(null_quad, 0.95),
        "p_floor": 1.0 / (1.0 + len(null_cat)) if null_cat else math.nan,
    }


# ---------------------------------------------------------------------------
# Small statistics helpers
# ---------------------------------------------------------------------------


def chi2_sf_df1(statistic: float) -> float:
    return math.erfc(math.sqrt(max(statistic, 0.0) / 2.0))


def chi2_sf_df2(statistic: float) -> float:
    return math.exp(-max(statistic, 0.0) / 2.0)


def wald_from_contrast(fit: dict[str, Any], contrast: list[list[float]]) -> dict[str, Any]:
    """Cluster-robust Wald test for R beta = 0 with df = rows(R)."""
    rows = len(contrast)
    values = [
        sum(contrast[i][j] * fit["beta"][j] for j in range(len(fit["beta"])))
        for i in range(rows)
    ]
    covariance = [
        [
            sum(
                contrast[i][a]
                * fit["cov"][a][b]
                * contrast[j][b]
                for a in range(len(fit["beta"]))
                for b in range(len(fit["beta"]))
            )
            for j in range(rows)
        ]
        for i in range(rows)
    ]
    if rows == 1:
        variance = covariance[0][0]
        statistic = values[0] * values[0] / variance if variance > 0 else math.inf
        p_value = chi2_sf_df1(statistic)
    else:
        inverse = _inverse(covariance)
        statistic = sum(
            values[i] * inverse[i][j] * values[j] for i in range(rows) for j in range(rows)
        )
        p_value = chi2_sf_df2(statistic)
    return {"statistic": statistic, "df": rows, "p_value": p_value}


def categorical_linearity_wald(fit: dict[str, Any]) -> dict[str, Any]:
    """Test the linear restriction beta_s2 = 2 beta_s1, beta_s3 = 3 beta_s1."""
    return wald_from_contrast(fit, [[-2.0, 1.0, 0.0], [-3.0, 0.0, 1.0]])


def quadratic_term_wald(fit: dict[str, Any]) -> dict[str, Any]:
    """Test beta_{s^2} = 0."""
    return wald_from_contrast(fit, [[0.0, 1.0]])


def coefficient_table(
    fit: dict[str, Any], labels: list[str] | None = None
) -> list[dict[str, Any]]:
    table = []
    for index, beta in enumerate(fit["beta"]):
        se = fit["se_cluster"][index]
        table.append(
            {
                "name": labels[index] if labels else f"beta_{index}",
                "beta": beta,
                "se_cluster": se,
                "or": math.exp(beta),
                "or_ci95": [math.exp(beta - Z95 * se), math.exp(beta + Z95 * se)],
                "z": beta / se if se > 0 else math.nan,
                "p": chi2_sf_df1((beta / se) ** 2) if se > 0 else math.nan,
            }
        )
    return table


def wilson_ci(k: int, n: int, z: float = Z95) -> dict[str, float | None]:
    if n <= 0:
        return {"rate": None, "lo": None, "hi": None}
    p = k / n
    denominator = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denominator
    return {"rate": p, "lo": max(0.0, centre - half), "hi": min(1.0, centre + half)}


def mcnemar_exact(b: int, c: int) -> float:
    """Exact two-sided McNemar p for discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(min(b, c) + 1)) / 2.0**n
    return min(1.0, 2.0 * tail)


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _file_record(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": repo_relative(path),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Inputs:
    models: list[str]
    prefixes: list[str]
    reserve_ids: set[str]
    rows: list[Any]
    n_step0_rows: int
    rows_by_key: dict[tuple[str, str, str], Any]
    labels: list[Any]
    label_by_key: dict[tuple[str, str, str], Any]
    perturbations: list[PerturbationRecord]
    files: list[dict[str, Any]]


def load_inputs(models: list[str] | None = None) -> Inputs:
    configured = [str(model["id"]) for model in load_config("models.yaml")["models"]]
    model_ids = models or configured
    manifest_path = MANIFEST_DIR / "toolresult800_v1.json"
    perturbations_path = MANIFEST_DIR / "perturbations.jsonl"
    prefixes_path = REPO_ROOT / "data" / "frozen" / "prefixes.jsonl"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    reserve_ids = set(manifest.get("reserve_ids", []))

    files: list[dict[str, Any]] = [
        _file_record(manifest_path, "manifest"),
        _file_record(perturbations_path, "perturbations"),
        _file_record(prefixes_path, "frozen_prefixes"),
        _file_record(REPO_ROOT / "configs" / "models.yaml", "model_config"),
    ]

    rows: list[Any] = []
    n_step0_rows = 0
    for model_id in model_ids:
        ledger_path = RUNS_DIR / "main" / model_id / "ledger.jsonl"
        step0 = [row for row in read_ledger(ledger_path) if row.step == 0]
        n_step0_rows += len(step0)
        rows.extend(row for row in step0 if row.prefix_id not in reserve_ids)
        files.append(_file_record(ledger_path, f"base_ledger:{model_id}"))
        for regime in ("transient", "persistent"):
            files.append(
                _file_record(
                    RUNS_DIR / "main" / model_id / f"recovery_{regime}.jsonl",
                    f"recovery_steps:{model_id}:{regime}",
                )
            )
            files.append(
                _file_record(
                    RUNS_DIR / "main" / "recovery" / model_id / f"{regime}.jsonl",
                    f"recovery_events:{model_id}:{regime}",
                )
            )

    perturbations = [
        PerturbationRecord.from_dict(item)
        for item in read_jsonl_dicts(perturbations_path)
    ]
    labels = compute_outcomes(rows, perturbations)
    label_by_key = {
        (label.prefix_id, label.model_id, label.arm): label for label in labels
    }
    rows_by_key = {(row.prefix_id, row.model_id, row.arm): row for row in rows}
    prefixes = sorted({row.prefix_id for row in rows})
    return Inputs(
        models=model_ids,
        prefixes=prefixes,
        reserve_ids=reserve_ids,
        rows=rows,
        n_step0_rows=n_step0_rows,
        rows_by_key=rows_by_key,
        labels=labels,
        label_by_key=label_by_key,
        perturbations=perturbations,
        files=files,
    )


# ---------------------------------------------------------------------------
# Severity functional form
# ---------------------------------------------------------------------------


def _design_inputs(
    inputs: Inputs,
    *,
    override: dict[tuple[str, str], int] | None = None,
    exclude: set[tuple[str, str]] | None = None,
    inactive: set[tuple[str, str]] | None = None,
) -> tuple[list[Group], dict[str, list[Group]]]:
    override = override or {}
    exclude = exclude or set()
    inactive = inactive or set()
    records = [
        (
            label.prefix_id,
            label.model_id,
            label.arm,
            4
            if (label.prefix_id, label.arm) in inactive
            else override.get((label.prefix_id, label.arm), SEVERITY[label.arm]),
            int(label.y_any),
        )
        for label in inputs.labels
        if (label.prefix_id, label.arm) not in exclude
    ]
    groups = groups_from_records(records)
    return groups, groups_by_prefix(groups, inputs.prefixes)


def severity_functional_form(
    inputs: Inputs, *, bootstrap_pooled: int, bootstrap_model: int, seed: int = SEED
) -> dict[str, Any]:
    pooled_groups, pooled_by_prefix = _design_inputs(inputs)
    pooled = fit_designs(pooled_groups)
    pooled_bootstrap = bootstrap_lrt(
        pooled_by_prefix,
        pooled,
        reps=bootstrap_pooled,
        seed=seed + 1,
        label="pooled",
    )
    pooled_summary = {
        "n_prefixes": len(inputs.prefixes),
        "n_informative_prefixes": len({group.cluster for group in pooled_groups}),
        "n_groups": pooled["linear"]["n_groups"],
        "n_rows": pooled["linear"]["n_rows"],
        "linear": {
            "beta": pooled["linear"]["beta"][0],
            "se_cluster": pooled["linear"]["se_cluster"][0],
            "p": coefficient_table(pooled["linear"])[0]["p"],
            "loglik": pooled["linear"]["loglik"],
        },
        "quadratic": {
            "beta": pooled["quadratic"]["beta"],
            "loglik": pooled["quadratic"]["loglik"],
            "term_wald": quadratic_term_wald(pooled["quadratic"]),
        },
        "categorical": {
            "coefficients": coefficient_table(
                pooled["categorical"], ["s1", "s2", "s3"]
            ),
            "loglik": pooled["categorical"]["loglik"],
            "linearity_wald": categorical_linearity_wald(pooled["categorical"]),
        },
        "lrt_categorical_vs_linear": pooled["lrt_categorical_vs_linear"],
        "lrt_categorical_asymptotic_p": chi2_sf_df2(
            pooled["lrt_categorical_vs_linear"]
        ),
        "lrt_quadratic_vs_linear": pooled["lrt_quadratic_vs_linear"],
        "lrt_quadratic_asymptotic_p": chi2_sf_df1(
            pooled["lrt_quadratic_vs_linear"]
        ),
        "bootstrap": pooled_bootstrap,
    }

    per_model: dict[str, Any] = {}
    raw_p: dict[str, float] = {}
    raw_wald: dict[str, float] = {}
    for model_id in inputs.models:
        model_records = [
            (
                label.prefix_id,
                label.model_id,
                label.arm,
                SEVERITY[label.arm],
                int(label.y_any),
            )
            for label in inputs.labels
            if label.model_id == model_id
        ]
        model_groups = groups_from_records(model_records)
        model_by_prefix = groups_by_prefix(model_groups, inputs.prefixes)
        fits = fit_designs(model_groups)
        bootstrap = bootstrap_lrt(
            model_by_prefix,
            fits,
            reps=bootstrap_model,
            seed=seed + 10 + len(per_model),
            label=model_id,
        )
        cat_wald = categorical_linearity_wald(fits["categorical"])
        quad_wald = quadratic_term_wald(fits["quadratic"])
        raw_p[f"{model_id}|categorical_vs_linear"] = bootstrap[
            "bootstrap_p_categorical_vs_linear"
        ]
        raw_p[f"{model_id}|quadratic_vs_linear"] = bootstrap[
            "bootstrap_p_quadratic_vs_linear"
        ]
        raw_wald[f"{model_id}|categorical_vs_linear"] = cat_wald["p_value"]
        raw_wald[f"{model_id}|quadratic_vs_linear"] = quad_wald["p_value"]
        per_model[model_id] = {
            "n_prefixes": len(inputs.prefixes),
            "n_informative_prefixes": len({group.cluster for group in model_groups}),
            "n_groups": fits["linear"]["n_groups"],
            "n_rows": fits["linear"]["n_rows"],
            "linear": {
                "beta": fits["linear"]["beta"][0],
                "se_cluster": fits["linear"]["se_cluster"][0],
                "p": coefficient_table(fits["linear"])[0]["p"],
            },
            "quadratic": {
                "beta": fits["quadratic"]["beta"],
                "term_wald": quad_wald,
            },
            "categorical": {
                "coefficients": coefficient_table(
                    fits["categorical"], ["s1", "s2", "s3"]
                ),
                "linearity_wald": cat_wald,
            },
            "lrt_categorical_vs_linear": fits["lrt_categorical_vs_linear"],
            "lrt_categorical_asymptotic_p": chi2_sf_df2(
                fits["lrt_categorical_vs_linear"]
            ),
            "lrt_quadratic_vs_linear": fits["lrt_quadratic_vs_linear"],
            "lrt_quadratic_asymptotic_p": chi2_sf_df1(
                fits["lrt_quadratic_vs_linear"]
            ),
            "bootstrap": bootstrap,
        }
    holm_bootstrap = holm_adjust(raw_p)
    holm_wald = holm_adjust(raw_wald)
    return {
        "estimand": (
            "conditional (fixed-effects) logit of the any-switch outcome on assigned "
            "severity, stratified by prefix x model and clustered by prefix; the LRT "
            "compares categorical or quadratic severity with the linear specification"
        ),
        "pooled": pooled_summary,
        "per_model": per_model,
        "multiplicity": {
            "family": "six per-model tests (categorical-vs-linear and quadratic-vs-linear x three models)",
            "method": (
                "Holm step-down on cluster-robust Wald p-values (primary family); "
                "bootstrap p-values are a resampling check with 1/(B+1) resolution"
            ),
            "raw_wald_p": raw_wald,
            "holm_wald_p": holm_wald,
            "raw_bootstrap_p": raw_p,
            "holm_bootstrap_p": holm_bootstrap,
            "note": (
                "The six tests reuse the same 800 prefixes in all three models, so they are "
                "positively dependent. Holm controls the family-wise error rate under arbitrary "
                "dependence and is therefore valid but conservative here; it does not model the "
                "shared-prefix correlation. The pooled bootstrap test is the primary and is not "
                "in the six-test family. The per-model bootstrap p-values have resolution "
                "1/(B+1); with B=40 the floor is 0.024, so Holm on bootstrap p-values is "
                "conservative and the Wald family is the primary multiplicity record."
            ),
        },
    }


# ---------------------------------------------------------------------------
# Severity reclassification
# ---------------------------------------------------------------------------


def _load_severity_passes() -> dict[str, Any]:
    items_path = AUDIT_DIR / "blind" / "severity_items.jsonl"
    items = list(read_jsonl_dicts(items_path))
    levels = {item["item_id"]: str(item["severity_level"]) for item in items}
    prefix_by_item = {item["item_id"]: str(item["prefix_id"]) for item in items}
    sheet = _read_csv_rows(AUDIT_DIR / "severity_audit_sheet.csv")
    visible = _read_csv_rows(AUDIT_DIR / "verification" / "severity_verification.csv")
    blind = _read_csv_rows(AUDIT_DIR / "verification" / "severity_verification_slices.csv")

    def combo(item_id: str) -> tuple[str, str]:
        return (prefix_by_item[item_id], f"s{levels[item_id]}")

    majority = sorted(
        row["item_id"]
        for row in sheet
        if levels.get(row["item_id"]) in ("2", "3")
        and sum(
            int(row[column])
            for column in (
                "rater1_decision_changing",
                "rater2_decision_changing",
                "rater3_decision_changing",
            )
        )
        <= 1
    )
    visible_flags = sorted(
        row["item_id"]
        for row in visible
        if levels.get(row["item_id"]) in ("2", "3") and row["decision_changing"] == "0"
    )
    blind_flags = sorted(
        row["item_id"]
        for row in blind
        if levels.get(row["item_id"]) in ("2", "3") and row["decision_changing"] == "0"
    )
    if (len(majority), len(visible_flags), len(blind_flags)) != (7, 11, 16):
        raise SystemExit(
            "severity pass counts drifted: "
            f"{len(majority)}/{len(visible_flags)}/{len(blind_flags)} (expected 7/11/16)"
        )
    passes = {}
    for name, flags in (
        ("majority", majority),
        ("sheet_visible_verifier", visible_flags),
        ("blind_verifier", blind_flags),
    ):
        combos = sorted({combo(item_id) for item_id in flags})
        passes[name] = {
            "items": flags,
            "k": len(flags),
            "n": 60,
            "by_arm": {
                arm: sum(1 for _prefix, level_arm in combos if level_arm == arm)
                for arm in S2S3
            },
            "combos": combos,
        }
    return {
        "levels": levels,
        "prefix_by_item": prefix_by_item,
        "passes": passes,
        "files": [
            _file_record(items_path, "severity_audit_items"),
            _file_record(AUDIT_DIR / "severity_audit_sheet.csv", "severity_audit_sheet"),
            _file_record(
                AUDIT_DIR / "verification" / "severity_verification.csv",
                "severity_verification_visible",
            ),
            _file_record(
                AUDIT_DIR / "verification" / "severity_verification_slices.csv",
                "severity_verification_blind",
            ),
        ],
    }


def _rubin_pool(
    draws: list[tuple[list[float], list[list[float]]]],
    labels: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Rubin's rules for a small parameter vector."""
    count = len(draws)
    params = len(draws[0][0])
    means = [sum(draw[0][j] for draw in draws) / count for j in range(params)]
    within = [
        sum(draw[1][j][j] for draw in draws) / count for j in range(params)
    ]
    between = [
        sum((draw[0][j] - means[j]) ** 2 for draw in draws) / (count - 1)
        for j in range(params)
    ]
    total = [within[j] + (1.0 + 1.0 / count) * between[j] for j in range(params)]
    return [
        {
            "name": labels[j] if labels else f"beta_{j}",
            "beta": means[j],
            "se": math.sqrt(total[j]),
            "or": math.exp(means[j]),
            "or_ci95": [
                math.exp(means[j] - Z95 * math.sqrt(total[j])),
                math.exp(means[j] + Z95 * math.sqrt(total[j])),
            ],
            "within_var": within[j],
            "between_var": between[j],
        }
        for j in range(params)
    ]


def severity_reclassification(
    inputs: Inputs, *, imputations: int, seed: int = SEED
) -> dict[str, Any]:
    audit = _load_severity_passes()
    baseline_groups, _ = _design_inputs(inputs)
    baseline = fit_conditional(baseline_groups, CATEGORICAL)

    critical = sorted(
        {
            (label.prefix_id, label.arm)
            for label in inputs.labels
            if label.arm in S2S3
        }
    )
    audited_all = {
        (audit["prefix_by_item"][item_id], f"s{level}")
        for item_id, level in audit["levels"].items()
        if level in ("2", "3")
    }
    audited_flagged = {
        combo for payload in audit["passes"].values() for combo in payload["combos"]
    }
    unaudited = [combo for combo in critical if combo not in audited_all]
    rng = random.Random(seed + 40)

    report: dict[str, Any] = {
        "estimand": (
            "realized severity, dilution-corrected contrast: donor-unused critical rows get "
            "their own inactive indicator in the conditional logit, so the s2/s3 coefficients "
            "compare truly-used critical rows with the original s0 baseline while the inactive "
            "rows keep their own coefficient. This is the interval analogue of the old "
            "point-only dilution correction. The secondary move_to_s0 variant codes "
            "donor-unused rows as s0, which contaminates the reference and gives a different "
            "(realized-s0) contrast; it is reported but not the headline."
        ),
        "baseline_assigned": {
            "coefficients": coefficient_table(baseline, ["s1", "s2", "s3"]),
            "loglik": baseline["loglik"],
            "n_groups": baseline["n_groups"],
            "n_rows": baseline["n_rows"],
        },
        "audited_items": len(audited_all),
        "audited_flagged_union": len(audited_flagged),
        "critical_combos": len(critical),
        "unaudited_combos": len(unaudited),
        "passes": {},
        "files": audit["files"],
    }
    for name, payload in audit["passes"].items():
        audited_inactive = set(payload["combos"])
        audited_groups, _ = _design_inputs(inputs, inactive=audited_inactive)
        audited_fit = fit_conditional(audited_groups, REALIZED)
        audited_move_groups, _ = _design_inputs(
            inputs, override={combo: 0 for combo in audited_inactive}
        )
        audited_move_fit = fit_conditional(audited_move_groups, CATEGORICAL)
        inactive_audited = sum(
            1
            for label in inputs.labels
            if (label.prefix_id, label.arm) in audited_inactive
        )
        draws: list[tuple[list[float], list[list[float]]]] = []
        inactive_total = 0
        for _ in range(imputations):
            m_s2 = rng.betavariate(
                payload["by_arm"]["s2"] + 0.5, 30 - payload["by_arm"]["s2"] + 0.5
            )
            m_s3 = rng.betavariate(
                payload["by_arm"]["s3"] + 0.5, 30 - payload["by_arm"]["s3"] + 0.5
            )
            inactive = set(audited_inactive)
            for prefix, arm in unaudited:
                probability = m_s2 if arm == "s2" else m_s3
                if rng.random() < probability:
                    inactive.add((prefix, arm))
            inactive_total += sum(
                1
                for label in inputs.labels
                if (label.prefix_id, label.arm) in inactive
            )
            groups, _ = _design_inputs(inputs, inactive=inactive)
            fit = fit_conditional(groups, REALIZED)
            draws.append((fit["beta"], fit["cov"]))
        report["passes"][name] = {
            "k": payload["k"],
            "n": payload["n"],
            "by_arm": payload["by_arm"],
            "audited_only": {
                "inactive_rows": inactive_audited,
                "realized": {
                    "coefficients": coefficient_table(
                        audited_fit, ["s1", "s2", "s3", "inactive_critical"]
                    )[:3],
                    "inactive_critical": {
                        "beta": audited_fit["beta"][3],
                        "se_cluster": audited_fit["se_cluster"][3],
                        "note": (
                            "nuisance indicator; with only 20 audited rows it can separate "
                            "and is not interpreted"
                        ),
                    },
                    "loglik": audited_fit["loglik"],
                    "n_groups": audited_fit["n_groups"],
                    "n_rows": audited_fit["n_rows"],
                },
                "move_to_s0": {
                    "coefficients": coefficient_table(
                        audited_move_fit, ["s1", "s2", "s3"]
                    ),
                    "loglik": audited_move_fit["loglik"],
                    "n_groups": audited_move_fit["n_groups"],
                    "n_rows": audited_move_fit["n_rows"],
                },
            },
            "extrapolated": {
                "imputations": imputations,
                "mean_inactive_rows": inactive_total / imputations,
                "realized": {
                    "coefficients": _rubin_pool(
                        draws, ["s1", "s2", "s3", "inactive_critical"]
                    )[:3],
                    "inactive_critical": {
                        **_rubin_pool(
                            draws, ["s1", "s2", "s3", "inactive_critical"]
                        )[3],
                        "note": (
                            "nuisance indicator; its MI coefficient mixes true donor-unused "
                            "rows with randomly reclassified active rows and is not interpreted"
                        ),
                    },
                },
            },
        }
    return report


# ---------------------------------------------------------------------------
# Missingness
# ---------------------------------------------------------------------------


def _task(prefix: str) -> str:
    parts = prefix.split("-")
    return parts[2] if len(parts) > 2 else ""


def _domain(prefix: str) -> str:
    return prefix.split("-")[0]


def _donor(prefix: str) -> str:
    parts = prefix.split("-")
    return parts[1] if len(parts) > 1 else ""


def build_cells(inputs: Inputs) -> list[dict[str, Any]]:
    cells: list[dict[str, Any]] = []
    for prefix in inputs.prefixes:
        for model_id in inputs.models:
            reference = inputs.rows_by_key.get((prefix, model_id, "V"))
            for arm in ARMS:
                key = (prefix, model_id, arm)
                label = inputs.label_by_key.get(key)
                row = inputs.rows_by_key.get(key)
                if label is not None:
                    reason = None
                elif reference is None or not reference.parsed or not reference.decision_json:
                    reason = "v_unparsed"
                elif row is None or not row.parsed or not row.decision_json:
                    reason = "arm_unparsed"
                else:
                    reason = "other"
                cells.append(
                    {
                        "prefix": prefix,
                        "model": model_id,
                        "arm": arm,
                        "observed": label is not None,
                        "y": int(label.y_any) if label is not None else None,
                        "reason": reason,
                        "domain": _domain(prefix),
                        "donor": _donor(prefix),
                        "task": _task(prefix),
                        "severity": SEVERITY[arm],
                    }
                )
    return cells


def _logistic_features(cell: dict[str, Any], models: list[str]) -> list[float]:
    features = [
        1.0 if cell["model"] == model and cell["arm"] == arm else 0.0
        for model in models
        for arm in ARMS
    ]
    features.append(1.0 if cell["domain"] == "retail" else 0.0)
    features.append(1.0 if cell["donor"] == "gpt4o" else 0.0)
    return features


def _fit_logistic(
    rows: list[list[float]], outcomes: list[int], *, ridge: float = 1e-6
) -> tuple[list[float], list[float], bool]:
    params = len(rows[0])
    beta = [0.0] * params
    for _ in range(100):
        gradient = [-ridge * value for value in beta]
        hessian = [[ridge if i == j else 0.0 for j in range(params)] for i in range(params)]
        probabilities = []
        for features, outcome in zip(rows, outcomes, strict=True):
            linear = sum(b * x for b, x in zip(beta, features, strict=True))
            p = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, linear))))
            probabilities.append(p)
            for j in range(params):
                gradient[j] += features[j] * (outcome - p)
                for k in range(params):
                    hessian[j][k] += features[j] * features[k] * p * (1.0 - p)
        delta = _solve(hessian, gradient)
        beta = [beta[j] + delta[j] for j in range(params)]
        if max(abs(value) for value in delta) < 1e-10:
            return beta, _predict_logistic(beta, rows), True
    return beta, _predict_logistic(beta, rows), False


def _predict_logistic(beta: list[float], rows: list[list[float]]) -> list[float]:
    probabilities = []
    for features in rows:
        linear = sum(b * x for b, x in zip(beta, features, strict=True))
        probabilities.append(1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, linear)))))
    return probabilities


def _weighted_arm_rates(cells: list[dict[str, Any]], weights: list[float]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for arm in ARMS:
        indices = [
            i
            for i, cell in enumerate(cells)
            if cell["arm"] == arm and cell["observed"]
        ]
        denominator = sum(weights[i] for i in indices)
        numerator = sum(weights[i] * int(cells[i]["y"]) for i in indices)
        report[arm] = {
            "k": numerator,
            "n_observed": len(indices),
            "weight_sum": denominator,
            "rate": numerator / denominator if denominator else None,
            "effective_n": (denominator * denominator / sum(weights[i] ** 2 for i in indices))
            if indices
            else None,
        }
    report["s3_minus_s2"] = (
        report["s3"]["rate"] - report["s2"]["rate"]
        if report["s3"]["rate"] is not None and report["s2"]["rate"] is not None
        else None
    )
    report["s3_minus_s0"] = (
        report["s3"]["rate"] - report["s0"]["rate"]
        if report["s3"]["rate"] is not None and report["s0"]["rate"] is not None
        else None
    )
    return report


def _manski(cells: list[dict[str, Any]]) -> dict[str, Any]:
    bounds: dict[str, Any] = {}
    for arm in ARMS:
        arm_cells = [cell for cell in cells if cell["arm"] == arm]
        observed = [cell for cell in arm_cells if cell["observed"]]
        switches = sum(int(cell["y"]) for cell in observed)
        potential = len(arm_cells)
        missing = potential - len(observed)
        bounds[arm] = {
            "potential": potential,
            "observed": len(observed),
            "switches": switches,
            "lower": switches / potential if potential else None,
            "upper": (switches + missing) / potential if potential else None,
        }
    bounds["s3_minus_s2"] = {
        "lower": bounds["s3"]["lower"] - bounds["s2"]["upper"],
        "upper": bounds["s3"]["upper"] - bounds["s2"]["lower"],
    }
    bounds["s3_minus_s0"] = {
        "lower": bounds["s3"]["lower"] - bounds["s0"]["upper"],
        "upper": bounds["s3"]["upper"] - bounds["s0"]["lower"],
    }
    return bounds


def _poststratified(cells: list[dict[str, Any]]) -> dict[str, Any]:
    strata: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(
        lambda: {"potential": 0, "observed": 0, "switches": 0}
    )
    for cell in cells:
        key = (cell["domain"], cell["task"], cell["model"], cell["arm"])
        strata[key]["potential"] += 1
        if cell["observed"]:
            strata[key]["observed"] += 1
            strata[key]["switches"] += int(cell["y"])
    total_weight = defaultdict(float)
    total_switches = defaultdict(float)
    uncovered = defaultdict(int)
    for (_domain, _task, _model, arm), value in strata.items():
        if value["observed"] == 0:
            uncovered[arm] += value["potential"]
            continue
        weight = value["potential"] / value["observed"]
        total_weight[arm] += value["potential"]
        total_switches[arm] += weight * value["switches"]
    rates = {
        arm: (total_switches[arm] / total_weight[arm] if total_weight[arm] else None)
        for arm in ARMS
    }
    return {
        "strata": len(strata),
        "uncovered_potential": dict(uncovered),
        "rates": rates,
        "s3_minus_s2": (
            rates["s3"] - rates["s2"]
            if rates["s3"] is not None and rates["s2"] is not None
            else None
        ),
    }


def missingness(
    inputs: Inputs, *, rate_bootstrap: int, slope_bootstrap: int, seed: int = SEED
) -> dict[str, Any]:
    cells = build_cells(inputs)
    observed_cells = [cell for cell in cells if cell["observed"]]
    missing_cells = [cell for cell in cells if not cell["observed"]]
    reasons = Counter(cell["reason"] for cell in missing_cells)
    features = [_logistic_features(cell, inputs.models) for cell in cells]
    outcomes = [int(cell["observed"]) for cell in cells]
    beta, fitted, converged = _fit_logistic(features, outcomes)
    probabilities = _predict_logistic(beta, features)
    weights = [1.0 / max(0.001, p) for p in probabilities]

    weighted = _weighted_arm_rates(cells, weights)
    complete = _weighted_arm_rates(cells, [1.0] * len(cells))

    # Fixed-weight prefix-cluster bootstrap for the IPW rates.
    by_prefix: dict[str, list[int]] = defaultdict(list)
    for index, cell in enumerate(cells):
        by_prefix[cell["prefix"]].append(index)
    keys = sorted(by_prefix)
    rng = random.Random(seed + 70)
    draws: dict[str, list[float]] = defaultdict(list)
    for _ in range(rate_bootstrap):
        selected: list[dict[str, Any]] = []
        selected_weights: list[float] = []
        for _draw in range(len(keys)):
            key = rng.choice(keys)
            for index in by_prefix[key]:
                selected.append(cells[index])
                selected_weights.append(weights[index])
        rates = _weighted_arm_rates(selected, selected_weights)
        for label in ("s3_minus_s2", "s3_minus_s0"):
            if rates[label] is not None:
                draws[label].append(rates[label])
    bootstrap = {
        label: {
            "lo": _quantile(values, 0.025),
            "hi": _quantile(values, 0.975),
            "reps": len(values),
        }
        for label, values in draws.items()
    }

    # IPW slope: group-mean inverse-probability weights in the conditional logit.
    group_weights: dict[str, list[float]] = defaultdict(list)
    for index, cell in enumerate(cells):
        if cell["observed"]:
            group_weights[f"{cell['prefix']}|{cell['model']}"].append(weights[index])
    group_weight = {
        key: sum(values) / len(values) for key, values in group_weights.items()
    }
    groups, _ = _design_inputs(inputs)
    weighted_slope = fit_conditional(groups, LINEAR, weights=group_weight)
    unweighted_slope = fit_conditional(groups, LINEAR)

    # Fixed-weight bootstrap for the IPW slope.
    prefix_groups = groups_by_prefix(groups, inputs.prefixes)
    slope_draws: list[float] = []
    slope_rng = random.Random(seed + 71)
    for _ in range(slope_bootstrap):
        resampled: list[Group] = []
        resampled_weights: dict[str, float] = {}
        for index in range(len(keys)):
            key = slope_rng.choice(keys)
            for group in prefix_groups[key]:
                new_key = f"{group.key}|b{index}"
                resampled.append(replace(group, key=new_key, cluster=new_key))
                resampled_weights[new_key] = group_weight.get(group.key, 1.0)
        if not resampled:
            continue
        fit = fit_conditional(resampled, LINEAR, weights=resampled_weights)
        if fit["converged"] and math.isfinite(fit["beta"][0]):
            slope_draws.append(fit["beta"][0])

    manski = _manski(cells)

    # Extreme-imputation bounds for the linear slope.
    slope_bounds: dict[str, Any] = {"upper": None, "lower": None}
    for direction in ("upper", "lower"):
        candidates = []
        for threshold in (1, 2, 3):
            records = []
            for cell in cells:
                if cell["observed"]:
                    outcome = int(cell["y"])
                elif direction == "upper":
                    outcome = 1 if cell["severity"] >= threshold else 0
                else:
                    outcome = 1 if cell["severity"] < threshold else 0
                records.append(
                    (
                        cell["prefix"],
                        cell["model"],
                        cell["arm"],
                        cell["severity"],
                        outcome,
                    )
                )
            bound_groups = groups_from_records(records)
            fit = fit_conditional(bound_groups, LINEAR)
            candidates.append((fit["beta"][0], threshold))
        selected = max(candidates) if direction == "upper" else min(candidates)
        slope_bounds[direction] = {"beta": selected[0], "threshold": selected[1]}

    return {
        "cells": {
            "potential": len(cells),
            "observed": len(observed_cells),
            "missing": len(missing_cells),
            "missing_rate": len(missing_cells) / len(cells),
            "reasons": dict(reasons),
            "v_unparsed_units": sum(1 for cell in missing_cells if cell["reason"] == "v_unparsed") // 4,
            "by_arm": {
                arm: {
                    "potential": sum(1 for cell in cells if cell["arm"] == arm),
                    "observed": sum(
                        1 for cell in cells if cell["arm"] == arm and cell["observed"]
                    ),
                    "missing": sum(
                        1 for cell in cells if cell["arm"] == arm and not cell["observed"]
                    ),
                }
                for arm in ARMS
            },
        },
        "propensity": {
            "model": "logistic observation model: model x arm dummies + domain + donor",
            "converged": converged,
            "min_probability": min(probabilities),
            "max_probability": max(probabilities),
            "max_weight": max(weights),
        },
        "complete_case": complete,
        "ipw": {
            "rates": weighted,
            "bootstrap_ci": bootstrap,
            "note": (
                "Hajek inverse-probability-weighted rates; bootstrap resamples prefixes with "
                "the fitted weights held fixed, so it does not propagate propensity-estimation "
                "uncertainty. The post-stratified check is the task-heterogeneity cross-check."
            ),
        },
        "poststratified": _poststratified(cells),
        "manski": manski,
        "slope": {
            "complete_case": {
                "beta": unweighted_slope["beta"][0],
                "se_cluster": unweighted_slope["se_cluster"][0],
            },
            "ipw": {
                "beta": weighted_slope["beta"][0],
                "se_cluster": weighted_slope["se_cluster"][0],
                "bootstrap_ci": [
                    _quantile(slope_draws, 0.025),
                    _quantile(slope_draws, 0.975),
                ],
                "bootstrap_reps": len(slope_draws),
                "note": (
                    "group-mean inverse-probability weights in the conditional likelihood; a "
                    "pseudo-likelihood approximation, reported as a sensitivity only"
                ),
            },
            "extreme_imputation_bounds": slope_bounds,
        },
    }


# ---------------------------------------------------------------------------
# Recovery
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Sequence:
    prefix: str
    model: str
    regime: str
    severity: int
    time: int
    status: str  # recovery, competing, censored
    endpoint: str
    reason: str


def _classify_censor(step_rows: list[Any]) -> str:
    ordered = sorted(step_rows, key=lambda row: row.step)
    if any(not row.parsed for row in ordered):
        return "parse_fail"
    if not signature_from_json(ordered[-1].decision_json or "{}").tool_name:
        return "final_answer"
    return "ran_to_H4"


def _persistent_selected(prefixes: dict[str, dict[str, Any]]) -> set[str]:
    selected: set[str] = set()
    for domain in ("airline", "retail"):
        pool = sorted(
            prefix_id
            for prefix_id, prefix in prefixes.items()
            if prefix.get("domain") == domain and prefix.get("split") == "primary"
        )
        rng = random.Random(f"{SEED}|persistent|{domain}")
        rng.shuffle(pool)
        selected.update(pool[:100])
    return selected


def recovery_sequences(inputs: Inputs) -> tuple[dict[str, list[Sequence]], dict[str, Any]]:
    prefixes = {
        str(row["prefix_id"]): row
        for row in read_jsonl_dicts(REPO_ROOT / "data" / "frozen" / "prefixes.jsonl")
    }
    selected = _persistent_selected(prefixes)
    cells = (
        ("transient", "s2", 2),
        ("transient", "s3", 3),
        ("persistent", "s3", 3),
    )
    sequences: dict[str, list[Sequence]] = {}
    metadata: dict[str, Any] = {}
    for model_id in inputs.models:
        step0 = [
            row
            for row in read_ledger(RUNS_DIR / "main" / model_id / "ledger.jsonl")
            if row.step == 0 and row.prefix_id not in inputs.reserve_ids
        ]
        by_key = {(row.prefix_id, row.arm): row for row in step0}
        prefix_ids = {row.prefix_id for row in step0}
        for regime, arm, severity in cells:
            semantic: set[str] = set()
            for prefix in prefix_ids:
                reference = by_key.get((prefix, "V"))
                current = by_key.get((prefix, arm))
                if reference is None or not reference.parsed or not reference.decision_json:
                    continue
                if current is None or not current.parsed or not current.decision_json:
                    continue
                if flag_detected(current.output_text):
                    continue
                if signatures_differ(
                    signature_from_json(reference.decision_json),
                    signature_from_json(current.decision_json),
                ):
                    semantic.add(prefix)
            if regime == "persistent":
                semantic = {prefix for prefix in semantic if prefix in selected}
            step_rows: dict[str, list[Any]] = defaultdict(list)
            for row in read_ledger(
                RUNS_DIR / "main" / model_id / f"recovery_{regime}.jsonl"
            ):
                if row.arm == arm and row.prefix_id not in inputs.reserve_ids:
                    step_rows[row.prefix_id].append(row)
            events = [
                RecoveryEvent.from_dict(item)
                for item in read_jsonl_dicts(
                    RUNS_DIR / "main" / "recovery" / model_id / f"{regime}.jsonl"
                )
                if item["severity"] == severity and item["prefix_id"] not in inputs.reserve_ids
            ]
            event_by_prefix = {event.prefix_id: event for event in events}
            analysed = semantic & set(step_rows)
            cell_sequences: list[Sequence] = []
            for prefix in sorted(analysed):
                event = event_by_prefix[prefix]
                rows = step_rows[prefix]
                if not event.censored and event.recovered_step is not None:
                    cell_sequences.append(
                        Sequence(
                            prefix=prefix,
                            model=model_id,
                            regime=regime,
                            severity=severity,
                            time=max(1, min(HORIZON, int(event.recovered_step))),
                            status="recovery",
                            endpoint=event.endpoint,
                            reason="",
                        )
                    )
                else:
                    reason = _classify_censor(rows)
                    status = "censored" if reason == "ran_to_H4" else "competing"
                    cell_sequences.append(
                        Sequence(
                            prefix=prefix,
                            model=model_id,
                            regime=regime,
                            severity=severity,
                            time=max(1, min(HORIZON, int(event.last_step or HORIZON))),
                            status=status,
                            endpoint="censored",
                            reason=reason,
                        )
                    )
            key = f"{model_id}|{regime}_s{severity}"
            sequences[key] = cell_sequences
            metadata[key] = {
                "model": model_id,
                "regime": regime,
                "severity": severity,
                "semantic_risk_set": len(semantic),
                "ran_with_sequences": len(step_rows),
                "analysed": len(analysed),
                "n": len(cell_sequences),
                "events": sum(1 for seq in cell_sequences if seq.status == "recovery"),
                "r1": sum(1 for seq in cell_sequences if seq.endpoint == "R1"),
                "r2": sum(1 for seq in cell_sequences if seq.endpoint == "R2"),
                "censored": sum(1 for seq in cell_sequences if seq.status == "censored"),
                "competing": sum(1 for seq in cell_sequences if seq.status == "competing"),
                "censor_reasons": dict(Counter(seq.reason for seq in cell_sequences if seq.status != "recovery")),
            }
    return sequences, metadata


def aalen_johansen(sequences: list[Sequence], horizon: int = HORIZON) -> list[dict[str, Any]]:
    rows = []
    survival = 1.0
    cumulative_recovery = 0.0
    cumulative_competing = 0.0
    for step in range(1, horizon + 1):
        at_risk = sum(1 for sequence in sequences if sequence.time >= step)
        recovery = sum(
            1 for sequence in sequences if sequence.status == "recovery" and sequence.time == step
        )
        competing = sum(
            1 for sequence in sequences if sequence.status == "competing" and sequence.time == step
        )
        if at_risk:
            cumulative_recovery += survival * recovery / at_risk
            cumulative_competing += survival * competing / at_risk
            survival *= 1.0 - (recovery + competing) / at_risk
        rows.append(
            {
                "step": step,
                "at_risk": at_risk,
                "recovery_events": recovery,
                "competing_events": competing,
                "cif_recovery": cumulative_recovery,
                "cif_competing": cumulative_competing,
                "survival": survival,
            }
        )
    return rows


def _recovery_bootstrap(
    sequences: list[Sequence], *, reps: int, seed: int
) -> dict[str, Any]:
    rng = random.Random(seed)
    values = []
    for _ in range(reps):
        sample = rng.choices(sequences, k=len(sequences))
        values.append(aalen_johansen(sample)[-1]["cif_recovery"])
    return {
        "cif_recovery_h4": aalen_johansen(sequences)[-1]["cif_recovery"],
        "ci95": [_quantile(values, 0.025), _quantile(values, 0.975)],
        "reps": len(values),
    }


def _paired_table(pairs: list[tuple[int, int]]) -> dict[str, Any]:
    b = sum(1 for left, right in pairs if left == 0 and right == 1)
    c = sum(1 for left, right in pairs if left == 1 and right == 0)
    return {
        "n_pairs": len(pairs),
        "b": b,
        "c": c,
        "p_exact": mcnemar_exact(b, c),
        "difference": (b - c) / len(pairs) if pairs else None,
    }


def recovery_analysis(
    inputs: Inputs, *, bootstrap: int, seed: int = SEED
) -> dict[str, Any]:
    sequences, metadata = recovery_sequences(inputs)
    # Cross-check against the frozen v2 re-estimation before reporting.
    g4_path = ANALYSIS_DIR / "g4_recovery_v2.json"
    g4 = json.loads(g4_path.read_text(encoding="utf-8"))["groups"]
    for key, cell in metadata.items():
        reference = g4[key]
        if cell["n"] != reference["n"] or cell["events"] != reference["events"]:
            raise SystemExit(
                f"recovery risk set drifted for {key}: {cell['n']}/{cell['events']} "
                f"vs {reference['n']}/{reference['events']}"
            )

    cells: dict[str, Any] = {}
    for key, cell_sequences in sequences.items():
        aj = aalen_johansen(cell_sequences)
        crude = metadata[key]["events"] / metadata[key]["n"] if metadata[key]["n"] else None
        km = kaplan_meier(
            [
                RecoveryEvent(
                    prefix_id=sequence.prefix,
                    model_id=sequence.model,
                    regime=sequence.regime,
                    severity=sequence.severity,
                    horizon=HORIZON,
                    recovered_step=sequence.time
                    if sequence.status == "recovery"
                    else None,
                    endpoint=sequence.endpoint,
                    censored=sequence.status != "recovery",
                    state_hash="",
                    last_step=sequence.time,
                )
                for sequence in cell_sequences
            ],
            horizon=HORIZON,
        )
        cells[key] = {
            **metadata[key],
            "crude_recovery": crude,
            "aj_minus_crude": aj[-1]["cif_recovery"] - crude if crude is not None else None,
            "kaplan_meier_recovery_h4": 1.0 - km[-1]["survival"],
            "aalen_johansen": aj,
            "aalen_johansen_h4": aj[-1]["cif_recovery"],
            "competing_cif_h4": aj[-1]["cif_competing"],
            "bootstrap": _recovery_bootstrap(
                cell_sequences, reps=bootstrap, seed=seed + 90 + len(cells)
            ),
        }

    paired: dict[str, Any] = {}
    model_pairs: list[dict[str, Any]] = []
    pooled_pairs: list[tuple[int, int]] = []
    for model_id in inputs.models:
        left = sequences[f"{model_id}|transient_s2"]
        right = sequences[f"{model_id}|transient_s3"]
        left_by_prefix = {sequence.prefix: sequence for sequence in left}
        right_by_prefix = {sequence.prefix: sequence for sequence in right}
        shared = sorted(set(left_by_prefix) & set(right_by_prefix))
        pairs = [
            (
                int(left_by_prefix[prefix].status == "recovery"),
                int(right_by_prefix[prefix].status == "recovery"),
            )
            for prefix in shared
        ]
        pooled_pairs.extend(pairs)
        paired[model_id] = _paired_table(pairs)
    paired["pooled_stratified"] = _paired_table(pooled_pairs)
    paired["pooled_stratified"]["note"] = (
        "sums discordant pairs across models; prefixes recur in three models, so the "
        "exact p is descriptive and slightly anti-conservative"
    )

    for i, left_model in enumerate(inputs.models):
        for right_model in inputs.models[i + 1 :]:
            left = {
                sequence.prefix: sequence
                for sequence in sequences[f"{left_model}|transient_s3"]
            }
            right = {
                sequence.prefix: sequence
                for sequence in sequences[f"{right_model}|transient_s3"]
            }
            shared = sorted(set(left) & set(right))
            pairs = [
                (
                    int(left[prefix].status == "recovery"),
                    int(right[prefix].status == "recovery"),
                )
                for prefix in shared
            ]
            model_pairs.append(
                {
                    "left": left_model,
                    "right": right_model,
                    **{key: value for key, value in _paired_table(pairs).items()},
                }
            )
    model_p = {f"{item['left']}|{item['right']}": item["p_exact"] for item in model_pairs}
    model_holm = holm_adjust(model_p)
    for item in model_pairs:
        item["holm_p"] = model_holm[f"{item['left']}|{item['right']}"]

    return {
        "identity_note": (
            "Aalen-Johansen cumulative incidence equals crude Events/n in every cell here: "
            "all administrative censoring is horizon-only (ran_to_H4), so the crude primary "
            "already counts terminal non-recovery as a competing event. Kaplan-Meier differs "
            "because it censors terminal non-recovery (final answer, parse failure) as if it "
            "were non-informative, which inflates recovery."
        ),
        "risk_set": (
            "v2 semantic risk set exactly as stage 15: signatures_differ (parser v4 / "
            "signature v2), nonflag, reserve excluded; persistent restricted to the "
            "deterministic 200-prefix selection"
        ),
        "estimand": (
            "cumulative incidence of recovery by H=4 with terminal non-recovery "
            "(final answer, parse failure) as a competing event and ran-to-H4 as "
            "administrative censoring; Aalen-Johansen is primary, crude and KM reconcile"
        ),
        "cells": cells,
        "paired_transient_s2_vs_s3": paired,
        "paired_transient_s3_models": {
            "pairs": model_pairs,
            "holm": model_holm,
            "note": "Holm over the three pairwise model comparisons; shared prefixes make the tests dependent.",
        },
        "inputs": [_file_record(g4_path, "g4_recovery_v2_reconciliation")],
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    inputs = load_inputs()
    if inputs.n_step0_rows != 13200:
        raise SystemExit(f"expected 13,200 step-0 rows, got {inputs.n_step0_rows}")
    if len(inputs.rows) != 12000:
        raise SystemExit(f"expected 12,000 analysis rows, got {len(inputs.rows)}")
    if len(inputs.labels) != 9075:
        raise SystemExit(f"expected 9,075 analysis labels, got {len(inputs.labels)}")
    expected_arms = {"s0": 2274, "s1": 2267, "s2": 2267, "s3": 2267}
    counts = Counter(label.arm for label in inputs.labels)
    if dict(counts) != expected_arms:
        raise SystemExit(f"arm counts drifted: {dict(counts)} vs {expected_arms}")

    severity = severity_functional_form(
        inputs,
        bootstrap_pooled=args.bootstrap_pooled,
        bootstrap_model=args.bootstrap_model,
        seed=args.seed,
    )
    # Reproduce the frozen pooled estimates before adding new inference.
    pooled_ors = [
        item["or"] for item in severity["pooled"]["categorical"]["coefficients"]
    ]
    reference_ors = [1.2690324517800897, 4.599101408037121, 11.209864571973922]
    if any(
        abs(left - right) > 1e-6
        for left, right in zip(pooled_ors, reference_ors, strict=True)
    ):
        raise SystemExit(f"pooled categorical ORs drifted: {pooled_ors}")
    if abs(severity["pooled"]["linear"]["beta"] - 0.8770845263944299) > 1e-6:
        raise SystemExit("pooled linear beta drifted")
    if abs(severity["pooled"]["lrt_categorical_vs_linear"] - 25.033368891114606) > 1e-5:
        raise SystemExit("pooled categorical LRT drifted")

    reclassification = severity_reclassification(
        inputs, imputations=args.imputations, seed=args.seed
    )
    missing = missingness(
        inputs,
        rate_bootstrap=args.ipw_rate_bootstrap,
        slope_bootstrap=args.ipw_slope_bootstrap,
        seed=args.seed,
    )
    recovery = recovery_analysis(
        inputs, bootstrap=args.recovery_bootstrap, seed=args.seed
    )

    files = list(inputs.files)
    files.extend(reclassification.pop("files"))
    files.extend(recovery.pop("inputs"))
    files.extend(
        [
            _file_record(ANALYSIS_DIR / "g3_analysis.json", "g3_reconciliation"),
            _file_record(ANALYSIS_DIR / "prereg_secondary.json", "prereg_secondary_reconciliation"),
        ]
    )

    return {
        "stage": "rowlevel_refits",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "provenance": PROVENANCE,
        "design": "docs/DECISIONS.md D-047",
        "seed": args.seed,
        "inputs": {
            "ledger_root": repo_relative(RUNS_DIR / "main"),
            "n_step0_rows": inputs.n_step0_rows,
            "n_analysis_rows": len(inputs.rows),
            "n_analysis_prefixes": len(inputs.prefixes),
            "n_analysis_labels": len(inputs.labels),
            "n_cells_potential": 800 * len(inputs.models) * len(ARMS),
            "reserve_excluded": len(inputs.reserve_ids),
            "files": files,
        },
        "severity_functional_form": severity,
        "severity_reclassification": reclassification,
        "missingness": missing,
        "recovery": recovery,
        "reconciliation": {
            "assigned_severity_pooled_or": pooled_ors,
            "assigned_severity_pooled_linear_beta": severity["pooled"]["linear"]["beta"],
            "note": (
                "These reproduce prereg_secondary.json / g3_analysis.json; the new "
                "cluster bootstrap and reclassification refits are sensitivity analyses, "
                "not replacements for the preregistered primary estimates."
            ),
        },
        "runtime": {
            "bootstrap_pooled": args.bootstrap_pooled,
            "bootstrap_model": args.bootstrap_model,
            "imputations": args.imputations,
            "ipw_rate_bootstrap": args.ipw_rate_bootstrap,
            "ipw_slope_bootstrap": args.ipw_slope_bootstrap,
            "recovery_bootstrap": args.recovery_bootstrap,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bootstrap-pooled", type=int, default=BOOT_POOLED_DEFAULT)
    parser.add_argument("--bootstrap-model", type=int, default=BOOT_MODEL_DEFAULT)
    parser.add_argument("--imputations", type=int, default=MI_DEFAULT)
    parser.add_argument("--ipw-rate-bootstrap", type=int, default=IPW_RATE_BOOT_DEFAULT)
    parser.add_argument("--ipw-slope-bootstrap", type=int, default=IPW_SLOPE_BOOT_DEFAULT)
    parser.add_argument("--recovery-bootstrap", type=int, default=RECOVERY_BOOT_DEFAULT)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out", default=str(ANALYSIS_DIR / "rowlevel_refits.json"))
    args = parser.parse_args(argv)
    report = build_report(args)
    output = resolve_repo_path(args.out)
    write_json(output, report)
    print(
        "[19_rowlevel] pooled LRT cat "
        f"{report['severity_functional_form']['pooled']['lrt_categorical_vs_linear']:.3f} "
        f"boot p {report['severity_functional_form']['pooled']['bootstrap']['bootstrap_p_categorical_vs_linear']:.4f}"
    )
    print(
        "[19_rowlevel] pooled LRT quad "
        f"{report['severity_functional_form']['pooled']['lrt_quadratic_vs_linear']:.3f} "
        f"boot p {report['severity_functional_form']['pooled']['bootstrap']['bootstrap_p_quadratic_vs_linear']:.4f}"
    )
    print(
        "[19_rowlevel] missing "
        f"{report['missingness']['cells']['missing']}/{report['missingness']['cells']['potential']} "
        f"({report['missingness']['cells']['missing_rate']:.2%})"
    )
    example = next(
        key for key in sorted(report["recovery"]["cells"]) if "transient_s3" in key
    )
    example_cell = report["recovery"]["cells"][example]
    print(
        f"[19_rowlevel] {example} AJ {example_cell['aalen_johansen_h4']:.4f} "
        f"vs crude {example_cell['crude_recovery']:.4f}"
    )
    print(f"[19_rowlevel] wrote {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
