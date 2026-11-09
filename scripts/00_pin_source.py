#!/usr/bin/env python
"""Stage 00 — pin the upstream τ-bench source.

Input:  configs/harvest.yaml (source.repository, source.pin)
Output: data/upstream/PIN.json, file hashes, retained MIT notice

GATE: pin resolves and all four trajectory files hash-match.

TODO: implement. This is a scaffold stub and intentionally performs no work.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="configs/harvest.yaml")
    args = parser.parse_args(argv)
    print(f"[00_pin_source] not implemented (config={args.config})")
    print("Planned: resolve commit, download four trajectory files, record SHA-256, keep MIT notice.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
