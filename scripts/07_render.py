#!/usr/bin/env python
"""Stage 07 — render five arms and generate perturbation records.

Input:  data/interim/sample.jsonl, configs/field_registry.yaml
Output: data/interim/rendered.jsonl, data/interim/perturbations.jsonl,
        artifacts/audit/render_report.json

V is the exact scrubbed observation as raw JSON. s=0 is a faithful prose
rendering with the same value set. s=1 changes or omits one non-critical field;
s=2 changes one critical field to a plausible wrong value; s=3 adds a second
contradiction. No LLM paraphrase enters the manipulation.

GATE: every sampled prefix has all five arms; 100% s=0 value-set equality;
2,640 perturbation records (880 each for s=1, s=2, s=3); no PII perturbations.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import config_hashes, load_config  # noqa: E402
from toolobs.harvest.parse import TrajectoryStore, read_jsonl, write_jsonl  # noqa: E402
from toolobs.harvest.relevance import PiiPolicy  # noqa: E402
from toolobs.harvest.scrub import (  # noqa: E402
    PiiMap,
    count_direct_identifiers,
    load_task_users,
    scrub_prefix_messages,
)
from toolobs.hashing import sha256_file  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, INTERIM_DIR, UPSTREAM_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402
from toolobs.render.render import (  # noqa: E402
    RENDERER_VERSION,
    build_arms,
    render_arm_messages,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample", default=str(INTERIM_DIR / "sample.jsonl"))
    parser.add_argument("--out", default=str(INTERIM_DIR / "rendered.jsonl"))
    parser.add_argument(
        "--perturbations-out", default=str(INTERIM_DIR / "perturbations.jsonl")
    )
    parser.add_argument("--report", default=str(ARTIFACTS_DIR / "audit" / "render_report.json"))
    parser.add_argument("--upstream", default=str(UPSTREAM_DIR / "tau-bench"))
    args = parser.parse_args(argv)

    sample_path = resolve_repo_path(args.sample)
    output_path = resolve_repo_path(args.out)
    perturbations_path = resolve_repo_path(args.perturbations_out)
    report_path = resolve_repo_path(args.report)
    upstream = resolve_repo_path(args.upstream)

    config = load_config("harvest.yaml")
    configured_version = config.get("freeze", {}).get("renderer_version", RENDERER_VERSION)
    if configured_version != RENDERER_VERSION:
        print(
            f"[07_render] FAIL: config renderer {configured_version} != code {RENDERER_VERSION}"
        )
        return 1

    policy = PiiPolicy.from_config(load_config("field_registry.yaml"))
    store = TrajectoryStore(upstream)
    users_cache: dict[str, dict] = {}
    maps: dict[str, PiiMap] = {}
    records = read_jsonl(sample_path)
    rendered_rows = []
    perturbations = []
    errors: list[str] = []
    direct_identifiers = 0

    for record in records:
        trajectory = store.get_trajectory(record)
        if trajectory.domain not in users_cache:
            users_cache[trajectory.domain] = load_task_users(upstream, trajectory.domain)
        pii_map = maps.get(trajectory.trajectory_id)
        messages, pii_map = scrub_prefix_messages(
            record,
            store,
            policy=policy,
            users=users_cache[trajectory.domain],
            pii_map=pii_map,
        )
        maps[trajectory.trajectory_id] = pii_map
        arms = build_arms(record, seed=int(config["harvest"]["random_seed"]))
        if arms.errors:
            errors.extend(f"{record.prefix_id}: {error}" for error in arms.errors)
            continue
        rows = render_arm_messages(record, messages, arms)
        if len(rows) != 5:
            errors.append(f"{record.prefix_id}: {len(rows)} arms rendered")
            continue
        for row in rows:
            direct_identifiers += count_direct_identifiers(row.observation_text)
        rendered_rows.extend(rows)
        perturbations.extend(arms.perturbations)

    by_arm = Counter(row.arm for row in rendered_rows)
    by_perturbation_arm = Counter(item.arm for item in perturbations)
    report = {
        "stage": "07_render",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "config_hashes": config_hashes(),
        "renderer_version": RENDERER_VERSION,
        "renderer_hash": sha256_file(Path(__file__).resolve().parents[1] / "src" / "toolobs" / "render" / "render.py"),
        "records": len(records),
        "rendered_arms": len(rendered_rows),
        "by_arm": dict(sorted(by_arm.items())),
        "perturbations": len(perturbations),
        "by_perturbation_arm": dict(sorted(by_perturbation_arm.items())),
        "direct_identifiers": direct_identifiers,
        "errors": errors[:50],
        "error_count": len(errors),
    }
    write_json(report_path, report)

    if errors:
        print(f"[07_render] FAIL: {len(errors)} render errors")
        for error in errors[:20]:
            print(f"  - {error}")
        return 1
    if len(rendered_rows) != 5 * len(records):
        print("[07_render] FAIL: not every prefix has five arms")
        return 1
    if by_perturbation_arm != {"s1": len(records), "s2": len(records), "s3": len(records)}:
        print("[07_render] FAIL: perturbation arm counts are not balanced")
        return 1
    if direct_identifiers:
        print("[07_render] FAIL: rendered observation still contains direct identifiers")
        return 1

    write_jsonl(rendered_rows, output_path)
    write_jsonl(perturbations, perturbations_path)
    print(f"[07_render] records {len(records)}")
    print(f"[07_render] rendered_arms {len(rendered_rows)}")
    print(f"[07_render] by_arm {dict(sorted(by_arm.items()))}")
    print(f"[07_render] perturbations {len(perturbations)}")
    print(f"[07_render] by_perturbation_arm {dict(sorted(by_perturbation_arm.items()))}")
    print(f"[07_render] wrote {output_path}")
    print(f"[07_render] wrote {perturbations_path}")
    print(f"[07_render] wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
