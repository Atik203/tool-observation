"""Recovery continuation runner.

The runner starts from a frozen prefix whose injected arm moved the decision, replays
the prefix's real tool calls to rebuild the τ-bench task database, and continues the
episode for H=4 steps. At each step the target model sees the current conversation and
its chosen tool is executed against the real environment. R1 is a signature match with
the verbatim V continuation; R2 is an explicit flag. The transient regime corrupts only
the injected observation; the persistent regime re-applies the same false value to each
new observation.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..analysis.outcomes import flag_detected
from ..hashing import canonical_json, sha256_text
from ..provenance import utc_now
from ..render.perturb import set_path
from ..schemas import LedgerRow, PerturbationRecord, RecoveryEvent
from ..taubench.replay import TauBenchReplay, load_domain_tools
from .ledger import append_ledger_row
from .parse_output import parse_decision, signature_hash, signature_json
from .prompt import build_prompt_messages, prompt_hash
from .runner import PARSER_VERSION, response_regex_for_tools


@dataclass(slots=True)
class RecoveryRunStats:
    """Aggregate recovery-run counts."""

    sequences: int = 0
    recovered_r1: int = 0
    recovered_r2: int = 0
    censored: int = 0
    parse_fail: int = 0
    flagged_at_injection: int = 0
    not_at_risk: int = 0
    ledger_rows: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "sequences": self.sequences,
            "recovered_r1": self.recovered_r1,
            "recovered_r2": self.recovered_r2,
            "censored": self.censored,
            "parse_fail": self.parse_fail,
            "flagged_at_injection": self.flagged_at_injection,
            "not_at_risk": self.not_at_risk,
            "ledger_rows": self.ledger_rows,
        }


def _append_event(path: str | Path, event: RecoveryEvent) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(event.to_dict()) + "\n")


def _persistent_observation(observation: str, perturbation: PerturbationRecord) -> str:
    try:
        payload = json.loads(observation)
    except (json.JSONDecodeError, TypeError):
        return observation
    if not isinstance(payload, (dict, list)):
        return observation
    try:
        set_path(payload, perturbation.json_path, perturbation.false_value)
    except (KeyError, IndexError, TypeError, ValueError):
        return observation
    return canonical_json(payload)


def run_recovery(
    *,
    prefixes: dict[str, dict[str, Any]],
    rendered: dict[tuple[str, str], dict[str, Any]],
    base_rows: dict[tuple[str, str], LedgerRow],
    perturbations: dict[tuple[str, str], PerturbationRecord],
    backend: Any,
    model_id: str,
    regime: str,
    upstream_dir: str | Path,
    ledger_path: str | Path,
    event_path: str | Path,
    manifest_hash: str,
    horizon: int = 4,
    max_sequences: int | None = None,
    replay_factory: Callable[..., TauBenchReplay] = TauBenchReplay,
    tools_by_domain: dict[str, list[dict[str, Any]]] | None = None,
) -> RecoveryRunStats:
    """Run one recovery regime for one model."""
    if regime not in {"transient", "persistent"}:
        raise ValueError(f"unknown regime: {regime}")
    arms = ("s2", "s3") if regime == "transient" else ("s3",)
    stats = RecoveryRunStats()
    tools_cache: dict[str, list[dict[str, Any]]] = dict(tools_by_domain or {})
    regex_cache: dict[str, str | None] = {
        domain: response_regex_for_tools(tools) for domain, tools in tools_cache.items()
    }
    replay_cache: dict[str, Any] = {}
    run_id = f"recovery-{regime}-{model_id}"

    for prefix_id in sorted(prefixes):
        if max_sequences is not None and stats.sequences >= max_sequences:
            break
        prefix = prefixes[prefix_id]
        domain = str(prefix["domain"])
        reference = base_rows.get((prefix_id, "V"))
        if reference is None or not reference.parsed or not reference.signature_hash:
            stats.not_at_risk += 1
            continue
        if domain not in tools_cache:
            tools_cache[domain] = load_domain_tools(upstream_dir, domain)
            regex_cache[domain] = response_regex_for_tools(tools_cache[domain])
        if domain not in replay_cache:
            replay_cache[domain] = replay_factory(upstream_dir, domain)

        for arm in arms:
            if max_sequences is not None and stats.sequences >= max_sequences:
                break
            injected = base_rows.get((prefix_id, arm))
            if injected is None or not injected.parsed or not injected.signature_hash:
                stats.not_at_risk += 1
                continue
            if flag_detected(injected.output_text):
                stats.flagged_at_injection += 1
                continue
            if injected.signature_hash == reference.signature_hash:
                stats.not_at_risk += 1
                continue
            rendered_row = rendered.get((prefix_id, arm))
            perturbation = perturbations.get((prefix_id, arm))
            if rendered_row is None or perturbation is None:
                stats.not_at_risk += 1
                continue

            stats.sequences += 1
            replay = replay_cache[domain]
            data = replay.prepare_state(prefix["messages"])
            messages = json.loads(rendered_row["messages_json"])
            tools = tools_cache[domain]
            regex = regex_cache[domain]
            recovered_step: int | None = None
            endpoint = "censored"

            for step in range(1, horizon + 1):
                prompt = build_prompt_messages(messages, tools)
                generation = backend.generate([prompt], response_regex=regex)[0]
                parsed = parse_decision(generation.text)
                append_ledger_row(
                    ledger_path,
                    LedgerRow(
                        run_id=run_id,
                        model_id=model_id,
                        prefix_id=prefix_id,
                        arm=arm,
                        step=step,
                        prompt_hash=prompt_hash(prompt),
                        output_text=generation.text,
                        parsed=parsed.parsed,
                        latency_ms=generation.latency_ms,
                        cost_usd=0.0,
                        timestamp_utc=utc_now(),
                        stage="main",
                        parser_version=PARSER_VERSION,
                        parser_status=parsed.status,
                        signature_hash=signature_hash(parsed) if parsed.parsed else "",
                        decision_json=signature_json(parsed) if parsed.parsed else "",
                        manifest_hash=manifest_hash,
                    ),
                )
                stats.ledger_rows += 1
                if not parsed.parsed:
                    stats.parse_fail += 1
                    break
                if flag_detected(generation.text):
                    recovered_step = step
                    endpoint = "R2"
                    stats.recovered_r2 += 1
                    break
                if signature_hash(parsed) == reference.signature_hash:
                    recovered_step = step
                    endpoint = "R1"
                    stats.recovered_r1 += 1
                    break
                if parsed.final_answer:
                    break
                observation = replay.invoke(data, parsed.tool_name, parsed.arguments)
                if regime == "persistent":
                    observation = _persistent_observation(observation, perturbation)
                messages.append({"role": "assistant", "content": generation.text})
                messages.append(
                    {
                        "role": "tool",
                        "name": parsed.tool_name,
                        "content": observation,
                    }
                )

            if recovered_step is None:
                stats.censored += 1
            _append_event(
                event_path,
                RecoveryEvent(
                    prefix_id=prefix_id,
                    model_id=model_id,
                    regime=regime,
                    severity=int(arm[-1]),
                    horizon=horizon,
                    recovered_step=recovered_step,
                    endpoint=endpoint,
                    censored=recovered_step is None,
                    state_hash=sha256_text(canonical_json(messages)),
                ),
            )

    return stats
