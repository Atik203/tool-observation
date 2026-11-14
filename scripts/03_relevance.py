#!/usr/bin/env python
"""Stage 03 — eligible value-used candidate set.

Input:  data/interim/scrubbed.jsonl
Output: data/interim/eligible.jsonl, artifacts/audit/relevance_report.json

The scrubbed records already carry the raw-value relevance labels from stage
02. This stage validates the labels, checks domain balance, and writes the
eligible set. The authoritative G0 floor is >=880 eligible and >=440/domain
before replay (docs/GATES.md); the older 6,500 planning figure is not a gate.

GATE: >=880 eligible overall; >=440 airline and >=440 retail; every record has
at least one used field and a scrubbed observation.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import config_hashes  # noqa: E402
from toolobs.harvest.parse import read_jsonl, write_jsonl  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, INTERIM_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="input", default=str(INTERIM_DIR / "scrubbed.jsonl"))
    parser.add_argument("--out", default=str(INTERIM_DIR / "eligible.jsonl"))
    parser.add_argument("--report", default=str(ARTIFACTS_DIR / "audit" / "relevance_report.json"))
    args = parser.parse_args(argv)

    input_path = resolve_repo_path(args.input)
    output_path = resolve_repo_path(args.out)
    report_path = resolve_repo_path(args.report)

    records = read_jsonl(input_path)
    problems: list[str] = []
    for record in records:
        if not record.eligible:
            problems.append(f"{record.prefix_id}: not eligible")
        if not record.used_fields:
            problems.append(f"{record.prefix_id}: no used fields")
        if not record.scrubbed_observation_json:
            problems.append(f"{record.prefix_id}: no scrubbed observation")
        if not record.scrubbed_prefix_hash:
            problems.append(f"{record.prefix_id}: no scrubbed prefix hash")

    by_domain = Counter(record.domain for record in records)
    by_tool = Counter(record.tool_name for record in records)
    report = {
        "stage": "03_relevance",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "config_hashes": config_hashes(),
        "records": len(records),
        "by_domain": dict(sorted(by_domain.items())),
        "by_tool": dict(sorted(by_tool.items())),
        "problems": problems[:50],
        "problem_count": len(problems),
    }
    write_json(report_path, report)

    if problems:
        print(f"[03_relevance] FAIL: {len(problems)} contract problems")
        for problem in problems[:20]:
            print(f"  - {problem}")
        return 1

    write_jsonl(records, output_path)
    print(f"[03_relevance] eligible {len(records)}")
    print(f"[03_relevance] by_domain {dict(sorted(by_domain.items()))}")
    print(f"[03_relevance] wrote {output_path}")
    print(f"[03_relevance] wrote {report_path}")

    if len(records) < 880 or min(by_domain.get("airline", 0), by_domain.get("retail", 0)) < 440:
        print("[03_relevance] FAIL: eligible set is below the G0 pre-replay floor")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
