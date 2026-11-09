"""Typed records shared across the pipeline.

These are plain dataclasses, not validation frameworks. Validation belongs in
the stage that constructs a record; serialization is explicit so the frozen
manifest format does not drift silently.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class PrefixRecord:
    """A frozen message prefix ending immediately after a real tool observation."""

    prefix_id: str
    domain: str
    task_id: str
    trajectory_id: str
    donor: str
    trial: int
    step_index: int
    tool_name: str
    observation_json: str
    factual_continuation: str
    message_hashes: list[str] = field(default_factory=list)
    observation_hash: str = ""
    replay_match: bool = False
    eligible: bool = False
    split: str = "unassigned"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PerturbationRecord:
    """One content perturbation applied to a prefix observation."""

    prefix_id: str
    arm: str
    severity: int
    json_path: str
    true_value: Any
    false_value: Any
    criticality: str
    expected_action_change: bool
    renderer_version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DecisionSignature:
    """Canonicalized next decision: tool name plus normalized arguments."""

    tool_name: str
    arguments: dict[str, Any]
    final_answer_slots: dict[str, Any] = field(default_factory=dict)
    action_verb: str = ""

    def canonical(self) -> str:
        import json

        return json.dumps(
            {
                "tool": self.tool_name,
                "args": self.arguments,
                "slots": self.final_answer_slots,
                "verb": self.action_verb,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(slots=True)
class OutcomeLabels:
    """Automatic and adjudicated labels for one generated decision."""

    prefix_id: str
    model_id: str
    arm: str
    y_any: bool
    y_silent: bool
    y_flag: bool
    y_action: bool
    signature_hash: str
    parser_status: str
    adjudicated_label: str | None = None
    rater_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RecoveryEvent:
    """Recovery observation for one prefix, model, and injection regime."""

    prefix_id: str
    model_id: str
    regime: str
    severity: int
    horizon: int
    recovered_step: int | None
    endpoint: str
    censored: bool
    state_hash: str = ""


@dataclass(slots=True)
class LedgerRow:
    """One generation ledger row. Every reported number must trace to one."""

    run_id: str
    model_id: str
    prefix_id: str
    arm: str
    step: int
    prompt_hash: str
    output_text: str
    parsed: bool
    latency_ms: float
    cost_usd: float
    timestamp_utc: str


@dataclass(slots=True)
class GateResult:
    """Pass/fail record for a pre-registered gate."""

    gate: str
    passed: bool
    criteria: dict[str, Any]
    observed: dict[str, Any]
    note: str = ""
