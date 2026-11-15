#!/usr/bin/env python
"""Stage 08b — G3/G4 audit packets and AI pre-audit fills.

Generates the severity audit (120 items, 3 raters), the outcome audit (160 items,
2 raters) and, once recovery data exists, the recovery audit (80 sequences, 2
raters). The AI pre-audit fills every sheet with the mechanical reference label
and records ``label_source=ai_preaudit_deferred_human``; the authors verify after
the experiments finish (D-027).
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.analysis.outcomes import compute_outcomes  # noqa: E402
from toolobs.harvest.parse import read_jsonl_dicts  # noqa: E402
from toolobs.infer.ledger import read_ledger  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, MANIFEST_DIR, RUNS_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402
from toolobs.schemas import LedgerRow, PerturbationRecord  # noqa: E402

SEVERITY_RATERS = 3
OUTCOME_RATERS = 2
SEED = 20261108


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})


# ---------------------------------------------------------------------------
# Severity audit
# ---------------------------------------------------------------------------

SEVERITY_PACKET_COLUMNS = (
    "item_id",
    "domain",
    "severity_level",
    "json_path",
    "true_value",
    "false_value",
    "criticality",
    "criticality_2",
    "expected_action_change",
    "plausibility_checks",
    "prefix_id",
)

SEVERITY_SHEET_COLUMNS = (
    "item_id",
    "severity_level",
    "rater1_severity",
    "rater1_decision_changing",
    "rater1_absurd",
    "rater2_severity",
    "rater2_decision_changing",
    "rater2_absurd",
    "rater3_severity",
    "rater3_decision_changing",
    "rater3_absurd",
    "notes",
)


def build_severity_packet(perturbations: list[dict], n_per_level: int = 40) -> list[dict]:
    """Select n_per_level items per severity level from the perturbation records."""
    by_level: dict[int, list[dict]] = {1: [], 2: [], 3: []}
    for record in perturbations:
        level = int(record.get("severity", 0))
        if level in by_level:
            by_level[level].append(record)

    selected: list[dict] = []
    for level in (1, 2, 3):
        pool = sorted(by_level[level], key=lambda item: item["record_id"])
        random.Random(f"{SEED}|severity|{level}").shuffle(pool)
        for record in pool[:n_per_level]:
            selected.append(
                {
                    "item_id": None,  # filled below
                    "domain": record["prefix_id"].split("-")[0],
                    "severity_level": level,
                    "json_path": record["json_path"],
                    "true_value": json.dumps(record.get("true_value"), ensure_ascii=False),
                    "false_value": json.dumps(record.get("false_value"), ensure_ascii=False),
                    "criticality": record.get("criticality", ""),
                    "criticality_2": record.get("criticality_2", ""),
                    "expected_action_change": str(record.get("expected_action_change", "")),
                    "plausibility_checks": json.dumps(
                        record.get("plausibility_checks", []), ensure_ascii=False
                    ),
                    "prefix_id": record["prefix_id"],
                }
            )
    # Add s=0 placebo items: true == false (no change), n_per_level items.
    s0_pool = sorted(
        {record["prefix_id"] for record in perturbations}, key=lambda item: item
    )
    random.Random(f"{SEED}|severity|0").shuffle(s0_pool)
    for prefix_id in s0_pool[:n_per_level]:
        selected.append(
            {
                "item_id": None,
                "domain": prefix_id.split("-")[0],
                "severity_level": 0,
                "json_path": "$.created_at",
                "true_value": '"2024-05-15T15:00:00"',
                "false_value": '"2024-05-15T15:00:00"',
                "criticality": "noncritical",
                "criticality_2": "",
                "expected_action_change": "False",
                "plausibility_checks": "[]",
                "prefix_id": prefix_id,
            }
        )

    # Trim to n_per_level per level.
    by_level_out: dict[int, list[dict]] = {0: [], 1: [], 2: [], 3: []}
    for item in selected:
        by_level_out[item["severity_level"]].append(item)
    final: list[dict] = []
    for level in (0, 1, 2, 3):
        final.extend(by_level_out[level][:n_per_level])
    for index, item in enumerate(final, start=1):
        item["item_id"] = f"SEV-{index:03d}"
    return final


def _ai_severity_fill(item: dict) -> dict[str, str]:
    level = int(item["severity_level"])
    decision_changing = "1" if level >= 2 else "0"
    absurd = "0"
    return {
        "rater1_severity": str(level),
        "rater1_decision_changing": decision_changing,
        "rater1_absurd": absurd,
        "rater2_severity": str(level),
        "rater2_decision_changing": decision_changing,
        "rater2_absurd": absurd,
        "rater3_severity": str(level),
        "rater3_decision_changing": decision_changing,
        "rater3_absurd": absurd,
    }


# ---------------------------------------------------------------------------
# Outcome audit
# ---------------------------------------------------------------------------


def build_outcome_packet(
    ledgers: dict[str, list[LedgerRow]],
    perturbations: list[PerturbationRecord],
    n_items: int = 160,
) -> tuple[list[dict], list]:
    """Select n_items (prefix, model, arm) rows balanced across models and arms."""
    all_rows: list[LedgerRow] = []
    for _model_id, rows in ledgers.items():
        for row in rows:
            if row.arm != "V" and row.parsed:
                all_rows.append(row)

    # Balance across models and arms.
    by_cell: dict[tuple[str, str], list[LedgerRow]] = {}
    for row in all_rows:
        by_cell.setdefault((row.model_id, row.arm), []).append(row)

    selected: list[LedgerRow] = []
    per_cell = n_items // (len(ledgers) * 4) if ledgers else 0
    for model_id in sorted(ledgers):
        for arm in ("s0", "s1", "s2", "s3"):
            pool = sorted(
                by_cell.get((model_id, arm), []), key=lambda row: row.prefix_id
            )
            random.Random(f"{SEED}|outcome|{model_id}|{arm}").shuffle(pool)
            selected.extend(pool[:per_cell])

    # Top up if rounding left items.
    if len(selected) < n_items:
        remaining = [row for row in all_rows if row not in selected]
        random.Random(f"{SEED}|outcome|topup").shuffle(remaining)
        selected.extend(remaining[: n_items - len(selected)])

    # Compute automatic labels for the selected rows (need V reference).
    v_index: dict[tuple[str, str], LedgerRow] = {}
    for model_id, rows in ledgers.items():
        for row in rows:
            if row.arm == "V":
                v_index[(row.prefix_id, model_id)] = row

    for row in selected:
        ref = v_index.get((row.prefix_id, row.model_id))
        if ref is None or not ref.parsed:
            continue
    # Use compute_outcomes on the full ledger set for labels.

    all_ledger_rows: list[LedgerRow] = []
    for rows in ledgers.values():
        all_ledger_rows.extend(rows)
    labels = compute_outcomes(all_ledger_rows, perturbations)
    label_index = {(lab.prefix_id, lab.model_id, lab.arm): lab for lab in labels}

    packet: list[dict] = []
    for index, row in enumerate(selected[:n_items], start=1):
        ref = v_index.get((row.prefix_id, row.model_id))
        lab = label_index.get((row.prefix_id, row.model_id, row.arm))
        packet.append(
            {
                "item_id": f"OUT-{index:03d}",
                "prefix_id": row.prefix_id,
                "model_id": row.model_id,
                "arm": row.arm,
                "prefix_domain": row.prefix_id.split("-")[0],
                "reference_output": (ref.output_text if ref else "")[:1500],
                "model_output": row.output_text[:1500],
                "automatic_Y": int(lab.y_any) if lab else "",
                "automatic_YA": int(lab.y_action) if lab else "",
                "automatic_YF": int(lab.y_flag) if lab else "",
                "automatic_YU": int(lab.y_silent) if lab else "",
            }
        )
    return packet, labels


OUTCOME_SHEET_COLUMNS = (
    "item_id",
    "rater1_Y",
    "rater1_YA",
    "rater1_YF",
    "rater1_YU",
    "rater2_Y",
    "rater2_YA",
    "rater2_YF",
    "rater2_YU",
    "notes",
)

OUTCOME_PACKET_COLUMNS = (
    "item_id",
    "prefix_id",
    "model_id",
    "arm",
    "prefix_domain",
    "reference_output",
    "model_output",
    "automatic_Y",
    "automatic_YA",
    "automatic_YF",
    "automatic_YU",
)


def _ai_outcome_fill(item: dict) -> dict[str, str]:
    y = str(item.get("automatic_Y", "0"))
    ya = str(item.get("automatic_YA", "0"))
    yf = str(item.get("automatic_YF", "0"))
    yu = str(item.get("automatic_YU", "0"))
    return {
        "rater1_Y": y,
        "rater1_YA": ya,
        "rater1_YF": yf,
        "rater1_YU": yu,
        "rater2_Y": y,
        "rater2_YA": ya,
        "rater2_YF": yf,
        "rater2_YU": yu,
    }


def build_recovery_packet(n_items: int = 80) -> list[dict]:
    """Placeholder: recovery audit needs completed recovery events."""
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--perturbations", default=str(MANIFEST_DIR / "perturbations.jsonl"))
    parser.add_argument("--ledger-root", default=str(RUNS_DIR / "main"))
    parser.add_argument("--audit-dir", default=str(ARTIFACTS_DIR / "audit"))
    parser.add_argument("--severity-items", type=int, default=120)
    parser.add_argument("--outcome-items", type=int, default=160)
    args = parser.parse_args(argv)

    audit_dir = resolve_repo_path(args.audit_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)

    # --- Severity audit ---
    perturbation_dicts = read_jsonl_dicts(resolve_repo_path(args.perturbations))
    perturbation_records = [PerturbationRecord.from_dict(item) for item in perturbation_dicts]
    perturbations = perturbation_dicts
    n_per_level = args.severity_items // 4
    severity_packet = build_severity_packet(perturbations, n_per_level=n_per_level)
    _write_csv(
        audit_dir / "severity_audit_packet.csv",
        SEVERITY_PACKET_COLUMNS,
        severity_packet,
    )
    severity_sheet_rows = []
    for item in severity_packet:
        row = {"item_id": item["item_id"], "severity_level": item["severity_level"]}
        row.update(_ai_severity_fill(item))
        row["notes"] = "ai_preaudit_deferred_human"
        severity_sheet_rows.append(row)
    _write_csv(
        audit_dir / "severity_audit_sheet.csv",
        SEVERITY_SHEET_COLUMNS,
        severity_sheet_rows,
    )

    # --- Outcome audit (only if ledgers exist) ---
    ledger_root = resolve_repo_path(args.ledger_root)
    ledgers: dict[str, list[LedgerRow]] = {}
    for model_dir in sorted(ledger_root.iterdir()) if ledger_root.exists() else []:
        ledger_path = model_dir / "ledger.jsonl"
        if ledger_path.exists():
            rows = [row for row in read_ledger(ledger_path) if row.step == 0]
            if rows:
                ledgers[model_dir.name] = rows

    if ledgers:
        outcome_packet, _ = build_outcome_packet(
            ledgers, perturbation_records, n_items=args.outcome_items
        )
        _write_csv(
            audit_dir / "outcome_audit_packet.csv",
            OUTCOME_PACKET_COLUMNS,
            outcome_packet,
        )
        outcome_sheet_rows = []
        for item in outcome_packet:
            row = {"item_id": item["item_id"]}
            row.update(_ai_outcome_fill(item))
            row["notes"] = "ai_preaudit_deferred_human"
            outcome_sheet_rows.append(row)
        _write_csv(
            audit_dir / "outcome_audit_sheet.csv",
            OUTCOME_SHEET_COLUMNS,
            outcome_sheet_rows,
        )

    write_json(
        audit_dir / "audit_packets_result.json",
        {
            "stage": "08b_audit_packets",
            "recorded_utc": utc_now(),
            "git_commit": git_commit(),
            "severity_items": len(severity_packet),
            "outcome_items": len(outcome_packet) if ledgers else 0,
            "models_with_ledgers": sorted(ledgers),
            "label_source": "ai_preaudit_deferred_human",
        },
    )
    print(f"[08b] severity items {len(severity_packet)}")
    if ledgers:
        print(f"[08b] outcome items {len(outcome_packet)} across {len(ledgers)} models")
    print(f"[08b] wrote packets to {audit_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
