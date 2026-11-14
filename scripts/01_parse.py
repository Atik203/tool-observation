#!/usr/bin/env python
"""Stage 01 — parse τ-bench trajectories into candidate post-tool decision points.

Input:  data/upstream/tau-bench (pinned), data/upstream/PIN.json
Output: data/interim/candidates.jsonl, data/interim/candidates.meta.json

Each candidate records trajectory ID, task ID, trial, donor, domain, step
index, tool name, raw observation, factual continuation, and prefix hashes.
The full prefix is materialized from the pinned file on demand.

GATE: every candidate has all required fields; frame counts match
configs/harvest.yaml (13,605 candidates; 11,318 JSON-parseable).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import config_hashes, load_config  # noqa: E402
from toolobs.harvest.parse import (  # noqa: E402
    parse_frame,
    validate_candidates,
    write_jsonl,
)
from toolobs.hashing import sha256_file  # noqa: E402
from toolobs.paths import INTERIM_DIR, UPSTREAM_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402
from toolobs.taubench.pin import PinError, load_pin, verify_pin  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="configs/harvest.yaml")
    parser.add_argument("--upstream", default=str(UPSTREAM_DIR / "tau-bench"))
    parser.add_argument("--pin", default=str(UPSTREAM_DIR / "PIN.json"))
    parser.add_argument("--out", default=str(INTERIM_DIR / "candidates.jsonl"))
    parser.add_argument("--meta-out", default=str(INTERIM_DIR / "candidates.meta.json"))
    parser.add_argument("--no-expected-check", action="store_true")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config).name)
    source = config["source"]
    upstream = resolve_repo_path(args.upstream)
    pin_path = resolve_repo_path(args.pin)
    out = resolve_repo_path(args.out)
    meta_out = resolve_repo_path(args.meta_out)

    if not pin_path.is_file():
        print(f"[01_parse] FAIL: missing pin {pin_path}; run scripts/00_pin_source.py first")
        return 1
    try:
        pin = load_pin(pin_path)
        problems = verify_pin(pin, upstream)
    except PinError as exc:
        print(f"[01_parse] FAIL: {exc}")
        return 1
    if problems:
        print("[01_parse] FAIL: upstream does not match pin")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    records, stats = parse_frame(upstream, source["trajectory_files"])
    problems = validate_candidates(records)
    if problems:
        print(f"[01_parse] FAIL: {len(problems)} candidate contract problems")
        for problem in problems[:20]:
            print(f"  - {problem}")
        return 1

    if not args.no_expected_check:
        expected = {
            "trajectories": source.get("expected_trajectories"),
            "candidates": source.get("expected_candidates"),
            "json_parseable": source.get("expected_json_parseable"),
        }
        observed = {
            "trajectories": stats.trajectories,
            "candidates": stats.candidates,
            "json_parseable": stats.json_parseable,
        }
        mismatches = [
            f"{key}: expected {expected[key]}, got {observed[key]}"
            for key in expected
            if expected[key] is not None and expected[key] != observed[key]
        ]
        if mismatches:
            print("[01_parse] FAIL: frame does not match the pinned harvest config")
            for mismatch in mismatches:
                print(f"  - {mismatch}")
            return 1

    if stats.unknown_tools:
        print("[01_parse] FAIL: unknown tool names need a family mapping")
        for name, count in sorted(stats.unknown_tools.items()):
            print(f"  - {name}: {count}")
        return 1

    write_jsonl(records, out)
    write_json(
        meta_out,
        {
            "stage": "01_parse",
            "recorded_utc": utc_now(),
            "git_commit": git_commit(),
            "pin_path": str(pin_path.relative_to(REPO_ROOT)) if pin_path.is_relative_to(REPO_ROOT) else str(pin_path),
            "pin_sha256": sha256_file(pin_path),
            "pin_commit": pin.commit_sha,
            "config_hashes": config_hashes(),
            "output": str(out.relative_to(REPO_ROOT)) if out.is_relative_to(REPO_ROOT) else str(out),
            "stats": stats.as_dict(),
        },
    )

    print(f"[01_parse] trajectories {stats.trajectories}")
    print(f"[01_parse] candidates {stats.candidates}")
    print(f"[01_parse] json_parseable {stats.json_parseable}")
    print(f"[01_parse] text_observations {stats.text_observations}")
    print(f"[01_parse] think_skipped {stats.think_skipped}")
    print(f"[01_parse] no_continuation_skipped {stats.no_continuation_skipped}")
    print(f"[01_parse] profile_tool_candidates {stats.profile_tool_candidates}")
    print(f"[01_parse] wrote {out}")
    print(f"[01_parse] wrote {meta_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
