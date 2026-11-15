"""Prompt, parser, and ledger-runner tests."""

from __future__ import annotations

from toolobs.hashing import canonical_json
from toolobs.infer.ledger import read_ledger
from toolobs.infer.parse_output import (
    decision_signature,
    parse_decision,
    signature_hash,
)
from toolobs.infer.prompt import build_prompt_messages, normalize_messages
from toolobs.infer.runner import FakeBackend, Generation, run_rendered_rows
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
    assert len(prompt) == len(messages)


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
    assert normalized[1]["content"].startswith("<tool_call>")
    assert '"name":"get_user_details"' in normalized[1]["content"]
    assert '"user_id":"user_abc"' in normalized[1]["content"]
    assert "tool_calls" not in normalized[1]
    assert "tool_call_id" not in normalized[1]
    assert normalized[2]["role"] == "user"
    assert normalized[2]["content"].startswith("[tool result]")
    # The frozen input is not mutated.
    assert messages[1]["content"] is None
    assert messages[1]["tool_calls"]
    assert messages[2]["role"] == "tool"


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

    def generate(self, prompts, **kwargs):
        self.batch_sizes.append(len(prompts))
        return [Generation(text='{"final_answer": "ok"}') for _ in prompts]


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
