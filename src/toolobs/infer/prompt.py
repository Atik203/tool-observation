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

PROMPT_VERSION = "toolresult-next-decision-v2"


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
    """Make historical tool calls plain text so every chat template renders them.

    τ-bench histories use OpenAI-style assistant ``tool_calls`` with JSON-string
    arguments and sometimes ``content: null``. Qwen's template expects a mapping,
    Llama's expects string content, and Ministral's backend drops the field
    silently. Rendering each call as a canonical text block gives all three
    families the same history without template-specific tool-call handling.
    """
    normalized: list[dict[str, Any]] = []
    for message in copy.deepcopy(messages):
        content = message.get("content")
        message["content"] = "" if content is None else content
        calls = message.pop("tool_calls", None) or []
        if calls:
            blocks: list[str] = []
            for call in calls:
                function = call.get("function") or {}
                name = function.get("name") or call.get("name") or ""
                arguments = _canonical_arguments(
                    function.get("arguments", call.get("arguments", {}))
                )
                payload = canonical_json({"name": name, "arguments": arguments})
                blocks.append(f"<tool_call>\n{payload}\n</tool_call>")
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
    return updated


def prompt_hash(messages: list[dict[str, Any]]) -> str:
    """Stable hash of the exact prompt messages."""
    return sha256_text(canonical_json(messages))
