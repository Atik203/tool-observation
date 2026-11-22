"""Second deterministic renderer: a flat field-list surface.

`toolresult-prose-v1` renders the scrubbed observation as nested bullets.
`toolresult-fieldlist-v1` renders the same scalar leaves as one flat
``path = value`` line each. Both are deterministic, template-only, and emit the
same information: every scalar leaf appears exactly once with the same value
and a structurally equivalent path.

The five-arm construction deliberately repeats stage 07's perturbation choices:
same candidate lists, same seed strings, same ``choose_perturbation`` calls.
The caller verifies that re-rendering the resulting observations with the v1
prose renderer reproduces the frozen arm strings before any GPU generation.

``V`` stays the raw scrubbed observation JSON; only the prose S arms change.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from ..harvest.relevance import (
    continuation_surface,
    is_simple_key,
    normalize_scalar,
    value_in_text,
)
from ..hashing import canonical_json, sha256_text
from ..schemas import PrefixRecord
from .perturb import PerturbationChoice, apply_choice, choose_perturbation, value_set
from .render import ARM_SEVERITY, ARMS, RenderedArm, render_observation, replace_observation

RENDERER2_VERSION = "toolresult-fieldlist-v1"


def format_scalar(value: Any) -> str:
    """Format a scalar for the flat field-list surface."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        if not value:
            return '""'
        return (
            value.replace("\\", "\\\\")
            .replace("\r", "\\r")
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )
    return str(value)


def _display_path(parent: str, key: str) -> str:
    segment = key if is_simple_key(key) else f"[{json.dumps(key, ensure_ascii=False)}]"
    if not parent:
        return segment
    return f"{parent}.{segment}" if is_simple_key(key) else f"{parent}{segment}"


def _render_node(
    value: Any,
    lines: list[str],
    emitted: list[tuple[str, Any]],
    *,
    path: str,
    pattern: str,
) -> None:
    if isinstance(value, dict):
        if not value:
            lines.append(f"{path or '$'} = {{}}")
            return
        for key in sorted(value):
            key_text = str(key)
            _render_node(
                value[key],
                lines,
                emitted,
                path=_display_path(path, key_text),
                pattern=f"{pattern}.{key_text}" if is_simple_key(key_text) else f"{pattern}.*",
            )
    elif isinstance(value, list):
        if not value:
            lines.append(f"{path or '$'} = []")
            return
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            _render_node(
                child,
                lines,
                emitted,
                path=child_path,
                pattern=f"{pattern}[]",
            )
    else:
        lines.append(f"{path or '$'} = {format_scalar(value)}")
        emitted.append((pattern, value))


def render_observation2(observation: Any) -> tuple[str, list[tuple[str, Any]]]:
    """Render an observation as a flat ``path = value`` field list."""
    lines = ["Observation (field list):"]
    emitted: list[tuple[str, Any]] = []
    _render_node(observation, lines, emitted, path="", pattern="$")
    return "\n".join(lines), emitted


def emitted_value_set(emitted: list[tuple[str, Any]]) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for pattern, value in emitted:
        normalized = normalize_scalar(value)
        if normalized is not None:
            values.append((pattern, normalized))
    return sorted(values)


@dataclass(slots=True)
class ArmSet2:
    """Five rendered arms, their v1 counterparts, and the perturbation map."""

    observations: dict[str, str] = field(default_factory=dict)
    prose_observations: dict[str, str] = field(default_factory=dict)
    changes: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    s0_value_set_ok: bool = False


def _change(arm: str, choice: PerturbationChoice) -> dict[str, Any]:
    return {
        "arm": arm,
        "json_path": choice.json_path,
        "true_value": choice.true_value,
        "false_value": choice.false_value,
        "criticality": choice.criticality,
        "mode": choice.mode,
    }


def build_arms2(record: PrefixRecord, *, seed: int) -> ArmSet2:
    """Build the frozen five arms and render the S arms as a flat field list.

    The perturbation selection mirrors ``render.build_arms`` exactly. The
    returned ``prose_observations`` allow the caller to prove that equivalence
    against the frozen v1 strings before running any model.
    """
    errors: list[str] = []
    try:
        observation = json.loads(record.scrubbed_observation_json)
    except json.JSONDecodeError:
        return ArmSet2(errors=["unparseable_scrubbed_observation"])

    observations: dict[str, Any] = {"V": observation}
    observations["s0"] = observation
    changes: list[dict[str, Any]] = []

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
        observations["s1"] = apply_choice(observation, s1)
        changes.append(_change("s1", s1))

    s2 = choose_perturbation(
        observation,
        record.critical_fields,
        criticality="critical",
        seed=f"{seed}|{record.prefix_id}|s2",
    )
    if s2 is None:
        errors.append("no_s2_field")
    else:
        observations["s2"] = apply_choice(observation, s2)
        changes.append(_change("s2", s2))
        s3 = choose_perturbation(
            observation,
            record.critical_fields,
            criticality="critical",
            seed=f"{seed}|{record.prefix_id}|s3",
            excluded_paths={s2.json_path},
        )
        if s3 is None:
            s3 = choose_perturbation(
                observation,
                record.noncritical_fields,
                criticality="noncritical",
                seed=f"{seed}|{record.prefix_id}|s3b",
                excluded_paths={s2.json_path},
            )
        if s3 is None:
            errors.append("no_s3_second_field")
        else:
            observations["s3"] = apply_choice(apply_choice(observation, s2), s3)
            changes.append(_change("s3", s3))

    rendered: dict[str, str] = {}
    prose: dict[str, str] = {}
    s0_ok = False
    for arm in ARMS:
        value = observations.get(arm)
        if value is None:
            continue
        text, emitted = render_observation2(value)
        prose_text, _ = render_observation(value)
        if arm == "V":
            text = record.scrubbed_observation_json
            prose_text = record.scrubbed_observation_json
        values_ok = value_set(value) == emitted_value_set(emitted)
        if not values_ok:
            errors.append(f"{arm}_value_set_mismatch")
        if arm == "s0":
            s0_ok = values_ok
        rendered[arm] = text
        prose[arm] = prose_text

    return ArmSet2(
        observations=rendered,
        prose_observations=prose,
        changes=changes,
        errors=errors,
        s0_value_set_ok=s0_ok,
    )


def render_arm_messages2(
    record: PrefixRecord,
    messages: list[dict[str, Any]],
    arm_set: ArmSet2,
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
                domain=record.domain,
                renderer_version=RENDERER2_VERSION,
            )
        )
    return rows
