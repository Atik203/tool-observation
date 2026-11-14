"""Parse τ-bench historical trajectories into post-tool candidate prefixes.

Candidate definition, validated against the preregistered frame:

* a ``tool`` message followed immediately by an ``assistant`` message;
* the internal ``think`` tool is excluded;
* every other tool result is a candidate, including error text and empty
  search results.

On the pinned four-file frame this yields 13,605 candidates and 11,318
JSON-parseable observations, matching ``configs/harvest.yaml``.

The parser stores message hashes and a source reference, not a second copy of
the full prefix. ``materialize_prefix`` reconstructs the exact messages from
the pinned trajectory and verifies the hash. The selected 800 prefixes are
materialized into the frozen payload at G0.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..hashing import canonical_json, sha256_record, sha256_text
from ..schemas import PrefixRecord

DOMAINS: tuple[str, ...] = ("airline", "retail")

# Filename prefix -> donor label used in the paper and the manifest.
DONOR_PREFIXES: tuple[tuple[str, str], ...] = (
    ("gpt-4o", "gpt-4o"),
    ("sonnet-35-new", "claude-3.5-sonnet"),
)

INTERNAL_TOOLS = frozenset({"think"})

# Profile/PII-adjacent tools excluded before sampling. The union of these four
# tools accounts for the preregistered 3,692 excluded candidates:
# get_user_details 1,719 + find_user_id_by_name_zip 1,159 +
# find_user_id_by_email 695 + modify_user_address 119.
PROFILE_TOOLS = frozenset(
    {
        "get_user_details",
        "find_user_id_by_name_zip",
        "find_user_id_by_email",
        "modify_user_address",
    }
)

# Tools whose next action directly targets a PII field. A prefix from one of
# these tools is excluded when its used content is PII, even after scrubbing.
PII_TARGET_TOOLS = frozenset({"modify_pending_order_address", "update_reservation_passengers"})

TOOL_FAMILIES: dict[str, str] = {
    # airline
    "book_reservation": "write",
    "calculate": "compute",
    "cancel_reservation": "write",
    "get_reservation_details": "read",
    "get_user_details": "profile",
    "list_all_airports": "read",
    "search_direct_flight": "read",
    "search_onestop_flight": "read",
    "send_certificate": "write",
    "think": "internal",
    "transfer_to_human_agents": "escalate",
    "update_reservation_baggages": "write",
    "update_reservation_flights": "write",
    "update_reservation_passengers": "write",
    # retail
    "cancel_pending_order": "write",
    "exchange_delivered_order_items": "write",
    "find_user_id_by_email": "lookup",
    "find_user_id_by_name_zip": "lookup",
    "get_order_details": "read",
    "get_product_details": "read",
    "list_all_product_types": "read",
    "modify_pending_order_address": "write",
    "modify_pending_order_items": "write",
    "modify_pending_order_payment": "write",
    "modify_user_address": "write",
    "return_delivered_order_items": "write",
}

# Step-index buckets used for sampling strata. The boundaries are a design
# choice, not an empirical result; they are recorded in docs/DECISIONS.md.
STEP_BUCKETS: tuple[tuple[int, int | None, str], ...] = (
    (0, 2, "early"),
    (3, 6, "mid"),
    (7, None, "late"),
)


class ParseError(ValueError):
    """Raised when a trajectory does not match the expected τ-bench schema."""


def trajectory_metadata(relative_path: str | Path) -> tuple[str, str]:
    """Return ``(domain, donor)`` from a pinned trajectory filename."""
    name = Path(relative_path).name
    if not name.endswith(".json"):
        raise ParseError(f"not a JSON trajectory: {relative_path}")
    stem = name[: -len(".json")]
    for prefix, donor in DONOR_PREFIXES:
        marker = f"{prefix}-"
        if stem.startswith(marker):
            domain = stem[len(marker) :]
            if domain not in DOMAINS:
                raise ParseError(f"unknown domain in {relative_path}: {domain!r}")
            return domain, donor
    raise ParseError(f"unknown donor in {relative_path}")


def tool_family(tool_name: str) -> str:
    """Map a τ-bench tool name to its family, or ``other`` if unknown."""
    return TOOL_FAMILIES.get(tool_name, "other")


def step_index_bucket(step_index: int) -> str:
    """Bucket a zero-based tool step index for stratified sampling."""
    if step_index < 0:
        raise ParseError(f"step index must be non-negative, got {step_index}")
    for low, high, label in STEP_BUCKETS:
        if step_index >= low and (high is None or step_index <= high):
            return label
    return "late"


def _slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def make_prefix_id(
    domain: str,
    donor: str,
    task_id: str,
    trial: int,
    step_index: int,
    tool_name: str,
) -> str:
    """Build a readable, deterministic prefix identifier."""
    return (
        f"{domain}-{_slug(donor)}-t{_slug(task_id)}-r{int(trial):02d}"
        f"-s{step_index:03d}-{_slug(tool_name)}"
    )


@dataclass(slots=True)
class Trajectory:
    """One τ-bench historical trajectory."""

    trajectory_id: str
    domain: str
    donor: str
    task_id: str
    trial: int
    messages: list[dict[str, Any]]
    source_file: str
    info: dict[str, Any] = field(default_factory=dict)
    reward: float | None = None


@dataclass(slots=True)
class ParseStats:
    """Counts that let the parser be checked against the harvest config."""

    files: int = 0
    trajectories: int = 0
    tool_messages: int = 0
    candidates: int = 0
    json_parseable: int = 0
    text_observations: int = 0
    think_skipped: int = 0
    no_continuation_skipped: int = 0
    profile_tool_candidates: int = 0
    unknown_tools: dict[str, int] = field(default_factory=dict)
    by_domain: dict[str, int] = field(default_factory=dict)
    by_donor: dict[str, int] = field(default_factory=dict)
    by_tool: dict[str, int] = field(default_factory=dict)
    by_tool_family: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "files": self.files,
            "trajectories": self.trajectories,
            "tool_messages": self.tool_messages,
            "candidates": self.candidates,
            "json_parseable": self.json_parseable,
            "text_observations": self.text_observations,
            "think_skipped": self.think_skipped,
            "no_continuation_skipped": self.no_continuation_skipped,
            "profile_tool_candidates": self.profile_tool_candidates,
            "unknown_tools": dict(sorted(self.unknown_tools.items())),
            "by_domain": dict(sorted(self.by_domain.items())),
            "by_donor": dict(sorted(self.by_donor.items())),
            "by_tool": dict(sorted(self.by_tool.items())),
            "by_tool_family": dict(sorted(self.by_tool_family.items())),
        }


def load_trajectory_file(
    path: str | Path,
    *,
    relative_path: str | None = None,
) -> list[Trajectory]:
    """Load one pinned trajectory file and validate its top-level shape."""
    source = Path(path)
    relative = relative_path or source.as_posix()
    domain, donor = trajectory_metadata(relative)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ParseError(f"trajectory file must contain a list: {source}")

    trajectories: list[Trajectory] = []
    seen: set[str] = set()
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise ParseError(f"record {index} is not an object: {source}")
        for key in ("task_id", "trial", "traj"):
            if key not in record:
                raise ParseError(f"record {index} missing {key!r}: {source}")
        messages = record["traj"]
        if not isinstance(messages, list):
            raise ParseError(f"record {index} traj is not a list: {source}")
        task_id = str(record["task_id"])
        trial = int(record["trial"])
        trajectory_id = f"{domain}:{donor}:{task_id}:{trial}"
        if trajectory_id in seen:
            raise ParseError(f"duplicate trajectory id {trajectory_id} in {source}")
        seen.add(trajectory_id)
        info = record.get("info") if isinstance(record.get("info"), dict) else {}
        reward = record.get("reward")
        trajectories.append(
            Trajectory(
                trajectory_id=trajectory_id,
                domain=domain,
                donor=donor,
                task_id=task_id,
                trial=trial,
                messages=messages,
                source_file=relative,
                info=info,
                reward=float(reward) if isinstance(reward, (int, float)) else None,
            )
        )
    return trajectories


def _raw_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    return canonical_json(content)


def _parse_observation(raw: str) -> tuple[Any, str]:
    """Return ``(parsed_value, format)`` for a raw tool observation."""
    try:
        return json.loads(raw), "json"
    except (json.JSONDecodeError, TypeError):
        return None, "text"


def _find_tool_call(
    messages: list[dict[str, Any]],
    tool_index: int,
    tool_call_id: str | None,
) -> dict[str, Any] | None:
    """Find the assistant tool call that produced a tool message."""
    cursor = tool_index - 1
    while cursor >= 0 and messages[cursor].get("role") == "tool":
        cursor -= 1
    if cursor < 0 or messages[cursor].get("role") != "assistant":
        return None
    calls = messages[cursor].get("tool_calls") or []
    if not isinstance(calls, list):
        return None
    for call in calls:
        if isinstance(call, dict) and call.get("id") == tool_call_id:
            return call
    if len(calls) == 1 and isinstance(calls[0], dict):
        return calls[0]
    return None


def _tool_arguments(call: dict[str, Any] | None) -> tuple[str, str]:
    """Return ``(call_id, canonical_arguments_json)`` for a tool call."""
    if not call:
        return "", ""
    call_id = str(call.get("id") or "")
    function = call.get("function") or {}
    arguments = function.get("arguments")
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            return call_id, canonical_json({"unparsed": arguments})
    return call_id, canonical_json(arguments)


def _continuation_type(message: dict[str, Any]) -> str:
    if message.get("tool_calls"):
        return "tool_call"
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return "final_answer"
    return "text"


def iter_candidates(trajectory: Trajectory) -> Iterator[PrefixRecord]:
    """Yield one candidate for every non-think tool result with a continuation."""
    messages = trajectory.messages
    tool_step = -1
    for index, message in enumerate(messages):
        if message.get("role") != "tool":
            continue
        tool_step += 1
        tool_name = str(message.get("name") or "")
        if tool_name in INTERNAL_TOOLS:
            continue
        if index + 1 >= len(messages) or messages[index + 1].get("role") != "assistant":
            continue

        raw_observation = _raw_content(message.get("content"))
        parsed, observation_format = _parse_observation(raw_observation)
        call = _find_tool_call(messages, index, message.get("tool_call_id"))
        call_id, arguments_json = _tool_arguments(call)
        prefix = messages[: index + 1]
        continuation = messages[index + 1]

        yield PrefixRecord(
            prefix_id=make_prefix_id(
                trajectory.domain,
                trajectory.donor,
                trajectory.task_id,
                trajectory.trial,
                tool_step,
                tool_name,
            ),
            domain=trajectory.domain,
            task_id=trajectory.task_id,
            trajectory_id=trajectory.trajectory_id,
            donor=trajectory.donor,
            trial=trajectory.trial,
            step_index=tool_step,
            tool_name=tool_name,
            observation_json=canonical_json(parsed) if observation_format == "json" else "",
            factual_continuation=canonical_json(continuation),
            raw_observation=raw_observation,
            observation_format=observation_format,
            tool_call_id=call_id or str(message.get("tool_call_id") or ""),
            tool_arguments_json=arguments_json,
            message_index=index,
            continuation_type=_continuation_type(continuation),
            source_file=trajectory.source_file,
            prefix_hash=sha256_record(prefix),
            message_hashes=[sha256_record(item) for item in prefix],
            observation_hash=sha256_text(raw_observation),
            tool_family=tool_family(tool_name),
            step_index_bucket=step_index_bucket(tool_step),
            split="unassigned",
        )


def _add_count(mapping: dict[str, int], key: str) -> None:
    mapping[key] = mapping.get(key, 0) + 1


def parse_trajectories(
    trajectories: Iterable[Trajectory],
    *,
    stats: ParseStats | None = None,
) -> list[PrefixRecord]:
    """Parse a set of trajectories and update optional aggregate statistics."""
    counters = stats if stats is not None else ParseStats()
    records: list[PrefixRecord] = []
    for trajectory in trajectories:
        counters.trajectories += 1
        counters.tool_messages += sum(
            1 for message in trajectory.messages if message.get("role") == "tool"
        )
        for record in iter_candidates(trajectory):
            records.append(record)
            counters.candidates += 1
            if record.observation_format == "json":
                counters.json_parseable += 1
            else:
                counters.text_observations += 1
            if record.tool_name in PROFILE_TOOLS:
                counters.profile_tool_candidates += 1
            if record.tool_family == "other":
                _add_count(counters.unknown_tools, record.tool_name)
            _add_count(counters.by_domain, record.domain)
            _add_count(counters.by_donor, record.donor)
            _add_count(counters.by_tool, record.tool_name)
            _add_count(counters.by_tool_family, record.tool_family)
        # Count skipped tool messages separately so the accounting is exact.
        for index, message in enumerate(trajectory.messages):
            if message.get("role") != "tool":
                continue
            if str(message.get("name") or "") in INTERNAL_TOOLS:
                counters.think_skipped += 1
            elif index + 1 >= len(trajectory.messages) or trajectory.messages[index + 1].get(
                "role"
            ) != "assistant":
                counters.no_continuation_skipped += 1
    return records


def parse_frame(
    upstream_dir: str | Path,
    trajectory_files: Iterable[str],
) -> tuple[list[PrefixRecord], ParseStats]:
    """Parse every pinned trajectory file in a frame."""
    root = Path(upstream_dir)
    stats = ParseStats()
    records: list[PrefixRecord] = []
    seen: set[str] = set()
    for relative in trajectory_files:
        trajectories = load_trajectory_file(root / relative, relative_path=relative)
        stats.files += 1
        for record in parse_trajectories(trajectories, stats=stats):
            if record.prefix_id in seen:
                raise ParseError(f"duplicate prefix id: {record.prefix_id}")
            seen.add(record.prefix_id)
            records.append(record)
    return records, stats


class TrajectoryStore:
    """Cache pinned trajectory files while materializing prefixes."""

    def __init__(self, upstream_dir: str | Path) -> None:
        self.root = Path(upstream_dir)
        self._cache: dict[str, dict[str, Trajectory]] = {}

    def _load(self, relative: str) -> dict[str, Trajectory]:
        if relative not in self._cache:
            trajectories = load_trajectory_file(self.root / relative, relative_path=relative)
            self._cache[relative] = {item.trajectory_id: item for item in trajectories}
        return self._cache[relative]

    def get_trajectory(self, record: PrefixRecord) -> Trajectory:
        """Return the source trajectory for a candidate."""
        trajectories = self._load(record.source_file)
        trajectory = trajectories.get(record.trajectory_id)
        if trajectory is None:
            raise ParseError(f"trajectory not found: {record.trajectory_id}")
        return trajectory

    def materialize(self, record: PrefixRecord) -> list[dict[str, Any]]:
        """Return the exact prefix messages and verify the stored hash."""
        trajectory = self.get_trajectory(record)
        prefix = trajectory.messages[: record.message_index + 1]
        actual = sha256_record(prefix)
        if actual != record.prefix_hash:
            raise ParseError(
                f"prefix hash mismatch for {record.prefix_id}: "
                f"expected {record.prefix_hash}, got {actual}"
            )
        return prefix


def materialize_prefix(record: PrefixRecord, upstream_dir: str | Path) -> list[dict[str, Any]]:
    """Materialize one prefix without an explicit cache."""
    return TrajectoryStore(upstream_dir).materialize(record)


def write_jsonl(records: Iterable[PrefixRecord], path: str | Path) -> Path:
    """Write records as one canonical JSON object per line."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(canonical_json(record.to_dict()) + "\n")
    return target


def read_jsonl(path: str | Path) -> list[PrefixRecord]:
    """Read a candidate JSONL file."""
    records: list[PrefixRecord] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(PrefixRecord.from_dict(json.loads(line)))
    return records


def read_jsonl_dicts(path: str | Path) -> list[dict[str, Any]]:
    """Read a JSONL file of arbitrary JSON objects."""
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ParseError(f"JSONL row is not an object: {path}")
                rows.append(payload)
    return rows


def write_jsonl_dicts(rows: Iterable[dict[str, Any]], path: str | Path) -> Path:
    """Write arbitrary JSON objects as canonical JSONL."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(canonical_json(row) + "\n")
    return target


def hash_jsonl_dicts(rows: Iterable[dict[str, Any]]) -> str:
    """Hash canonical JSONL rows without writing a file."""
    text = "\n".join(canonical_json(row) for row in rows)
    return sha256_text(text + ("\n" if text else ""))


def validate_candidate(record: PrefixRecord) -> list[str]:
    """Return missing or inconsistent fields for one candidate."""
    problems: list[str] = []
    for name in (
        "prefix_id",
        "domain",
        "task_id",
        "trajectory_id",
        "donor",
        "tool_name",
        "raw_observation",
        "factual_continuation",
        "prefix_hash",
        "source_file",
    ):
        if not getattr(record, name):
            problems.append(f"missing {name}")
    if record.step_index < 0:
        problems.append("negative step_index")
    if record.message_index < 0:
        problems.append("negative message_index")
    if record.observation_format not in {"json", "text"}:
        problems.append(f"bad observation_format: {record.observation_format}")
    return problems


def validate_candidates(records: Iterable[PrefixRecord]) -> list[str]:
    """Return validation problems prefixed by prefix id."""
    problems: list[str] = []
    for record in records:
        for problem in validate_candidate(record):
            problems.append(f"{record.prefix_id}: {problem}")
    return problems
