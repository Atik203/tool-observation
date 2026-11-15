"""Parse a model's next-decision output into a canonical signature.

The parser accepts the requested JSON object, OpenAI-style tool-call JSON, and
a fenced JSON block. It records parse failures and refusals instead of silently
dropping them.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from ..hashing import sha256_text
from ..schemas import DecisionSignature

_REFUSAL = re.compile(
    r"\b(?:i can't|i cannot|i am unable|i'm unable|unable to comply|"
    r"as an ai|i won't|i will not|sorry, but)\b",
    re.IGNORECASE,
)
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

# Decision-critical status slots for a final answer: the action verbs the answer
# asserts. Stems match inflections ("cancel" matches "cancelled"). Numbers, IDs,
# dates, and generic words such as "succeed" are not slots; silent propagation
# (Y^U) checks the false value against the full output.
_ACTION_TERMS = (
    "cancel",
    "book",
    "modify",
    "confirm",
    "deny",
    "refund",
    "transfer",
    "upgrade",
    "downgrade",
    "exchange",
    "return",
    "keep",
)
_STATUS_TERMS = _ACTION_TERMS


def final_answer_slots(text: str) -> tuple[dict[str, Any], str]:
    """Return decision-critical status slots and the action verb for a final answer."""
    normalized = unicodedata.normalize("NFKC", text or "").lower()
    status = sorted(
        {term for term in _STATUS_TERMS if re.search(rf"\b{re.escape(term)}", normalized)}
    )
    verb = next((term for term in _ACTION_TERMS if term in status), "respond")
    return {"status": status}, verb


@dataclass(slots=True)
class ParsedDecision:
    """One parsed generation."""

    status: str
    tool_name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    final_answer: str = ""
    raw: str = ""
    error: str = ""

    @property
    def parsed(self) -> bool:
        return self.status == "ok"


def _canonical_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _canonical_value(child) for key, child in value.items()}
    if isinstance(value, list):
        return [_canonical_value(child) for child in value]
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, str):
        return unicodedata.normalize("NFKC", value).strip().lower()
    return value


def canonical_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize argument keys, numbers, and entity strings."""
    return _canonical_value(arguments)


def _json_object(text: str) -> dict[str, Any] | None:
    candidate = text.strip()
    if not candidate:
        return None
    fenced = _FENCE.search(candidate)
    if fenced:
        candidate = fenced.group(1).strip()
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            payload = json.loads(candidate[start : end + 1])
        except json.JSONDecodeError:
            return None
    return payload if isinstance(payload, dict) else None


def parse_decision(text: str) -> ParsedDecision:
    """Parse one generation into a tool call or final answer."""
    raw = text or ""
    if not raw.strip():
        return ParsedDecision(status="empty", raw=raw, error="empty output")
    if _REFUSAL.search(raw):
        return ParsedDecision(status="refusal", raw=raw, error="refusal language")

    payload = _json_object(raw)
    if payload is None:
        return ParsedDecision(status="parse_error", raw=raw, error="no JSON object")

    tool_name = payload.get("tool") or payload.get("name")
    arguments = payload.get("arguments", payload.get("args", {}))
    if isinstance(payload.get("tool_calls"), list) and payload["tool_calls"]:
        call = payload["tool_calls"][0]
        if isinstance(call, dict):
            function = call.get("function") or {}
            tool_name = tool_name or function.get("name")
            arguments = function.get("arguments", arguments)
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return ParsedDecision(status="parse_error", raw=raw, error="arguments are not JSON")
    if not isinstance(arguments, dict):
        arguments = {}

    final_answer = payload.get("final_answer", payload.get("answer"))
    if isinstance(tool_name, str) and tool_name.strip():
        return ParsedDecision(
            status="ok",
            tool_name=tool_name.strip(),
            arguments=canonical_arguments(arguments),
            raw=raw,
        )
    if isinstance(final_answer, str) and final_answer.strip():
        return ParsedDecision(status="ok", final_answer=final_answer.strip(), raw=raw)
    return ParsedDecision(status="parse_error", raw=raw, error="no tool or final_answer")


def decision_signature(parsed: ParsedDecision) -> DecisionSignature:
    """Build the canonical signature used for outcome comparison."""
    if parsed.final_answer:
        slots, verb = final_answer_slots(parsed.final_answer)
        return DecisionSignature(
            tool_name="",
            arguments={},
            final_answer_slots=slots,
            action_verb=verb,
        )
    return DecisionSignature(
        tool_name=parsed.tool_name,
        arguments=parsed.arguments,
        final_answer_slots={},
        action_verb="tool_call",
    )


def signature_hash(parsed: ParsedDecision) -> str:
    """Stable hash of a parsed decision signature."""
    return sha256_text(decision_signature(parsed).canonical())


def signature_json(parsed: ParsedDecision) -> str:
    """Canonical JSON of the decision signature, for ledgers."""
    return decision_signature(parsed).canonical()
