#!/usr/bin/env python
"""Stage 09c — re-score an existing ledger with the current parser version.

The generation outputs are unchanged; only derived parser fields are recomputed.
Use this when a parser/signature change lands after a calibration run.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.infer.ledger import append_ledger_row, read_ledger  # noqa: E402
from toolobs.infer.rescore import rescore_rows  # noqa: E402
from toolobs.paths import resolve_repo_path  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    input_path = resolve_repo_path(args.input)
    output_path = resolve_repo_path(args.output)
    if output_path.exists() and not args.force:
        print(f"[09c_rescore] FAIL: output exists at {output_path}; pass --force")
        return 1
    # Materialize the input before touching the output so an in-place rescore
    # (input == output) is safe.
    rows = read_ledger(input_path)
    if output_path.exists():
        output_path.unlink()
    rescored = rescore_rows(rows)
    for row in rescored:
        append_ledger_row(output_path, row)

    statuses = Counter(row.parser_status for row in rescored)
    versions = Counter(row.parser_version for row in rescored)
    print(f"[09c_rescore] rows {len(rescored)}")
    print(f"[09c_rescore] statuses {dict(statuses)}")
    print(f"[09c_rescore] parser_versions {dict(versions)}")
    print(f"[09c_rescore] wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
