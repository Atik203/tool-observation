"""Replay pinned τ-bench tool calls and compare the last observation.

Replay starts from a fresh task database, executes every assistant tool call in
the frozen prefix in order, and compares the final tool output with the
historical observation. It never calls a model or the user simulator. The
pinned data and tool modules are loaded directly, so τ-bench's package
``__init__`` and its optional model dependencies are not imported.

A match is exact string equality or normalized JSON/text equality. The
normalized comparison rounds floats and sorts object keys so JSON formatting
and insignificant float noise do not count as mismatches.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..harvest.parse import TrajectoryStore
from ..harvest.relevance import normalize_text
from ..hashing import canonical_json, sha256_text
from ..schemas import PrefixRecord

TERMINATE_TOOLS = frozenset({"transfer_to_human_agents"})


def _ensure_package(name: str, path: Path) -> types.ModuleType:
    """Create a package shim without executing τ-bench's ``__init__``."""
    if name in sys.modules:
        return sys.modules[name]
    module = types.ModuleType(name)
    module.__path__ = [str(path)]
    module.__package__ = name
    sys.modules[name] = module
    return module


def _load_module(name: str, path: Path) -> types.ModuleType:
    """Load a pinned τ-bench module directly from its file."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    if path.name == "__init__.py":
        module.__path__ = [str(path.parent)]
        module.__package__ = name
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_domain(root: Path, domain: str) -> tuple[Any, list[Any]]:
    """Load the pinned data loader and tool classes for one domain."""
    _ensure_package("tau_bench", root / "tau_bench")
    _ensure_package("tau_bench.envs", root / "tau_bench" / "envs")
    _ensure_package(f"tau_bench.envs.{domain}", root / "tau_bench" / "envs" / domain)
    if "tau_bench.envs.tool" not in sys.modules:
        _load_module("tau_bench.envs.tool", root / "tau_bench" / "envs" / "tool.py")
    data_module = _load_module(
        f"tau_bench.envs.{domain}.data",
        root / "tau_bench" / "envs" / domain / "data" / "__init__.py",
    )
    tools_module = _load_module(
        f"tau_bench.envs.{domain}.tools",
        root / "tau_bench" / "envs" / domain / "tools" / "__init__.py",
    )
    return data_module.load_data, list(tools_module.ALL_TOOLS)


def normalize_json(value: Any) -> Any:
    """Normalize a JSON value for comparison: sort objects and round floats."""
    if isinstance(value, dict):
        return {str(key): normalize_json(child) for key, child in value.items()}
    if isinstance(value, list):
        return [normalize_json(child) for child in value]
    if isinstance(value, float):
        if value != value:
            return "NaN"
        return round(value, 6)
    return value


def normalize_observation(raw: str) -> tuple[str, str]:
    """Return ``(normalized_text, kind)`` for a tool observation."""
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return normalize_text(raw), "text"
    return canonical_json(normalize_json(parsed)), "json"


@dataclass(slots=True)
class ReplayResult:
    """Comparison of one historical observation with its replay."""

    match: bool
    diff: str
    historical_hash: str
    observed_hash: str
    historical_kind: str
    observed_kind: str
    executed_calls: int
    error: str = ""


def compare_observations(historical: str, observed: str) -> ReplayResult:
    """Compare historical and replayed observations with a diff taxonomy."""
    historical_norm, historical_kind = normalize_observation(historical)
    observed_norm, observed_kind = normalize_observation(observed)
    historical_hash = sha256_text(historical_norm)
    observed_hash = sha256_text(observed_norm)

    if historical == observed:
        diff = "exact"
        match = True
    elif historical_kind != observed_kind:
        diff = "json_vs_text"
        match = False
    elif historical_kind == "json":
        match = historical_norm == observed_norm
        diff = "json_normalized" if match else "json_value_mismatch"
    else:
        match = historical_norm == observed_norm
        diff = "text_normalized" if match else "text_mismatch"

    if not match and isinstance(observed, str) and observed.startswith("Error:"):
        diff = "replayed_error"
    elif not match and not observed:
        diff = "empty_replayed"

    return ReplayResult(
        match=match,
        diff=diff,
        historical_hash=historical_hash,
        observed_hash=observed_hash,
        historical_kind=historical_kind,
        observed_kind=observed_kind,
        executed_calls=0,
    )


def extract_tool_calls(messages: Iterable[dict[str, Any]]) -> tuple[list[tuple[str, dict[str, Any]]], int]:
    """Return ordered ``(tool_name, kwargs)`` calls and an argument-error count."""
    calls: list[tuple[str, dict[str, Any]]] = []
    argument_errors = 0
    for message in messages:
        if message.get("role") != "assistant":
            continue
        for call in message.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            function = call.get("function") or {}
            name = function.get("name")
            arguments = function.get("arguments")
            if not isinstance(name, str):
                continue
            if isinstance(arguments, str):
                try:
                    kwargs = json.loads(arguments)
                except json.JSONDecodeError:
                    kwargs = {}
                    argument_errors += 1
            elif isinstance(arguments, dict):
                kwargs = arguments
            elif arguments is None:
                kwargs = {}
            else:
                kwargs = {}
                argument_errors += 1
            if not isinstance(kwargs, dict):
                kwargs = {}
                argument_errors += 1
            calls.append((name, kwargs))
    return calls, argument_errors


class TauBenchReplay:
    """Replay harness for one τ-bench domain."""

    def __init__(self, upstream_dir: str | Path, domain: str) -> None:
        if domain not in {"airline", "retail"}:
            raise ValueError(f"unknown domain: {domain}")
        self.root = Path(upstream_dir).resolve()
        self.domain = domain
        self._load_data, tools = _load_domain(self.root, domain)
        self._tools = {tool.get_info()["function"]["name"]: tool for tool in tools}

    def replay_messages(self, messages: list[dict[str, Any]], historical: str) -> ReplayResult:
        """Execute all tool calls in a prefix and compare the last observation."""
        calls, argument_errors = extract_tool_calls(messages)
        if not calls:
            result = compare_observations(historical, "")
            result.diff = "no_tool_calls"
            result.error = "no tool calls in prefix"
            return result

        data = self._load_data()
        observed = ""
        error = ""
        executed = 0
        for name, kwargs in calls:
            tool = self._tools.get(name)
            if tool is None:
                observed = f"Unknown action {name}"
                error = f"unknown tool: {name}"
                break
            try:
                observed = tool.invoke(data=data, **kwargs)
            except Exception as exc:  # noqa: BLE001 - τ-bench wraps tool errors
                observed = f"Error: {exc}"
            executed += 1
            if name in TERMINATE_TOOLS:
                break

        result = compare_observations(historical, observed)
        result.executed_calls = executed
        if argument_errors:
            result.error = f"argument_parse_errors={argument_errors}"
        elif error:
            result.error = error
        return result

    def replay_record(self, record: PrefixRecord, messages: list[dict[str, Any]]) -> ReplayResult:
        return self.replay_messages(messages, record.raw_observation)


def replay_candidates(
    records: Iterable[PrefixRecord],
    *,
    upstream_dir: str | Path,
    only_eligible: bool = True,
) -> tuple[list[PrefixRecord], dict[str, Any]]:
    """Replay candidates and annotate replay fields in place."""
    store = TrajectoryStore(upstream_dir)
    harnesses: dict[str, TauBenchReplay] = {}
    replayed: list[PrefixRecord] = []
    diffs: dict[str, int] = {}
    by_domain: dict[str, dict[str, int]] = {}
    by_tool: dict[str, dict[str, int]] = {}
    matches = 0
    skipped = 0

    for record in records:
        if only_eligible and not record.eligible:
            skipped += 1
            continue
        if record.domain not in harnesses:
            harnesses[record.domain] = TauBenchReplay(upstream_dir, record.domain)
        messages = store.materialize(record)
        result = harnesses[record.domain].replay_record(record, messages)
        record.replay_match = result.match
        record.replay_diff = result.diff
        record.replay_historical_hash = result.historical_hash
        record.replay_observed_hash = result.observed_hash
        record.replay_error = result.error
        record.replay_executed_calls = result.executed_calls
        replayed.append(record)

        if result.match:
            matches += 1
        diffs[result.diff] = diffs.get(result.diff, 0) + 1
        domain_stats = by_domain.setdefault(record.domain, {"total": 0, "matches": 0})
        domain_stats["total"] += 1
        domain_stats["matches"] += int(result.match)
        tool_stats = by_tool.setdefault(record.tool_name, {"total": 0, "matches": 0})
        tool_stats["total"] += 1
        tool_stats["matches"] += int(result.match)

    total = len(replayed)
    return replayed, {
        "total": total,
        "matches": matches,
        "mismatches": total - matches,
        "match_rate": (matches / total) if total else 0.0,
        "skipped": skipped,
        "diffs": dict(sorted(diffs.items())),
        "by_domain": {key: dict(sorted(value.items())) for key, value in sorted(by_domain.items())},
        "by_tool": {key: dict(sorted(value.items())) for key, value in sorted(by_tool.items())},
    }
