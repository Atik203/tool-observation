#!/usr/bin/env python
"""Stage 16 — P4.4 inference robustness + audit-circularity record (M1/M5/M7/M9).

Re-verifies the weakness-register inference numbers from frozen analysis
artifacts (read-only) with stdlib-only recomputation, and adds the
robustness checks that do not require row-level refits (run ledgers are
not in the repo):

- per-model exact McNemar s2-vs-s3 as the primary paired contrast, with the
  pooled exact test demoted to secondary (it treats up to three
  model-prefix pairs per prefix as independent);
- pooled McNemar under a prefix-cluster design-effect grid
  (DEFF = 1 + (m-1)*rho, m <= 3 pairs per prefix) plus a model-stratified
  (CMH-style) McNemar;
- categorical/quadratic LRT p-values recomputed from the reported chi2
  statistics (asymptotic check); the 2,000-replicate prefix-cluster
  bootstrap tier-OR intervals already in ``prereg_secondary.json`` are
  collated as the resampling robustness (no new refit is possible without
  the ledgers, and none is claimed);
- recovery comparisons: marginal log-rank recomputed from chi2 (labeled
  descriptive), model-stratified log-rank, and the exact paired McNemar on
  the H=4 recovery indicator as the within-prefix check;
- H1-H7 status table (H5 s3-vs-s1 recomputed; H4 crude cited read-only
  from the T2 v2 re-estimation);
- outcome-definition sensitivity: strict (flag-excluding, signature-only)
  vs lenient coding;
- pre/post-fix slope record (pre-fix beta .684 cited from A-006/ROADMAP;
  artifact not retained) and the prereg freeze/deposit record.

CPU-only, stdlib-only. Output is regenerable and gitignored by design.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402

PROVENANCE = "multi-role agent panel, author-overseen"
SEED = 20261108

PREREG_SECONDARY = REPO_ROOT / "artifacts" / "analysis" / "prereg_secondary.json"
RECOVERY_DEEP = REPO_ROOT / "artifacts" / "analysis" / "recovery_deep.json"
G3_ANALYSIS = REPO_ROOT / "artifacts" / "analysis" / "g3_analysis.json"
G4_RECOVERY_V2 = REPO_ROOT / "artifacts" / "analysis" / "g4_recovery_v2.json"
OUT_PATH = REPO_ROOT / "artifacts" / "analysis" / "inference_robustness.json"

SHORT = {
    "llama_3_1_8b_instruct_awq": "Llama-3.1-8B",
    "ministral_3_8b_instruct_2512_awq": "Ministral-3-8B",
    "qwen3_5_9b_instruct_awq": "Qwen3.5-9B",
}


def exact_mcnemar_two_sided(b: int, c: int) -> float:
    """Exact two-sided McNemar p: B ~ Binomial(b+c, 0.5), doubling the lower tail."""
    n = b + c
    if n == 0:
        return 1.0
    lo = min(b, c)
    tail = sum(math.comb(n, k) for k in range(lo + 1)) / 2.0**n
    return min(1.0, 2.0 * tail)


def chi2_p_df1(stat: float) -> float:
    """Upper-tail p for chi2(1) via erfc."""
    return math.erfc(math.sqrt(max(stat, 0.0) / 2.0))


def chi2_p_df2(stat: float) -> float:
    """Upper-tail p for chi2(2): exp(-x/2)."""
    return math.exp(-max(stat, 0.0) / 2.0)


def stratified_mcnemar(pairs: list[tuple[int, int]]) -> dict[str, float]:
    """CMH-style paired test across strata: sum(b-c) over sqrt(sum(b+c)).

    Each stratum contributes one discordant table; valid when strata
    partition the pairs (here: models partition the pooled pairs).
    """
    diff = sum(b - c for b, c in pairs)
    var = sum(b + c for b, c in pairs)
    chi2 = diff * diff / var if var > 0 else 0.0
    return {"diff": float(diff), "var": float(var), "chi2": chi2,
            "p_value": chi2_p_df1(chi2)}


def deff_adjusted_pooled(b: int, c: int, m: float, rhos: list[float]) -> list[dict[str, float]]:
    """Pooled McNemar chi2 deflated by DEFF = 1 + (m-1)*rho over a rho grid."""
    n = b + c
    chi2 = (b - c) ** 2 / n if n > 0 else 0.0
    rows = []
    for rho in rhos:
        deff = 1.0 + (m - 1.0) * rho
        adj = chi2 / deff
        rows.append({"rho": rho, "m_pairs_per_prefix": m, "deff": deff,
                     "chi2_adjusted": adj, "p_value": chi2_p_df1(adj)})
    return rows


def _load(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(OUT_PATH))
    args = ap.parse_args()

    secondary = _load(PREREG_SECONDARY)
    deep = _load(RECOVERY_DEEP)

    # ---- M1: McNemar s2-vs-s3, per-model primary + pooled secondary ----
    mcn = secondary["mcnemar"]
    mcnemar_check: dict[str, dict] = {}
    for model, row in mcn["per_model"].items():
        b, c = row["b_s2_no_s3_yes"], row["c_s2_yes_s3_no"]
        p = exact_mcnemar_two_sided(b, c)
        mcnemar_check[model] = {
            "b": b, "c": c, "n_pairs": row["n_pairs"],
            "reported_two_sided_p": row["exact_binomial_p_two_sided"],
            "recomputed_two_sided_p": p,
            "match_within_1pct": abs(p - row["exact_binomial_p_two_sided"])
            <= 0.01 * row["exact_binomial_p_two_sided"],
            # One pair per prefix within a model: prefixes are the
            # independent units, so no cross-model clustering applies.
            "cluster_note": "primary; one pair per prefix, independent units",
        }
    pooled = mcn["pooled"]
    bp, cp = pooled["b_s2_no_s3_yes"], pooled["c_s2_yes_s3_no"]
    p_pool = exact_mcnemar_two_sided(bp, cp)
    pairs = [(r["b_s2_no_s3_yes"], r["c_s2_yes_s3_no"])
             for r in mcn["per_model"].values()]
    strat = stratified_mcnemar(pairs)
    # At most 3 pairs (one per model) share a prefix; bound m by 3 and also
    # report the realized mean under full prefix overlap as reference.
    deff_grid = deff_adjusted_pooled(bp, cp, 3.0, [0.0, 0.1, 0.3, 0.5])
    mcnemar_check["pooled"] = {
        "b": bp, "c": cp, "n_pairs": pooled["n_pairs"],
        "reported_two_sided_p": pooled["exact_binomial_p_two_sided"],
        "recomputed_two_sided_p": p_pool,
        "match_within_1pct": abs(p_pool - pooled["exact_binomial_p_two_sided"])
        <= 0.01 * pooled["exact_binomial_p_two_sided"],
        "status": "secondary; pooled exact p treats model-prefix pairs as "
                  "independent and is anti-conservative for prefix-level inference",
        "stratified_by_model": strat,
        "design_effect_grid_m_le_3": deff_grid,
    }

    # ---- H5: s3-vs-s1 McNemar recomputed ----
    h5 = mcn["s3_vs_s1"]
    h5_check: dict[str, dict] = {}
    for model, row in h5["per_model"].items():
        b, c = row["b_s1_no_s3_yes"], row["c_s1_yes_s3_no"]
        p = exact_mcnemar_two_sided(b, c)
        h5_check[model] = {"b": b, "c": c, "n_pairs": row["n_pairs"],
                           "recomputed_two_sided_p": p,
                           "reported_two_sided_p": row["exact_binomial_p_two_sided"]}
    bp5, cp5 = h5["pooled"]["b_s1_no_s3_yes"], h5["pooled"]["c_s1_yes_s3_no"]
    h5_check["pooled"] = {"b": bp5, "c": cp5,
                          "n_pairs": h5["pooled"]["n_pairs"],
                          "recomputed_two_sided_p": exact_mcnemar_two_sided(bp5, cp5),
                          "reported_two_sided_p": h5["pooled"]["exact_binomial_p_two_sided"]}

    # ---- Categorical/quadratic LRT asymptotic re-verification + bootstrap support ----
    lin = secondary["linearity"]
    lrt_check: dict[str, dict] = {}
    for scope in ("pooled",):
        block = lin[scope]
        cat = block["lrt_categorical_vs_linear"]
        quad = block["lrt_quadratic_vs_linear"]
        lrt_check[scope] = {
            "categorical_chi2": cat["statistic"],
            "categorical_recomputed_p": chi2_p_df2(cat["statistic"]),
            "categorical_reported_p": cat["p_value"],
            "quadratic_chi2": quad["statistic"],
            "quadratic_recomputed_p": chi2_p_df1(quad["statistic"]),
            "quadratic_reported_p": quad["p_value"],
        }
    for model, block in lin["per_model"].items():
        cat = block["lrt_categorical_vs_linear"]
        quad = block["lrt_quadratic_vs_linear"]
        lrt_check[model] = {
            "categorical_chi2": cat["statistic"],
            "categorical_recomputed_p": chi2_p_df2(cat["statistic"]),
            "categorical_reported_p": cat["p_value"],
            "quadratic_chi2": quad["statistic"],
            "quadratic_recomputed_p": chi2_p_df1(quad["statistic"]),
            "quadratic_reported_p": quad["p_value"],
        }
    # Resampling robustness already in the artifact: tier-OR bootstrap CIs.
    tier_boot: dict[str, dict] = {}
    for model, block in secondary["tier_or"]["per_model"].items():
        lo = block["bootstrap_or_ci_low"]
        hi = block["bootstrap_or_ci_high"]
        ors = block["categorical_fit"]["or"]
        tier_boot[model] = {
            "or_point": ors,
            "bootstrap_ci_low": lo, "bootstrap_ci_high": hi,
            "s2_s3_exclude_1": all(lo[k] > 1.0 for k in (1, 2)),
            "s1_includes_1": lo[0] < 1.0 < hi[0],
        }
    lrt_check["bootstrap_support_note"] = (
        "No row-level refit: run ledgers are not in the repo, so no new "
        "bootstrap LRT was run. Resampling robustness is the 2,000-replicate "
        "prefix-cluster bootstrap tier-OR intervals already in "
        "prereg_secondary.json (seed 20261108): s2/s3 CIs exclude 1 in all "
        "models; the Qwen s1 CI includes 1."
    )

    # ---- M5: recovery paired vs marginal ----
    logrank = deep["analysis_3_logrank"]
    recovery_tests: dict[str, dict] = {}
    for contrast in ("transient_s2_vs_transient_s3", "transient_s3_vs_persistent_s3"):
        block = logrank[contrast]
        entry: dict[str, dict] = {"cells": {}}
        for key, cell in block.items():
            if not isinstance(cell, dict) or "chi2" not in cell:
                continue
            entry["cells"][key] = {
                "chi2": cell["chi2"],
                "reported_p": cell["p_value"],
                "recomputed_p": chi2_p_df1(cell["chi2"]),
                "label": ("descriptive marginal" if key in ("pooled",) or
                          key in SHORT else
                          ("model-stratified" if key == "pooled_stratified_by_model"
                           else "descriptive marginal")),
            }
        entry["paired_mcnemar_h4"] = logrank["paired_supplement"]["mcnemar_exact"][
            "transient_s2_minus_transient_s3" if contrast.startswith("transient_s2")
            else "transient_s3_minus_persistent_s3"]
        # Recompute paired p-values from the discordant recovery counts.
        recomputed = {}
        for model, prow in entry["paired_mcnemar_h4"].items():
            b = prow["recovered_group1_only"]
            c = prow["recovered_group2_only"]
            recomputed[model] = {
                "b": b, "c": c, "n_pairs": prow["n_pairs"],
                "reported_p": prow["exact_binomial_p"],
                "recomputed_p": exact_mcnemar_two_sided(b, c),
            }
        entry["paired_mcnemar_recomputed"] = recomputed
        entry["reading"] = (
            "Marginal and stratified log-rank tests are descriptive: the risk "
            "sets share prefixes, so independence fails. The within-prefix "
            "check is the exact paired McNemar on the H=4 recovery indicator. "
            "Neither rejects equality in either contrast."
        )
        recovery_tests[contrast] = entry

    # ---- H1-H7 status (H4 crude cited read-only from T2 v2) ----
    h4_crude: dict[str, dict] = {}
    if G4_RECOVERY_V2.exists():
        v2 = _load(G4_RECOVERY_V2)
        for key, g in v2.get("groups", {}).items():
            if key.endswith("|persistent_s3"):
                continue
            model, arm = key.split("|")
            if arm != "transient_s3":
                continue
            h4_crude[SHORT.get(model, model)] = {
                "n": g["n"], "events": g["events"],
                "crude": g["crude"]["rate"],
                "wilson": [g["crude"]["lo"], g["crude"]["hi"]],
                "gate_pass_crude": g["gate_pass_crude"],
                "source": "artifacts/analysis/g4_recovery_v2.json (T2 re-estimation, read-only)",
            }
    diag = secondary["diagnostic_summary"]
    hypotheses = {
        "H1": {"claim": "pooled slope beta>0",
               "observed": "beta=0.877 [0.770,0.998], p=2.3e-49",
               "status": "supported (measurement only; gates failed)"},
        "H2": {"claim": "per-model slope positive in >=2/3 models",
               "observed": "3/3 positive, Holm-significant",
               "status": "pass"},
        "H3": {"claim": "silent propagation nonzero share at s2/s3",
               "observed": "419/1964=21.3% lower bound; recall-adjusted ~28.5%",
               "status": "supported (descriptive; gated on outcome audit)"},
        "H4": {"claim": ">=50% of s3 risk set recovers by H=4",
               "observed": h4_crude, "status": "FAIL (crude primary; KM secondary)"},
        "H5": {"claim": "s3 switch rate exceeds s1",
               "observed": {"b": bp5, "c": cp5,
                            "p": h5_check["pooled"]["recomputed_two_sided_p"]},
               "status": "supported"},
        "H6": {"claim": "donor/task slopes directionally consistent",
               "observed": {"donor_interaction_p": diag["donor_interaction_p"],
                            "domain_interaction_p": diag["domain_interaction_p"]},
               "status": "consistent (domain interaction p=.035 exploratory)"},
        "H7": {"claim": "model x severity, task x severity not claimed",
               "observed": "exploratory only", "status": "---"},
    }

    # ---- M7: outcome-definition sensitivity (strict ~= signature-only) ----
    sl = secondary["strict_lenient"]["pooled"]
    outcome_sensitivity = {
        "primary_includes": "signature difference OR explicit flag (Y = Y^A+Y^F+Y^U+Y^O)",
        "strict_beta": sl["strict"]["beta"],
        "strict_ci": [sl["strict"]["bootstrap_ci_low"], sl["strict"]["bootstrap_ci_high"]],
        "lenient_beta": sl["lenient"]["beta"],
        "lenient_ci": [sl["lenient"]["bootstrap_ci_low"], sl["lenient"]["bootstrap_ci_high"]],
        "difference_lenient_minus_strict": sl["difference_lenient_minus_strict"]["point_estimate"],
        "reading": ("Strict coding excludes flags (signature-only Y); the slope is "
                    "unchanged vs primary (0.876 vs 0.877). Lenient action-only "
                    "coding halves the magnitude (0.434) but preserves the sign. "
                    "No prereg amendment: the signature-only sensitivity is reported "
                    "and Y^O (34.4% of critical switches) is decomposed separately."),
    }

    # ---- M9/M22: pre/post-fix record + in-sample circularity label ----
    fix_record = {
        "pre_fix_beta": 0.684,
        "pre_fix_ci": [0.584, 0.797],
        "pre_fix_provenance": ("cited from A-006/ROADMAP; artifact not retained; "
                               "recorded before the conformance fix, triggered by "
                               "the blind audit, not by the slope"),
        "all880_post_fix_beta": 0.867,
        "all880_post_fix_ci": [0.760, 0.988],
        "reported_beta": 0.877,
        "reported_ci": [0.770, 0.998],
        "circularity": ("post-fix coder conformed on the same 160 outcome items "
                        "used to certify kappa=.987/PPV=1.00: the audit is "
                        "in-sample, not a fresh held-out check. Held-out plan: a "
                        "future 60-120-item human audit on reserve prefixes; until "
                        "then agreement stats are reproducibility evidence, not "
                        "independent human reliability."),
    }

    result = {
        "stage": "inference_robustness",
        "provenance": PROVENANCE,
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "seed": SEED,
        "inputs": {
            "prereg_secondary": "artifacts/analysis/prereg_secondary.json",
            "recovery_deep": "artifacts/analysis/recovery_deep.json",
            "g4_recovery_v2": ("artifacts/analysis/g4_recovery_v2.json "
                               "(read-only T2 cite)" if h4_crude else "absent; H4 TBD"),
        },
        "mcnemar_s2_vs_s3": mcnemar_check,
        "h5_s3_vs_s1": h5_check,
        "lrt_robustness": lrt_check,
        "tier_bootstrap_support": tier_boot,
        "recovery_paired_vs_marginal": recovery_tests,
        "hypotheses_h1_h7": hypotheses,
        "outcome_definition_sensitivity": outcome_sensitivity,
        "fix_and_circularity_record": fix_record,
        "prereg_deposit": {
            "frozen_version": "commit 1675376 (2026-11-15), tag prereg-freeze-v1",
            "prereg_hash": "e0d107c6 (authoritative; header DRAFT/TBD lines stale)",
            "external_registry": "none; deposit is in-repo until release DOI (T7)",
            "amendments": "A-001..A-006 in prereg/AMENDMENTS.md; no new amendment "
                          "in this task (sensitivity reported, no rule changed)",
        },
        "assumptions": [
            "Per-model McNemar pairs are prefix-level and independent within model.",
            "Pooled McNemar design-effect grid bounds cross-model prefix correlation; "
            "rho grid is a sensitivity, not an estimated ICC.",
            "No row-level refit was run; bootstrap evidence is collated read-only.",
            "T2/T3 numbers are cited read-only; nothing here recomputes recovery or severity.",
        ],
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_json(out, result)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
