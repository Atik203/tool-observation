"""Second renderer, arm equivalence, and paired analysis tests."""

from __future__ import annotations

from toolobs.analysis.renderer2 import (
    paired_rate_difference,
    slope_rows,
    summarize_table,
    unit_table,
)
from toolobs.hashing import canonical_json
from toolobs.render.perturb import value_set
from toolobs.render.render import build_arms
from toolobs.render.render2 import (
    build_arms2,
    emitted_value_set,
    render_observation2,
)
from toolobs.schemas import LedgerRow, PrefixRecord


def _record() -> PrefixRecord:
    observation = {
        "status": "delivered",
        "price": 47.84,
        "note": "fragile",
        "items": [{"name": "Water Bottle", "options": {"color": "blue"}}],
    }
    return PrefixRecord(
        prefix_id="retail-gpt4o-t1-r00-s001-getorderdetails",
        domain="retail",
        task_id="1",
        trajectory_id="retail:gpt-4o:1:0",
        donor="gpt-4o",
        trial=0,
        step_index=1,
        tool_name="get_order_details",
        observation_json=canonical_json(observation),
        factual_continuation=canonical_json(
            {"role": "assistant", "content": "The order is delivered and costs 47.84."}
        ),
        scrubbed_observation_json=canonical_json(observation),
        critical_fields=["$.status", "$.price", "$.items[0].name"],
        noncritical_fields=["$.note", "$.items[0].options.color"],
        renderer_version="toolresult-prose-v1",
    )


def _ledger(prefix_id: str, model: str, arm: str, decision: dict) -> LedgerRow:
    return LedgerRow(
        run_id="test",
        model_id=model,
        prefix_id=prefix_id,
        arm=arm,
        step=0,
        prompt_hash="x",
        output_text="",
        parsed=True,
        latency_ms=0.0,
        cost_usd=0.0,
        timestamp_utc="2026-11-23T00:00:00+00:00",
        decision_json=canonical_json(decision),
        signature_hash="h",
        parser_status="ok",
    )


def test_render_observation2_emits_every_leaf() -> None:
    observation = {
        "status": "delivered",
        "items": [{"price": 47.84, "options": {"color": "blue"}}],
        "empty": [],
        "missing": None,
    }
    text, emitted = render_observation2(observation)
    assert text.splitlines()[0] == "Observation (field list):"
    assert "status = delivered" in text
    assert "items[0].price = 47.84" in text
    assert "empty = []" in text
    assert "missing = null" in text
    assert value_set(observation) == emitted_value_set(emitted)


def test_render_observation2_surface_differs_from_prose() -> None:
    observation = {"status": "delivered", "items": [{"price": 47.84}]}
    text, _ = render_observation2(observation)
    assert "Observation:" not in text.splitlines()[0]
    assert "- status:" not in text
    assert "items[0].price = 47.84" in text


def test_build_arms2_reproduces_prose_and_same_values() -> None:
    record = _record()
    prose = build_arms(record, seed=20261108)
    flat = build_arms2(record, seed=20261108)
    assert not flat.errors
    assert flat.s0_value_set_ok
    for arm in ("V", "s0", "s1", "s2", "s3"):
        assert flat.prose_observations[arm] == prose.observations[arm]
        assert flat.observations[arm]
    for arm in ("s0", "s1", "s2", "s3"):
        assert flat.observations[arm] != flat.prose_observations[arm]
    assert len(flat.changes) == 3


def test_unit_table_rates_and_slope() -> None:
    rows = []
    for index in range(4):
        prefix = f"p{index}"
        base = {"tool": "lookup", "args": {"id": index}}
        rows.append(_ledger(prefix, "m", "V", base))
        rows.append(_ledger(prefix, "m", "s0", base if index % 2 == 0 else {"tool": "other", "args": {}}))
        rows.append(_ledger(prefix, "m", "s1", base))
        rows.append(_ledger(prefix, "m", "s2", {"tool": "other", "args": {}}))
        rows.append(_ledger(prefix, "m", "s3", {"tool": "other", "args": {}}))
    table = unit_table(rows)
    assert table[("p0", "m")]["s0"] is False
    assert table[("p1", "m")]["s0"] is True
    assert table[("p1", "m")]["s1"] is False
    summary = summarize_table(table, replicates=20, seed=7)
    assert summary["arm_switch_rates"]["m"]["s0"]["switches"] == 2
    assert summary["arm_switch_rates"]["m"]["s3"]["switches"] == 4
    assert len(slope_rows(table)) == 16


def test_paired_rate_difference_is_zero_for_identical_tables() -> None:
    table = {
        ("p0", "m"): {"s0": False},
        ("p1", "m"): {"s0": True},
        ("p2", "m"): {"s0": True},
    }
    result = paired_rate_difference(table, dict(table), "s0", replicates=50, seed=3)
    assert result["n_units"] == 3
    assert result["difference"] == 0.0
    assert result["ci_low"] == 0.0 and result["ci_high"] == 0.0
