#!/usr/bin/env python
"""Stage 01 — parse τ-bench trajectories into candidate post-tool decision points.

Input:  data/upstream/*.json (pinned)
Output: data/interim/candidates.parquet

Each candidate records trajectory ID, task ID, trial, donor, domain, step index,
tool name, raw observation, factual continuation, and the reconstructed prefix.

GATE: every candidate has all required fields.

TODO: implement. This is a scaffold stub and intentionally performs no work.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--upstream", default="data/upstream")
    parser.add_argument("--out", default="data/interim/candidates.parquet")
    args = parser.parse_args(argv)
    print(f"[01_parse] not implemented (upstream={args.upstream}, out={args.out})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
