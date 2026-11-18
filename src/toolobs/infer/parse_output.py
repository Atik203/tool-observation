"""Parse a model's next-decision output into a canonical signature.

The parser accepts the requested JSON object, OpenAI-style tool-call JSON, and
a fenced JSON block. It records parse failures and refusals instead of silently
dropping them.

The decision signature follows the preregistration (``Outcome signature``): the
tool name plus canonicalized arguments, or the final answer's normalized action
verb plus decision-critical slots (status claims, money amounts, dates, times,
and identifiers, canonicalized per the prereg). Free-text prose arguments (for
example ``transfer_to_human_agents.summary``) are not decision slots.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from ..hashing import sha256_text
from ..schemas import DecisionSignature

_REFUSAL = re.compile(
    r"\b(?:i can't|i cannot|i am unable|i'm unable|unable to comply|"
    r"as an ai|i won't|i will not|sorry, but)\b",
    re.IGNORECASE,
)
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)

# Decision-critical action verbs. Matching is stem-based and word-bounded; the
# head verb is the earliest act term in the text, not the first in this tuple.
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

# Canonical status claims for final answers (word-bounded, case-folded).
_STATUS_CANON = {
    "pending": "pending",
    "delivered": "delivered",
    "shipped": "shipped",
    "completed": "completed",
    "processing": "processing",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "refunded": "refunded",
    "failed": "failed",
    "denied": "denied",
}

_MONEY_CURRENCY = re.compile(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)")
_MONEY_WORD = re.compile(r"\b([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:usd|dollars?)\b", re.IGNORECASE)
_DATE_ISO = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_DATE_US = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_TIME = re.compile(r"\b(\d{1,2}):(\d{2})(?::\d{2})?\s*(am|pm)?\b", re.IGNORECASE)
_ID_HASH = re.compile(r"#([A-Za-z0-9]{4,})")
_ID_MIXED = re.compile(
    r"\b(?=[A-Za-z0-9]{5,}\b)(?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*[0-9])[A-Za-z0-9]+\b"
)

# Free-text argument keys: prose, not decision slots (e.g. transfer summaries).
_PROSE_ARG_KEYS = frozenset(
    {"summary", "note", "notes", "description", "reason", "message", "explanation", "comment", "comments"}
)

# Action detection looks at the assertion region (the opening of the answer);
# advisory mentions later in a long answer are not the asserted act.
_ACTION_WINDOW = 200


def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text or "")


def _decimal_token(raw: str) -> str | None:
    """Canonical decimal string for a matched numeric token."""
    try:
        value = Decimal(raw.replace(",", ""))
    except InvalidOperation:
        return None
    if value == value.to_integral_value():
        value = value.to_integral_value()
    return format(value.normalize(), "f")


def value_slots(text: str) -> dict[str, list[str]]:
    """Decision-critical value slots from a final answer, canonically formatted."""
    normalized = _normalize_text(text)
    money: list[str] = []
    for match in _MONEY_CURRENCY.finditer(normalized):
        token = _decimal_token(match.group(1))
        if token is not None:
            money.append(token)
    for match in _MONEY_WORD.finditer(normalized):
        token = _decimal_token(match.group(1))
        if token is not None:
            money.append(token)

    dates: list[str] = []
    for match in _DATE_ISO.finditer(normalized):
        dates.append(match.group(1))
    for match in _DATE_US.finditer(normalized):
        month, day, year = match.groups()
        dates.append(f"{year}-{int(month):02d}-{int(day):02d}")

    times: list[str] = []
    for match in _TIME.finditer(normalized):
        hour = int(match.group(1))
        minute = match.group(2)
        suffix = (match.group(3) or "").lower()
        if suffix == "pm" and hour != 12:
            hour += 12
        if suffix == "am" and hour == 12:
            hour = 0
        times.append(f"{hour:02d}:{minute}")

    ids: list[str] = []
    for match in _ID_HASH.finditer(normalized):
        token = match.group(1).lower()
        if token not in ids:
            ids.append(token)
    for match in _ID_MIXED.finditer(normalized):
        token = match.group(0).lower()
        if token not in ids:
            ids.append(token)

    return {
        "money": sorted(set(money)),
        "dates": sorted(set(dates)),
        "times": sorted(set(times)),
        "ids": sorted(set(ids)),
    }


def status_terms(text: str) -> list[str]:
    """Canonical status claims asserted in a final answer."""
    normalized = _normalize_text(text).lower()
    found = {
        canonical
        for term, canonical in _STATUS_CANON.items()
        if re.search(rf"\b{re.escape(term)}\b", normalized)
    }
    return sorted(found)


def head_action(text: str) -> str:
    """Canonical action class of the earliest act term in the assertion region."""
    normalized = _normalize_text(text).lower()[:_ACTION_WINDOW]
    best: tuple[int, str] | None = None
    for term in _ACTION_TERMS:
        match = re.search(rf"\b{re.escape(term)}", normalized)
        if match is not None and (best is None or match.start() < best[0]):
            best = (match.start(), term)
    return best[1] if best is not None else "respond"


def final_answer_slots(text: str) -> tuple[dict[str, Any], str]:
    """Return decision-critical slots and the action verb for a final answer."""
    verb = head_action(text)
    return {
        "action": verb,
        "status": status_terms(text),
        "values": value_slots(text),
    }, verb


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
        text = unicodedata.normalize("NFKC", value).strip()
        # Models sometimes emit nested arguments as JSON-encoded strings.
        if text[:1] in ("{", "["):
            try:
                nested = json.loads(text)
            except json.JSONDecodeError:
                nested = None
            if isinstance(nested, (dict, list)):
                return _canonical_value(nested)
        return text.lower()
    return value


def canonical_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """Canonicalize argument keys, numbers, and entity strings."""
    return _canonical_value(arguments)


def _decision_arguments(arguments: dict[str, Any]) -> dict[str, Any]:
    """Arguments that carry a decision: free-text prose keys are not decision slots."""
    canonical = canonical_arguments(arguments)
    return {
        key: value
        for key, value in canonical.items()
        if str(key).lower() not in _PROSE_ARG_KEYS
    }


def _json_object(text: str) -> dict[str, Any] | None:
    candidate = text.strip()
    if not candidate:
        return None
    fenced = _FENCE.search(candidate)
    if fenced:
        candidate = fenced.group(1).strip()
    try:
        payload = json.loads(candidate, strict=False)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            payload = json.loads(candidate[start : end + 1], strict=False)
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
        arguments=_decision_arguments(parsed.arguments),
        final_answer_slots={},
        action_verb="tool_call",
    )


def signature_hash(parsed: ParsedDecision) -> str:
    """Stable hash of a parsed decision signature."""
    return sha256_text(decision_signature(parsed).canonical())


def signature_json(parsed: ParsedDecision) -> str:
    """Canonical JSON of the decision signature, for ledgers."""
    return decision_signature(parsed).canonical()


def signature_from_json(text: str) -> DecisionSignature:
    """Rebuild a DecisionSignature from the canonical JSON stored in a ledger."""
    try:
        payload = json.loads(text or "{}")
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    arguments = payload.get("args", payload.get("arguments", {}))
    if not isinstance(arguments, dict):
        arguments = {}
    slots = payload.get("slots", {})
    if not isinstance(slots, dict):
        slots = {}
    return DecisionSignature(
        tool_name=str(payload.get("tool") or ""),
        arguments=arguments,
        final_answer_slots=slots,
        action_verb=str(payload.get("verb") or ""),
    )


def _sets_conflict(ref_values: list[str], cur_values: list[str]) -> bool:
    """True when two non-empty value sets contradict each other.

    Additions and omissions are paraphrase (one set contains the other);
    a contradiction is when neither set contains the other.
    """
    ref_set, cur_set = set(ref_values), set(cur_values)
    if not ref_set or not cur_set:
        return False
    return not (ref_set <= cur_set) and not (cur_set <= ref_set)


def signatures_differ(ref: DecisionSignature, cur: DecisionSignature) -> bool:
    """Decision-level comparison used for Y (signature differs from the reference)."""
    ref_is_tool = bool(ref.tool_name)
    cur_is_tool = bool(cur.tool_name)
    if ref_is_tool != cur_is_tool:
        return True
    if ref_is_tool:
        return ref.tool_name != cur.tool_name or ref.arguments != cur.arguments
    if ref.action_verb != cur.action_verb:
        return True
    ref_slots = ref.final_answer_slots or {}
    cur_slots = cur.final_answer_slots or {}
    if _sets_conflict(ref_slots.get("status", []), cur_slots.get("status", [])):
        return True
    ref_values = ref_slots.get("values", {}) or {}
    cur_values = cur_slots.get("values", {}) or {}
    return any(
        _sets_conflict(ref_values.get(kind, []), cur_values.get(kind, []))
        for kind in ("money", "dates", "times", "ids")
    )


def action_switch(ref: DecisionSignature, cur: DecisionSignature) -> bool:
    """YA: tool-name switch, or action-verb switch between final answers."""
    if ref.tool_name or cur.tool_name:
        return ref.tool_name != cur.tool_name
    return ref.action_verb != cur.action_verb
