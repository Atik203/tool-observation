#!/usr/bin/env python
"""Stage 04 — replay verification against the τ-bench task database.

Input:  data/interim/eligible.parquet, data/upstream/ task databases
Output: data/interim/replay.parquet, artifacts/audit/replay_report.json

Load the task DB, execute the prefix's tool calls from the initial state, and
compare the last observation to the historical one (hash + normalized values).
Keep only >= 98% matches.

GATE: replay match >= 98% on retained prefixes.

TODO: implement. This is a scaffold stub and intentionally performs no work.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="input", default="data/interim/eligible.parquet")
    parser.add_argument("--out", default="data/interim/replay.parquet")
    parser.add_argument("--threshold", type=float, default=0.98)
    args = parser.parse_args(argv)
    print(f"[04_replay] not implemented (in={args.input}, threshold={args.threshold})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
