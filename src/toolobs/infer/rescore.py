"""Re-parse ledger rows with the current parser without regenerating outputs.

Used when the parser's signature semantics change after a calibration run: the
stored ``output_text`` is unchanged, while ``parsed``, ``parser_status``,
``signature_hash``, ``decision_json``, and ``parser_version`` are recomputed.
"""

from __future__ import annotations

from collections.abc import Iterable

from ..schemas import LedgerRow
from .parse_output import parse_decision, signature_hash, signature_json
from .runner import PARSER_VERSION


def rescore_rows(rows: Iterable[LedgerRow]) -> list[LedgerRow]:
    """Return rows with derived parser fields recomputed by the current parser."""
    rescored: list[LedgerRow] = []
    for row in rows:
        parsed = parse_decision(row.output_text)
        row.parsed = parsed.parsed
        row.parser_status = parsed.status
        row.signature_hash = signature_hash(parsed) if parsed.parsed else ""
        row.decision_json = signature_json(parsed) if parsed.parsed else ""
        row.parser_version = PARSER_VERSION
        rescored.append(row)
    return rescored
