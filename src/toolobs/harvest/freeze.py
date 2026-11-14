"""Build and write the frozen ToolResult-800 manifest.

The manifest stores identity, hashes, counts, arm assignments, perturbation
hashes, the audit result, and the preregistration hash. It never stores raw
observations or PII. The sidecar records the manifest's own hash because a file
cannot contain its own digest.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..hashing import sha256_text_file
from ..provenance import git_commit, manifest_sidecar, utc_now, write_json
from ..schemas import (
    MANIFEST_SCHEMA_VERSION,
    FrozenManifest,
    PerturbationRecord,
    PrefixRecord,
)
from .sample import stratum_key

MANIFEST_ID = "toolresult800-v1"
ARMS = ("V", "s0", "s1", "s2", "s3")
PERTURBATION_ARMS = ("s1", "s2", "s3")


@dataclass(slots=True)
class FreezeInputs:
    """Everything the manifest needs, already loaded and hashed."""

    sample: list[PrefixRecord]
    rendered: list[dict[str, Any]]
    perturbations: list[PerturbationRecord]
    calibration: list[PrefixRecord]
    audit: dict[str, Any]
    config_hashes: dict[str, str]
    prereg_hash: str
    renderer_version: str
    renderer_hash: str
    field_registry_hash: str
    source_pin_hash: str
    sample_hash: str
    perturbations_hash: str
    frozen_prefixes_hash: str = ""


def _hash_file(path: str | Path) -> str:
    return sha256_text_file(path)


def build_frozen_prefixes(
    sample: list[PrefixRecord],
    rendered: list[dict[str, Any]],
    perturbations: list[PerturbationRecord],
) -> list[dict[str, Any]]:
    """Build the self-contained scrubbed prefix payload for release."""
    rendered_by_key = {
        (str(row.get("prefix_id")), str(row.get("arm"))): row for row in rendered
    }
    perturbations_by_prefix: dict[str, list[PerturbationRecord]] = defaultdict(list)
    for item in perturbations:
        perturbations_by_prefix[item.prefix_id].append(item)
    rows: list[dict[str, Any]] = []
    for record in sorted(sample, key=lambda item: item.prefix_id):
        v_row = rendered_by_key.get((record.prefix_id, "V"))
        if v_row is None:
            raise ValueError(f"missing V arm for {record.prefix_id}")
        messages = json.loads(str(v_row["messages_json"]))
        arm_observations = {
            arm: str(rendered_by_key[(record.prefix_id, arm)]["observation_text"])
            for arm in ARMS
            if (record.prefix_id, arm) in rendered_by_key
        }
        rows.append(
            {
                "prefix_id": record.prefix_id,
                "domain": record.domain,
                "task_id": record.task_id,
                "trajectory_id": record.trajectory_id,
                "donor": record.donor,
                "split": record.split,
                "stratum": stratum_key(record),
                "messages": messages,
                "arm_observations": arm_observations,
                "perturbation_ids": [
                    item.record_id for item in perturbations_by_prefix.get(record.prefix_id, [])
                ],
                "observation_hash": record.observation_hash,
                "prefix_hash": record.prefix_hash,
                "scrubbed_observation_hash": record.scrubbed_observation_hash,
                "scrubbed_prefix_hash": record.scrubbed_prefix_hash,
                "replay_match": record.replay_match,
                "replay_diff": record.replay_diff,
                "renderer_version": str(v_row.get("renderer_version", "")),
            }
        )
    return rows


def build_manifest(inputs: FreezeInputs) -> FrozenManifest:
    """Build the manifest from validated inputs."""
    rendered_by_prefix: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in inputs.rendered:
        rendered_by_prefix[str(row.get("prefix_id", ""))].append(row)
    perturbations_by_prefix: dict[str, list[PerturbationRecord]] = defaultdict(list)
    for record in inputs.perturbations:
        perturbations_by_prefix[record.prefix_id].append(record)

    prefixes: list[dict[str, Any]] = []
    for record in sorted(inputs.sample, key=lambda item: item.prefix_id):
        rows = rendered_by_prefix.get(record.prefix_id, [])
        perturbations = sorted(
            perturbations_by_prefix.get(record.prefix_id, []),
            key=lambda item: item.arm,
        )
        prefixes.append(
            {
                "prefix_id": record.prefix_id,
                "domain": record.domain,
                "task_id": record.task_id,
                "trajectory_id": record.trajectory_id,
                "donor": record.donor,
                "trial": record.trial,
                "step_index": record.step_index,
                "step_index_bucket": record.step_index_bucket,
                "tool_name": record.tool_name,
                "tool_family": record.tool_family,
                "split": record.split,
                "stratum": stratum_key(record),
                "message_hashes": record.message_hashes,
                "observation_hash": record.observation_hash,
                "prefix_hash": record.prefix_hash,
                "scrubbed_observation_hash": record.scrubbed_observation_hash,
                "scrubbed_prefix_hash": record.scrubbed_prefix_hash,
                "replay_match": record.replay_match,
                "replay_diff": record.replay_diff,
                "replay_historical_hash": record.replay_historical_hash,
                "replay_observed_hash": record.replay_observed_hash,
                "renderer_version": inputs.renderer_version,
                "arms": sorted({str(row.get("arm")) for row in rows}),
                "prompt_hashes": {
                    str(row.get("arm")): str(row.get("prompt_hash")) for row in rows
                },
                "perturbation_ids": [item.record_id for item in perturbations],
                "perturbation_hashes": [item.perturbation_hash for item in perturbations],
                "used_field_paths": [field.get("json_path") for field in record.used_fields],
                "critical_field_paths": record.critical_fields,
                "noncritical_field_paths": record.noncritical_fields,
                "pii_field_paths": record.pii_fields,
            }
        )

    primary = [record for record in inputs.sample if record.split == "primary"]
    reserve = [record for record in inputs.sample if record.split == "reserve"]
    counts = {
        "primary": len(primary),
        "reserve": len(reserve),
        "primary_by_domain": dict(sorted(Counter(row.domain for row in primary).items())),
        "reserve_by_domain": dict(sorted(Counter(row.domain for row in reserve).items())),
        "rendered_arms": len(inputs.rendered),
        "perturbations": len(inputs.perturbations),
        "perturbations_by_arm": dict(
            sorted(Counter(item.arm for item in inputs.perturbations).items())
        ),
        "calibration": len(inputs.calibration),
    }
    return FrozenManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        manifest_id=MANIFEST_ID,
        created_utc=utc_now(),
        prereg_hash=inputs.prereg_hash,
        renderer_version=inputs.renderer_version,
        renderer_hash=inputs.renderer_hash,
        field_registry_hash=inputs.field_registry_hash,
        sample_hash=inputs.sample_hash,
        perturbations_hash=inputs.perturbations_hash,
        frozen_prefixes_hash=inputs.frozen_prefixes_hash,
        prefixes=prefixes,
        calibration_ids=sorted(record.prefix_id for record in inputs.calibration),
        reserve_ids=sorted(record.prefix_id for record in reserve),
        counts=counts,
        config_hashes=inputs.config_hashes,
        source_pin_hash=inputs.source_pin_hash,
        audit=inputs.audit,
        freeze={
            "frozen_utc": utc_now(),
            "git_commit": git_commit(),
            "no_target_outputs_before_freeze": True,
            "audit_gate_pass": bool(inputs.audit.get("gate_pass")),
        },
    )


def validate_freeze_inputs(
    inputs: FreezeInputs,
    *,
    require_audit: bool = True,
    primary_per_domain: int = 400,
    reserve_per_domain: int = 40,
) -> list[str]:
    """Return contract violations for a freeze attempt."""
    problems: list[str] = []
    sample = inputs.sample
    primary = [record for record in sample if record.split == "primary"]
    reserve = [record for record in sample if record.split == "reserve"]
    if len(sample) != 880:
        problems.append(f"sample size {len(sample)} != 880")
    if len(primary) != 800:
        problems.append(f"primary size {len(primary)} != 800")
    if len(reserve) != 80:
        problems.append(f"reserve size {len(reserve)} != 80")
    for domain in ("airline", "retail"):
        if sum(1 for row in primary if row.domain == domain) != primary_per_domain:
            problems.append(f"primary {domain} count is wrong")
        if sum(1 for row in reserve if row.domain == domain) != reserve_per_domain:
            problems.append(f"reserve {domain} count is wrong")

    ids = [record.prefix_id for record in sample]
    if len(ids) != len(set(ids)):
        problems.append("duplicate sample prefix ids")
    calibration_ids = {record.prefix_id for record in inputs.calibration}
    if set(ids) & calibration_ids:
        problems.append("calibration overlaps the frozen sample")
    if len(calibration_ids) != 60:
        problems.append(f"calibration size {len(calibration_ids)} != 60")

    rendered_by_prefix: dict[str, list[str]] = defaultdict(list)
    for row in inputs.rendered:
        rendered_by_prefix[str(row.get("prefix_id", ""))].append(str(row.get("arm")))
    perturbed_by_prefix: dict[str, list[str]] = defaultdict(list)
    for item in inputs.perturbations:
        perturbed_by_prefix[item.prefix_id].append(item.arm)
    for record in sample:
        if not record.eligible:
            problems.append(f"{record.prefix_id}: not eligible")
        if not record.replay_match:
            problems.append(f"{record.prefix_id}: replay did not match")
        arms = sorted(rendered_by_prefix.get(record.prefix_id, []))
        if arms != sorted(ARMS):
            problems.append(f"{record.prefix_id}: arms {arms} != {list(ARMS)}")
        pert_arms = sorted(perturbed_by_prefix.get(record.prefix_id, []))
        if pert_arms != sorted(PERTURBATION_ARMS):
            problems.append(f"{record.prefix_id}: perturbation arms {pert_arms}")
    hashes = [item.perturbation_hash for item in inputs.perturbations]
    if len(hashes) != len(set(hashes)):
        problems.append("duplicate perturbation hashes")
    if len(inputs.perturbations) != 2640:
        problems.append(f"perturbations {len(inputs.perturbations)} != 2640")
    if not inputs.frozen_prefixes_hash:
        problems.append("missing frozen prefix payload hash")
    if require_audit and not inputs.audit.get("gate_pass"):
        problems.append("human audit gate is not passed")
    return problems


def write_manifest(manifest: FrozenManifest, path: str | Path) -> tuple[Path, Path]:
    """Write the manifest and its hash sidecar."""
    target = write_json(path, manifest.to_dict())
    sidecar = target.with_suffix(".sha256.json")
    write_json(sidecar, manifest_sidecar(target))
    return target, sidecar


def load_audit(path: str | Path) -> dict[str, Any]:
    """Load a G0 audit result, returning an empty mapping if absent."""
    candidate = Path(path)
    if not candidate.is_file():
        return {}
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def hash_renderer(render_path: str | Path, perturb_path: str | Path) -> str:
    """Hash the renderer and perturbation generator sources together."""
    from ..hashing import sha256_record

    return sha256_record(
        {
            "render": _hash_file(render_path),
            "perturb": _hash_file(perturb_path),
        }
    )
