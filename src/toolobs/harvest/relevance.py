"""Automatic value-used relevance and criticality for candidate observations.

The preregistration defines criticality by whether a scalar value from the
observation appears in the donor's factual continuation after normalization.
This module implements that rule. It also marks PII paths from the draft path
policy and excludes candidates whose used content is itself PII.

The field registry remains the pre-specified prior for audit; this module's
automatic labels are the operational fallback for tools the registry does not
cover yet.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from ..schemas import PrefixRecord
from .parse import PII_TARGET_TOOLS, PROFILE_TOOLS

_NUMERIC = re.compile(r"^-?\d+(?:\.\d+)?$")
_NUMBER_TOKEN = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?)(?![\w]|\.\d)")
_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class Leaf:
    """One scalar leaf in an observation."""

    json_path: str
    path_pattern: str
    value: Any
    value_type: str


@dataclass(slots=True)
class RelevanceResult:
    """Automatic relevance labels for one candidate."""

    used_fields: list[dict[str, Any]]
    critical_fields: list[str]
    noncritical_fields: list[str]
    pii_fields: list[str]
    eligible: bool
    exclusion_reason: str
    leaf_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "used_fields": self.used_fields,
            "critical_fields": self.critical_fields,
            "noncritical_fields": self.noncritical_fields,
            "pii_fields": self.pii_fields,
            "eligible": self.eligible,
            "exclusion_reason": self.exclusion_reason,
            "leaf_count": self.leaf_count,
        }


def _is_simple_key(key: str) -> bool:
    return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_ -]*", key) is not None


def _join(path: str, key: str) -> str:
    if _is_simple_key(key):
        return f"{path}.{key}"
    return f'{path}["{key}"]'


def flatten_leaves(
    value: Any,
    *,
    path: str = "$",
    pattern: str = "$",
) -> Iterator[Leaf]:
    """Yield scalar leaves with concrete paths and list-wildcard patterns."""
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            yield from flatten_leaves(
                child,
                path=_join(path, key_text),
                pattern=f"{pattern}.{key_text}" if _is_simple_key(key_text) else f"{pattern}.*",
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from flatten_leaves(child, path=f"{path}[{index}]", pattern=f"{pattern}[]")
    else:
        yield Leaf(
            json_path=path,
            path_pattern=pattern,
            value=value,
            value_type=type(value).__name__,
        )


def normalize_text(text: str) -> str:
    """Lower-case, NFKC-normalize, collapse whitespace, and strip digit commas."""
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = _WHITESPACE.sub(" ", normalized)
    normalized = re.sub(r"(?<=\d),(?=\d)", "", normalized)
    return normalized.strip()


def normalize_scalar(value: Any) -> str | None:
    """Return a comparable string for a scalar, or ``None`` for null/empty."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value:  # NaN
            return None
        return format(value, ".10g")
    text = normalize_text(str(value))
    return text or None


def _canonical_number(token: str) -> str:
    try:
        return format(Decimal(token).normalize(), "f")
    except InvalidOperation:
        return token


def _normalize_numbers(text: str) -> str:
    return _NUMBER_TOKEN.sub(lambda match: _canonical_number(match.group(1)), text)


def value_in_text(value: Any, normalized_text: str) -> bool:
    """Return whether a scalar appears as a token/phrase in normalized text."""
    token = normalize_scalar(value)
    if token is None or len(token) < 2:
        return False
    if _NUMERIC.fullmatch(token):
        canonical = _canonical_number(token)
        numeric_text = _normalize_numbers(normalized_text)
        return (
            re.search(rf"(?<![\w.]){re.escape(canonical)}(?![\w]|\.\d)", numeric_text)
            is not None
        )
    return re.search(rf"(?<!\w){re.escape(token)}(?!\w)", normalized_text) is not None


def continuation_surface(record: PrefixRecord) -> str:
    """Extract the donor's decision text: answer content or tool call arguments."""
    try:
        message = json.loads(record.factual_continuation)
    except json.JSONDecodeError:
        return normalize_text(record.factual_continuation)
    if not isinstance(message, dict):
        return normalize_text(record.factual_continuation)
    parts: list[str] = []
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        parts.append(content)
    calls = message.get("tool_calls") or []
    if isinstance(calls, list):
        for call in calls:
            if not isinstance(call, dict):
                continue
            function = call.get("function") or {}
            name = function.get("name")
            arguments = function.get("arguments")
            if isinstance(name, str):
                parts.append(name)
            if isinstance(arguments, str):
                parts.append(arguments)
            elif arguments is not None:
                parts.append(json.dumps(arguments, ensure_ascii=False, sort_keys=True))
    return normalize_text("\n".join(parts))


def _pattern_regex(pattern: str) -> re.Pattern[str]:
    escaped = re.escape(pattern)
    escaped = escaped.replace(r"\[\]", r"\[\d*\]")
    escaped = escaped.replace(r"\.\*", r"\.[^.\[\]]+")
    return re.compile(rf"^{escaped}$")


@dataclass(slots=True)
class PiiPolicy:
    """Compiled PII path patterns."""

    patterns: tuple[str, ...]
    _regexes: tuple[re.Pattern[str], ...] = ()

    def __post_init__(self) -> None:
        self._regexes = tuple(_pattern_regex(pattern) for pattern in self.patterns)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> PiiPolicy:
        patterns = config.get("path_policy", {}).get("pii", [])
        return cls(tuple(str(pattern) for pattern in patterns))

    def matches(self, path_pattern: str) -> bool:
        return any(regex.match(path_pattern) for regex in self._regexes)


def evaluate_relevance(
    record: PrefixRecord,
    *,
    pii_policy: PiiPolicy | None = None,
) -> RelevanceResult:
    """Label one candidate by value use and PII path policy."""
    if record.tool_name in PROFILE_TOOLS:
        return RelevanceResult([], [], [], [], False, "profile_tool", 0)
    if record.observation_format != "json" or not record.observation_json:
        return RelevanceResult([], [], [], [], False, "text_observation", 0)

    try:
        observation = json.loads(record.observation_json)
    except json.JSONDecodeError:
        return RelevanceResult([], [], [], [], False, "unparseable_observation", 0)

    policy = pii_policy or PiiPolicy(())
    surface = continuation_surface(record)
    used_fields: list[dict[str, Any]] = []
    critical: list[str] = []
    noncritical: list[str] = []
    pii_fields: list[str] = []
    used_pii: list[str] = []
    leaf_count = 0

    for leaf in flatten_leaves(observation):
        leaf_count += 1
        used = value_in_text(leaf.value, surface)
        is_pii = policy.matches(leaf.path_pattern)
        if is_pii:
            pii_fields.append(leaf.json_path)
        if used:
            used_fields.append(
                {
                    "json_path": leaf.json_path,
                    "path_pattern": leaf.path_pattern,
                    "value": leaf.value,
                    "value_type": leaf.value_type,
                    "pii": is_pii,
                }
            )
            if is_pii:
                used_pii.append(leaf.json_path)
            else:
                critical.append(leaf.json_path)
        elif not is_pii:
            noncritical.append(leaf.json_path)

    if used_pii and (record.tool_name in PII_TARGET_TOOLS or not critical):
        reason = "decision_critical_pii"
        eligible = False
    elif not critical:
        reason = "no_used_fields"
        eligible = False
    else:
        reason = ""
        eligible = True

    return RelevanceResult(
        used_fields=used_fields,
        critical_fields=critical,
        noncritical_fields=noncritical,
        pii_fields=pii_fields,
        eligible=eligible,
        exclusion_reason=reason,
        leaf_count=leaf_count,
    )


def apply_relevance(
    record: PrefixRecord,
    *,
    pii_policy: PiiPolicy | None = None,
) -> RelevanceResult:
    """Annotate a record in place and return the relevance result."""
    result = evaluate_relevance(record, pii_policy=pii_policy)
    record.used_fields = result.used_fields
    record.critical_fields = result.critical_fields
    record.noncritical_fields = result.noncritical_fields
    record.pii_fields = result.pii_fields
    record.exclusion_reason = result.exclusion_reason
    record.eligible = result.eligible
    return result


def annotate_candidates(
    records: Iterable[PrefixRecord],
    *,
    pii_policy: PiiPolicy | None = None,
) -> tuple[list[PrefixRecord], dict[str, Any]]:
    """Annotate a sequence of candidates and return aggregate counts."""
    annotated: list[PrefixRecord] = []
    reasons: dict[str, int] = {}
    eligible = 0
    for record in records:
        result = apply_relevance(record, pii_policy=pii_policy)
        annotated.append(record)
        if result.eligible:
            eligible += 1
        else:
            reasons[result.exclusion_reason] = reasons.get(result.exclusion_reason, 0) + 1
    return annotated, {
        "candidates": len(annotated),
        "eligible": eligible,
        "excluded": len(annotated) - eligible,
        "reasons": dict(sorted(reasons.items())),
    }
