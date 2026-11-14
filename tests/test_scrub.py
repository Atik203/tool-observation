"""PII scrubber tests."""

from __future__ import annotations

import json

from toolobs.harvest.parse import Trajectory
from toolobs.harvest.relevance import PiiPolicy
from toolobs.harvest.scrub import (
    PiiMap,
    build_pii_map,
    make_token,
    scrub_candidate,
    scrub_message,
    scrub_text,
)
from toolobs.hashing import canonical_json
from toolobs.schemas import PrefixRecord

POLICY = PiiPolicy(
    (
        "$.user_id",
        "$.passengers[].first_name",
        "$.passengers[].last_name",
        "$.passengers[].dob",
        "$.payment_history[].payment_id",
        "$.email",
    )
)


def _record(observation, continuation: str) -> PrefixRecord:
    return PrefixRecord(
        prefix_id="p1",
        domain="airline",
        task_id="1",
        trajectory_id="airline:gpt-4o:1:0",
        donor="gpt-4o",
        trial=0,
        step_index=0,
        tool_name="get_reservation_details",
        observation_json=canonical_json(observation),
        factual_continuation=canonical_json({"role": "assistant", "content": continuation}),
        observation_format="json",
        raw_observation=canonical_json(observation),
    )


def test_token_is_deterministic() -> None:
    assert make_token("person", "Chen") == make_token("person", "Chen")
    assert make_token("person", "Chen") != make_token("person", "Jackson")
    assert make_token("person", "Chen").startswith("person_")


def test_pii_map_replaces_names_and_payment_ids() -> None:
    pii_map = PiiMap()
    pii_map.add_name("Chen", "Jackson")
    pii_map.add("payment", "gift_card_123")
    text = pii_map.replace("Chen Jackson paid with gift_card_123.")
    assert "Chen" not in text
    assert "Jackson" not in text
    assert "gift_card_123" not in text
    assert "person_" in text
    assert "payment_" in text


def test_scrub_text_handles_email_and_phone() -> None:
    pii_map = PiiMap()
    text = scrub_text("Email chen@example.com or call +1 555-123-4567.", pii_map)
    assert "chen@example.com" not in text
    assert "555-123-4567" not in text
    assert "email_" in text
    assert "phone_" in text


def test_scrub_message_scrubs_tool_json_and_arguments() -> None:
    pii_map = PiiMap()
    pii_map.add_name("Chen", "Jackson")
    pii_map.add("payment", "gift_card_123")
    message = {
        "role": "tool",
        "name": "get_reservation_details",
        "content": json.dumps(
            {
                "user_id": "chen_jackson_3290",
                "passengers": [{"first_name": "Chen", "last_name": "Jackson", "dob": "1956-07-07"}],
                "payment_history": [{"payment_id": "gift_card_123", "amount": 10}],
            }
        ),
    }
    scrubbed = scrub_message(message, POLICY, pii_map)
    payload = json.loads(scrubbed["content"])
    assert payload["user_id"].startswith("user_")
    assert payload["passengers"][0]["first_name"].startswith("person_")
    assert payload["passengers"][0]["last_name"].startswith("person_")
    assert payload["passengers"][0]["dob"].startswith("dob_")
    assert payload["payment_history"][0]["payment_id"].startswith("payment_")
    assert payload["payment_history"][0]["amount"] == 10


def test_scrub_candidate_is_deterministic_and_hashes_scrubbed_prefix() -> None:
    observation = {
        "user_id": "chen_jackson_3290",
        "passengers": [{"first_name": "Chen", "last_name": "Jackson", "dob": "1956-07-07"}],
        "payment_history": [{"payment_id": "gift_card_123", "amount": 10}],
    }
    record = _record(observation, "Chen Jackson paid with gift_card_123.")
    messages = [
        {"role": "system", "content": "policy"},
        {"role": "tool", "name": "get_reservation_details", "content": canonical_json(observation)},
    ]
    first_map = PiiMap()
    second_map = PiiMap()
    first = scrub_candidate(record, messages, policy=POLICY, pii_map=first_map)
    second = scrub_candidate(record, messages, policy=POLICY, pii_map=second_map)
    assert first.scrubbed_observation_json == second.scrubbed_observation_json
    assert first.scrubbed_prefix_hash == second.scrubbed_prefix_hash
    assert first.scrubbed_observation_hash == second.scrubbed_observation_hash
    assert "Chen" not in first.scrubbed_observation_json
    assert "gift_card_123" not in first.scrubbed_observation_json


def test_build_pii_map_uses_task_user_record() -> None:
    trajectory = Trajectory(
        trajectory_id="airline:gpt-4o:1:0",
        domain="airline",
        donor="gpt-4o",
        task_id="1",
        trial=0,
        messages=[],
        source_file="historical_trajectories/gpt-4o-airline.json",
        info={"task": {"user_id": "u1"}},
    )
    users = {
        "u1": {
            "name": {"first_name": "Chen", "last_name": "Jackson"},
            "email": "chen@example.com",
            "address": {"address1": "1 Main St", "city": "New York", "zip": "10001"},
            "dob": "1956-07-07",
            "payment_methods": {"credit_card_1": {"id": "credit_card_1", "last_four": "4242"}},
        }
    }
    pii_map = build_pii_map(trajectory, None, policy=POLICY, users=users)
    assert "Chen" in pii_map.mapping
    assert "Chen Jackson" in pii_map.mapping
    assert "chen@example.com" in pii_map.mapping
    assert "credit_card_1" in pii_map.mapping
