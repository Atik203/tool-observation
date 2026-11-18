#!/usr/bin/env python
"""Stage 08c — merge blind-rater audit sheets and score the preregistered gates.

Reads the packets (evidence) and the per-rater answer files in
``artifacts/audit/blind/``, writes the merged sheets in ``artifacts/audit/``,
and scores the G3/G4 audit gates into ``artifacts/audit/blind_audit_result.json``:

  Severity (120 items, 3 raters): Jonckheere-Terpstra p < .01, Krippendorff
  alpha >= .75, >=90% of s=1 non-decision-changing, >=90% of s=2/s=3
  decision-changing, s=3 absurd <= 20%.

  Outcome (160 items, 2 raters): 4-way Cohen's kappa >= .80, silent-propagation
  PPV >= .90, 10% seed-repeat stability >= .90 (read from
  artifacts/analysis/jitter_stability_*.json).

  Recovery (80 items, 2 raters): Cohen's kappa >= .75 on step and endpoint.

The raters are blind: they see only ``artifacts/audit/blind/*_items.jsonl``.
The sheets are answers, not evidence; the packets are never modified here.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.analysis.audit import (  # noqa: E402
    cohen_kappa,
    consensus_severity,
    fourway,
    jt_test,
    kripp_alpha,
    majority,
)
from toolobs.paths import ARTIFACTS_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402

SEVERITY_SHEET_COLUMNS = (
    "item_id", "severity_level",
    "rater1_severity", "rater1_decision_changing", "rater1_absurd",
    "rater2_severity", "rater2_decision_changing", "rater2_absurd",
    "rater3_severity", "rater3_decision_changing", "rater3_absurd",
    "notes",
)
OUTCOME_SHEET_COLUMNS = (
    "item_id",
    "rater1_Y", "rater1_YA", "rater1_YF", "rater1_YU",
    "rater2_Y", "rater2_YA", "rater2_YF", "rater2_YU",
    "notes",
)
RECOVERY_SHEET_COLUMNS = (
    "item_id", "rater1_recovery_step", "rater1_endpoint",
    "rater2_recovery_step", "rater2_endpoint", "notes",
)

NOTE_BASE = {
    3: ("blind_rater_1", "blind_rater_2", "blind_rater_3"),
    2: ("blind_rater_1", "blind_rater_2"),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _validate(path: Path, expected_ids: list[str], field: str, vocab: set[str]) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"missing rater file: {path}")
    rows = _read_rows(path)
    if len(rows) != len(expected_ids):
        raise SystemExit(f"{path.name}: {len(rows)} rows, expected {len(expected_ids)}")
    if [r["item_id"] for r in rows] != expected_ids:
        raise SystemExit(f"{path.name}: item order differs from the packet")
    for row in rows:
        value = str(row.get(field, "")).strip()
        if value not in vocab:
            raise SystemExit(f"{path.name} {row['item_id']}: {field}={value!r} not allowed")
        row[field] = value
    return rows


def _notes(rater_count: int, flags: list[str], rater_notes: list[tuple[str, str]]) -> str:
    parts = list(NOTE_BASE[rater_count])
    parts.extend(flags)
    for name, note in rater_notes:
        note = (note or "").strip()
        if note:
            parts.append(f"{name}:{note[:60]}")
    return ";".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--audit-dir", default=str(ARTIFACTS_DIR / "audit"))
    parser.add_argument("--blind-dir", default=str(ARTIFACTS_DIR / "audit" / "blind"))
    parser.add_argument("--jitter-dir", default=str(ARTIFACTS_DIR / "analysis"))
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    audit_dir = resolve_repo_path(args.audit_dir)
    blind_dir = resolve_repo_path(args.blind_dir)
    out_path = resolve_repo_path(args.out) if args.out else audit_dir / "blind_audit_result.json"

    severity_items = _read_jsonl(blind_dir / "severity_items.jsonl")
    outcome_items = _read_jsonl(blind_dir / "outcome_items.jsonl")
    recovery_items = _read_jsonl(blind_dir / "recovery_items.jsonl")
    severity_ids = [item["item_id"] for item in severity_items]
    outcome_ids = [item["item_id"] for item in outcome_items]
    recovery_ids = [item["item_id"] for item in recovery_items]

    severity_raters = {}
    for number in (1, 2, 3):
        rows = _validate(
            blind_dir / f"rater{number}_severity.csv", severity_ids, "severity", {"0", "1", "2", "3"}
        )
        for row in rows:
            for field in ("decision_changing", "absurd"):
                if str(row[field]).strip() not in {"0", "1"}:
                    raise SystemExit(f"rater{number}_severity {row['item_id']}: {field} invalid")
                row[field] = str(row[field]).strip()
        severity_raters[number] = {row["item_id"]: row for row in rows}

    outcome_raters = {}
    for number in (1, 2):
        rows = _validate(blind_dir / f"rater{number}_outcome.csv", outcome_ids, "Y", {"0", "1"})
        for row in rows:
            for field in ("YA", "YF", "YU"):
                if str(row[field]).strip() not in {"0", "1"}:
                    raise SystemExit(f"rater{number}_outcome {row['item_id']}: {field} invalid")
                row[field] = str(row[field]).strip()
            row["Y"] = str(row["Y"]).strip()
        outcome_raters[number] = {row["item_id"]: row for row in rows}

    recovery_raters = {}
    for number in (1, 2):
        rows = _validate(
            blind_dir / f"rater{number}_recovery.csv",
            recovery_ids,
            "recovery_step",
            {"1", "2", "3", "4"},
        )
        for row in rows:
            endpoint = str(row["endpoint"]).strip()
            if endpoint not in {"R1", "R2", "censored"}:
                raise SystemExit(f"rater{number}_recovery {row['item_id']}: endpoint invalid")
            row["endpoint"] = endpoint
        recovery_raters[number] = {row["item_id"]: row for row in rows}

    # ---------------------------------------------------------------- severity
    severity_rows = []
    disagreements = overrides = 0
    for packet in severity_items:
        item_id = packet["item_id"]
        level = int(packet["severity_level"])
        raters = {number: severity_raters[number][item_id] for number in (1, 2, 3)}
        fields = ("severity", "decision_changing", "absurd")
        disagree = any(len({raters[n][f] for n in (1, 2, 3)}) > 1 for f in fields)
        majority_severity = consensus_severity([int(raters[n]["severity"]) for n in (1, 2, 3)])
        majority_decision = majority([int(raters[n]["decision_changing"]) for n in (1, 2, 3)])
        reference_decision = 1 if level >= 2 else 0
        override = majority_severity != level or majority_decision != reference_decision
        disagreements += int(disagree)
        overrides += int(override)
        flags = []
        if disagree:
            flags.append("rater_disagree")
        if override:
            flags.append("ref_override")
        severity_rows.append(
            {
                "item_id": item_id,
                "severity_level": packet["severity_level"],
                **{
                    f"rater{n}_{field}": raters[n][field]
                    for n in (1, 2, 3)
                    for field in ("severity", "decision_changing", "absurd")
                },
                "notes": _notes(
                    3,
                    flags,
                    [(f"rater{n}", raters[n].get("note", "")) for n in (1, 2, 3)],
                ),
            }
        )

    levels = (0, 1, 2, 3)
    by_level_majority = {level: [] for level in levels}
    by_level_rater = {number: {level: [] for level in levels} for number in (1, 2, 3)}
    for packet in severity_items:
        item_id = packet["item_id"]
        level = int(packet["severity_level"])
        by_level_majority[level].append(
            consensus_severity([int(severity_raters[n][item_id]["severity"]) for n in (1, 2, 3)])
        )
        for number in (1, 2, 3):
            by_level_rater[number][level].append(int(severity_raters[number][item_id]["severity"]))

    jt_majority = jt_test([by_level_majority[level] for level in levels])
    jt_raters = {
        f"blind_rater_{number}": jt_test([by_level_rater[number][level] for level in levels])
        for number in (1, 2, 3)
    }

    severity_matrix = [
        [int(severity_raters[n][item_id]["severity"]) for n in (1, 2, 3)]
        for item_id in severity_ids
    ]
    decision_matrix = [
        [int(severity_raters[n][item_id]["decision_changing"]) for n in (1, 2, 3)]
        for item_id in severity_ids
    ]
    absurd_matrix = [
        [int(severity_raters[n][item_id]["absurd"]) for n in (1, 2, 3)]
        for item_id in severity_ids
    ]
    alpha_severity_nominal = kripp_alpha(severity_matrix, "nominal")
    alpha_severity_interval = kripp_alpha(severity_matrix, "interval")
    alpha_decision = kripp_alpha(decision_matrix, "nominal")
    alpha_absurd = kripp_alpha(absurd_matrix, "nominal")

    level1 = [p for p in severity_items if p["severity_level"] == "1"]
    level23 = [p for p in severity_items if p["severity_level"] in ("2", "3")]
    level3 = [p for p in severity_items if p["severity_level"] == "3"]

    def majority_decision(item_id: str) -> int:
        return majority([int(severity_raters[n][item_id]["decision_changing"]) for n in (1, 2, 3)])

    def majority_absurd(item_id: str) -> int:
        return majority([int(severity_raters[n][item_id]["absurd"]) for n in (1, 2, 3)])

    rate_s1 = sum(1 for p in level1 if majority_decision(p["item_id"]) == 0) / len(level1)
    rate_s23 = sum(1 for p in level23 if majority_decision(p["item_id"]) == 1) / len(level23)
    rate_s3_absurd = sum(1 for p in level3 if majority_absurd(p["item_id"]) == 1) / len(level3)

    severity_gates = [
        {
            "criterion": "Jonckheere-Terpstra p < .01 (monotone severity, majority rating; permutation p, 20k perms)",
            "observed": round(jt_majority["p_permutation_one_sided"], 8),
            "pass": jt_majority["p_permutation_one_sided"] < 0.01,
        },
        {
            "criterion": "Krippendorff alpha >= .75 (severity, 3 raters, nominal / interval)",
            "observed": {
                "nominal": round(alpha_severity_nominal, 4),
                "interval": round(alpha_severity_interval, 4),
            },
            "pass": alpha_severity_nominal >= 0.75,
        },
        {
            "criterion": ">= 90% of s=1 items rated non-decision-changing (majority)",
            "observed": round(rate_s1, 4),
            "pass": rate_s1 >= 0.90,
        },
        {
            "criterion": ">= 90% of s=2/s=3 items rated decision-changing (majority)",
            "observed": round(rate_s23, 4),
            "pass": rate_s23 >= 0.90,
        },
        {
            "criterion": "s=3 absurd rate <= 20% (majority)",
            "observed": round(rate_s3_absurd, 4),
            "pass": rate_s3_absurd <= 0.20,
        },
    ]

    # ---------------------------------------------------------------- outcome
    outcome_rows = []
    outcome_disagreements = 0
    for packet in outcome_items:
        item_id = packet["item_id"]
        first = outcome_raters[1][item_id]
        second = outcome_raters[2][item_id]
        label_first = fourway(first)
        label_second = fourway(second)
        disagree = label_first != label_second
        outcome_disagreements += int(disagree)
        automatic_label = (
            "blank"
            if packet["automatic_Y"] == ""
            else (
                "YA"
                if packet["automatic_YA"] == "1"
                else "YF"
                if packet["automatic_YF"] == "1"
                else "YU"
                if packet["automatic_YU"] == "1"
                else "N"
            )
        )
        flags = []
        if disagree:
            flags.append("rater_disagree")
        if not disagree and label_first != automatic_label:
            flags.append(f"ref_override:auto={automatic_label}")
        outcome_rows.append(
            {
                "item_id": item_id,
                **{f"rater1_{field}": first[field] for field in ("Y", "YA", "YF", "YU")},
                **{f"rater2_{field}": second[field] for field in ("Y", "YA", "YF", "YU")},
                "notes": _notes(
                    2,
                    flags,
                    [("rater1", first.get("note", "")), ("rater2", second.get("note", ""))],
                ),
            }
        )

    labels_first = [fourway(outcome_raters[1][item_id]) for item_id in outcome_ids]
    labels_second = [fourway(outcome_raters[2][item_id]) for item_id in outcome_ids]
    kappa_outcome, kappa_detail = cohen_kappa(labels_first, labels_second)

    automatic_yu = [p for p in outcome_items if p["automatic_YU"] == "1"]
    strict_ppv = lenient_ppv = None
    unconfirmed = []
    if automatic_yu:
        confirmed_strict = sum(
            1
            for p in automatic_yu
            if fourway(outcome_raters[1][p["item_id"]]) == "YU"
            and fourway(outcome_raters[2][p["item_id"]]) == "YU"
        )
        confirmed_lenient = sum(
            1
            for p in automatic_yu
            if fourway(outcome_raters[1][p["item_id"]]) == "YU"
            or fourway(outcome_raters[2][p["item_id"]]) == "YU"
        )
        strict_ppv = confirmed_strict / len(automatic_yu)
        lenient_ppv = confirmed_lenient / len(automatic_yu)
        unconfirmed = [
            {
                "item_id": p["item_id"],
                "arm": p["arm"],
                "automatic_Y_YA_YF_YU": [
                    p["automatic_Y"], p["automatic_YA"], p["automatic_YF"], p["automatic_YU"]
                ],
                "rater1_label": fourway(outcome_raters[1][p["item_id"]]),
                "rater2_label": fourway(outcome_raters[2][p["item_id"]]),
            }
            for p in automatic_yu
            if fourway(outcome_raters[1][p["item_id"]]) != "YU"
            or fourway(outcome_raters[2][p["item_id"]]) != "YU"
        ]

    jitter_reports = {}
    jitter_dir = resolve_repo_path(args.jitter_dir)
    for jitter_path in sorted(jitter_dir.glob("jitter_stability_*.json")):
        model = jitter_path.stem.replace("jitter_stability_", "")
        payload = json.loads(jitter_path.read_text(encoding="utf-8"))
        jitter_reports[model] = {
            "rate": payload.get("rate"),
            "n": payload.get("n"),
            "passed": payload.get("passed"),
            "mode": payload.get("mode"),
        }
    stability_pass = bool(jitter_reports) and all(
        value["rate"] is not None and value["rate"] >= 0.90
        for value in jitter_reports.values()
    )

    outcome_gates = [
        {
            "criterion": "4-way Cohen's kappa >= .80 (N/YA/YF/YU)",
            "observed": round(kappa_outcome, 4),
            "pass": kappa_outcome >= 0.80,
        },
        {
            "criterion": "silent-propagation PPV >= .90 (automatic YU items confirmed by both raters)",
            "observed": None if strict_ppv is None else round(strict_ppv, 4),
            "pass": strict_ppv is not None and strict_ppv >= 0.90,
        },
        {
            "criterion": "10% seed-repeat stability >= .90 (per model)",
            "observed": {model: value["rate"] for model, value in jitter_reports.items()},
            "pass": stability_pass,
        },
    ]

    # ---------------------------------------------------------------- recovery
    recovery_rows = []
    recovery_disagreements = 0
    corrections = []
    for packet in recovery_items:
        item_id = packet["item_id"]
        first = recovery_raters[1][item_id]
        second = recovery_raters[2][item_id]
        automatic_step = packet["automatic_recovered_step"] or "4"
        automatic_endpoint = packet["automatic_endpoint"]
        if (first["recovery_step"], first["endpoint"]) != (
            second["recovery_step"],
            second["endpoint"],
        ):
            recovery_disagreements += 1
        if (first["recovery_step"], first["endpoint"]) != (
            automatic_step,
            automatic_endpoint,
        ) or (second["recovery_step"], second["endpoint"]) != (
            automatic_step,
            automatic_endpoint,
        ):
            corrections.append(item_id)
        flags = []
        if (first["recovery_step"], first["endpoint"]) != (
            second["recovery_step"],
            second["endpoint"],
        ):
            flags.append("rater_disagree")
        if item_id in corrections:
            flags.append("ref_override")
        recovery_rows.append(
            {
                "item_id": item_id,
                "rater1_recovery_step": first["recovery_step"],
                "rater1_endpoint": first["endpoint"],
                "rater2_recovery_step": second["recovery_step"],
                "rater2_endpoint": second["endpoint"],
                "notes": _notes(
                    2,
                    flags,
                    [("rater1", first.get("note", "")), ("rater2", second.get("note", ""))],
                ),
            }
        )

    kappa_step, kappa_step_detail = cohen_kappa(
        [recovery_raters[1][item]["recovery_step"] for item in recovery_ids],
        [recovery_raters[2][item]["recovery_step"] for item in recovery_ids],
    )
    kappa_endpoint, kappa_endpoint_detail = cohen_kappa(
        [recovery_raters[1][item]["endpoint"] for item in recovery_ids],
        [recovery_raters[2][item]["endpoint"] for item in recovery_ids],
    )
    recovery_gates = [
        {
            "criterion": "Cohen's kappa >= .75 on recovery step",
            "observed": round(kappa_step, 4),
            "pass": kappa_step >= 0.75,
        },
        {
            "criterion": "Cohen's kappa >= .75 on endpoint",
            "observed": round(kappa_endpoint, 4),
            "pass": kappa_endpoint >= 0.75,
        },
    ]

    # ---------------------------------------------------------------- write
    def _write_sheet(path: Path, columns, rows) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in columns})

    _write_sheet(audit_dir / "severity_audit_sheet.csv", SEVERITY_SHEET_COLUMNS, severity_rows)
    _write_sheet(audit_dir / "outcome_audit_sheet.csv", OUTCOME_SHEET_COLUMNS, outcome_rows)
    _write_sheet(audit_dir / "recovery_audit_sheet.csv", RECOVERY_SHEET_COLUMNS, recovery_rows)

    result = {
        "stage": "08c_blind_audit_score",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "raters": {
            "count": 3,
            "roles": {
                "blind_rater_1": "severity + outcome + recovery",
                "blind_rater_2": "severity + outcome + recovery",
                "blind_rater_3": "severity only",
            },
            "blinding": "raters saw only artifacts/audit/blind/*_items.jsonl",
            "human_verification": "pending per D-021 / D-027",
        },
        "provenance": {
            "packets": {
                name: (_sha256(audit_dir / name) if (audit_dir / name).exists() else None)
                for name in (
                    "severity_audit_packet.csv",
                    "outcome_audit_packet.csv",
                    "recovery_audit_packet.csv",
                )
            },
            "rater_files": {
                path.name: _sha256(path)
                for path in sorted(blind_dir.glob("rater*.csv"))
            },
            "sheets": {
                name: _sha256(audit_dir / name)
                for name in (
                    "severity_audit_sheet.csv",
                    "outcome_audit_sheet.csv",
                    "recovery_audit_sheet.csv",
                )
            },
        },
        "severity": {
            "items": len(severity_items),
            "jonckheere_terpstra": jt_majority,
            "per_rater_jt": jt_raters,
            "krippendorff_alpha": {
                "severity_nominal": round(alpha_severity_nominal, 4),
                "severity_interval": round(alpha_severity_interval, 4),
                "decision_changing_nominal": round(alpha_decision, 4),
                "absurd_nominal": round(alpha_absurd, 4),
            },
            "rates_majority": {
                "s1_non_decision_changing": round(rate_s1, 4),
                "s23_decision_changing": round(rate_s23, 4),
                "s3_absurd": round(rate_s3_absurd, 4),
            },
            "rater_disagreements": disagreements,
            "majority_overrides_of_reference": overrides,
            "gates": severity_gates,
            "passed": all(gate["pass"] for gate in severity_gates),
        },
        "outcome": {
            "items": len(outcome_items),
            "cohen_kappa_4way": {"kappa": round(kappa_outcome, 4), **kappa_detail},
            "silent_ppv": {
                "automatic_yu_items": len(automatic_yu),
                "strict_both_raters": None if strict_ppv is None else round(strict_ppv, 4),
                "lenient_either_rater": None if lenient_ppv is None else round(lenient_ppv, 4),
                "unconfirmed_items": unconfirmed,
            },
            "rater_disagreements": outcome_disagreements,
            "seed_repeat_stability": jitter_reports,
            "gates": outcome_gates,
            "passed": all(gate["pass"] for gate in outcome_gates),
        },
        "recovery": {
            "items": len(recovery_items),
            "cohen_kappa_recovery_step": {"kappa": round(kappa_step, 4), **kappa_step_detail},
            "cohen_kappa_endpoint": {"kappa": round(kappa_endpoint, 4), **kappa_endpoint_detail},
            "rater_disagreements": recovery_disagreements,
            "corrections_of_automatic_coding": corrections,
            "gates": recovery_gates,
            "passed": all(gate["pass"] for gate in recovery_gates),
        },
        "caveats": [
            "Ratings come from blind rater sessions (AI subagents); the authors' verification (D-021/D-027) is pending, so every gate result is provisional.",
            "Sheet notes name the raters per row (blind_rater_1;blind_rater_2;blind_rater_3 for severity; blind_rater_1;blind_rater_2 for outcome and recovery) plus rater_disagree / ref_override markers and per-rater remarks.",
            "Recovery ratings use the per-step evidence in the packet (steps_json), generated under parser toolresult-parser-v4; the automatic recovery coding is recomputed by stage 09e.",
            "Seed-repeat stability is read from artifacts/analysis/jitter_stability_*.json (parser v4 rescores of the preregistered 10% jitter shard).",
            "Outcome items with a blank automatic label have a reference parsed as a refusal; the automatic coder skips them (no imputation), while raters score them from the packet text.",
            "Recovery flag detection is keyword-based and remains inconsistent at the margin; rated overrides and remaining ambiguities are recorded in the per-rater notes.",
        ],
    }
    write_json(out_path, result)
    print(
        f"[08c] severity={result['severity']['passed']} "
        f"outcome={result['outcome']['passed']} recovery={result['recovery']['passed']}"
    )
    print(f"[08c] wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
