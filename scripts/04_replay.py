#!/usr/bin/env python
"""Stage 04 — replay pinned tool calls and filter on normalized match.

Input:  data/interim/eligible.jsonl
Output: data/interim/replayed.jsonl, data/interim/replay_matched.jsonl,
        artifacts/audit/replay_report.json

Replay starts from a fresh task database, executes every assistant tool call in
the frozen prefix, and compares the final observation with the historical one.
No model or user simulator is called.

GATE: normalized match rate >= 98%; >=880 matched eligible; >=440/domain after
the 10/task cap (the airline arm is the binding constraint).
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import config_hashes, load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl, write_jsonl  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, INTERIM_DIR, UPSTREAM_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402
from toolobs.taubench.replay import replay_candidates  # noqa: E402


def cap10_counts(records) -> dict[str, int]:
    counts: dict[str, Counter[str]] = {}
    for record in records:
        counts.setdefault(record.domain, Counter())[record.task_id] += 1
    return {
        domain: sum(min(value, 10) for value in tasks.values())
        for domain, tasks in sorted(counts.items())
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="input", default=str(INTERIM_DIR / "eligible.jsonl"))
    parser.add_argument("--out", default=str(INTERIM_DIR / "replayed.jsonl"))
    parser.add_argument("--matched-out", default=str(INTERIM_DIR / "replay_matched.jsonl"))
    parser.add_argument("--report", default=str(ARTIFACTS_DIR / "audit" / "replay_report.json"))
    parser.add_argument("--upstream", default=str(UPSTREAM_DIR / "tau-bench"))
    parser.add_argument("--threshold", type=float, default=0.98)
    args = parser.parse_args(argv)

    input_path = resolve_repo_path(args.input)
    output_path = resolve_repo_path(args.out)
    matched_path = resolve_repo_path(args.matched_out)
    report_path = resolve_repo_path(args.report)
    upstream = resolve_repo_path(args.upstream)

    config = load_config("harvest.yaml")
    threshold = float(config.get("eligibility", {}).get("replay_match_threshold", args.threshold))
    records = read_jsonl(input_path)
    replayed, stats = replay_candidates(
        records,
        upstream_dir=upstream,
        only_eligible=False,
    )
    matched = [record for record in replayed if record.replay_match and record.eligible]
    caps = cap10_counts(matched)
    by_domain = Counter(record.domain for record in matched)
    passed = stats["match_rate"] >= threshold
    supply_ok = len(matched) >= 880 and min(caps.get("airline", 0), caps.get("retail", 0)) >= 440

    report = {
        "stage": "04_replay",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "config_hashes": config_hashes(),
        "threshold": threshold,
        "stats": stats,
        "matched": len(matched),
        "matched_by_domain": dict(sorted(by_domain.items())),
        "cap10_by_domain": caps,
        "passed": passed,
        "supply_ok": supply_ok,
    }
    write_json(report_path, report)
    write_jsonl(replayed, output_path)
    write_jsonl(matched, matched_path)

    print(f"[04_replay] replayed {stats['total']}")
    print(f"[04_replay] matches {stats['matches']}")
    print(f"[04_replay] match_rate {stats['match_rate']:.4f}")
    print(f"[04_replay] diffs {stats['diffs']}")
    print(f"[04_replay] matched_eligible {len(matched)}")
    print(f"[04_replay] matched_by_domain {dict(sorted(by_domain.items()))}")
    print(f"[04_replay] cap10_by_domain {caps}")
    print(f"[04_replay] wrote {output_path}")
    print(f"[04_replay] wrote {matched_path}")
    print(f"[04_replay] wrote {report_path}")

    if not passed:
        print(f"[04_replay] FAIL: match rate below {threshold:.2%}")
        return 1
    if not supply_ok:
        print("[04_replay] FAIL: matched supply or domain cap is below the G0 floor")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
