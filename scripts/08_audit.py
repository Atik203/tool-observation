#!/usr/bin/env python
"""Stage 08 — human and automatic audits.

Input:  frozen sample, scrub report, replay report
Output: artifacts/audit/g0_audit.csv, severity/outcome/recovery label reports

G0: 40 random prefixes, >= 36/40 (90%) on eligibility, PII, relevance, replay.
Severity: 120 observations, 30/level, 3 blind raters, alpha >= .75.
Outcome: 160 responses, 2 blind raters, kappa >= .80 (downgrade threshold .70).
Recovery: 80 sequences, kappa >= .75.

GATE: the audit thresholds in configs/analysis.yaml.

TODO: implement. This is a scaffold stub and intentionally performs no work.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", default="data/manifests/cto800_v1.json")
    parser.add_argument("--out", default="artifacts/audit/g0_audit.csv")
    args = parser.parse_args(argv)
    print(f"[08_audit] not implemented (manifest={args.manifest})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
