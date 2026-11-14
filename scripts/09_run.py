#!/usr/bin/env python
"""Stage 09 — calibration and main inference run.

Input:  frozen manifest, perturbations, configs/calibration.yaml or main.yaml
Output: data/runs/{calibration,main}/ledger.jsonl and raw traces

G1: 60 prefixes x 5 arms x 3 models; parse >= 95%, placebo jitter <= 20%,
    s=3 switch 10-80%, refusal < 5%.
P2: 34,800-generation envelope; stop at 45 GPU-hours or 200 GB storage.

Every generation writes one ledger row. No result may be reported without a row.

TODO: implement. This is a scaffold stub and intentionally performs no work.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stage", choices=["calibration", "main"], default="calibration")
    parser.add_argument("--config", default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args(argv)
    config = args.config or f"configs/{args.stage}.yaml"
    print(f"[09_run] not implemented (stage={args.stage}, config={config}, resume={args.resume})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
