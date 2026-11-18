"""Prompt, parser, and ledger-runner tests."""

from __future__ import annotations

import re

from toolobs.hashing import canonical_json
from toolobs.infer.ledger import read_ledger
from toolobs.infer.parse_output import (
    decision_signature,
    parse_decision,
    signature_hash,
    signatures_differ,
)
from toolobs.infer.prompt import build_prompt_messages, normalize_messages
from toolobs.infer.runner import (
    FakeBackend,
    Generation,
    response_regex_for_tools,
    run_rendered_rows,
)
from toolobs.infer.vllm_backend import chat_template_kwargs

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Get order details.",
            "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}},
        },
    }
]

TOOLS_WITH_THINK = TOOLS + [
    {
        "type": "function",
        "function": {
            "name": "think",
            "description": "Reason about the next step.",
            "parameters": {"type": "object", "properties": {"thought": {"type": "string"}}},
        },
    }
]


def test_prompt_appends_instruction_and_preserves_prefix() -> None:
    messages = [
        {"role": "system", "content": "policy"},
        {"role": "user", "content": "hello"},
        {"role": "tool", "name": "get_order_details", "content": "{}"},
    ]
    prompt = build_prompt_messages(messages, TOOLS)
    assert prompt[0]["role"] == "system"
    assert prompt[0]["content"].startswith("policy")
    assert "Respond with exactly one JSON object" in prompt[0]["content"]
    assert "get_order_details" in prompt[0]["content"]
    assert messages[0]["content"] == "policy"
    assert len(prompt) == len(messages) + 1
    assert prompt[-1]["role"] == "user"
    assert prompt[-1]["content"].startswith("Respond now with exactly one JSON object")


def test_parse_tool_call() -> None:
    parsed = parse_decision(
        '{"tool": "get_order_details", "arguments": {"order_id": "#W1"}}'
    )
    assert parsed.status == "ok"
    assert parsed.tool_name == "get_order_details"
    assert parsed.arguments == {"order_id": "#w1"}


def test_parse_final_answer() -> None:
    parsed = parse_decision('{"final_answer": "The order is delivered."}')
    assert parsed.status == "ok"
    assert parsed.final_answer == "The order is delivered."
    assert decision_signature(parsed).action_verb == "respond"


def test_parse_fenced_json() -> None:
    parsed = parse_decision('```json\n{"final_answer": "done"}\n```')
    assert parsed.status == "ok"
    assert parsed.final_answer == "done"


def test_parse_openai_style_arguments_string() -> None:
    parsed = parse_decision(
        '{"name": "get_order_details", "arguments": "{\\"order_id\\": \\"#W2\\"}"}'
    )
    assert parsed.status == "ok"
    assert parsed.arguments == {"order_id": "#w2"}


def test_parse_refusal_and_empty() -> None:
    assert parse_decision("I cannot comply with that request.").status == "refusal"
    assert parse_decision("   ").status == "empty"
    assert parse_decision("not json").status == "parse_error"


def test_normalize_messages_renders_tool_calls_as_text() -> None:
    messages = [
        {"role": "system", "content": "policy"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "function": {
                        "name": "get_user_details",
                        "arguments": '{"user_id": "user_abc"}',
                    },
                    "id": "call_1",
                    "type": "function",
                }
            ],
        },
        {"role": "tool", "content": "{}"},
    ]
    normalized = normalize_messages(messages)
    assert normalized[0]["content"] == "policy"
    assert normalized[1]["content"].startswith("I called get_user_details with")
    assert '"user_id":"user_abc"' in normalized[1]["content"]
    assert "tool_calls" not in normalized[1]
    assert "tool_call_id" not in normalized[1]
    assert normalized[2]["role"] == "user"
    assert normalized[2]["content"].startswith("[tool result]")
    # The frozen input is not mutated.
    assert messages[1]["content"] is None
    assert messages[1]["tool_calls"]
    assert messages[2]["role"] == "tool"


def test_normalize_messages_drops_empty_assistant_turn() -> None:
    normalized = normalize_messages(
        [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": None},
            {"role": "user", "content": "again"},
        ]
    )
    assert [message["role"] for message in normalized] == ["user", "user"]


def test_parse_literal_newline_inside_json_string() -> None:
    parsed = parse_decision('{"final_answer": "line one\nline two"}')
    assert parsed.status == "ok"
    assert "line one" in parsed.final_answer


def test_final_answer_signature_uses_status_slots() -> None:
    cancelled = parse_decision('{"final_answer": "The reservation was cancelled and refunded."}')
    cancelled_paraphrase = parse_decision(
        '{"final_answer": "Cancelled; the refund is on its way."}'
    )
    # Same decision, different prose: no decision change.
    assert signatures_differ(decision_signature(cancelled), decision_signature(cancelled_paraphrase)) is False

    modified = parse_decision('{"final_answer": "The reservation was modified."}')
    assert signatures_differ(decision_signature(cancelled), decision_signature(modified)) is True

    # Decision-critical amounts are slots: the blind audit showed amount conflicts
    # (refund/total/price difference) are decision changes, not paraphrase.
    refund_100 = parse_decision('{"final_answer": "Refunded $100."}')
    refund_200 = parse_decision('{"final_answer": "Refunded $200."}')
    assert signatures_differ(decision_signature(refund_100), decision_signature(refund_200)) is True

    # Same amount in a different format canonicalizes to the same slot.
    refund_100_alt = parse_decision('{"final_answer": "Refunded 100 dollars."}')
    assert signature_hash(refund_100) == signature_hash(refund_100_alt)

    # The action verb is positional (earliest act term), not vocabulary order.
    keep_note = parse_decision(
        '{"final_answer": "I have cancelled the booking. Keep the receipt."}'
    )
    assert decision_signature(keep_note).action_verb == "cancel"


def test_tool_signature_ignores_prose_arguments() -> None:
    first = parse_decision(
        '{"tool": "transfer_to_human_agents", "arguments": {"summary": "User wants to cancel insurance, but cannot be done through the system"}}'
    )
    second = parse_decision(
        '{"tool": "transfer_to_human_agents", "arguments": {"summary": "User wants to cancel insurance, but cannot be done through automated means"}}'
    )
    assert signature_hash(first) == signature_hash(second)

    left = parse_decision(
        '{"tool": "book_reservation", "arguments": {"reservation_id": "ABC123", "note": "a long free text note that is not a decision slot at all"}}'
    )
    right = parse_decision(
        '{"tool": "book_reservation", "arguments": {"reservation_id": "XYZ999", "note": "a different long free text note that is not a decision slot"}}'
    )
    assert signature_hash(left) != signature_hash(right)


def test_signature_hash_is_key_order_independent() -> None:
    left = parse_decision('{"tool": "f", "arguments": {"b": 2, "a": 1}}')
    right = parse_decision('{"tool": "f", "arguments": {"a": 1, "b": 2}}')
    assert signature_hash(left) == signature_hash(right)


def test_chat_template_kwargs_default_and_passthrough() -> None:
    assert chat_template_kwargs({}) == {}
    assert chat_template_kwargs({"chat_template_kwargs": {"enable_thinking": False}}) == {
        "enable_thinking": False
    }


def test_fake_runner_writes_ledger(tmp_path) -> None:
    rows = [
        {
            "prefix_id": "airline-gpt4o-t0-r00-s000-getreservationdetails",
            "domain": "airline",
            "arm": "V",
            "messages_json": canonical_json(
                [
                    {"role": "system", "content": "policy"},
                    {"role": "tool", "name": "get_reservation_details", "content": "{}"},
                ]
            ),
        }
    ]
    backend = FakeBackend(
        '{"tool": "get_reservation_details", "arguments": {"reservation_id": "ABC"}}'
    )
    ledger = tmp_path / "ledger.jsonl"
    stats = run_rendered_rows(
        rows,
        backend=backend,
        model_id="qwen",
        run_id="run-1",
        stage="calibration",
        manifest_hash="m" * 64,
        ledger_path=ledger,
        tools_by_domain={"airline": TOOLS},
    )
    assert stats.total == 1
    assert stats.parsed == 1
    assert backend.calls and "Respond with exactly one JSON object" in backend.calls[0][0]["content"]
    stored = read_ledger(ledger)
    assert len(stored) == 1
    assert stored[0].parsed is True
    assert stored[0].parser_status == "ok"
    assert stored[0].signature_hash
    assert stored[0].manifest_hash == "m" * 64


class _BatchRecordingBackend:
    def __init__(self) -> None:
        self.batch_sizes: list[int] = []
        self.regexes: list[str | None] = []
        self.prompts: list[list[dict]] = []

    def generate(self, prompts, **kwargs):
        self.batch_sizes.append(len(prompts))
        self.regexes.append(kwargs.get("response_regex"))
        self.prompts.extend(prompts)
        return [Generation(text='{"final_answer": "ok"}') for _ in prompts]


def test_response_regex_allows_tool_or_final_answer_but_not_think() -> None:
    pattern = response_regex_for_tools(TOOLS)
    assert pattern is not None
    assert re.fullmatch(pattern, '{"tool": "get_order_details", "arguments": {"order_id": "#w1"}}')
    assert re.fullmatch(pattern, '{"final_answer": "done"}')
    assert re.fullmatch(pattern, '{"tool": "think", "arguments": {"thought": "hmm"}}') is None


def test_runner_excludes_think_and_passes_regex(tmp_path) -> None:
    rows = [
        {
            "prefix_id": "airline-a",
            "domain": "airline",
            "arm": "V",
            "messages_json": canonical_json(
                [
                    {"role": "system", "content": "policy"},
                    {"role": "tool", "name": "get_order_details", "content": "{}"},
                ]
            ),
        }
    ]
    backend = _BatchRecordingBackend()
    run_rendered_rows(
        rows,
        backend=backend,
        model_id="qwen",
        run_id="run-regex",
        stage="calibration",
        manifest_hash="m" * 64,
        ledger_path=tmp_path / "ledger.jsonl",
        tools_by_domain={"airline": TOOLS_WITH_THINK},
        excluded_tools=["think"],
    )
    assert backend.regexes and backend.regexes[0] is not None
    assert "think" not in backend.prompts[0][0]["content"]
    assert re.fullmatch(
        backend.regexes[0], '{"tool": "think", "arguments": {"thought": "hmm"}}'
    ) is None


def test_runner_resumes_without_duplicating(tmp_path) -> None:
    def row(prefix_id: str, arm: str) -> dict:
        return {
            "prefix_id": prefix_id,
            "domain": "airline",
            "arm": arm,
            "messages_json": canonical_json(
                [
                    {"role": "system", "content": "policy"},
                    {"role": "tool", "name": "get_reservation_details", "content": "{}"},
                ]
            ),
        }

    rows = [row("airline-a", "V"), row("airline-a", "s0"), row("airline-b", "V")]
    ledger = tmp_path / "ledger.jsonl"
    backend = FakeBackend('{"final_answer": "ok"}')
    common = dict(
        backend=backend,
        model_id="qwen",
        run_id="run-3",
        stage="calibration",
        manifest_hash="m" * 64,
        ledger_path=ledger,
        tools_by_domain={"airline": TOOLS},
    )
    first = run_rendered_rows(rows[:2], **common)
    assert first.total == 2
    completed = {
        (stored.prefix_id, stored.arm, stored.step) for stored in read_ledger(ledger)
    }
    resumed = run_rendered_rows(rows, skip_completed=completed, **common)
    assert resumed.total == 1
    stored = read_ledger(ledger)
    assert len(stored) == 3
    assert sorted((item.prefix_id, item.arm) for item in stored) == [
        ("airline-a", "V"),
        ("airline-a", "s0"),
        ("airline-b", "V"),
    ]


def test_runner_batches_same_domain_rows(tmp_path) -> None:
    def row(prefix_id: str, arm: str) -> dict:
        return {
            "prefix_id": prefix_id,
            "domain": "airline",
            "arm": arm,
            "messages_json": canonical_json(
                [
                    {"role": "system", "content": "policy"},
                    {"role": "tool", "name": "get_reservation_details", "content": "{}"},
                ]
            ),
        }

    rows = [row("airline-a", "V"), row("airline-a", "s0"), row("airline-b", "V")]
    backend = _BatchRecordingBackend()
    ledger = tmp_path / "ledger.jsonl"
    stats = run_rendered_rows(
        rows,
        backend=backend,
        model_id="qwen",
        run_id="run-2",
        stage="calibration",
        manifest_hash="m" * 64,
        ledger_path=ledger,
        tools_by_domain={"airline": TOOLS},
        batch_size=2,
    )
    assert backend.batch_sizes == [2, 1]
    assert stats.total == 3
    assert len(read_ledger(ledger)) == 3
