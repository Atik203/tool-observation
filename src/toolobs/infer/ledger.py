"""Append-only generation ledger.

Every reported number must trace to a ledger row. Rows are written one JSON
object per line and never rewritten by the runner.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..hashing import canonical_json
from ..schemas import LedgerRow


def append_ledger_row(path: str | Path, row: LedgerRow) -> None:
    """Append one ledger row, creating the parent directory."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(canonical_json(row.to_dict()) + "\n")


def read_ledger(path: str | Path) -> list[LedgerRow]:
    """Read a ledger file."""
    rows: list[LedgerRow] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(LedgerRow.from_dict(json.loads(line)))
    return rows
