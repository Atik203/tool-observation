"""Typed records shared across the pipeline.

These are plain dataclasses, not validation frameworks. Validation belongs in
the stage that constructs a record; serialization is explicit so the frozen
manifest format does not drift silently.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


class RecordMixin:
    """Small serialization helper shared by every record."""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        names = {item.name for item in fields(cls)}
        return cls(**{key: value for key, value in data.items() if key in names})


PREFIX_SCHEMA_VERSION = "toolresult800-prefix-v1"
PERTURBATION_SCHEMA_VERSION = "toolresult800-perturbation-v1"
LEDGER_SCHEMA_VERSION = "toolresult800-ledger-v1"
SAMPLE_SCHEMA_VERSION = "toolresult800-sample-v1"
PIN_SCHEMA_VERSION = "toolresult800-pin-v1"
MODEL_PINS_SCHEMA_VERSION = "toolresult800-model-pins-v1"
MANIFEST_SCHEMA_VERSION = "toolresult800-manifest-v1"


@dataclass(slots=True)
class PrefixRecord(RecordMixin):
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

    # G0 contract additions
    tool_family: str = ""
    step_index_bucket: str = ""
    used_fields: list[dict[str, Any]] = field(default_factory=list)
    critical_fields: list[str] = field(default_factory=list)
    perturbations: list[str] = field(default_factory=list)
    renderer_version: str = ""
    arm: str = ""
    severity: int | None = None
    decision_signature: str = ""
    schema_version: str = PREFIX_SCHEMA_VERSION


@dataclass(slots=True)
class PerturbationRecord(RecordMixin):
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

    # G0 contract additions
    record_id: str = ""
    perturbation_hash: str = ""
    renderer_hash: str = ""
    second_perturbation_id: str | None = None
    value_type: str = ""
    registry_criticality: str = ""
    value_used_in_continuation: bool = False
    selection_rule: str = ""
    perturbation_mode: str = ""
    plausibility_checks: list[str] = field(default_factory=list)
    pii_check: bool = False
    identifier_check: bool = False
    s2_base_record_id: str | None = None
    json_path_2: str = ""
    true_value_2: Any = None
    false_value_2: Any = None
    criticality_2: str = ""
    contradiction_type: str = ""
    contradiction_basis: str = ""
    schema_version: str = PERTURBATION_SCHEMA_VERSION


@dataclass(slots=True)
class DecisionSignature(RecordMixin):
    """Canonicalized next decision: tool name plus normalized arguments."""

    tool_name: str
    arguments: dict[str, Any]
    final_answer_slots: dict[str, Any] = field(default_factory=dict)
    action_verb: str = ""
    schema_version: str = "toolresult800-signature-v1"

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
class OutcomeLabels(RecordMixin):
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
    schema_version: str = "toolresult800-outcome-v1"


@dataclass(slots=True)
class RecoveryEvent(RecordMixin):
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
    schema_version: str = "toolresult800-recovery-v1"


@dataclass(slots=True)
class LedgerRow(RecordMixin):
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

    # G1/G2 contract additions
    stage: str = ""
    gpu_hours: float = 0.0
    storage_gb: float = 0.0
    parser_version: str = ""
    prompt_version: str = ""
    manifest_hash: str = ""
    schema_version: str = LEDGER_SCHEMA_VERSION


@dataclass(slots=True)
class GateResult(RecordMixin):
    """Pass/fail record for a pre-registered gate."""

    gate: str
    passed: bool
    criteria: dict[str, Any]
    observed: dict[str, Any]
    note: str = ""
    schema_version: str = "toolresult800-gate-v1"


@dataclass(slots=True)
class SampleRecord(RecordMixin):
    """One selected prefix in the frozen sample."""

    prefix_id: str
    domain: str
    task_id: str
    donor: str
    step_bucket: str
    tool_family: str
    split: str
    stratum: str
    seed: int
    schema_version: str = SAMPLE_SCHEMA_VERSION


@dataclass(slots=True)
class PinRecord(RecordMixin):
    """Pinned upstream source and environment hashes."""

    repo_url: str
    commit_sha: str
    license: str
    trajectory_hashes: dict[str, str] = field(default_factory=dict)
    task_db_hashes: dict[str, str] = field(default_factory=dict)
    harness_hash: str = ""
    pinned_utc: str = ""
    pin_version: str = PIN_SCHEMA_VERSION
    schema_version: str = PIN_SCHEMA_VERSION


@dataclass(slots=True)
class ModelPins(RecordMixin):
    """Pinned model revisions and tokenizer hashes."""

    model_id: str
    repo_id: str
    revision: str
    quantization: str
    tokenizer_hash: str
    license: str
    pinned_utc: str = ""
    schema_version: str = MODEL_PINS_SCHEMA_VERSION


@dataclass(slots=True)
class FrozenManifest(RecordMixin):
    """Top-level frozen dataset manifest.

    Per-prefix payloads are stored in ``prefix_index.jsonl``; this object
    records identity, hashes, counts, and freeze integrity.
    """

    schema_version: str
    manifest_id: str
    created_utc: str
    prereg_hash: str
    renderer_version: str
    renderer_hash: str
    field_registry_hash: str
    sample_hash: str
    perturbations_hash: str
    prefixes: list[dict[str, Any]] = field(default_factory=list)
    calibration_ids: list[str] = field(default_factory=list)
    reserve_ids: list[str] = field(default_factory=list)
    counts: dict[str, Any] = field(default_factory=dict)
    config_hashes: dict[str, str] = field(default_factory=dict)
    source_pin_hash: str = ""
    audit: dict[str, Any] = field(default_factory=dict)
    freeze: dict[str, Any] = field(default_factory=dict)
