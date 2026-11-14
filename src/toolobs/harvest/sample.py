"""Deterministic stratified sampling for the frozen 800 + 80 set.

The sampler caps each task-domain at 10 prefixes, then allocates primary and
reserve slots across the preregistered strata (domain, donor, step-index
bucket, tool family). Allocation uses a deterministic D'Hondt-style divisor so
small strata are represented without letting one large stratum dominate.
"""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from ..schemas import PrefixRecord, SampleRecord

DEFAULT_SEED = 20261108
DEFAULT_CAP = 10
DEFAULT_PRIMARY = {"airline": 400, "retail": 400}
DEFAULT_RESERVE = {"airline": 40, "retail": 40}


def stratum_key(record: PrefixRecord) -> str:
    """Return the preregistered stratum label for a prefix."""
    return "|".join(
        (record.domain, record.donor, record.step_index_bucket, record.tool_family)
    )


def is_renderable(record: PrefixRecord) -> bool:
    """A full five-arm prefix needs one critical and one noncritical field."""
    return bool(record.critical_fields) and bool(record.noncritical_fields)


def cap_by_task(
    records: Iterable[PrefixRecord],
    *,
    cap: int = DEFAULT_CAP,
    seed: int = DEFAULT_SEED,
) -> list[PrefixRecord]:
    """Keep at most ``cap`` prefixes per task-domain, deterministically."""
    grouped: dict[tuple[str, str], list[PrefixRecord]] = defaultdict(list)
    for record in records:
        grouped[(record.domain, record.task_id)].append(record)
    kept: list[PrefixRecord] = []
    for (domain, task_id), group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda record: record.prefix_id)
        random.Random(f"{seed}|cap|{domain}|{task_id}").shuffle(ordered)
        kept.extend(ordered[:cap])
    return kept


def allocate_quotas(sizes: dict[str, int], total: int) -> dict[str, int]:
    """Allocate ``total`` slots across strata with capacity ``sizes``."""
    quotas = {key: 0 for key in sizes}
    if total <= 0:
        return quotas
    for _ in range(total):
        available = [key for key in sizes if quotas[key] < sizes[key]]
        if not available:
            break
        best = max(
            available,
            key=lambda key: (sizes[key] / (quotas[key] + 1), key),
        )
        quotas[best] += 1

    # Guarantee at least one slot for every non-empty stratum when possible.
    empty = [key for key in sizes if sizes[key] > 0 and quotas[key] == 0]
    for key in empty:
        donor = max(quotas, key=lambda candidate: (quotas[candidate], candidate))
        if quotas[donor] > 1:
            quotas[donor] -= 1
            quotas[key] = 1
    return quotas


def _select_from_strata(
    records: list[PrefixRecord],
    *,
    target: int,
    seed: int,
    split: str,
    used: set[str],
) -> list[PrefixRecord]:
    available: dict[str, list[PrefixRecord]] = defaultdict(list)
    for record in records:
        if record.prefix_id in used:
            continue
        available[stratum_key(record)].append(record)
    sizes = {key: len(group) for key, group in available.items()}
    quotas = allocate_quotas(sizes, target)
    selected: list[PrefixRecord] = []
    for key in sorted(available):
        group = sorted(available[key], key=lambda record: record.prefix_id)
        random.Random(f"{seed}|{split}|{key}").shuffle(group)
        take = min(quotas.get(key, 0), len(group))
        for record in group[:take]:
            record.split = split
            selected.append(record)
            used.add(record.prefix_id)
    return selected


@dataclass(slots=True)
class SampleResult:
    """Primary and reserve selections plus audit statistics."""

    primary: list[PrefixRecord]
    reserve: list[PrefixRecord]
    stats: dict[str, Any]

    def sample_records(self, seed: int) -> list[SampleRecord]:
        rows: list[SampleRecord] = []
        for record in self.primary + self.reserve:
            rows.append(
                SampleRecord(
                    prefix_id=record.prefix_id,
                    domain=record.domain,
                    task_id=record.task_id,
                    donor=record.donor,
                    step_bucket=record.step_index_bucket,
                    tool_family=record.tool_family,
                    split=record.split,
                    stratum=stratum_key(record),
                    seed=seed,
                )
            )
        return rows


def sample_candidates(
    records: Iterable[PrefixRecord],
    *,
    primary_targets: dict[str, int] | None = None,
    reserve_targets: dict[str, int] | None = None,
    cap: int = DEFAULT_CAP,
    seed: int = DEFAULT_SEED,
    require_renderable: bool = True,
) -> SampleResult:
    """Select primary and reserve sets from matched eligible candidates."""
    primary_targets = dict(primary_targets or DEFAULT_PRIMARY)
    reserve_targets = dict(reserve_targets or DEFAULT_RESERVE)
    all_records = list(records)
    if require_renderable:
        renderable = [record for record in all_records if is_renderable(record)]
    else:
        renderable = all_records
    unrenderable = len(all_records) - len(renderable)
    capped = cap_by_task(renderable, cap=cap, seed=seed)
    by_domain: dict[str, list[PrefixRecord]] = defaultdict(list)
    for record in capped:
        by_domain[record.domain].append(record)

    primary: list[PrefixRecord] = []
    reserve: list[PrefixRecord] = []
    used: set[str] = set()
    shortfalls: dict[str, int] = {}
    for domain in sorted(primary_targets):
        domain_records = by_domain.get(domain, [])
        chosen = _select_from_strata(
            domain_records,
            target=primary_targets[domain],
            seed=seed,
            split="primary",
            used=used,
        )
        primary.extend(chosen)
        if len(chosen) < primary_targets[domain]:
            shortfalls[f"{domain}:primary"] = primary_targets[domain] - len(chosen)

    for domain in sorted(reserve_targets):
        domain_records = by_domain.get(domain, [])
        chosen = _select_from_strata(
            domain_records,
            target=reserve_targets[domain],
            seed=seed,
            split="reserve",
            used=used,
        )
        reserve.extend(chosen)
        if len(chosen) < reserve_targets[domain]:
            shortfalls[f"{domain}:reserve"] = reserve_targets[domain] - len(chosen)

    def counts(rows: list[PrefixRecord], field: str) -> dict[str, int]:
        return dict(sorted(Counter(getattr(row, field) for row in rows).items()))

    stats = {
        "input": len(capped),
        "unrenderable": unrenderable,
        "primary": len(primary),
        "reserve": len(reserve),
        "primary_by_domain": counts(primary, "domain"),
        "reserve_by_domain": counts(reserve, "domain"),
        "primary_by_donor": counts(primary, "donor"),
        "reserve_by_donor": counts(reserve, "donor"),
        "primary_by_tool_family": counts(primary, "tool_family"),
        "reserve_by_tool_family": counts(reserve, "tool_family"),
        "primary_by_step_bucket": counts(primary, "step_index_bucket"),
        "reserve_by_step_bucket": counts(reserve, "step_index_bucket"),
        "primary_strata": len({stratum_key(row) for row in primary}),
        "reserve_strata": len({stratum_key(row) for row in reserve}),
        "shortfalls": dict(sorted(shortfalls.items())),
        "cap": cap,
        "seed": seed,
    }
    return SampleResult(primary=primary, reserve=reserve, stats=stats)


def select_calibration(
    records: Iterable[PrefixRecord],
    *,
    exclude_ids: set[str],
    per_domain: int = 30,
    seed: int = DEFAULT_SEED,
) -> tuple[list[PrefixRecord], dict[str, Any]]:
    """Select a disjoint, renderable calibration set (30/domain by default)."""
    pool = [
        record
        for record in records
        if record.prefix_id not in exclude_ids and is_renderable(record)
    ]
    by_domain: dict[str, list[PrefixRecord]] = defaultdict(list)
    for record in pool:
        by_domain[record.domain].append(record)
    used = set(exclude_ids)
    selected: list[PrefixRecord] = []
    for domain in sorted(by_domain):
        chosen = _select_from_strata(
            by_domain[domain],
            target=per_domain,
            seed=seed,
            split="calibration",
            used=used,
        )
        selected.extend(chosen)
    return selected, {
        "calibration": len(selected),
        "by_domain": dict(sorted(Counter(record.domain for record in selected).items())),
        "available": len(pool),
    }


def validate_sample(
    result: SampleResult,
    *,
    primary_targets: dict[str, int] | None = None,
    reserve_targets: dict[str, int] | None = None,
    cap: int = DEFAULT_CAP,
) -> list[str]:
    """Return contract violations for a sampled set."""
    primary_targets = primary_targets or DEFAULT_PRIMARY
    reserve_targets = reserve_targets or DEFAULT_RESERVE
    problems: list[str] = []
    all_rows = result.primary + result.reserve
    ids = [row.prefix_id for row in all_rows]
    if len(ids) != len(set(ids)):
        problems.append("duplicate prefix ids across primary and reserve")
    if len(result.primary) != sum(primary_targets.values()):
        problems.append(f"primary size {len(result.primary)} != {sum(primary_targets.values())}")
    if len(result.reserve) != sum(reserve_targets.values()):
        problems.append(f"reserve size {len(result.reserve)} != {sum(reserve_targets.values())}")
    for domain, target in primary_targets.items():
        observed = sum(1 for row in result.primary if row.domain == domain)
        if observed != target:
            problems.append(f"primary {domain} {observed} != {target}")
    for domain, target in reserve_targets.items():
        observed = sum(1 for row in result.reserve if row.domain == domain)
        if observed != target:
            problems.append(f"reserve {domain} {observed} != {target}")
    per_task = Counter((row.domain, row.task_id) for row in all_rows)
    over = {key: value for key, value in per_task.items() if value > cap}
    if over:
        problems.append(f"task cap exceeded: {over}")
    for row in all_rows:
        if not row.replay_match:
            problems.append(f"{row.prefix_id}: replay did not match")
        if not row.eligible:
            problems.append(f"{row.prefix_id}: not eligible")
        if not is_renderable(row):
            problems.append(f"{row.prefix_id}: not renderable")
    return problems
