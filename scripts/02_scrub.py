#!/usr/bin/env python
"""Stage 02 — PII scrub and profile-tool exclusion.

Input:  data/interim/candidates.parquet
Output: data/interim/scrubbed.parquet, artifacts/audit/scrub_report.json

Rules: exclude get_user_details/profile tools; replace names, emails, addresses,
phones, and payment identifiers with stable synthetic tokens; exclude a prefix if
the decision-relevant content is itself PII.

GATE: zero raw direct identifiers in the scan; excluded-tool count reported.

TODO: implement. This is a scaffold stub and intentionally performs no work.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--in", dest="input", default="data/interim/candidates.parquet")
    parser.add_argument("--out", default="data/interim/scrubbed.parquet")
    args = parser.parse_args(argv)
    print(f"[02_scrub] not implemented (in={args.input}, out={args.out})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
