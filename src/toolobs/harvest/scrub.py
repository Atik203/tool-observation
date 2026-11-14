"""Deterministic PII scrubbing for candidate observations and prefixes.

The scrubber replaces direct identifiers with stable synthetic tokens derived
from a fixed project salt. It is pseudonymization, not anonymization: the same
input value always yields the same token, which keeps the paired arms and the
donor continuation aligned. Raw values stay in the gitignored interim data;
only scrubbed fields enter the frozen release.

The path policy is draft until the field-registry decision at G0. The scrubber
is deliberately conservative: a candidate whose used content is PII is already
marked ineligible by :mod:`toolobs.harvest.relevance`.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..hashing import canonical_json, sha256_record, sha256_text
from ..schemas import PrefixRecord
from .parse import Trajectory, TrajectoryStore
from .relevance import PiiPolicy

PII_SALT = "toolresult800-pii-v1"

_IGNORE_VALUES = frozenset(
    {"none", "null", "n/a", "na", "unknown", "not available", "yes", "no", "true", "false"}
)

_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
_PHONE = re.compile(
    r"(?<!\w)(?:\+\d{1,3}[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?!\w)"
)
_TOKEN = re.compile(r"\b(?:person|email|phone|address|dob|payment|user|pii)_[0-9a-f]{12}\b")


def token_kind(path_pattern: str) -> str:
    """Choose a stable token prefix from a PII path pattern."""
    if "first_name" in path_pattern or "last_name" in path_pattern:
        return "person"
    if path_pattern.endswith(".name") or ".name." in path_pattern:
        return "person"
    if "email" in path_pattern:
        return "email"
    if "phone" in path_pattern:
        return "phone"
    if "dob" in path_pattern:
        return "dob"
    if "address" in path_pattern:
        return "address"
    if "payment" in path_pattern:
        return "payment"
    if "user_id" in path_pattern:
        return "user"
    return "pii"


def make_token(kind: str, value: Any) -> str:
    """Return a deterministic token for a PII value."""
    digest = sha256_text(f"{PII_SALT}|{kind}|{value}")[:12]
    return f"{kind}_{digest}"


@dataclass(slots=True)
class PiiMap:
    """Exact-value replacements applied to free text."""

    mapping: dict[str, str] = field(default_factory=dict)
    kinds: dict[str, str] = field(default_factory=dict)

    def add(self, kind: str, value: Any) -> None:
        text = str(value).strip()
        if len(text) < 2 or text in self.mapping or text.lower() in _IGNORE_VALUES:
            return
        self.mapping[text] = make_token(kind, text)
        self.kinds[text] = kind

    def add_name(self, first: Any, last: Any) -> None:
        first_text = str(first or "").strip()
        last_text = str(last or "").strip()
        if first_text:
            self.add("person", first_text)
        if last_text:
            self.add("person", last_text)
        if first_text and last_text:
            self.add("person", f"{first_text} {last_text}")

    def replace(self, text: str) -> str:
        for original, token in sorted(self.mapping.items(), key=lambda item: -len(item[0])):
            pattern = re.compile(rf"(?<!\w){re.escape(original)}(?!\w)", re.IGNORECASE)
            text = pattern.sub(token, text)
        return text


def _add_task_user(pii_map: PiiMap, user: dict[str, Any], user_id: str) -> None:
    pii_map.add("user", user_id)
    name = user.get("name") or {}
    if isinstance(name, dict):
        pii_map.add_name(name.get("first_name"), name.get("last_name"))
    pii_map.add("email", user.get("email"))
    address = user.get("address") or {}
    if isinstance(address, dict):
        for key in ("address1", "address2", "city", "zip"):
            pii_map.add("address", address.get(key))
    pii_map.add("dob", user.get("dob"))
    payments = user.get("payment_methods") or {}
    if isinstance(payments, dict):
        for payment_id, payment in payments.items():
            pii_map.add("payment", payment_id)
            if isinstance(payment, dict):
                pii_map.add("payment", payment.get("id"))
                pii_map.add("payment", payment.get("last_four"))
                pii_map.add("payment", payment.get("source"))
    for passenger in user.get("saved_passengers") or []:
        if isinstance(passenger, dict):
            pii_map.add_name(passenger.get("first_name"), passenger.get("last_name"))
            pii_map.add("dob", passenger.get("dob"))


def _collect_observation_pii(
    value: Any,
    policy: PiiPolicy,
    pii_map: PiiMap,
    *,
    path: str = "$",
    pattern: str = "$",
) -> None:
    if isinstance(value, dict):
        first = value.get("first_name")
        last = value.get("last_name")
        if first is not None or last is not None:
            pii_map.add_name(first, last)
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}" if key_text.isidentifier() else f'{path}["{key_text}"]'
            child_pattern = f"{pattern}.{key_text}" if key_text.isidentifier() else f"{pattern}.*"
            if "payment_methods" in pattern and isinstance(child, dict):
                pii_map.add("payment", key_text)
            _collect_observation_pii(
                child,
                policy,
                pii_map,
                path=child_path,
                pattern=child_pattern,
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_observation_pii(
                child,
                policy,
                pii_map,
                path=f"{path}[{index}]",
                pattern=f"{pattern}[]",
            )
    elif policy.matches(pattern):
        pii_map.add(token_kind(pattern), value)


def _scrub_value(
    value: Any,
    policy: PiiPolicy,
    pii_map: PiiMap,
    *,
    path: str = "$",
    pattern: str = "$",
) -> Any:
    if policy.matches(pattern):
        if isinstance(value, dict):
            return {
                pii_map.mapping.get(str(key), make_token("payment", key)): _scrub_value(
                    child,
                    policy,
                    pii_map,
                    path=f"{path}.{key}",
                    pattern=f"{pattern}.{key}",
                )
                for key, child in value.items()
            }
        if isinstance(value, list):
            return [
                _scrub_value(
                    child,
                    policy,
                    pii_map,
                    path=f"{path}[{index}]",
                    pattern=f"{pattern}[]",
                )
                for index, child in enumerate(value)
            ]
        text = str(value)
        return pii_map.mapping.get(text, make_token(token_kind(pattern), text))

    if isinstance(value, dict):
        return {
            key: _scrub_value(
                child,
                policy,
                pii_map,
                path=f"{path}.{key}" if str(key).isidentifier() else f'{path}["{key}"]',
                pattern=f"{pattern}.{key}" if str(key).isidentifier() else f"{pattern}.*",
            )
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [
            _scrub_value(
                child,
                policy,
                pii_map,
                path=f"{path}[{index}]",
                pattern=f"{pattern}[]",
            )
            for index, child in enumerate(value)
        ]
    if isinstance(value, str):
        return scrub_text(value, pii_map)
    return value


def scrub_text(text: str, pii_map: PiiMap) -> str:
    """Replace known PII values plus email and phone patterns in free text."""
    scrubbed = pii_map.replace(text)
    scrubbed = _EMAIL.sub(lambda match: make_token("email", match.group(0)), scrubbed)
    scrubbed = _PHONE.sub(lambda match: make_token("phone", match.group(0)), scrubbed)
    return scrubbed


def count_direct_identifiers(text: str) -> int:
    """Count email and phone patterns remaining in a string."""
    return len(_EMAIL.findall(text)) + len(_PHONE.findall(text))


def scrub_generic(value: Any, pii_map: PiiMap) -> Any:
    """Scrub a JSON-like value with text-level PII detection only."""
    if isinstance(value, dict):
        return {key: scrub_generic(child, pii_map) for key, child in value.items()}
    if isinstance(value, list):
        return [scrub_generic(child, pii_map) for child in value]
    if isinstance(value, str):
        return scrub_text(value, pii_map)
    return value


def scrub_message(
    message: dict[str, Any],
    policy: PiiPolicy,
    pii_map: PiiMap,
) -> dict[str, Any]:
    """Scrub one chat message, including tool-call arguments."""
    result = dict(message)
    content = result.get("content")
    if isinstance(content, str):
        if result.get("role") == "tool":
            try:
                parsed = json.loads(content)
            except json.JSONDecodeError:
                result["content"] = scrub_text(content, pii_map)
            else:
                result["content"] = canonical_json(_scrub_value(parsed, policy, pii_map))
        else:
            result["content"] = scrub_text(content, pii_map)

    calls = result.get("tool_calls")
    if isinstance(calls, list):
        scrubbed_calls = []
        for call in calls:
            if not isinstance(call, dict):
                scrubbed_calls.append(call)
                continue
            scrubbed = dict(call)
            function = scrubbed.get("function")
            if isinstance(function, dict):
                function = dict(function)
                arguments = function.get("arguments")
                if isinstance(arguments, str):
                    try:
                        parsed = json.loads(arguments)
                    except json.JSONDecodeError:
                        function["arguments"] = scrub_text(arguments, pii_map)
                    else:
                        function["arguments"] = canonical_json(scrub_generic(parsed, pii_map))
                elif arguments is not None:
                    function["arguments"] = canonical_json(scrub_generic(arguments, pii_map))
                scrubbed["function"] = function
            scrubbed_calls.append(scrubbed)
        result["tool_calls"] = scrubbed_calls
    return result


@dataclass(slots=True)
class ScrubResult:
    """Scrubbed fields for one candidate."""

    prefix_id: str
    scrubbed_observation_json: str
    scrubbed_factual_continuation: str
    scrubbed_observation_hash: str
    scrubbed_prefix_hash: str
    pii_token_count: int


def scrub_candidate(
    record: PrefixRecord,
    messages: list[dict[str, Any]],
    *,
    policy: PiiPolicy,
    pii_map: PiiMap,
) -> ScrubResult:
    """Scrub one candidate observation, continuation, and prefix."""
    observation = json.loads(record.observation_json) if record.observation_json else None
    if observation is not None:
        _collect_observation_pii(observation, policy, pii_map)
    scrubbed_observation = (
        canonical_json(_scrub_value(observation, policy, pii_map))
        if observation is not None
        else ""
    )

    try:
        continuation = json.loads(record.factual_continuation)
    except json.JSONDecodeError:
        scrubbed_continuation = scrub_text(record.factual_continuation, pii_map)
    else:
        scrubbed_continuation = canonical_json(scrub_generic(continuation, pii_map))

    scrubbed_messages = [scrub_message(message, policy, pii_map) for message in messages]
    return ScrubResult(
        prefix_id=record.prefix_id,
        scrubbed_observation_json=scrubbed_observation,
        scrubbed_factual_continuation=scrubbed_continuation,
        scrubbed_observation_hash=sha256_text(scrubbed_observation),
        scrubbed_prefix_hash=sha256_record(scrubbed_messages),
        pii_token_count=len(_TOKEN.findall(scrubbed_observation))
        + len(_TOKEN.findall(scrubbed_continuation)),
    )


def load_task_users(upstream_dir: str | Path, domain: str) -> dict[str, dict[str, Any]]:
    """Load the task-database user records for a domain."""
    path = Path(upstream_dir) / "tau_bench" / "envs" / domain / "data" / "users.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"users.json must be an object: {path}")
    return payload


def build_pii_map(
    trajectory: Trajectory,
    observation: Any,
    *,
    policy: PiiPolicy,
    users: dict[str, dict[str, Any]],
) -> PiiMap:
    """Build the exact-value replacement map for one trajectory."""
    pii_map = PiiMap()
    task = trajectory.info.get("task") if isinstance(trajectory.info, dict) else {}
    user_id = task.get("user_id") if isinstance(task, dict) else None
    if isinstance(user_id, str):
        user = users.get(user_id)
        if isinstance(user, dict):
            _add_task_user(pii_map, user, user_id)
        else:
            pii_map.add("user", user_id)
    if observation is not None:
        _collect_observation_pii(observation, policy, pii_map)
    return pii_map


def _iter_scalar_texts(value: Any) -> Iterable[str]:
    """Yield scalar values, excluding dict keys, for leak scanning."""
    if isinstance(value, dict):
        for child in value.values():
            yield from _iter_scalar_texts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_scalar_texts(child)
    elif isinstance(value, str):
        yield value
    elif value is not None:
        yield str(value)


def _scalar_scan_text(text: str) -> str:
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text
    return "\n".join(_iter_scalar_texts(parsed))


def scrub_candidates(
    records: Iterable[PrefixRecord],
    *,
    upstream_dir: str | Path,
    policy: PiiPolicy,
    only_eligible: bool = True,
) -> tuple[list[PrefixRecord], dict[str, Any]]:
    """Scrub candidates and annotate the scrubbed hashes in place.

    The map is built from the task user record and every observation in a
    trajectory before any candidate is scrubbed, so a value gets the same token
    everywhere it appears. Full scrubbed prefixes are not stored here; the
    freeze stage re-scrubs the selected 800 with the same deterministic map.
    """
    store = TrajectoryStore(upstream_dir)
    users_cache: dict[str, dict[str, dict[str, Any]]] = {}
    grouped: dict[str, list[PrefixRecord]] = {}
    for record in records:
        grouped.setdefault(record.trajectory_id, []).append(record)

    scrubbed: list[PrefixRecord] = []
    leaks: list[dict[str, Any]] = []
    token_total = 0
    skipped = 0
    maps_built = 0

    for group in grouped.values():
        trajectory = store.get_trajectory(group[0])
        if trajectory.domain not in users_cache:
            users_cache[trajectory.domain] = load_task_users(upstream_dir, trajectory.domain)
        users = users_cache[trajectory.domain]

        pii_map = PiiMap()
        task = trajectory.info.get("task") if isinstance(trajectory.info, dict) else {}
        user_id = task.get("user_id") if isinstance(task, dict) else None
        if isinstance(user_id, str):
            user = users.get(user_id)
            if isinstance(user, dict):
                _add_task_user(pii_map, user, user_id)
            else:
                pii_map.add("user", user_id)
        for record in group:
            if record.observation_json:
                try:
                    observation = json.loads(record.observation_json)
                except json.JSONDecodeError:
                    continue
                _collect_observation_pii(observation, policy, pii_map)
        maps_built += 1

        for record in group:
            if only_eligible and not record.eligible:
                skipped += 1
                continue
            messages = store.materialize(record)
            result = scrub_candidate(
                record,
                messages,
                policy=policy,
                pii_map=pii_map,
            )
            record.scrubbed_observation_json = result.scrubbed_observation_json
            record.scrubbed_factual_continuation = result.scrubbed_factual_continuation
            record.scrubbed_observation_hash = result.scrubbed_observation_hash
            record.scrubbed_prefix_hash = result.scrubbed_prefix_hash
            record.pii_token_count = result.pii_token_count
            token_total += result.pii_token_count
            scrubbed.append(record)

            combined = "\n".join(
                (
                    _scalar_scan_text(result.scrubbed_observation_json),
                    _scalar_scan_text(result.scrubbed_factual_continuation),
                )
            )
            combined = _TOKEN.sub(" ", combined)
            for original in pii_map.mapping:
                if len(original) < 2:
                    continue
                pattern = re.compile(rf"(?<!\w){re.escape(original)}(?!\w)", re.IGNORECASE)
                if pattern.search(combined):
                    leaks.append(
                        {
                            "prefix_id": record.prefix_id,
                            "kind": pii_map.kinds.get(original, "unknown"),
                            "value_sha256": sha256_text(original)[:16],
                            "value_length": len(original),
                        }
                    )

    return scrubbed, {
        "scrubbed": len(scrubbed),
        "skipped": skipped,
        "pii_tokens": token_total,
        "trajectories_with_maps": maps_built,
        "leaks": leaks,
    }
