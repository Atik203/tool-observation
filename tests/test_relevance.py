"""Relevance and PII-path policy tests."""

from __future__ import annotations

from toolobs.harvest.relevance import (
    PiiPolicy,
    apply_relevance,
    evaluate_relevance,
    flatten_leaves,
    normalize_scalar,
    normalize_text,
    value_in_text,
)
from toolobs.hashing import canonical_json
from toolobs.schemas import PrefixRecord


def _record(
    observation,
    content: str,
    *,
    tool_name: str = "get_order_details",
    observation_format: str = "json",
) -> PrefixRecord:
    return PrefixRecord(
        prefix_id="p1",
        domain="retail",
        task_id="1",
        trajectory_id="retail:gpt-4o:1:0",
        donor="gpt-4o",
        trial=0,
        step_index=0,
        tool_name=tool_name,
        observation_json=canonical_json(observation) if observation_format == "json" else "",
        factual_continuation=canonical_json({"role": "assistant", "content": content}),
        observation_format=observation_format,
        raw_observation=canonical_json(observation) if observation_format == "json" else content,
    )


def test_flatten_leaves_keeps_concrete_paths_and_patterns() -> None:
    leaves = list(flatten_leaves({"items": [{"price": 1.5}], "status": "ok"}))
    assert [(leaf.json_path, leaf.path_pattern) for leaf in leaves] == [
        ("$.items[0].price", "$.items[].price"),
        ("$.status", "$.status"),
    ]


def test_value_matching_normalizes_case_and_digit_commas() -> None:
    text = normalize_text("The total is $4,986.00 and the status is DELIVERED.")
    assert value_in_text(4986, text)
    assert value_in_text("delivered", text)
    assert not value_in_text("cancelled", text)
    assert not value_in_text(0, text)


def test_numeric_normalization_handles_trailing_zero() -> None:
    assert normalize_scalar(47.0) == "47"
    assert value_in_text(47, normalize_text("price 47.00"))
    assert value_in_text(47.84, normalize_text("price 47.840"))


def test_pii_policy_matches_list_and_wildcard_paths() -> None:
    policy = PiiPolicy(("$.address.*", "$.payment_history[].payment_method_id"))
    assert policy.matches("$.address.city")
    assert policy.matches("$.payment_history[].payment_method_id")
    assert not policy.matches("$.payment_history[].amount")
    assert not policy.matches("$.items[].price")


def test_relevance_marks_used_and_noncritical_fields() -> None:
    observation = {
        "status": "delivered",
        "items": [{"price": 47.84, "options": {"color": "blue"}}],
        "address": {"city": "New York", "zip": "10083"},
        "payment_history": [{"payment_method_id": "credit_card_123", "amount": 47.84}],
    }
    record = _record(observation, "The order is delivered and the price is $47.84.")
    policy = PiiPolicy(("$.address.*", "$.payment_history[].payment_method_id"))
    result = evaluate_relevance(record, pii_policy=policy)
    assert result.eligible is True
    assert result.exclusion_reason == ""
    assert "$.status" in result.critical_fields
    assert "$.items[0].price" in result.critical_fields
    assert "$.items[0].options.color" in result.noncritical_fields
    assert "$.address.city" in result.pii_fields
    assert "$.payment_history[0].payment_method_id" in result.pii_fields
    assert "$.address.city" not in result.noncritical_fields


def test_relevance_excludes_used_pii() -> None:
    observation = {
        "status": "delivered",
        "payment_history": [{"payment_method_id": "credit_card_123", "amount": 47.84}],
    }
    record = _record(observation, "I used credit_card_123 for the refund.")
    policy = PiiPolicy(("$.payment_history[].payment_method_id",))
    result = evaluate_relevance(record, pii_policy=policy)
    assert result.eligible is False
    assert result.exclusion_reason == "decision_critical_pii"


def test_incidental_pii_is_allowed_when_non_pii_content_is_used() -> None:
    observation = {
        "status": "delivered",
        "payment_history": [{"payment_method_id": "credit_card_123", "amount": 47.84}],
    }
    record = _record(observation, "The order is delivered; I used credit_card_123.")
    policy = PiiPolicy(("$.payment_history[].payment_method_id",))
    result = evaluate_relevance(record, pii_policy=policy)
    assert result.eligible is True
    assert result.critical_fields == ["$.status"]


def test_pii_target_tool_is_excluded_even_with_other_used_fields() -> None:
    observation = {
        "status": "pending",
        "address": {"city": "New York"},
    }
    record = _record(
        observation,
        "The pending order ships to New York.",
        tool_name="modify_pending_order_address",
    )
    policy = PiiPolicy(("$.address.*",))
    result = evaluate_relevance(record, pii_policy=policy)
    assert result.eligible is False
    assert result.exclusion_reason == "decision_critical_pii"


def test_relevance_rejects_profile_and_text_observations() -> None:
    profile = _record({}, "", tool_name="get_user_details")
    assert evaluate_relevance(profile).exclusion_reason == "profile_tool"
    text = _record({}, "ok", observation_format="text")
    assert evaluate_relevance(text).exclusion_reason == "text_observation"


def test_apply_relevance_updates_record() -> None:
    record = _record({"status": "delivered"}, "The order is delivered.")
    result = apply_relevance(record)
    assert result.eligible is True
    assert record.eligible is True
    assert record.critical_fields == ["$.status"]
