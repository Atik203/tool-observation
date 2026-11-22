"""Analysis helpers for the second-renderer (P6.7) robustness check.

A switch is ``y_any`` exactly as in :mod:`toolobs.analysis.outcomes`: the parsed
decision signature differs from the same prefix-model's ``V`` signature, or the
output contains an explicit doubt/inconsistency flag. The unit table is keyed
by ``(prefix_id, model_id)`` and records only arms with a parsed reference and a
parsed arm row, so every rate is paired within a unit.

The checks here are exploratory. They never pool with the confirmatory slope and
they do not alter any primary estimand.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from ..infer.parse_output import signature_from_json, signatures_differ
from ..schemas import LedgerRow
from .outcomes import flag_detected
from .slope import SEVERITY, SlopeRow, bootstrap_slope, conditional_logit

REFERENCE_ARM = "V"
SEVERITY_ARMS = ("s0", "s1", "s2", "s3")


def _switch(row: LedgerRow, reference: LedgerRow) -> bool:
    ref_signature = signature_from_json(reference.decision_json)
    cur_signature = signature_from_json(row.decision_json)
    return signatures_differ(ref_signature, cur_signature) or flag_detected(row.output_text)


def unit_table(rows: Iterable[LedgerRow]) -> dict[tuple[str, str], dict[str, bool]]:
    """Return parsed paired switches keyed by ``(prefix_id, model_id)``."""
    indexed: dict[tuple[str, str, str], LedgerRow] = {}
    for row in rows:
        indexed[(row.prefix_id, row.model_id, row.arm)] = row
    table: dict[tuple[str, str], dict[str, bool]] = defaultdict(dict)
    for (prefix_id, model_id, arm), row in indexed.items():
        if arm == REFERENCE_ARM or arm not in SEVERITY_ARMS:
            continue
        reference = indexed.get((prefix_id, model_id, REFERENCE_ARM))
        if reference is None or not reference.parsed or not row.parsed:
            continue
        table[(prefix_id, model_id)][arm] = _switch(row, reference)
    return dict(table)


def rate(table: dict[tuple[str, str], dict[str, bool]], arm: str, model: str | None = None):
    """Return ``(n, switches, rate)`` for one arm and optional model."""
    values = [
        int(switches[arm])
        for (prefix_id, model_id), switches in table.items()
        if arm in switches and (model is None or model_id == model)
    ]
    n = len(values)
    return n, sum(values), (sum(values) / n if n else None)


def models_in(table: dict[tuple[str, str], dict[str, bool]]) -> list[str]:
    return sorted({model_id for (_prefix, model_id) in table})


def slope_rows(
    table: dict[tuple[str, str], dict[str, bool]], model: str | None = None
) -> list[SlopeRow]:
    """Return conditional-logit rows for the s0-s3 arms."""
    rows: list[SlopeRow] = []
    for (prefix_id, model_id), switches in sorted(table.items()):
        if model is not None and model_id != model:
            continue
        for arm, value in switches.items():
            rows.append(
                SlopeRow(
                    group_id=f"{prefix_id}|{model_id}",
                    cluster_id=prefix_id,
                    model_id=model_id,
                    severity=SEVERITY[arm],
                    y=int(value),
                )
            )
    return rows


def _percentile_ci(values: list[float]) -> tuple[float | None, float | None]:
    if not values:
        return None, None
    ordered = sorted(values)
    low = ordered[max(0, int(0.025 * len(ordered)) - 1)]
    high = ordered[min(len(ordered) - 1, int(0.975 * len(ordered)))]
    return low, high


def _clusters(keys: Iterable[tuple[str, str]]) -> dict[str, list[tuple[str, str]]]:
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key in keys:
        grouped[key[0]].append(key)
    return grouped


def paired_rate_difference(
    table_a: dict[tuple[str, str], dict[str, bool]],
    table_b: dict[tuple[str, str], dict[str, bool]],
    arm: str,
    *,
    model: str | None = None,
    replicates: int = 2000,
    seed: int = 20261108,
) -> dict[str, Any]:
    """Prefix-cluster bootstrap for ``rate_a(arm) - rate_b(arm)`` on common units."""
    keys = [
        key
        for key in table_a
        if key in table_b
        and arm in table_a[key]
        and arm in table_b[key]
        and (model is None or key[1] == model)
    ]
    if not keys:
        return {"n_units": 0, "difference": None, "ci_low": None, "ci_high": None}
    differences = {key: int(table_a[key][arm]) - int(table_b[key][arm]) for key in keys}
    point = sum(differences.values()) / len(differences)
    clusters = _clusters(differences)
    prefixes = sorted(clusters)
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(replicates):
        sample = [rng.choice(prefixes) for _ in prefixes]
        values: list[int] = []
        for prefix in sample:
            values.extend(differences[key] for key in clusters[prefix])
        if values:
            estimates.append(sum(values) / len(values))
    low, high = _percentile_ci(estimates)
    return {
        "n_units": len(differences),
        "difference": point,
        "ci_low": low,
        "ci_high": high,
        "replicates": len(estimates),
    }


def paired_contrast(
    table: dict[tuple[str, str], dict[str, bool]],
    high_arm: str,
    low_arm: str,
    *,
    model: str | None = None,
    replicates: int = 2000,
    seed: int = 20261108,
) -> dict[str, Any]:
    """Prefix-cluster bootstrap for ``rate(high) - rate(low)`` within units."""
    keys = [
        key
        for key, switches in table.items()
        if high_arm in switches
        and low_arm in switches
        and (model is None or key[1] == model)
    ]
    if not keys:
        return {"n_units": 0, "difference": None, "ci_low": None, "ci_high": None}
    differences = {key: int(table[key][high_arm]) - int(table[key][low_arm]) for key in keys}
    point = sum(differences.values()) / len(differences)
    clusters = _clusters(differences)
    prefixes = sorted(clusters)
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(replicates):
        sample = [rng.choice(prefixes) for _ in prefixes]
        values: list[int] = []
        for prefix in sample:
            values.extend(differences[key] for key in clusters[prefix])
        if values:
            estimates.append(sum(values) / len(values))
    low, high = _percentile_ci(estimates)
    return {
        "n_units": len(differences),
        "difference": point,
        "ci_low": low,
        "ci_high": high,
        "replicates": len(estimates),
    }


def _cluster_slope_rows(
    table: dict[tuple[str, str], dict[str, bool]],
    model: str,
    prefixes: list[str],
    *,
    tag: str,
) -> list[SlopeRow]:
    rows: list[SlopeRow] = []
    for position, prefix in enumerate(prefixes):
        for arm, value in sorted(table.get((prefix, model), {}).items()):
            group = f"{prefix}|{model}|{tag}|{position}"
            rows.append(
                SlopeRow(
                    group_id=group,
                    cluster_id=f"{prefix}|{tag}|{position}",
                    model_id=model,
                    severity=SEVERITY[arm],
                    y=int(value),
                )
            )
    return rows


def paired_slope_difference(
    table_a: dict[tuple[str, str], dict[str, bool]],
    table_b: dict[tuple[str, str], dict[str, bool]],
    model: str,
    *,
    replicates: int = 2000,
    seed: int = 20261108,
) -> dict[str, Any]:
    """Prefix-cluster bootstrap for ``beta_a(model) - beta_b(model)``."""
    prefixes = sorted(
        {
            prefix
            for (prefix, model_id) in table_a
            if model_id == model and (prefix, model_id) in table_b
        }
    )
    if not prefixes:
        return {"difference": None, "ci_low": None, "ci_high": None, "replicates": 0}
    beta_a = conditional_logit(slope_rows(table_a, model=model)).beta
    beta_b = conditional_logit(slope_rows(table_b, model=model)).beta
    point = beta_a - beta_b
    rng = random.Random(seed)
    estimates: list[float] = []
    for replicate in range(replicates):
        sample = [rng.choice(prefixes) for _ in prefixes]
        rows_a = _cluster_slope_rows(
            table_a, model, sample, tag=f"{replicate}a"
        )
        rows_b = _cluster_slope_rows(
            table_b, model, sample, tag=f"{replicate}b"
        )
        difference = conditional_logit(rows_a).beta - conditional_logit(rows_b).beta
        if math.isfinite(difference):
            estimates.append(difference)
    low, high = _percentile_ci(estimates)
    return {
        "beta_a": beta_a,
        "beta_b": beta_b,
        "difference": point,
        "ci_low": low,
        "ci_high": high,
        "replicates": len(estimates),
    }


def summarize_table(
    table: dict[tuple[str, str], dict[str, bool]],
    *,
    replicates: int = 2000,
    seed: int = 20261108,
) -> dict[str, Any]:
    """Per-model arm rates, slopes, and the s3-s0 contrast."""
    models = models_in(table)
    arm_rates: dict[str, dict[str, Any]] = {}
    for model in models:
        arm_rates[model] = {}
        for arm in SEVERITY_ARMS:
            n, switches, value = rate(table, arm, model=model)
            arm_rates[model][arm] = {
                "n": n,
                "switches": switches,
                "rate": value,
            }
    per_model_slopes: dict[str, Any] = {}
    per_model_bootstrap: dict[str, Any] = {}
    for model in models:
        rows = slope_rows(table, model=model)
        per_model_slopes[model] = conditional_logit(rows).as_dict()
        per_model_bootstrap[model] = bootstrap_slope(
            rows, replicates=replicates, seed=seed
        ).as_dict()
    pooled = conditional_logit(slope_rows(table)).as_dict()
    contrasts: dict[str, Any] = {}
    for model in models:
        contrasts[model] = paired_contrast(
            table, "s3", "s0", model=model, replicates=replicates, seed=seed
        )
    contrasts["pooled"] = paired_contrast(
        table, "s3", "s0", replicates=replicates, seed=seed
    )
    return {
        "arm_switch_rates": arm_rates,
        "slope": {
            "pooled": pooled,
            "per_model": per_model_slopes,
            "per_model_bootstrap": per_model_bootstrap,
        },
        "s3_minus_s0_contrast": contrasts,
    }


def parser_summary(rows: Iterable[LedgerRow]) -> dict[str, Any]:
    """Count parser statuses and duplicate keys per model."""
    counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    keys: dict[str, set[tuple[str, str, int]]] = defaultdict(set)
    duplicates: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row.model_id][row.parser_status or "unknown"] += 1
        key = (row.prefix_id, row.arm, row.step)
        if key in keys[row.model_id]:
            duplicates[row.model_id] += 1
        keys[row.model_id].add(key)
    return {
        model: {
            "status": dict(sorted(status.items())),
            "rows": sum(status.values()),
            "duplicate_keys": duplicates.get(model, 0),
        }
        for model, status in sorted(counts.items())
    }
