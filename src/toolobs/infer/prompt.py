"""Next-decision prompt construction.

The prompt is the frozen scrubbed prefix plus one deterministic instruction that
asks for exactly one next action as JSON. Tool schemas are serialized into the
system message so the same prompt shape works across the three model families;
no model-specific tool-call grammar is required.
"""

from __future__ import annotations

import copy
import json
from typing import Any

from ..hashing import canonical_json, sha256_text

PROMPT_VERSION = "toolresult-next-decision-v3"

NEXT_ACTION_TAIL = "Respond now with exactly one JSON object for the next action."


def _instruction(tools_info: list[dict[str, Any]]) -> str:
    tools_json = canonical_json(tools_info)
    return (
        "You are continuing the conversation at the decision point immediately after the "
        "tool observation above. Choose the single next action.\n\n"
        "Respond with exactly one JSON object and no other text. Valid forms:\n"
        '{"tool": "<tool_name>", "arguments": { ... }}\n'
        '{"final_answer": "<answer>"}\n\n'
        "Use only the tools listed below. Do not invent a tool name. Do not explain your "
        "choice outside the JSON object.\n\n"
        f"Available tools:\n{tools_json}"
    )


def _canonical_arguments(raw: Any) -> Any:
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def normalize_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Render historical tool calls and results as a plain chat transcript.

    τ-bench histories use OpenAI-style assistant ``tool_calls`` with JSON-string
    arguments and sometimes ``content: null``. Qwen's template expects a mapping,
    Llama's expects string content, and Ministral's validator rejects the original
    tool-call ids. Rendering calls as "I called ..." text, tool results as user
    turns with a ``[tool result: name]`` marker, and a final user instruction turn
    gives all three families the same valid transcript without template-specific
    tool grammar; Ministral otherwise emits an empty completion when the last turn
    is a bare tool result.
    """
    normalized: list[dict[str, Any]] = []
    for message in copy.deepcopy(messages):
        content = message.get("content")
        message["content"] = "" if content is None else content
        calls = message.pop("tool_calls", None) or []
        if message.get("role") == "assistant" and not message["content"].strip() and not calls:
            # Six historical assistant turns are empty; they carry no information
            # and Mistral's tokenizer rejects them.
            continue
        if message.get("role") == "tool":
            name = str(message.get("name") or "")
            marker = f"[tool result: {name}]" if name else "[tool result]"
            message["role"] = "user"
            message["content"] = f"{marker}\n{message['content']}"
            message.pop("name", None)
            message.pop("tool_call_id", None)
        if calls:
            blocks: list[str] = []
            for call in calls:
                function = call.get("function") or {}
                name = function.get("name") or call.get("name") or ""
                arguments = _canonical_arguments(
                    function.get("arguments", call.get("arguments", {}))
                )
                payload = canonical_json(arguments)
                blocks.append(f"I called {name} with {payload}.")
            body = message["content"].rstrip()
            message["content"] = "\n\n".join(part for part in (body, *blocks) if part)
        if message.get("tool_call_id") is None:
            message.pop("tool_call_id", None)
        normalized.append(message)
    return normalized


def build_prompt_messages(
    messages: list[dict[str, Any]],
    tools_info: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Append the next-decision instruction to the prefix's system message."""
    updated = normalize_messages(messages)
    instruction = _instruction(tools_info)
    if updated and updated[0].get("role") == "system":
        content = updated[0].get("content")
        content = content if isinstance(content, str) else ""
        updated[0]["content"] = f"{content.rstrip()}\n\n{instruction}"
    else:
        updated.insert(0, {"role": "system", "content": instruction})
    updated.append({"role": "user", "content": NEXT_ACTION_TAIL})
    return updated


def prompt_hash(messages: list[dict[str, Any]]) -> str:
    """Stable hash of the exact prompt messages."""
    return sha256_text(canonical_json(messages))
