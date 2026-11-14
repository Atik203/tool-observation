#!/usr/bin/env python
"""Stage 06 — freeze the ToolResult-800 manifest.

Input:  data/interim/sample.jsonl, rendered.jsonl, perturbations.jsonl,
        data/interim/replay_matched.jsonl, artifacts/audit/g0_audit_result.json
Output: data/manifests/toolresult800_v1.json + .sha256.json,
        data/interim/calibration.jsonl, artifacts/audit/g0_report.md

The final manifest is written only after the human audit passes. `--dry-run`
validates every other freeze input and writes a dry-run report without creating
the frozen manifest.

GATE: 880 sample (400/400 primary + 40/40 reserve); 5 arms per prefix; 2,640
perturbations; audit >=36/40; no target-model output before freeze.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import config_hashes, load_config  # noqa: E402
from toolobs.harvest.freeze import (  # noqa: E402
    FreezeInputs,
    build_manifest,
    hash_renderer,
    load_audit,
    validate_freeze_inputs,
    write_manifest,
)
from toolobs.harvest.parse import read_jsonl, read_jsonl_dicts, write_jsonl  # noqa: E402
from toolobs.harvest.sample import select_calibration  # noqa: E402
from toolobs.hashing import sha256_text_file  # noqa: E402
from toolobs.paths import (  # noqa: E402
    ARTIFACTS_DIR,
    CONFIG_DIR,
    INTERIM_DIR,
    MANIFEST_DIR,
    PREREG_DIR,
    resolve_repo_path,
)
from toolobs.provenance import assert_no_target_outputs, git_commit, utc_now, write_json  # noqa: E402
from toolobs.schemas import PerturbationRecord  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample", default=str(INTERIM_DIR / "sample.jsonl"))
    parser.add_argument("--rendered", default=str(INTERIM_DIR / "rendered.jsonl"))
    parser.add_argument("--perturbations", default=str(INTERIM_DIR / "perturbations.jsonl"))
    parser.add_argument(
        "--replay-matched", default=str(INTERIM_DIR / "replay_matched.jsonl")
    )
    parser.add_argument(
        "--audit-result", default=str(ARTIFACTS_DIR / "audit" / "g0_audit_result.json")
    )
    parser.add_argument("--calibration-out", default=str(INTERIM_DIR / "calibration.jsonl"))
    parser.add_argument("--out", default=str(MANIFEST_DIR / "toolresult800_v1.json"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    sample_path = resolve_repo_path(args.sample)
    rendered_path = resolve_repo_path(args.rendered)
    perturbations_path = resolve_repo_path(args.perturbations)
    replay_path = resolve_repo_path(args.replay_matched)
    audit_path = resolve_repo_path(args.audit_result)
    calibration_path = resolve_repo_path(args.calibration_out)
    output_path = resolve_repo_path(args.out)

    config = load_config("harvest.yaml")
    sample = read_jsonl(sample_path)
    rendered = read_jsonl_dicts(rendered_path)
    perturbations = [
        PerturbationRecord.from_dict(row)
        for row in read_jsonl_dicts(perturbations_path)
    ]
    replay_matched = read_jsonl(replay_path)
    audit = load_audit(audit_path)
    sample_ids = {record.prefix_id for record in sample}
    calibration, calibration_stats = select_calibration(
        replay_matched,
        exclude_ids=sample_ids,
        per_domain=30,
        seed=int(config["harvest"]["random_seed"]),
    )
    write_jsonl(calibration, calibration_path)

    try:
        assert_no_target_outputs()
    except RuntimeError as exc:
        print(f"[06_freeze] FAIL: {exc}")
        return 1

    renderer_path = REPO_ROOT / "src" / "toolobs" / "render" / "render.py"
    perturb_path = REPO_ROOT / "src" / "toolobs" / "render" / "perturb.py"
    inputs = FreezeInputs(
        sample=sample,
        rendered=rendered,
        perturbations=perturbations,
        calibration=calibration,
        audit=audit,
        config_hashes=config_hashes(),
        prereg_hash=sha256_text_file(PREREG_DIR / "PREREGISTRATION.md"),
        renderer_version=str(config.get("freeze", {}).get("renderer_version", "")),
        renderer_hash=hash_renderer(renderer_path, perturb_path),
        field_registry_hash=sha256_text_file(CONFIG_DIR / "field_registry.yaml"),
        source_pin_hash=sha256_text_file(MANIFEST_DIR / "source_pin.json"),
        sample_hash=sha256_text_file(sample_path),
        perturbations_hash=sha256_text_file(perturbations_path),
    )
    problems = validate_freeze_inputs(inputs, require_audit=False)
    audit_pass = bool(audit.get("gate_pass"))
    if problems:
        print(f"[06_freeze] FAIL: {len(problems)} freeze contract problems")
        for problem in problems[:20]:
            print(f"  - {problem}")
        return 1
    if not audit_pass and not args.dry_run:
        print("[06_freeze] FAIL: human audit is not passed")
        print("  run scripts/08_audit.py --score artifacts/audit/g0_audit_sheet.csv")
        return 1

    manifest = build_manifest(inputs)
    if args.dry_run:
        dry_run_path = ARTIFACTS_DIR / "audit" / "freeze_dry_run.json"
        write_json(
            dry_run_path,
            {
                "stage": "06_freeze_dry_run",
                "recorded_utc": utc_now(),
                "git_commit": git_commit(),
                "audit_status": "passed" if audit_pass else "pending_human",
                "calibration": calibration_stats,
                "counts": manifest.counts,
                "problems": [],
                "manifest_preview": manifest.to_dict(),
            },
        )
        print(f"[06_freeze] dry-run counts {manifest.counts}")
        print(f"[06_freeze] calibration {calibration_stats}")
        print(f"[06_freeze] audit_status {'passed' if audit_pass else 'pending_human'}")
        print(f"[06_freeze] wrote {dry_run_path}")
        return 0

    target, sidecar = write_manifest(manifest, output_path)
    report_path = ARTIFACTS_DIR / "audit" / "g0_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "# G0 report\n\n"
        f"- Manifest: `{target}`\n"
        f"- Sidecar: `{sidecar}`\n"
        f"- Git commit: `{git_commit()}`\n"
        f"- Counts: `{json.dumps(manifest.counts, sort_keys=True)}`\n"
        f"- Audit: `{json.dumps(manifest.audit, sort_keys=True)}`\n"
        f"- Renderer: `{manifest.renderer_version}` ({manifest.renderer_hash})\n"
        f"- Prereg hash: `{manifest.prereg_hash}`\n"
        f"- Source pin hash: `{manifest.source_pin_hash}`\n",
        encoding="utf-8",
    )
    print(f"[06_freeze] counts {manifest.counts}")
    print(f"[06_freeze] wrote {target}")
    print(f"[06_freeze] wrote {sidecar}")
    print(f"[06_freeze] wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
