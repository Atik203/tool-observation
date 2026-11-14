#!/usr/bin/env python
"""Stage 02 — relevance annotation and PII scrubbing.

Input:  data/interim/candidates.jsonl, configs/field_registry.yaml
Output: data/interim/scrubbed.jsonl, artifacts/audit/scrub_report.json

Relevance is evaluated on raw values first, so the used/PII labels are not
changed by tokenization. Only eligible candidates are scrubbed and carried
forward; the full scrubbed prefix is re-derived at freeze from the pinned
trajectory with the same deterministic token map.

GATE: zero raw direct identifiers in the scrubbed scan; excluded-tool count
reported; >=880 eligible and >=440/domain before replay.
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
from toolobs.harvest.relevance import PiiPolicy, annotate_candidates  # noqa: E402
from toolobs.harvest.scrub import (  # noqa: E402
    count_direct_identifiers,
    scrub_candidates,
)
from toolobs.paths import ARTIFACTS_DIR, INTERIM_DIR, UPSTREAM_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="input", default=str(INTERIM_DIR / "candidates.jsonl"))
    parser.add_argument("--out", default=str(INTERIM_DIR / "scrubbed.jsonl"))
    parser.add_argument("--report", default=str(ARTIFACTS_DIR / "audit" / "scrub_report.json"))
    parser.add_argument("--upstream", default=str(UPSTREAM_DIR / "tau-bench"))
    args = parser.parse_args(argv)

    input_path = resolve_repo_path(args.input)
    output_path = resolve_repo_path(args.out)
    report_path = resolve_repo_path(args.report)
    upstream = resolve_repo_path(args.upstream)

    registry = load_config("field_registry.yaml")
    policy = PiiPolicy.from_config(registry)
    records = read_jsonl(input_path)
    annotated, relevance_stats = annotate_candidates(records, pii_policy=policy)
    scrubbed, scrub_stats = scrub_candidates(
        annotated,
        upstream_dir=upstream,
        policy=policy,
        only_eligible=True,
    )

    direct_identifiers = sum(
        count_direct_identifiers(record.scrubbed_observation_json)
        + count_direct_identifiers(record.scrubbed_factual_continuation)
        for record in scrubbed
    )
    by_domain = Counter(record.domain for record in scrubbed)
    report = {
        "stage": "02_scrub",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "config_hashes": config_hashes(),
        "policy": registry.get("path_policy", {}),
        "relevance": relevance_stats,
        "scrub": scrub_stats,
        "direct_identifiers_remaining": direct_identifiers,
        "by_domain": dict(sorted(by_domain.items())),
    }
    write_json(report_path, report)
    write_jsonl(scrubbed, output_path)

    print(f"[02_scrub] candidates {relevance_stats['candidates']}")
    print(f"[02_scrub] eligible {relevance_stats['eligible']}")
    print(f"[02_scrub] scrubbed {scrub_stats['scrubbed']}")
    print(f"[02_scrub] pii_tokens {scrub_stats['pii_tokens']}")
    print(f"[02_scrub] leaks {len(scrub_stats['leaks'])}")
    print(f"[02_scrub] direct_identifiers_remaining {direct_identifiers}")
    print(f"[02_scrub] by_domain {dict(sorted(by_domain.items()))}")
    print(f"[02_scrub] wrote {output_path}")
    print(f"[02_scrub] wrote {report_path}")

    if scrub_stats["leaks"] or direct_identifiers:
        print("[02_scrub] FAIL: scrubbed output still contains direct identifiers")
        return 1
    if len(scrubbed) < 880 or min(by_domain.get("airline", 0), by_domain.get("retail", 0)) < 440:
        print("[02_scrub] FAIL: eligible supply is below the G0 pre-replay floor")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
