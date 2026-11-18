"""Blind-audit statistics: agreement, monotonicity, and label derivation.

Used by ``scripts/08c_blind_audit_score.py``. Standard library only, so the
repository keeps running without numpy/scipy (AGENTS.md, environment rules).

Implementations:
  * Cohen's kappa: unweighted, two raters, nominal categories.
  * Krippendorff's alpha: coincidence-matrix algorithm (nominal and interval
    difference functions), any number of raters, complete or missing values.
  * Jonckheere-Terpstra: ordered-alternative statistic with a Monte-Carlo
    permutation p-value (primary) and a no-tie normal approximation (ties make
    the approximation conservative).
"""

from __future__ import annotations

import math
import random
import statistics
from collections import Counter
from typing import Any


def phi(z: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def jt_statistic(groups: list[list[int]]) -> float:
    """Jonckheere-Terpstra J: cross-group exceedances with half credit for ties."""
    total = 0.0
    for a in range(len(groups)):
        for b in range(a + 1, len(groups)):
            for x in groups[a]:
                for y in groups[b]:
                    if y > x:
                        total += 1.0
                    elif y == x:
                        total += 0.5
    return total


def _jt_from_labels(sorted_values: list[int], labels: list[int]) -> float:
    """O(N * k) sweep computing J for a group-label assignment."""
    k = max(labels) + 1
    total = 0.0
    prior = [0] * k
    i, n = 0, len(sorted_values)
    while i < n:
        j = i
        while j < n and sorted_values[j] == sorted_values[i]:
            j += 1
        batch = [0] * k
        for t in range(i, j):
            batch[labels[t]] += 1
        for t in range(i, j):
            group = labels[t]
            total += sum(prior[:group]) + 0.5 * sum(batch[:group])
        for group in range(k):
            prior[group] += batch[group]
        i = j
    return total


def jt_test(
    groups: list[list[int]],
    *,
    n_permutations: int = 20000,
    seed: int = 20261108,
) -> dict:
    """Jonckheere-Terpstra test for an increasing ordered alternative."""
    statistic = jt_statistic(groups)
    n_total = sum(len(group) for group in groups)
    expected = (n_total * n_total - sum(len(group) ** 2 for group in groups)) / 4.0
    variance = (
        n_total * n_total * (2 * n_total + 3)
        - sum(len(group) ** 2 * (2 * len(group) + 3) for group in groups)
    ) / 72.0
    z = (statistic - expected) / math.sqrt(variance)
    p_asymptotic = 1.0 - phi(z)

    values: list[int] = []
    labels: list[int] = []
    for group_index, group in enumerate(groups):
        for value in group:
            values.append(value)
            labels.append(group_index)
    order = sorted(range(len(values)), key=lambda index: values[index])
    sorted_values = [values[index] for index in order]
    sorted_labels = [labels[index] for index in order]
    rng = random.Random(seed)
    exceed = 0
    for _ in range(n_permutations):
        rng.shuffle(sorted_labels)
        if _jt_from_labels(sorted_values, sorted_labels) >= statistic - 1e-9:
            exceed += 1
    return {
        "J": statistic,
        "expected_J": expected,
        "sd": math.sqrt(variance),
        "z": z,
        "N": n_total,
        "p_asymptotic_one_sided": p_asymptotic,
        "p_permutation_one_sided": exceed / n_permutations,
        "n_permutations": n_permutations,
        "permutation_seed": seed,
    }


def cohen_kappa(a: list[str], b: list[str]) -> tuple[float, dict]:
    """Unweighted Cohen's kappa for two raters with nominal categories."""
    if len(a) != len(b):
        raise ValueError("rater vectors differ in length")
    n = len(a)
    if n == 0:
        raise ValueError("empty rating vectors")
    categories = sorted(set(a) | set(b))
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    expected = sum((a.count(c) / n) * (b.count(c) / n) for c in categories)
    if expected >= 1.0:
        kappa = 1.0 if observed >= 1.0 else 0.0
    else:
        kappa = (observed - expected) / (1.0 - expected)
    return kappa, {
        "po": observed,
        "pe": expected,
        "n": n,
        "categories": categories,
    }


def kripp_alpha(matrix: list[list[Any]], metric: str = "nominal") -> float:
    """Krippendorff's alpha via the coincidence matrix.

    ``matrix`` holds one list of codes per unit. ``metric`` is ``nominal`` or
    ``interval`` (squared numeric difference).
    """
    if metric not in {"nominal", "interval"}:
        raise ValueError(f"unknown metric: {metric}")

    def delta(c: Any, k: Any) -> float:
        if metric == "nominal":
            return 0.0 if c == k else 1.0
        return float(c - k) ** 2

    units = [unit for unit in matrix if any(code is not None for code in unit)]
    if not units:
        return float("nan")
    coincidence: Counter = Counter()
    n_total = 0
    for unit in units:
        values = [code for code in unit if code is not None]
        n_unit = len(values)
        n_total += n_unit
        for i in range(n_unit):
            for j in range(n_unit):
                if i != j:
                    coincidence[(values[i], values[j])] += 1.0 / (n_unit - 1)
    if n_total <= 1:
        return float("nan")
    row = Counter()
    column = Counter()
    for (c, k), value in coincidence.items():
        row[c] += value
        column[k] += value
    observed = sum(
        value * delta(c, k) for (c, k), value in coincidence.items()
    ) / n_total
    expected = sum(
        (row[c] * column[k] / (n_total - 1)) * delta(c, k)
        for c in row
        for k in column
    ) / n_total
    if expected == 0:
        return 1.0
    return 1.0 - observed / expected


def majority(values: list[int]) -> int:
    """Majority vote for an odd number of binary codes."""
    return 1 if sum(values) * 2 > len(values) else 0


def consensus_severity(values: list[int]) -> int:
    """Median severity across an odd number of raters."""
    return int(statistics.median(values))


def fourway(labels: dict[str, str]) -> str:
    """Derive the N/YA/YF/YU audit label from a rater's four binaries.

    Priority: Y=0 -> N; action switch -> YA; explicit flag -> YF; silent
    propagation -> YU; otherwise ``Y_other`` (signature change without a
    mechanism, e.g. a value conflict outside silent propagation).
    """
    if labels["Y"] == "0":
        return "N"
    if labels["YA"] == "1":
        return "YA"
    if labels["YF"] == "1":
        return "YF"
    if labels["YU"] == "1":
        return "YU"
    return "Y_other"
