"""Replay stored recovery sequences into events with the current parser.

The recovery runner (stage 09b) writes one summary event per sequence
(``recovered_step``, ``endpoint``, ``censored``) under the parser that produced
it. After a parser/signature change (stage 09c rescore), the per-step decision
signatures change, so the event coding must be replayed from the stored rows:
R1 is a signature match with the verbatim V continuation, R2 an explicit flag,
censored means no recovery within the horizon. The sequence-level ``state_hash``
is preserved from the original event because the generations did not change.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from ..infer.parse_output import signature_from_json
from .outcomes import flag_detected
from ..schemas import LedgerRow, RecoveryEvent


def replay_recovery_events(
    rows: Iterable[LedgerRow],
    reference_hashes: dict[str, str],
    *,
    model_id: str,
    regime: str,
    state_hashes: dict[tuple[str, int], str] | None = None,
    horizon: int = 4,
) -> list[RecoveryEvent]:
    """Recompute recovery events from per-step ledger rows."""
    grouped: dict[tuple[str, str], list[LedgerRow]] = defaultdict(list)
    for row in rows:
        grouped[(row.prefix_id, row.arm)].append(row)

    events: list[RecoveryEvent] = []
    for (prefix_id, arm), steps in sorted(grouped.items()):
        steps.sort(key=lambda row: row.step)
        reference_hash = reference_hashes.get(prefix_id, "")
        recovered_step: int | None = None
        endpoint = "censored"
        for row in steps:
            if not row.parsed:
                break
            if flag_detected(row.output_text):
                recovered_step, endpoint = row.step, "R2"
                break
            if reference_hash and row.signature_hash == reference_hash:
                recovered_step, endpoint = row.step, "R1"
                break
            if not signature_from_json(row.decision_json).tool_name:
                break  # final answer without recovery
        severity = int(arm[-1])
        events.append(
            RecoveryEvent(
                prefix_id=prefix_id,
                model_id=model_id,
                regime=regime,
                severity=severity,
                horizon=horizon,
                recovered_step=recovered_step,
                endpoint=endpoint,
                censored=recovered_step is None,
                state_hash=(state_hashes or {}).get((prefix_id, severity), ""),
            )
        )
    return events
