"""Renderer and perturbation tests."""

from __future__ import annotations

from toolobs.harvest.relevance import normalize_scalar, value_in_text
from toolobs.hashing import canonical_json
from toolobs.render.perturb import (
    alternative_value,
    delete_path,
    get_path,
    parse_path,
    set_path,
    value_set,
)
from toolobs.render.render import (
    build_arms,
    render_arm_messages,
    render_observation,
    replace_observation,
)
from toolobs.schemas import PrefixRecord


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
        raw_observation=canonical_json(observation),
        scrubbed_observation_json=canonical_json(observation),
        observation_format="json",
        critical_fields=["$.status", "$.price", "$.items[0].name"],
        noncritical_fields=["$.note", "$.items[0].options.color"],
        eligible=True,
        replay_match=True,
    )


def test_parse_get_set_delete_path() -> None:
    value = {"items": [{"price": 1}], "note": "x"}
    assert parse_path("$.items[0].price") == ["items", 0, "price"]
    assert get_path(value, "$.items[0].price") == 1
    set_path(value, "$.items[0].price", 2)
    assert get_path(value, "$.items[0].price") == 2
    delete_path(value, "$.note")
    assert "note" not in value


def test_render_observation_emits_every_leaf() -> None:
    observation = {
        "status": "delivered",
        "items": [{"price": 47.84, "options": {"color": "blue"}}],
        "empty": [],
    }
    text, emitted = render_observation(observation)
    assert "Observation:" in text
    assert "- status:" in text
    assert "- delivered" in text
    assert "- price:" in text
    assert "- 47.84" in text
    expected = sorted(
        (pattern, normalize_scalar(value))
        for pattern, value in emitted
        if normalize_scalar(value) is not None
    )
    assert value_set(observation) == expected


def test_alternative_values_are_plausible_and_different() -> None:
    assert alternative_value("$.status", "delivered", {}, criticality="critical") == "pending"
    assert alternative_value("$.cabin", "economy", {}, criticality="critical") == "business"
    assert alternative_value("$.price", 100, {}, criticality="critical") == 115
    assert alternative_value("$.date", "2024-05-22", {}, criticality="critical") == "2024-05-23"
    assert alternative_value("$.flight_number", "HAT170", {}, criticality="critical") == "HAT171"
    assert alternative_value("$.insurance", "yes", {}, criticality="critical") == "no"
    assert alternative_value("$.payment_id", "card_1", {}, criticality="critical") is None


def test_build_arms_constructs_five_arms_and_three_records() -> None:
    record = _record()
    arms = build_arms(record, seed=20261108)
    assert arms.errors == []
    assert arms.s0_value_set_ok is True
    assert set(arms.observations) == {"V", "s0", "s1", "s2", "s3"}
    assert len(arms.perturbations) == 3
    assert {item.arm for item in arms.perturbations} == {"s1", "s2", "s3"}
    assert arms.perturbations[0].criticality == "noncritical"
    assert arms.perturbations[1].criticality == "critical"
    assert arms.perturbations[2].severity == 3
    assert arms.perturbations[2].json_path_2


def test_s1_field_is_absent_from_continuation() -> None:
    record = _record()
    arms = build_arms(record, seed=20261108)
    s1 = next(item for item in arms.perturbations if item.arm == "s1")
    assert not value_in_text(s1.true_value, record.factual_continuation.lower())


def test_calculate_is_not_renderable() -> None:
    record = PrefixRecord(
        prefix_id="airline-gpt4o-t0-r00-s000-calculate",
        domain="airline",
        task_id="0",
        trajectory_id="airline:gpt-4o:0:0",
        donor="gpt-4o",
        trial=0,
        step_index=0,
        tool_name="calculate",
        observation_json="0.5",
        scrubbed_observation_json="0.5",
        factual_continuation=canonical_json({"role": "assistant", "content": "0.5"}),
        raw_observation="0.5",
        observation_format="json",
        critical_fields=["$"],
        noncritical_fields=[],
    )
    arms = build_arms(record, seed=20261108)
    assert "no_s1_field" in arms.errors


def test_replace_observation_replaces_last_tool_message() -> None:
    messages = [
        {"role": "system", "content": "policy"},
        {"role": "tool", "name": "get_order_details", "content": "{}"},
    ]
    updated = replace_observation(messages, "Observation:\n- status: delivered")
    assert updated[-1]["content"] == "Observation:\n- status: delivered"
    assert messages[-1]["content"] == "{}"


def test_render_arm_messages_hashes_prompts() -> None:
    record = _record()
    arms = build_arms(record, seed=20261108)
    messages = [
        {"role": "system", "content": "policy"},
        {"role": "tool", "name": "get_order_details", "content": "{}"},
    ]
    rows = render_arm_messages(record, messages, arms)
    assert [row.arm for row in rows] == ["V", "s0", "s1", "s2", "s3"]
    assert all(len(row.prompt_hash) == 64 for row in rows)
    assert rows[0].observation_text == record.scrubbed_observation_json
    assert rows[1].observation_text.startswith("Observation:")
