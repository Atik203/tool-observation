"""Parser contract tests on a synthetic τ-bench-shaped trajectory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from toolobs.harvest.parse import (
    PROFILE_TOOLS,
    ParseError,
    TrajectoryStore,
    load_trajectory_file,
    make_prefix_id,
    parse_frame,
    parse_trajectories,
    read_jsonl,
    step_index_bucket,
    tool_family,
    trajectory_metadata,
    validate_candidate,
    write_jsonl,
)
from toolobs.hashing import canonical_json, sha256_record


def _payload() -> list[dict]:
    return [
        {
            "task_id": 7,
            "trial": 0,
            "reward": 1.0,
            "info": {"task": {"instruction": "synthetic"}},
            "traj": [
                {"role": "system", "content": "policy"},
                {"role": "user", "content": "hello"},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "get_order_details",
                                "arguments": json.dumps({"order_id": "W1"}),
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "name": "get_order_details",
                    "tool_call_id": "call_1",
                    "content": json.dumps({"order_id": "W1", "status": "delivered"}),
                },
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_2",
                            "type": "function",
                            "function": {"name": "think", "arguments": "{}"},
                        }
                    ],
                },
                {"role": "tool", "name": "think", "tool_call_id": "call_2", "content": ""},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_3",
                            "type": "function",
                            "function": {
                                "name": "search_direct_flight",
                                "arguments": json.dumps({"origin": "SFO"}),
                            },
                        }
                    ],
                },
                {
                    "role": "tool",
                    "name": "search_direct_flight",
                    "tool_call_id": "call_3",
                    "content": "Error: no flights",
                },
                {"role": "assistant", "content": "I cannot find a flight."},
                {
                    "role": "tool",
                    "name": "get_order_details",
                    "tool_call_id": "call_4",
                    "content": "{}",
                },
            ],
        }
    ]


def _write_fixture(tmp_path: Path) -> Path:
    path = tmp_path / "gpt-4o-airline.json"
    path.write_text(json.dumps(_payload()), encoding="utf-8")
    return path


def test_trajectory_metadata_maps_donor_and_domain() -> None:
    assert trajectory_metadata("historical_trajectories/gpt-4o-airline.json") == (
        "airline",
        "gpt-4o",
    )
    assert trajectory_metadata("historical_trajectories/sonnet-35-new-retail.json") == (
        "retail",
        "claude-3.5-sonnet",
    )
    with pytest.raises(ParseError):
        trajectory_metadata("historical_trajectories/unknown-airline.json")


def test_tool_family_and_step_buckets() -> None:
    assert tool_family("get_order_details") == "read"
    assert tool_family("modify_pending_order_items") == "write"
    assert tool_family("find_user_id_by_email") == "lookup"
    assert tool_family("not_a_tool") == "other"
    assert PROFILE_TOOLS == {
        "get_user_details",
        "find_user_id_by_name_zip",
        "find_user_id_by_email",
        "modify_user_address",
    }
    assert [step_index_bucket(i) for i in (0, 2, 3, 6, 7, 100)] == [
        "early",
        "early",
        "mid",
        "mid",
        "late",
        "late",
    ]


def test_prefix_id_is_stable() -> None:
    first = make_prefix_id("airline", "claude-3.5-sonnet", "7", 0, 2, "search_direct_flight")
    second = make_prefix_id("airline", "claude-3.5-sonnet", "7", 0, 2, "search_direct_flight")
    assert first == second
    assert first == "airline-claude35sonnet-t7-r00-s002-searchdirectflight"


def test_candidate_extraction_skips_think_and_missing_continuation(tmp_path: Path) -> None:
    path = _write_fixture(tmp_path)
    trajectories = load_trajectory_file(path, relative_path=path.name)
    assert len(trajectories) == 1
    records = parse_trajectories(trajectories)
    assert [record.tool_name for record in records] == [
        "get_order_details",
        "search_direct_flight",
    ]

    first, second = records
    assert first.step_index == 0
    assert first.step_index_bucket == "early"
    assert first.tool_family == "read"
    assert first.observation_format == "json"
    assert json.loads(first.observation_json) == {"order_id": "W1", "status": "delivered"}
    assert first.continuation_type == "tool_call"
    assert first.tool_call_id == "call_1"
    assert json.loads(first.tool_arguments_json) == {"order_id": "W1"}
    assert first.message_index == 3
    assert first.prefix_hash == sha256_record(trajectories[0].messages[:4])

    assert second.step_index == 2
    assert second.observation_format == "text"
    assert second.observation_json == ""
    assert second.raw_observation == "Error: no flights"
    assert second.continuation_type == "final_answer"
    assert second.factual_continuation == canonical_json(trajectories[0].messages[8])

    assert validate_candidate(first) == []
    assert validate_candidate(second) == []


def test_materialize_prefix_verifies_hash(tmp_path: Path) -> None:
    path = _write_fixture(tmp_path)
    trajectories = load_trajectory_file(path, relative_path=path.name)
    record = parse_trajectories(trajectories)[0]
    store = TrajectoryStore(tmp_path)
    prefix = store.materialize(record)
    assert prefix == trajectories[0].messages[:4]
    assert prefix[-1]["role"] == "tool"


def test_jsonl_round_trip(tmp_path: Path) -> None:
    path = _write_fixture(tmp_path)
    trajectories = load_trajectory_file(path, relative_path=path.name)
    records = parse_trajectories(trajectories)
    out = tmp_path / "candidates.jsonl"
    write_jsonl(records, out)
    restored = read_jsonl(out)
    assert restored == records


def test_parse_frame_counts(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    records, stats = parse_frame(
        tmp_path,
        ("gpt-4o-airline.json",),
    )
    assert len(records) == 2
    assert stats.files == 1
    assert stats.trajectories == 1
    assert stats.tool_messages == 4
    assert stats.candidates == 2
    assert stats.json_parseable == 1
    assert stats.text_observations == 1
    assert stats.think_skipped == 1
    assert stats.no_continuation_skipped == 1
    assert stats.by_domain == {"airline": 2}
    assert stats.by_donor == {"gpt-4o": 2}
    assert stats.by_tool_family == {"read": 2}


def test_duplicate_prefix_ids_are_rejected(tmp_path: Path) -> None:
    _write_fixture(tmp_path)
    with pytest.raises(ParseError):
        parse_frame(tmp_path, ("gpt-4o-airline.json", "gpt-4o-airline.json"))
