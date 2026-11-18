"""Automatic outcome labels from ledger rows and perturbation records.

Y is a decision-level signature change from the verbatim V continuation:
a tool/verb switch, a contradictory status claim, or a contradictory
decision-critical value (money/date/time/identifier). The decomposition is
action switch (YA), explicit flag (YF), and silent propagation (YU).

YU requires the decision to change AND the injected false value to be
attributed to the model's decision (present in the model's signature values and
absent from the reference's), with no action switch and no flag. This matches
the preregistration and the G3 blind-audit findings.
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from ..infer.parse_output import action_switch, signature_from_json, signatures_differ
from ..schemas import DecisionSignature, LedgerRow, OutcomeLabels, PerturbationRecord

_FLAG = re.compile(
    r"\b(?:inconsistenc(?:y|ies)|discrepanc(?:y|ies)|possible error|looks wrong|looks incorrect|"
    r"verify|re-?check|double[- ]check|cannot trust|can't trust|do not trust|"
    r"not sure|suspicious|unusual|contradict(?:s|ion)?|"
    r"(?:don'?t|do not|doesn'?t|does not) see any)\b",
    re.IGNORECASE,
)


def flag_detected(text: str) -> bool:
    """Return whether a generation explicitly flags doubt or inconsistency."""
    return bool(_FLAG.search(text or ""))


def _normalize_scalar(value: Any) -> tuple[str, Any] | None:
    if isinstance(value, bool):
        return ("bool", str(value).lower())
    if isinstance(value, (int, float, Decimal)):
        return ("num", Decimal(str(value)))
    if isinstance(value, str):
        text = unicodedata.normalize("NFKC", value).strip().casefold()
        return ("str", text) if text else None
    return None


def _flatten_scalars(value: Any, out: set[tuple[str, Any]]) -> None:
    if isinstance(value, dict):
        for child in value.values():
            _flatten_scalars(child, out)
    elif isinstance(value, list):
        for child in value:
            _flatten_scalars(child, out)
    else:
        token = _normalize_scalar(value)
        if token is not None:
            out.add(token)


def _decision_tokens(signature: DecisionSignature) -> set[tuple[str, Any]]:
    """Typed values that the decision asserts (no prose)."""
    tokens: set[tuple[str, Any]] = set()
    if signature.tool_name:
        _flatten_scalars(signature.arguments, tokens)
        return tokens
    slots = signature.final_answer_slots or {}
    for status in slots.get("status", []):
        tokens.add(("str", status))
    values = slots.get("values", {}) or {}
    for money in values.get("money", []):
        tokens.add(("num", Decimal(money)))
    for kind in ("dates", "times", "ids"):
        for item in values.get(kind, []):
            tokens.add(("str", item))
    return tokens


def _attributed(signature: DecisionSignature, false_value: Any) -> bool:
    """Whether the false value is asserted by this decision."""
    token = _normalize_scalar(false_value)
    if token is None:
        return False
    return token in _decision_tokens(signature)


def compute_outcomes(
    rows: Iterable[LedgerRow],
    perturbations: Iterable[PerturbationRecord],
) -> list[OutcomeLabels]:
    """Compute automatic labels for every non-V arm with a parsed V reference."""
    materialized = list(rows)
    by_key: dict[tuple[str, str, str], LedgerRow] = {}
    for row in materialized:
        by_key[(row.prefix_id, row.model_id, row.arm)] = row
    perturbation_by_key = {
        (item.prefix_id, item.arm): item for item in perturbations
    }

    labels: list[OutcomeLabels] = []
    for row in materialized:
        if row.arm == "V":
            continue
        reference = by_key.get((row.prefix_id, row.model_id, "V"))
        if reference is None or not reference.parsed or not row.parsed:
            continue
        if not reference.decision_json or not row.decision_json:
            continue
        ref_signature = signature_from_json(reference.decision_json)
        cur_signature = signature_from_json(row.decision_json)
        y_flag = flag_detected(row.output_text)
        # A flag is itself a decision-relevant deviation (the prereg's 4-way
        # Y/YA/YF/YU taxonomy and the G3 audit rubric both treat YF as Y=1).
        y_any = signatures_differ(ref_signature, cur_signature) or y_flag
        y_action = action_switch(ref_signature, cur_signature)
        perturbation = perturbation_by_key.get((row.prefix_id, row.arm))
        y_silent = False
        if (
            y_any
            and perturbation is not None
            and perturbation.severity >= 2
            and perturbation.false_value is not None
            and not y_action
            and not y_flag
        ):
            y_silent = _attributed(
                cur_signature, perturbation.false_value
            ) and not _attributed(ref_signature, perturbation.false_value)
        labels.append(
            OutcomeLabels(
                prefix_id=row.prefix_id,
                model_id=row.model_id,
                arm=row.arm,
                y_any=y_any,
                y_silent=y_silent,
                y_flag=y_flag,
                y_action=y_action,
                signature_hash=row.signature_hash,
                parser_status=row.parser_status,
            )
        )
    return sorted(labels, key=lambda item: (item.prefix_id, item.model_id, item.arm))


def outcome_counts(labels: Iterable[OutcomeLabels]) -> dict[str, dict[str, int]]:
    """Aggregate outcome counts by model and arm."""
    grouped: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"n": 0, "any": 0, "silent": 0, "flag": 0, "action": 0}
    )
    for label in labels:
        bucket = grouped[(label.model_id, label.arm)]
        bucket["n"] += 1
        bucket["any"] += int(label.y_any)
        bucket["silent"] += int(label.y_silent)
        bucket["flag"] += int(label.y_flag)
        bucket["action"] += int(label.y_action)
    return {
        f"{model}|{arm}": dict(sorted(values.items()))
        for (model, arm), values in sorted(grouped.items())
    }
