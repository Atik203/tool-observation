"""Generation runner with a backend-agnostic interface.

The vLLM backend is loaded lazily only when a GPU run is authorized. Tests use
FakeBackend and never import torch or vLLM.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ..provenance import utc_now
from ..schemas import LedgerRow
from ..taubench.replay import load_domain_tools
from .ledger import append_ledger_row
from .parse_output import ParsedDecision, parse_decision, signature_hash, signature_json
from .prompt import PROMPT_VERSION, build_prompt_messages, prompt_hash

PARSER_VERSION = "toolresult-parser-v1"


@dataclass(slots=True)
class Generation:
    """One backend generation."""

    text: str
    latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0


class Backend(Protocol):
    """Minimal generation backend."""

    def generate(self, prompts: list[list[dict[str, Any]]], **kwargs: Any) -> list[Generation]:
        """Generate one continuation per prompt."""


class FakeBackend:
    """Deterministic backend for tests and smoke checks."""

    def __init__(self, responses: list[str] | str) -> None:
        self.responses = [responses] if isinstance(responses, str) else list(responses)
        self.calls: list[list[dict[str, Any]]] = []

    def generate(self, prompts: list[list[dict[str, Any]]], **kwargs: Any) -> list[Generation]:
        outputs: list[Generation] = []
        for prompt in prompts:
            self.calls.append(prompt)
            index = (len(self.calls) - 1) % len(self.responses)
            outputs.append(Generation(text=self.responses[index]))
        return outputs


@dataclass(slots=True)
class RunStats:
    """Aggregate generation and parser statistics."""

    total: int = 0
    parsed: int = 0
    parse_error: int = 0
    refusal: int = 0
    empty: int = 0
    latency_ms: float = 0.0
    by_arm: dict[str, int] = field(default_factory=dict)
    by_domain: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "parsed": self.parsed,
            "parse_error": self.parse_error,
            "refusal": self.refusal,
            "empty": self.empty,
            "parse_rate": (self.parsed / self.total) if self.total else 0.0,
            "latency_ms": self.latency_ms,
            "by_arm": dict(sorted(self.by_arm.items())),
            "by_domain": dict(sorted(self.by_domain.items())),
        }


def _domain_for(row: dict[str, Any]) -> str:
    domain = row.get("domain")
    if isinstance(domain, str) and domain:
        return domain
    prefix_id = str(row.get("prefix_id", ""))
    return prefix_id.split("-", 1)[0] if "-" in prefix_id else ""


def _count_status(stats: RunStats, parsed: ParsedDecision) -> None:
    if parsed.status == "ok":
        stats.parsed += 1
    elif parsed.status == "parse_error":
        stats.parse_error += 1
    elif parsed.status == "refusal":
        stats.refusal += 1
    elif parsed.status == "empty":
        stats.empty += 1


def run_rendered_rows(
    rows: list[dict[str, Any]],
    *,
    backend: Backend,
    model_id: str,
    run_id: str,
    stage: str,
    manifest_hash: str,
    ledger_path: str | Path,
    upstream_dir: str | Path | None = None,
    tools_by_domain: dict[str, list[dict[str, Any]]] | None = None,
    prompt_version: str = PROMPT_VERSION,
    parser_version: str = PARSER_VERSION,
    step: int = 0,
) -> RunStats:
    """Run one model over rendered arms and append one ledger row per generation."""
    stats = RunStats()
    tools_cache = dict(tools_by_domain or {})
    for row in rows:
        domain = _domain_for(row)
        if domain not in tools_cache:
            if upstream_dir is None:
                raise ValueError(f"no tools for domain {domain!r}")
            tools_cache[domain] = load_domain_tools(upstream_dir, domain)
        messages = json.loads(row["messages_json"])
        prompt_messages = build_prompt_messages(messages, tools_cache[domain])
        prompt_digest = prompt_hash(prompt_messages)
        generation = backend.generate([prompt_messages])[0]
        parsed = parse_decision(generation.text)
        stats.total += 1
        stats.latency_ms += generation.latency_ms
        stats.by_arm[row["arm"]] = stats.by_arm.get(row["arm"], 0) + 1
        stats.by_domain[domain] = stats.by_domain.get(domain, 0) + 1
        _count_status(stats, parsed)
        append_ledger_row(
            ledger_path,
            LedgerRow(
                run_id=run_id,
                model_id=model_id,
                prefix_id=str(row["prefix_id"]),
                arm=str(row["arm"]),
                step=step,
                prompt_hash=prompt_digest,
                output_text=generation.text,
                parsed=parsed.parsed,
                latency_ms=generation.latency_ms,
                cost_usd=0.0,
                timestamp_utc=utc_now(),
                stage=stage,
                gpu_hours=0.0,
                storage_gb=0.0,
                parser_version=parser_version,
                parser_status=parsed.status,
                signature_hash=signature_hash(parsed) if parsed.parsed else "",
                decision_json=signature_json(parsed) if parsed.parsed else "",
                prompt_version=prompt_version,
                manifest_hash=manifest_hash,
            ),
        )
    return stats


def status_counts(rows: list[LedgerRow]) -> dict[str, int]:
    """Count parser statuses in a ledger."""
    return dict(sorted(Counter(row.parser_status for row in rows).items()))
