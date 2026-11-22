#!/usr/bin/env python
"""Stage 15 — P4.2 recovery re-estimation on the semantic risk set.

CPU-only reanalysis of the frozen ledgers. No text is generated: every number
traces to a step-0 main-ledger row (risk set), a recovery per-step ledger row
(censor reason), or a replayed recovery event (outcome).

Risk set: the semantic switch definition from ``signatures_differ``
(parser v4 / signature v2) — a prefix whose injected decision differs from the
verbatim-V reference and did not flag at injection. This replaces the
run-time hash-inequality risk set (stage 09b), which admits final-answer
paraphrases the semantic coding treats as unchanged.

Estimand: crude cumulative incidence Events/n is primary (final answers and
parse failures stay in the denominator as non-recoveries). Kaplan-Meier is
secondary with a competing-risk caveat (it censors terminal non-recovery
states as non-informative). Co-primary/sensitivity variants make the
censoring treatment explicit; the gate (``>=50%`` of the transient s=3 risk
set recovers by H=4) is evaluated on the crude primary.

Writes ``artifacts/analysis/g4_recovery_v2.json`` and the ``.md`` gate note.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.analysis.outcomes import flag_detected  # noqa: E402
from toolobs.analysis.recovery import (  # noqa: E402
    fit_exponential,
    kaplan_meier,
    rmst,
    weibull_lrt,
)
from toolobs.harvest.parse import read_jsonl_dicts  # noqa: E402
from toolobs.infer.ledger import read_ledger  # noqa: E402
from toolobs.infer.parse_output import (  # noqa: E402
    signature_from_json,
    signatures_differ,
)
from toolobs.paths import (  # noqa: E402
    ARTIFACTS_DIR,
    MANIFEST_DIR,
    RUNS_DIR,
    resolve_repo_path,
)
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402
from toolobs.schemas import LedgerRow, RecoveryEvent  # noqa: E402

PROVENANCE = "multi-role agent panel, author-overseen"
HORIZON = 4
GATE_CRUDE_MIN = 0.50
PERSISTENT_SEED = 20261108  # same shuffle as scripts/09b_recovery.py select_persistent
BOOTSTRAP_REPS = 2000
BOOTSTRAP_SEED = 20261108
Z95 = 1.96


def wilson_ci(events: int, n: int, z: float = Z95) -> dict[str, float | None]:
    """Wilson 95% interval for a binomial proportion."""
    if n <= 0:
        return {"rate": None, "lo": None, "hi": None}
    p = events / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return {"rate": p, "lo": max(0.0, center - half), "hi": min(1.0, center + half)}


def greenwood_ci(km_rows: list[dict]) -> list[dict]:
    """Attach Greenwood standard errors and 95% CIs to KM rows."""
    rows: list[dict] = []
    cumulative = 0.0
    for row in km_rows:
        at_risk = int(row["at_risk"])
        observed = int(row["events"])
        survival = float(row["survival"])
        if at_risk > 0 and at_risk != observed:
            cumulative += observed / (at_risk * (at_risk - observed))
        se = survival * math.sqrt(cumulative)
        rows.append(
            {
                **row,
                "greenwood_se": se,
                "ci95": [max(0.0, survival - Z95 * se), min(1.0, survival + Z95 * se)],
            }
        )
    return rows


def rmst_bootstrap(
    events: list[RecoveryEvent],
    *,
    reps: int = BOOTSTRAP_REPS,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, float]:
    """Nonparametric bootstrap CI for RMST, resampling sequences."""
    rng = random.Random(seed)
    point = rmst(events, horizon=HORIZON)
    if not events:
        return {"rmst": 0.0, "mean": 0.0, "se": 0.0, "ci95": [0.0, 0.0], "reps": reps}
    draws = [rmst(rng.choices(events, k=len(events)), horizon=HORIZON) for _ in range(reps)]
    mean = sum(draws) / len(draws)
    var = sum((value - mean) ** 2 for value in draws) / max(1, len(draws) - 1)
    ordered = sorted(draws)
    return {
        "rmst": point,
        "mean": mean,
        "se": math.sqrt(var),
        "ci95": [ordered[int(0.025 * reps)], ordered[min(reps - 1, int(0.975 * reps))]],
        "reps": reps,
    }


def classify_censor(step_rows: list[LedgerRow]) -> str:
    """Censor reason for one censored sequence.

    Rule (validated: reproduces every cell of recovery_deep analysis_6
    exactly): any unparsed step -> parse_fail; last decision without a tool
    call -> final_answer; otherwise the sequence ran to H=4.
    """
    ordered = sorted(step_rows, key=lambda row: row.step)
    if any(not row.parsed for row in ordered):
        return "parse_fail"
    if not signature_from_json(ordered[-1].decision_json or "{}").tool_name:
        return "final_answer"
    return "ran_to_H"


def semantic_return_step(
    reference_json: str, step_rows: list[LedgerRow]
) -> int | None:
    """First step whose parsed, unflagged decision matches V semantically.

    Diagnostic for the retained hash-exact R1 coding: hash equality implies
    semantic equality, so hash-R1 is a conservative subset of semantic-R1.
    Flag takes precedence (R2), matching the 09e replay ordering.
    """
    reference = signature_from_json(reference_json or "{}")
    for row in sorted(step_rows, key=lambda item: item.step):
        if not row.parsed or not row.decision_json:
            return None
        if flag_detected(row.output_text):
            return None
        if not signatures_differ(reference, signature_from_json(row.decision_json)):
            return row.step
        if not signature_from_json(row.decision_json).tool_name:
            return None
    return None


def persistent_selected(prefixes: dict[str, dict]) -> set[str]:
    """Reconstruct the stage-09b persistent prefix set (deterministic)."""
    selected: set[str] = set()
    for domain in ("airline", "retail"):
        pool = sorted(
            prefix_id
            for prefix_id, prefix in prefixes.items()
            if prefix.get("domain") == domain and prefix.get("split") == "primary"
        )
        rng = random.Random(f"{PERSISTENT_SEED}|persistent|{domain}")
        rng.shuffle(pool)
        selected.update(pool[:100])
    return selected


def _read_events(path: Path) -> list[RecoveryEvent]:
    if not path.exists():
        return []
    return [RecoveryEvent.from_dict(item) for item in read_jsonl_dicts(path)]


def _cell_estimate(
    cell_events: list[RecoveryEvent],
    step_rows_by_prefix: dict[str, list[LedgerRow]],
    reference_json_by_prefix: dict[str, str],
    *,
    bootstrap_reps: int = BOOTSTRAP_REPS,
) -> dict:
    """Crude-primary / KM-secondary estimate for one analysis set."""
    n = len(cell_events)
    recovered = [event for event in cell_events if not event.censored]
    censored = [event for event in cell_events if event.censored]
    crude = wilson_ci(len(recovered), n)
    km_rows = greenwood_ci(kaplan_meier(cell_events, horizon=HORIZON))
    survival_h4 = float(km_rows[-1]["survival"]) if km_rows else 0.0
    km_recovered = 1.0 - survival_h4
    km_se = float(km_rows[-1]["greenwood_se"]) if km_rows else 0.0
    fit = fit_exponential(cell_events, horizon=HORIZON)
    weibull = weibull_lrt(cell_events, horizon=HORIZON)
    reasons = Counter()
    for event in censored:
        rows = step_rows_by_prefix.get(event.prefix_id, [])
        reasons[classify_censor(rows) if rows else "parse_fail"] += 1
    r1 = sum(1 for event in recovered if event.endpoint == "R1")
    r2 = sum(1 for event in recovered if event.endpoint == "R2")
    flips = sum(
        1
        for event in censored
        if event.prefix_id in step_rows_by_prefix
        and event.prefix_id in reference_json_by_prefix
        and semantic_return_step(
            reference_json_by_prefix[event.prefix_id],
            step_rows_by_prefix[event.prefix_id],
        )
        is not None
    )
    n_parse = int(reasons.get("parse_fail", 0))
    return {
        "n": n,
        "events": len(recovered),
        "censored": len(censored),
        "r1": r1,
        "r2": r2,
        "crude": crude,
        "crude_ci95_wilson": [crude["lo"], crude["hi"]],
        "kaplan_meier": km_rows,
        "km_recovered_h4": km_recovered,
        "km_ci95_greenwood": [
            max(0.0, km_recovered - Z95 * km_se),
            min(1.0, km_recovered + Z95 * km_se),
        ],
        "rmst": rmst_bootstrap(cell_events, reps=bootstrap_reps),
        "exponential": fit.as_dict(),
        "t12_half_life": fit.half_life,
        "weibull": weibull,
        "censor_reasons": {
            "parse_fail": int(reasons.get("parse_fail", 0)),
            "final_answer": int(reasons.get("final_answer", 0)),
            "ran_to_H4": int(reasons.get("ran_to_H", 0)),
        },
        "recovery_parse_fail_rate": (n_parse / n) if n else None,
        "sensitivity_parse_worst_case": wilson_ci(len(recovered) + n_parse, n)["rate"],
        "sensitivity_semantic_r1_flips": flips,
        "sensitivity_semantic_r1_crude": wilson_ci(len(recovered) + flips, n)["rate"],
        "gate_pass_crude": (len(recovered) / n) >= GATE_CRUDE_MIN if n else False,
    }


def _markdown(groups: dict[str, dict], overlap: dict[str, dict]) -> str:
    lines = [
        "# G4 — Recovery re-estimation (v2, semantic risk set)",
        "",
        f"Recorded: {utc_now()}",
        f"Provenance: {PROVENANCE}.",
        "",
        "Primary: crude cumulative incidence Events/n on the semantic risk set",
        "(`signatures_differ`, parser v4 / signature v2; flags at injection coded",
        "h=0 and not at risk). Kaplan-Meier is secondary: it censors terminal",
        "non-recovery states (final answers, parse failures) as non-informative,",
        "which biases recovery upward under competing risk. R1 stays hash-exact",
        "(a conservative subset of semantic return; flip bound reported).",
        "",
        "## Gate (crude primary)",
        "",
        "| Group | n (semantic) | Events | Crude (primary) | KM (secondary) | RMST | t12 | Censor P/F/R | Parse-fail rate | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for name in sorted(groups):
        report = groups[name]
        if report.get("missing"):
            lines.append(f"| {name} | 0 | — | — | — | — | — | — | — | no data |")
            continue
        reasons = report["censor_reasons"]
        pfr = report["recovery_parse_fail_rate"]
        t12 = report["t12_half_life"]
        pfr_text = f"{pfr:.1%}" if pfr is not None else "—"
        t12_text = f"{t12:.2f}" if t12 is not None else "—"
        lines.append(
            f"| {name} | {report['n']} | {report['events']} | {report['crude']['rate']:.1%} | "
            f"{report['km_recovered_h4']:.1%} | {report['rmst']['rmst']:.3f} | "
            f"{t12_text} | {reasons['parse_fail']}/{reasons['final_answer']}/{reasons['ran_to_H4']} | "
            f"{pfr_text} | {'PASS' if report['gate_pass_crude'] else 'FAIL'} |"
        )
    lines += [
        "",
        "Censor P/F/R = parse-fail / final-answer / ran-to-H4 among censored.",
        f"Gate: crude >= {GATE_CRUDE_MIN:.0%} by H=4. A failed gate is reported as a failed gate.",
        "",
        "## Hash-vs-semantic overlap (analysis sample, reserve excluded)",
        "",
        "| Group | Hash n (run) | Semantic any (g3) | Both | Hash-only (paraphrase) | "
        "Sem-only flagged (h=0) | Sem-only never run |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in sorted(overlap):
        cell = overlap[name]
        sem_any = cell['semantic_any'] if cell['semantic_any'] is not None else "—"
        lines.append(
            f"| {name} | {cell['hash_n']} | {sem_any} | {cell['both']} | "
            f"{cell['hash_only']} | {cell['sem_only_flagged']} | {cell['sem_only_nonflag_norun']} |"
        )
    lines += [
        "",
        "Hash-only members ran but are not semantic switchers; the v2 analysis drops",
        "them (and their events). Sem-only flagged prefixes are detection h=0 by design.",
        "Sem-only never-run prefixes have no recovery sequences (run-time parser); bounds in JSON.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", nargs="*", default=None)
    parser.add_argument("--ledger-root", default=str(RUNS_DIR / "main"))
    parser.add_argument("--event-root", default=str(RUNS_DIR / "main" / "recovery"))
    parser.add_argument("--manifest", default=str(MANIFEST_DIR / "toolresult800_v1.json"))
    parser.add_argument("--prefixes", default="data/frozen/prefixes.jsonl")
    parser.add_argument("--g3", default=str(ARTIFACTS_DIR / "analysis" / "g3_analysis.json"))
    parser.add_argument("--g4", default=str(ARTIFACTS_DIR / "analysis" / "g4_recovery.json"))
    parser.add_argument("--horizon", type=int, default=HORIZON)
    parser.add_argument("--bootstrap-reps", type=int, default=BOOTSTRAP_REPS)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    # Horizon threads through helpers via the module default (CPU-only script;
    # the CLI override below is the single mutation point).
    globals()["HORIZON"] = args.horizon

    from toolobs.config import load_config  # noqa: E402 - lazy, keeps import light

    configured = [str(model["id"]) for model in load_config("models.yaml")["models"]]
    model_ids = args.models or configured
    ledger_root = resolve_repo_path(args.ledger_root)
    event_root = resolve_repo_path(args.event_root)
    manifest = json.loads(resolve_repo_path(args.manifest).read_text(encoding="utf-8"))
    reserve_ids = set(manifest.get("reserve_ids", []))
    prefixes_path = resolve_repo_path(args.prefixes)
    prefixes = (
        {str(row["prefix_id"]): row for row in read_jsonl_dicts(prefixes_path)}
        if prefixes_path.exists()
        else {}
    )
    selected_persistent = persistent_selected(prefixes) if prefixes else set()
    g3_path = resolve_repo_path(args.g3)
    g3 = json.loads(g3_path.read_text(encoding="utf-8")) if g3_path.exists() else {}
    g3_any = (g3.get("arm_table") or {}) if isinstance(g3, dict) else {}
    g4_path = resolve_repo_path(args.g4)
    g4 = json.loads(g4_path.read_text(encoding="utf-8")) if g4_path.exists() else {}
    g4_groups = (g4.get("groups") or {}) if isinstance(g4, dict) else {}

    cells = (
        ("transient", "s2", 2),
        ("transient", "s3", 3),
        ("persistent", "s3", 3),
    )
    groups: dict[str, dict] = {}
    overlap: dict[str, dict] = {}
    inclusion: dict[str, dict] = {}
    hash_bridge: dict[str, dict] = {}
    analysis_events_by_cell: dict[str, list[RecoveryEvent]] = {}
    analysis_steps_by_cell: dict[str, dict[str, list[LedgerRow]]] = {}
    reference_json_by_cell: dict[str, dict[str, str]] = {}
    ledger_rows_used = 0

    for model_id in model_ids:
        ledger_path = ledger_root / model_id / "ledger.jsonl"
        if not ledger_path.exists():
            continue
        step0 = [row for row in read_ledger(ledger_path) if row.step == 0]
        ledger_rows_used += len(step0)
        by_key = {(row.prefix_id, row.arm): row for row in step0}
        prefix_ids = {row.prefix_id for row in step0 if row.prefix_id not in reserve_ids}

        for regime, arm, severity in cells:
            name = f"{model_id}|{regime}_s{severity}"
            # Semantic risk set from v4 ledger rows (analysis sample only).
            sem_nonflag: set[str] = set()
            sem_flagged: set[str] = set()
            funnel = Counter()
            for prefix_id in prefix_ids:
                reference = by_key.get((prefix_id, "V"))
                current = by_key.get((prefix_id, arm))
                if reference is None or not reference.parsed or not reference.decision_json:
                    funnel["v_unparsed_or_missing"] += 1
                    continue
                if current is None or not current.parsed or not current.decision_json:
                    funnel["arm_unparsed_or_missing"] += 1
                    continue
                flagged = flag_detected(current.output_text)
                switched = signatures_differ(
                    signature_from_json(reference.decision_json),
                    signature_from_json(current.decision_json),
                )
                if flagged:
                    if switched:
                        sem_flagged.add(prefix_id)
                    else:
                        funnel["flagged_nonswitch"] += 1
                    funnel["flagged_at_injection"] += 1
                    continue
                if not switched:
                    funnel["semantic_non_switch"] += 1
                    continue
                sem_nonflag.add(prefix_id)
            if regime == "persistent":
                sem_full = {pid for pid in sem_nonflag if pid in selected_persistent} if prefixes else set(sem_nonflag)
            else:
                sem_full = set(sem_nonflag)
            sem_flagged_full = (
                {pid for pid in sem_flagged if pid in selected_persistent}
                if (regime == "persistent" and prefixes)
                else set(sem_flagged)
            )

            # Actual run membership (stage 09b hash risk set) + replayed events.
            rec_path = ledger_root / model_id / f"recovery_{regime}.jsonl"
            step_rows: dict[str, list[LedgerRow]] = {}
            if rec_path.exists():
                for row in read_ledger(rec_path):
                    if row.arm == arm and row.prefix_id not in reserve_ids:
                        step_rows.setdefault(row.prefix_id, []).append(row)
            rec_membership = set(step_rows)
            events = [event for event in _read_events(event_root / model_id / f"{regime}.jsonl")
                      if event.severity == severity and event.prefix_id not in reserve_ids]
            event_by_prefix = {event.prefix_id: event for event in events}
            if set(event_by_prefix) != rec_membership:
                print(f"[warn] {name}: event/ledger membership differs "
                      f"({len(event_by_prefix)} vs {len(rec_membership)})")

            both = sem_full & rec_membership
            hash_only = rec_membership - sem_full
            norun = sem_full - rec_membership
            reference_json = {
                pid: by_key[(pid, "V")].decision_json
                for pid in both
                if (pid, "V") in by_key and by_key[(pid, "V")].decision_json
            }
            analysis_events = [event_by_prefix[pid] for pid in sorted(both) if pid in event_by_prefix]
            analysis_steps = {pid: step_rows[pid] for pid in sorted(both) if pid in step_rows}
            analysis_events_by_cell[name] = list(analysis_events)
            analysis_steps_by_cell[name] = dict(analysis_steps)
            reference_json_by_cell[name] = dict(reference_json)

            g3_entry = (g3_any.get(f"{model_id}|{arm}", {}) or {}).get("any")
            if regime == "transient":
                recomputed_any = (
                    len(sem_nonflag) + len(sem_flagged) + int(funnel.get("flagged_nonswitch", 0))
                )
            else:
                recomputed_any = len(sem_full) + len(sem_flagged_full)
            if g3_entry is not None and regime == "transient" and recomputed_any != g3_entry:
                print(f"[warn] {name}: recomputed semantic-any {recomputed_any} != g3 {g3_entry}")
            overlap[name] = {
                "hash_n": len(rec_membership),
                "semantic_any": g3_entry if regime == "transient" else None,
                "semantic_any_recomputed": recomputed_any,
                "semantic_nonflag_n": len(sem_full),
                "both": len(both),
                "hash_only": len(hash_only),
                "sem_only_flagged": len(sem_flagged_full),
                "sem_only_nonflag_norun": len(norun),
            }
            inclusion[name] = {
                "analysis_sample_prefixes": len(prefix_ids),
                **{key: int(value) for key, value in funnel.items()},
                "semantic_risk_set": len(sem_full),
                "ran_with_sequences": len(both),
                "never_run": len(norun),
                "hash_only_run_dropped": len(hash_only),
            }
            if regime == "persistent":
                inclusion[name]["persistent_selected_prefixes"] = len(
                    {pid for pid in selected_persistent if pid in prefix_ids}
                )
            if not analysis_events:
                groups[name] = {"n": 0, "missing": True,
                                "semantic_full_n": len(sem_full), "never_run": len(norun)}
                continue
            estimate = _cell_estimate(
                analysis_events, analysis_steps, reference_json,
                bootstrap_reps=args.bootstrap_reps,
            )
            n_full = len(sem_full)
            events_n = estimate["events"]
            estimate["semantic_full_n"] = n_full
            estimate["never_run"] = len(norun)
            estimate["never_run_bounds_crude"] = [
                wilson_ci(events_n, n_full)["rate"] if n_full else None,
                wilson_ci(events_n + len(norun), n_full)["rate"] if n_full else None,
            ]
            estimate["model_id"] = model_id
            estimate["regime"] = regime
            estimate["severity"] = severity
            estimate["horizon"] = HORIZON
            estimate["risk_set"] = "semantic signatures_differ (parser v4 / signature v2), nonflag, reserve excluded"
            groups[name] = estimate

            # Hash bridge: dropped hash-only members reconcile the g4 triple.
            hash_events = [event_by_prefix[pid] for pid in sorted(hash_only) if pid in event_by_prefix]
            hash_recovered = sum(1 for event in hash_events if not event.censored)
            g4_cell = g4_groups.get(name, {}) if isinstance(g4_groups, dict) else {}
            g4_exp = (g4_cell.get("exponential") or {}) if isinstance(g4_cell, dict) else {}
            hash_bridge[name] = {
                "hash_only_n": len(hash_only),
                "hash_only_events": hash_recovered,
                "hash_only_crude": (hash_recovered / len(hash_only)) if hash_only else None,
                "g4_n": g4_cell.get("n"),
                "g4_events": g4_exp.get("events"),
                "analysis_n": estimate["n"],
                "analysis_events": events_n,
                "bridge_events_sum": events_n + hash_recovered,
                "bridge_n_sum": estimate["n"] + len(hash_only),
            }

    primary_names = sorted(name for name in groups if name.endswith("transient_s3"))
    primary_passed = bool(primary_names) and all(
        groups[name].get("gate_pass_crude", False) for name in primary_names
    )
    pooled_events: list[RecoveryEvent] = []
    pooled_steps: dict[str, list[LedgerRow]] = {}
    pooled_refs: dict[str, str] = {}
    for name in primary_names:
        model_id = name.split("|")[0]
        for event in analysis_events_by_cell.get(name, []):
            namespaced = RecoveryEvent(
                prefix_id=f"{model_id}|{event.prefix_id}",
                model_id=event.model_id,
                regime=event.regime,
                severity=event.severity,
                horizon=event.horizon,
                recovered_step=event.recovered_step,
                endpoint=event.endpoint,
                censored=event.censored,
                state_hash=event.state_hash,
                last_step=event.last_step,
            )
            pooled_events.append(namespaced)
        for prefix_id, rows in analysis_steps_by_cell.get(name, {}).items():
            pooled_steps[f"{model_id}|{prefix_id}"] = rows
        for prefix_id, ref_json in reference_json_by_cell.get(name, {}).items():
            pooled_refs[f"{model_id}|{prefix_id}"] = ref_json
    pooled_estimate = (
        _cell_estimate(pooled_events, pooled_steps, pooled_refs, bootstrap_reps=args.bootstrap_reps)
        if pooled_events
        else {"n": 0, "missing": True}
    )
    payload_pooled = dict(pooled_estimate)
    payload_pooled["cells"] = primary_names
    payload = {
        "stage": "g4_recovery_v2",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "provenance": PROVENANCE,
        "horizon": HORIZON,
        "gate": {"crude_recovered_by_h4_min": GATE_CRUDE_MIN},
        "methods": {
            "risk_set": "semantic signatures_differ (parser v4 / signature v2); "
                        "parsed V and injected rows, reserve excluded, flags at "
                        "injection coded h=0 and not at risk",
            "primary": "crude cumulative incidence Events/n; final answers and "
                       "parse failures remain in the denominator as non-recoveries",
            "secondary": "Kaplan-Meier 1-S(4) with Greenwood CI; censors terminal "
                         "non-recovery states as non-informative (competing-risk caveat)",
            "r1_coding": "hash-exact R1 retained (conservative subset of semantic "
                         "return); semantic-R1 flip bound reported per cell",
            "rmst_ci": f"nonparametric bootstrap, {BOOTSTRAP_REPS} reps, seed {BOOTSTRAP_SEED}",
        },
        "inputs": {
            "ledger_rows_step0": ledger_rows_used,
            "reserve_excluded": len(reserve_ids),
            "parser": "toolresult-parser-v4",
            "g3_cross_checked": bool(g3_any),
        },
        "models": model_ids,
        "groups": groups,
        "overlap": overlap,
        "inclusion": inclusion,
        "hash_bridge": hash_bridge,
        "pooled_transient_s3": payload_pooled,
        "primary_cells": primary_names,
        "primary_passed": primary_passed,
    }
    out_path = resolve_repo_path(args.out or (ARTIFACTS_DIR / "analysis" / "g4_recovery_v2.json"))
    write_json(out_path, payload)
    markdown_path = out_path.with_suffix(".md")
    markdown_path.write_text(_markdown(groups, overlap), encoding="utf-8", newline="\n")
    for name in sorted(groups):
        report = groups[name]
        print(f"[15_recovery] {name} n_sem={overlap[name]['semantic_nonflag_n']} "
              f"n_analysis={report.get('n')} crude={report.get('crude', {}).get('rate')}")
    print(f"[15_recovery] primary_passed {primary_passed}")
    print(f"[15_recovery] wrote {out_path} and {markdown_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
