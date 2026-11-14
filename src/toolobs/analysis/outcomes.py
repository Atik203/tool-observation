"""Automatic outcome labels from ledger rows and perturbation records.

Y is any signature change from the verbatim V continuation. The decomposition
uses action switch, explicit flag, and silent propagation. Labels are primary;
the human audit validates them later.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from ..harvest.relevance import normalize_scalar, normalize_text
from ..schemas import LedgerRow, OutcomeLabels, PerturbationRecord

_FLAG = re.compile(
    r"\b(?:inconsistent|inconsistency|possible error|looks wrong|looks incorrect|"
    r"verify|re-?check|double[- ]check|cannot trust|can't trust|do not trust|"
    r"not sure|suspicious|contradict(?:s|ion)?)\b",
    re.IGNORECASE,
)


def flag_detected(text: str) -> bool:
    """Return whether a generation explicitly flags doubt or inconsistency."""
    return bool(_FLAG.search(text or ""))


def _decision_parts(decision_json: str) -> tuple[str, dict[str, Any]]:
    try:
        payload = json.loads(decision_json)
    except json.JSONDecodeError:
        return "", {}
    if not isinstance(payload, dict):
        return "", {}
    tool = payload.get("tool")
    arguments = payload.get("arguments")
    return (
        tool if isinstance(tool, str) else "",
        arguments if isinstance(arguments, dict) else {},
    )


def _contains(text: str, value: Any) -> bool:
    token = normalize_scalar(value)
    if token is None or len(token) < 2:
        return False
    return token in normalize_text(text)


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
        y_any = row.signature_hash != reference.signature_hash
        tool, arguments = _decision_parts(row.decision_json)
        ref_tool, ref_arguments = _decision_parts(reference.decision_json)
        y_action = (tool, arguments) != (ref_tool, ref_arguments)
        y_flag = flag_detected(row.output_text)
        perturbation = perturbation_by_key.get((row.prefix_id, row.arm))
        y_silent = False
        if (
            perturbation is not None
            and perturbation.severity >= 2
            and perturbation.false_value is not None
            and not y_action
            and not y_flag
        ):
            y_silent = _contains(row.output_text, perturbation.false_value) or _contains(
                row.decision_json, perturbation.false_value
            )
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
