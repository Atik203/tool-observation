"""Stratified sampler contract tests."""

from __future__ import annotations

from toolobs.harvest.sample import (
    allocate_quotas,
    cap_by_task,
    sample_candidates,
    stratum_key,
    validate_sample,
)
from toolobs.schemas import PrefixRecord


def _record(
    domain: str,
    task_id: str,
    donor: str,
    bucket: str,
    family: str,
    index: int,
) -> PrefixRecord:
    return PrefixRecord(
        prefix_id=f"{domain}-{task_id}-{donor}-{bucket}-{family}-{index:03d}",
        domain=domain,
        task_id=task_id,
        trajectory_id=f"{domain}:{donor}:{task_id}:0",
        donor=donor,
        trial=0,
        step_index=index,
        tool_name="get_order_details" if domain == "retail" else "get_reservation_details",
        observation_json="{}",
        factual_continuation="{}",
        raw_observation="{}",
        tool_family=family,
        step_index_bucket=bucket,
        critical_fields=["$.status"],
        noncritical_fields=["$.note"],
        eligible=True,
        replay_match=True,
    )


def _frame() -> list[PrefixRecord]:
    rows: list[PrefixRecord] = []
    for domain in ("airline", "retail"):
        for task in range(4):
            for donor in ("gpt-4o", "claude-3.5-sonnet"):
                for bucket in ("early", "mid"):
                    for family in ("read", "write"):
                        for index in range(3):
                            rows.append(
                                _record(domain, str(task), donor, bucket, family, index)
                            )
    return rows


def test_allocate_quotas_respects_capacity_and_total() -> None:
    quotas = allocate_quotas({"a": 100, "b": 2, "c": 1}, 20)
    assert sum(quotas.values()) == 20
    assert quotas["b"] <= 2
    assert quotas["c"] <= 1
    assert quotas["b"] >= 1
    assert quotas["c"] >= 1


def test_cap_by_task_never_exceeds_cap() -> None:
    rows = cap_by_task(_frame(), cap=2, seed=20261108)
    counts: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row.domain, row.task_id)
        counts[key] = counts.get(key, 0) + 1
    assert max(counts.values()) <= 2


def test_sample_is_deterministic_and_disjoint() -> None:
    first = sample_candidates(
        _frame(),
        primary_targets={"airline": 12, "retail": 12},
        reserve_targets={"airline": 4, "retail": 4},
        cap=4,
        seed=20261108,
    )
    second = sample_candidates(
        _frame(),
        primary_targets={"airline": 12, "retail": 12},
        reserve_targets={"airline": 4, "retail": 4},
        cap=4,
        seed=20261108,
    )
    assert [row.prefix_id for row in first.primary] == [row.prefix_id for row in second.primary]
    assert [row.prefix_id for row in first.reserve] == [row.prefix_id for row in second.reserve]
    primary_ids = {row.prefix_id for row in first.primary}
    reserve_ids = {row.prefix_id for row in first.reserve}
    assert primary_ids.isdisjoint(reserve_ids)
    assert validate_sample(
        first,
        primary_targets={"airline": 12, "retail": 12},
        reserve_targets={"airline": 4, "retail": 4},
        cap=4,
    ) == []


def test_stratum_key_uses_all_four_dimensions() -> None:
    row = _record("retail", "1", "gpt-4o", "mid", "read", 0)
    assert stratum_key(row) == "retail|gpt-4o|mid|read"


def test_sample_reports_shortfall_when_supply_is_insufficient() -> None:
    rows = _frame()[:5]
    result = sample_candidates(
        rows,
        primary_targets={"airline": 100, "retail": 100},
        reserve_targets={"airline": 10, "retail": 10},
        cap=3,
    )
    assert result.stats["shortfalls"]
    assert len(result.primary) < 200
