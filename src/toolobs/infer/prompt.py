"""Next-decision prompt construction.

The prompt is the frozen scrubbed prefix plus one deterministic instruction that
asks for exactly one next action as JSON. Tool schemas are serialized into the
system message so the same prompt shape works across the three model families;
no model-specific tool-call grammar is required.
"""

from __future__ import annotations

import copy
from typing import Any

from ..hashing import canonical_json, sha256_text

PROMPT_VERSION = "toolresult-next-decision-v1"


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


def build_prompt_messages(
    messages: list[dict[str, Any]],
    tools_info: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Append the next-decision instruction to the prefix's system message."""
    updated = copy.deepcopy(messages)
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
