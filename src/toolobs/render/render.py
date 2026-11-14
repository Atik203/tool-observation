"""Deterministic prose renderer and five-arm construction.

V is the exact scrubbed observation as raw JSON. s=0 is a faithful prose
rendering that emits every scalar leaf exactly once. s=1 changes or omits one
non-critical field; s=2 changes one critical field to a plausible wrong value;
s=3 adds a second contradiction. No LLM paraphrase enters the manipulation.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any

from ..harvest.relevance import (
    continuation_surface,
    is_simple_key,
    join_path,
    normalize_scalar,
    value_in_text,
)
from ..hashing import canonical_json, sha256_record, sha256_text
from ..schemas import PerturbationRecord, PrefixRecord
from .perturb import (
    PerturbationChoice,
    apply_choice,
    choose_perturbation,
    value_set,
)

RENDERER_VERSION = "toolresult-prose-v1"
ARM_SEVERITY = {"V": 0, "s0": 0, "s1": 1, "s2": 2, "s3": 3}
ARMS = ("V", "s0", "s1", "s2", "s3")


@dataclass(slots=True)
class RenderedArm:
    """One rendered arm for one prefix."""

    prefix_id: str
    arm: str
    severity: int
    observation_text: str
    messages_json: str
    prompt_hash: str
    renderer_version: str = RENDERER_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "prefix_id": self.prefix_id,
            "arm": self.arm,
            "severity": self.severity,
            "observation_text": self.observation_text,
            "messages_json": self.messages_json,
            "prompt_hash": self.prompt_hash,
            "renderer_version": self.renderer_version,
        }


@dataclass(slots=True)
class ArmSet:
    """All five arms and perturbation records for one prefix."""

    observations: dict[str, str]
    perturbations: list[PerturbationRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    s0_value_set_ok: bool = False


def format_scalar(value: Any) -> str:
    """Format a scalar for the prose template."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if value is None:
        return "none"
    if isinstance(value, str):
        return value if value else "(empty string)"
    return str(value)


def _render_node(
    value: Any,
    lines: list[str],
    emitted: list[tuple[str, Any]],
    *,
    indent: int,
    path: str,
    pattern: str,
) -> None:
    prefix = "  " * indent
    if isinstance(value, dict):
        if not value:
            lines.append(f"{prefix}- (empty object)")
            return
        for key in sorted(value):
            key_text = str(key)
            lines.append(f"{prefix}- {key_text}:")
            _render_node(
                value[key],
                lines,
                emitted,
                indent=indent + 1,
                path=join_path(path, key_text),
                pattern=f"{pattern}.{key_text}" if is_simple_key(key_text) else f"{pattern}.*",
            )
    elif isinstance(value, list):
        if not value:
            lines.append(f"{prefix}- (empty list)")
            return
        for index, child in enumerate(value):
            lines.append(f"{prefix}- [{index}]:")
            _render_node(
                child,
                lines,
                emitted,
                indent=indent + 1,
                path=f"{path}[{index}]",
                pattern=f"{pattern}[]",
            )
    else:
        lines.append(f"{prefix}- {format_scalar(value)}")
        emitted.append((pattern, value))


def render_observation(observation: Any) -> tuple[str, list[tuple[str, Any]]]:
    """Render an observation as deterministic key-value/bullet prose."""
    lines = ["Observation:"]
    emitted: list[tuple[str, Any]] = []
    _render_node(observation, lines, emitted, indent=0, path="$", pattern="$")
    return "\n".join(lines), emitted


def _emitted_value_set(emitted: list[tuple[str, Any]]) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for pattern, value in emitted:
        normalized = normalize_scalar(value)
        if normalized is not None:
            values.append((pattern, normalized))
    return sorted(values)


def _perturbation_record(
    record: PrefixRecord,
    choice: PerturbationChoice,
    *,
    arm: str,
    severity: int,
    selection_rule: str,
    s2_base_record_id: str | None = None,
    second: PerturbationChoice | None = None,
    contradiction_type: str = "",
) -> PerturbationRecord:
    record_id = f"{record.prefix_id}:{arm}:{choice.json_path}"
    core = {
        "prefix_id": record.prefix_id,
        "arm": arm,
        "severity": severity,
        "json_path": choice.json_path,
        "true_value": choice.true_value,
        "false_value": choice.false_value,
        "renderer_version": RENDERER_VERSION,
        "second": None
        if second is None
        else {
            "json_path": second.json_path,
            "true_value": second.true_value,
            "false_value": second.false_value,
        },
    }
    checks = ["value_differs", "not_pii"]
    if severity == 1:
        checks.append("absent_from_continuation")
    if severity >= 2:
        checks.append("changes_action")
    return PerturbationRecord(
        prefix_id=record.prefix_id,
        arm=arm,
        severity=severity,
        json_path=choice.json_path,
        true_value=choice.true_value,
        false_value=choice.false_value,
        criticality=choice.criticality,
        expected_action_change=severity >= 2,
        renderer_version=RENDERER_VERSION,
        record_id=record_id,
        perturbation_hash=sha256_record(core),
        renderer_hash=sha256_text(RENDERER_VERSION),
        second_perturbation_id=None
        if second is None
        else f"{record.prefix_id}:{arm}:{second.json_path}",
        value_type=choice.value_type,
        registry_criticality=choice.criticality,
        value_used_in_continuation=severity >= 2,
        selection_rule=selection_rule,
        perturbation_mode=choice.mode,
        plausibility_checks=checks,
        pii_check=True,
        identifier_check=True,
        s2_base_record_id=s2_base_record_id,
        json_path_2="" if second is None else second.json_path,
        true_value_2=None if second is None else second.true_value,
        false_value_2=None if second is None else second.false_value,
        criticality_2="" if second is None else second.criticality,
        contradiction_type=contradiction_type,
        contradiction_basis="" if second is None else "second field changed in the same observation",
    )


def build_arms(
    record: PrefixRecord,
    *,
    seed: int,
) -> ArmSet:
    """Build V, s=0, s=1, s=2, and s=3 for one frozen prefix."""
    errors: list[str] = []
    try:
        observation = json.loads(record.scrubbed_observation_json)
    except json.JSONDecodeError:
        return ArmSet(observations={}, errors=["unparseable_scrubbed_observation"])

    observations: dict[str, str] = {"V": record.scrubbed_observation_json}
    s0_text, s0_emitted = render_observation(observation)
    s0_ok = value_set(observation) == _emitted_value_set(s0_emitted)
    observations["s0"] = s0_text
    if not s0_ok:
        errors.append("s0_value_set_mismatch")

    perturbations: list[PerturbationRecord] = []

    s1 = choose_perturbation(
        observation,
        record.noncritical_fields,
        criticality="noncritical",
        seed=f"{seed}|{record.prefix_id}|s1",
    )
    if s1 is None:
        errors.append("no_s1_field")
    else:
        if value_in_text(s1.true_value, continuation_surface(record)):
            errors.append("s1_field_used_in_continuation")
        observations["s1"] = render_observation(apply_choice(observation, s1))[0]
        perturbations.append(
            _perturbation_record(
                record,
                s1,
                arm="s1",
                severity=1,
                selection_rule="first shuffled noncritical field with a generated alternative",
            )
        )

    s2 = choose_perturbation(
        observation,
        record.critical_fields,
        criticality="critical",
        seed=f"{seed}|{record.prefix_id}|s2",
    )
    if s2 is None:
        errors.append("no_s2_field")
    else:
        observations["s2"] = render_observation(apply_choice(observation, s2))[0]
        s2_record = _perturbation_record(
            record,
            s2,
            arm="s2",
            severity=2,
            selection_rule="first shuffled critical field with a generated alternative",
        )
        perturbations.append(s2_record)

        s3 = choose_perturbation(
            observation,
            record.critical_fields,
            criticality="critical",
            seed=f"{seed}|{record.prefix_id}|s3",
            excluded_paths={s2.json_path},
        )
        contradiction_type = "second_critical_field"
        if s3 is None:
            s3 = choose_perturbation(
                observation,
                record.noncritical_fields,
                criticality="noncritical",
                seed=f"{seed}|{record.prefix_id}|s3b",
                excluded_paths={s2.json_path},
            )
            contradiction_type = "second_noncritical_field"
        if s3 is None:
            errors.append("no_s3_second_field")
        else:
            s3_observation = apply_choice(apply_choice(observation, s2), s3)
            observations["s3"] = render_observation(s3_observation)[0]
            perturbations.append(
                _perturbation_record(
                    record,
                    s2,
                    arm="s3",
                    severity=3,
                    selection_rule="s2 critical field plus a second contradiction",
                    s2_base_record_id=s2_record.record_id,
                    second=s3,
                    contradiction_type=contradiction_type,
                )
            )

    return ArmSet(
        observations=observations,
        perturbations=perturbations,
        errors=errors,
        s0_value_set_ok=s0_ok,
    )


def replace_observation(messages: list[dict[str, Any]], observation_text: str) -> list[dict[str, Any]]:
    """Replace the last tool message content with an arm's observation text."""
    updated = copy.deepcopy(messages)
    for message in reversed(updated):
        if message.get("role") == "tool":
            message["content"] = observation_text
            return updated
    raise ValueError("prefix has no tool message")


def render_arm_messages(
    record: PrefixRecord,
    messages: list[dict[str, Any]],
    arm_set: ArmSet,
) -> list[RenderedArm]:
    """Build rendered prompt messages for every arm that exists."""
    rows: list[RenderedArm] = []
    for arm in ARMS:
        observation_text = arm_set.observations.get(arm)
        if observation_text is None:
            continue
        messages_json = canonical_json(replace_observation(messages, observation_text))
        rows.append(
            RenderedArm(
                prefix_id=record.prefix_id,
                arm=arm,
                severity=ARM_SEVERITY[arm],
                observation_text=observation_text,
                messages_json=messages_json,
                prompt_hash=sha256_text(messages_json),
            )
        )
    return rows
