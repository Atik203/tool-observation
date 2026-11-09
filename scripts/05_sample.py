#!/usr/bin/env python
"""Stage 05 — stratified sample of 880 prefixes (800 primary + 80 reserve).

Input:  data/interim/replay.parquet
Output: data/manifests/sample_880.json

Cap at 10 per task-domain; target 400 airline + 400 retail; stratify by domain,
donor, step-index bucket, and tool family; seed 20261108.

GATE: 400/400 domain target met; donor and step strata reported.

TODO: implement. This is a scaffold stub and intentionally performs no work.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="input", default="data/interim/replay.parquet")
    parser.add_argument("--out", default="data/manifests/sample_880.json")
    parser.add_argument("--seed", type=int, default=20261108)
    args = parser.parse_args(argv)
    print(f"[05_sample] not implemented (in={args.input}, seed={args.seed})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
