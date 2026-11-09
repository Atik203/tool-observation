#!/usr/bin/env python
"""Stage 03 — decision-relevance labeling (value-used proxy).

Input:  data/interim/scrubbed.parquet
Output: data/interim/eligible.parquet

Flatten scalar values in the observation and check which appear in the donor's
factual continuation after normalization. Keep prefixes with at least one used
field. This is the automatic criticality label that makes s=1/s=2 constructible.

GATE: >= 6,500 eligible overall; >= 1,500 airline; no prefix with zero used field.

TODO: implement. This is a scaffold stub and intentionally performs no work.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="input", default="data/interim/scrubbed.parquet")
    parser.add_argument("--out", default="data/interim/eligible.parquet")
    args = parser.parse_args(argv)
    print(f"[03_relevance] not implemented (in={args.input}, out={args.out})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
