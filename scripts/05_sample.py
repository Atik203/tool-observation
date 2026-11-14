#!/usr/bin/env python
"""Stage 05 — deterministic stratified 880/800/80 sample.

Input:  data/interim/replay_matched.jsonl
Output: data/interim/sample.jsonl, data/interim/sample_index.jsonl,
        artifacts/audit/sample_report.json

Caps at 10 prefixes per task-domain, then allocates 400 airline + 400 retail
primary and 40 + 40 reserve across donor, step-index bucket, and tool family.
Seed is fixed at 20261108.

GATE: exactly 800 primary (400/400) and 80 reserve (40/40); no task above the
cap; primary and reserve are disjoint; every row is eligible and replay-matched.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import config_hashes, load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl, write_jsonl  # noqa: E402
from toolobs.harvest.sample import (  # noqa: E402
    DEFAULT_CAP,
    DEFAULT_PRIMARY,
    DEFAULT_RESERVE,
    DEFAULT_SEED,
    sample_candidates,
    validate_sample,
)
from toolobs.paths import ARTIFACTS_DIR, INTERIM_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="input", default=str(INTERIM_DIR / "replay_matched.jsonl"))
    parser.add_argument("--out", default=str(INTERIM_DIR / "sample.jsonl"))
    parser.add_argument("--index-out", default=str(INTERIM_DIR / "sample_index.jsonl"))
    parser.add_argument("--report", default=str(ARTIFACTS_DIR / "audit" / "sample_report.json"))
    args = parser.parse_args(argv)

    input_path = resolve_repo_path(args.input)
    output_path = resolve_repo_path(args.out)
    index_path = resolve_repo_path(args.index_out)
    report_path = resolve_repo_path(args.report)

    config = load_config("harvest.yaml")
    harvest = config.get("harvest", {})
    seed = int(harvest.get("random_seed", DEFAULT_SEED))
    cap = int(harvest.get("cap_per_task_domain", DEFAULT_CAP))
    primary_targets = dict(DEFAULT_PRIMARY)
    reserve_targets = dict(DEFAULT_RESERVE)

    records = read_jsonl(input_path)
    result = sample_candidates(
        records,
        primary_targets=primary_targets,
        reserve_targets=reserve_targets,
        cap=cap,
        seed=seed,
    )
    problems = validate_sample(
        result,
        primary_targets=primary_targets,
        reserve_targets=reserve_targets,
        cap=cap,
    )
    report = {
        "stage": "05_sample",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "config_hashes": config_hashes(),
        "stats": result.stats,
        "problems": problems[:50],
        "problem_count": len(problems),
    }
    write_json(report_path, report)

    if problems:
        print(f"[05_sample] FAIL: {len(problems)} sample contract problems")
        for problem in problems[:20]:
            print(f"  - {problem}")
        return 1

    rows = result.primary + result.reserve
    write_jsonl(rows, output_path)
    write_jsonl(result.sample_records(seed), index_path)
    print(f"[05_sample] primary {len(result.primary)}")
    print(f"[05_sample] reserve {len(result.reserve)}")
    print(f"[05_sample] unrenderable {result.stats['unrenderable']}")
    print(f"[05_sample] primary_by_domain {result.stats['primary_by_domain']}")
    print(f"[05_sample] reserve_by_domain {result.stats['reserve_by_domain']}")
    print(f"[05_sample] primary_strata {result.stats['primary_strata']}")
    print(f"[05_sample] reserve_strata {result.stats['reserve_strata']}")
    print(f"[05_sample] wrote {output_path}")
    print(f"[05_sample] wrote {index_path}")
    print(f"[05_sample] wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
