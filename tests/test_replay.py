"""Replay comparison and tool-call extraction tests."""

from __future__ import annotations

import json

from toolobs.taubench.replay import (
    compare_observations,
    extract_tool_calls,
    normalize_json,
    normalize_observation,
)


def test_exact_match() -> None:
    result = compare_observations('{"a": 1}', '{"a": 1}')
    assert result.match is True
    assert result.diff == "exact"


def test_json_key_order_is_normalized() -> None:
    result = compare_observations('{"b": 2, "a": 1}', '{"a": 1, "b": 2}')
    assert result.match is True
    assert result.diff == "json_normalized"


def test_float_noise_is_normalized() -> None:
    result = compare_observations('{"price": 47.84}', '{"price": 47.84000000000001}')
    assert result.match is True
    assert result.diff == "json_normalized"


def test_json_value_mismatch_is_not_a_match() -> None:
    result = compare_observations('{"price": 47.84}', '{"price": 48.84}')
    assert result.match is False
    assert result.diff == "json_value_mismatch"


def test_text_whitespace_is_normalized() -> None:
    result = compare_observations("Transfer   successful", "transfer successful")
    assert result.match is True
    assert result.diff == "text_normalized"


def test_json_vs_text_is_not_a_match() -> None:
    result = compare_observations('{"a": 1}', "not json")
    assert result.match is False
    assert result.diff == "json_vs_text"


def test_replayed_error_taxonomy() -> None:
    result = compare_observations('{"a": 1}', "Error: user not found")
    assert result.match is False
    assert result.diff == "replayed_error"


def test_normalize_observation_kinds() -> None:
    assert normalize_observation('{"a": 1}')[1] == "json"
    assert normalize_observation("Error: nope")[1] == "text"


def test_normalize_json_rounds_floats() -> None:
    assert normalize_json({"x": 1.23456789}) == {"x": 1.234568}


def test_extract_tool_calls_preserves_order_and_parses_arguments() -> None:
    messages = [
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "function": {
                        "name": "get_order_details",
                        "arguments": json.dumps({"order_id": "#W1"}),
                    }
                }
            ],
        },
        {"role": "tool", "content": "{}"},
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "function": {
                        "name": "calculate",
                        "arguments": json.dumps({"expression": "1 + 1"}),
                    }
                }
            ],
        },
    ]
    calls, errors = extract_tool_calls(messages)
    assert calls == [
        ("get_order_details", {"order_id": "#W1"}),
        ("calculate", {"expression": "1 + 1"}),
    ]
    assert errors == 0


def test_extract_tool_calls_counts_bad_arguments() -> None:
    messages = [
        {
            "role": "assistant",
            "tool_calls": [{"function": {"name": "calculate", "arguments": "not json"}}],
        }
    ]
    calls, errors = extract_tool_calls(messages)
    assert calls == [("calculate", {})]
    assert errors == 1
