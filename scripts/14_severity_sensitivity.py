#!/usr/bin/env python
"""Stage 14 — P4.3 severity reclassification bounded sensitivity + silent-share bounds.

Re-derives the C5/C12/C13 weakness-register numbers from the audit sheets
(read-only) and emits a bounded sensitivity for the severity tier effects:

- donor-unused rates among the 60 audited critical-arm (s2/s3) items under
  three passes: blind majority (7/60), sheet-visible verifier (11/60), and
  blind verifier (16/60), each with a Wilson 95% interval;
- s1 contamination: 3/30 s1 items rated decision-changing (majority);
- pooled marginal arm rates and marginal tier ORs (s1/s2/s3 vs s0) from the
  frozen ``g3_analysis.json`` arm table, with a dilution re-estimate that
  treats donor-unused critical-arm rows as switching at the s1 rate;
- the s1 negative-control record: conditional s1 OR 1.27 [1.04, 1.55],
  p=.019 cited read-only from ``prereg_secondary.json`` (no row-level refit;
  run ledgers are not in the repo), plus the marginal s1-s0 contrast;
- silent propagation as a lower bound: 419/1964 with Wilson interval, the
  recall-adjusted share from the panel's 9/12 recall, and the exact
  Clopper-Pearson PPV lower bound for 9/9.

Conditional tier ORs (1.27/4.60/11.21) are assigned-severity effects; the
dilution table bounds the realized-criticality direction without refitting.
CPU-only, stdlib-only. Output is regenerable and gitignored by design.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402

PROVENANCE = "multi-role agent panel, author-overseen"
Z95 = 1.96


def wilson_ci(k: int, n: int, z: float = Z95) -> dict[str, float | None]:
    """Wilson score 95% interval for a binomial rate."""
    if n <= 0:
        return {"rate": None, "lo": None, "hi": None}
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / denom
    return {"rate": p, "lo": max(0.0, center - half), "hi": min(1.0, center + half)}


def _binom_sf(k: int, n: int, p: float) -> float:
    """P(X >= k) for Binomial(n, p), via exact integer arithmetic."""
    return sum(
        math.comb(n, i) * (p**i) * ((1.0 - p) ** (n - i)) for i in range(k, n + 1)
    )


def exact_lower_bound(k: int, n: int, alpha: float = 0.05) -> float | None:
    """Two-sided Clopper-Pearson lower bound: p with P(X>=k) = alpha/2.

    Bisection on the exact binomial tail; no scipy dependency.
    """
    if n <= 0 or k <= 0:
        return 0.0 if n > 0 else None
    if k >= n:
        return (alpha / 2.0) ** (1.0 / n)
    target = alpha / 2.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if _binom_sf(k, n, mid) > target:
            hi = mid
        else:
            lo = mid
    return hi


def marginal_or(
    a1: int, n1: int, a0: int, n0: int, z: float = Z95
) -> dict[str, float | None]:
    """Marginal odds ratio for arm 1 vs arm 0 with Wald 95% interval."""
    if min(a1, n1 - a1, a0, n0 - a0) <= 0:
        return {"or": None, "lo": None, "hi": None}
    log_or = math.log((a1 / (n1 - a1)) / (a0 / (n0 - a0)))
    se = math.sqrt(1.0 / a1 + 1.0 / (n1 - a1) + 1.0 / a0 + 1.0 / (n0 - a0))
    return {
        "or": math.exp(log_or),
        "lo": math.exp(log_or - z * se),
        "hi": math.exp(log_or + z * se),
    }


def newcombe_diff(
    a1: int, n1: int, a0: int, n0: int, z: float = Z95
) -> dict[str, float | None]:
    """Risk difference (arm1 - arm0) with Newcombe 95% interval (method 10)."""
    w1, w0 = wilson_ci(a1, n1, z), wilson_ci(a0, n0, z)
    if w1["rate"] is None or w0["rate"] is None:
        return {"diff": None, "lo": None, "hi": None}
    diff = w1["rate"] - w0["rate"]
    assert w1["lo"] is not None and w1["hi"] is not None
    assert w0["lo"] is not None and w0["hi"] is not None
    lo = diff - math.sqrt((w1["rate"] - w1["lo"]) ** 2 + (w0["hi"] - w0["rate"]) ** 2)
    hi = diff + math.sqrt((w1["hi"] - w1["rate"]) ** 2 + (w0["rate"] - w0["lo"]) ** 2)
    return {"diff": diff, "lo": lo, "hi": hi}


def dilution_adjusted_or(
    p_obs: float, m: float, p_ref: float, a0: int, n0: int
) -> dict[str, float | None]:
    """Realized-criticality point OR under the dilution model.

    p_obs is the observed critical-arm switch rate, m the donor-unused
    fraction, p_ref the rate donor-unused rows switch at (s1 pooled rate).
    p_true = (p_obs - m * p_ref) / (1 - m); OR against the s0 arm. Point
    estimate only: interval estimation needs a row-level refit.
    """
    if m >= 1.0:
        return {"or": None, "p_true": None}
    p_true = (p_obs - m * p_ref) / (1.0 - m)
    if not 0.0 < p_true < 1.0:
        return {"or": None, "p_true": p_true}
    odds0 = (a0 / n0) / (1.0 - a0 / n0)
    return {"or": (p_true / (1.0 - p_true)) / odds0, "p_true": p_true}


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_levels(items_path: Path) -> dict[str, str]:
    levels: dict[str, str] = {}
    with items_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                item = json.loads(line)
                levels[item["item_id"]] = str(item["severity_level"])
    return levels


def majority_flags(
    sheet_rows: list[dict[str, str]], levels: dict[str, str], arm: str
) -> list[str]:
    """Item IDs whose blind majority disagrees with the assigned dose.

    For s2/s3: majority NOT decision-changing (donor-unused). For s1:
    majority decision-changing (contamination).
    """
    cols = ("rater1_decision_changing", "rater2_decision_changing", "rater3_decision_changing")
    flagged = []
    for row in sheet_rows:
        level = levels.get(row["item_id"])
        if level is None:
            continue
        votes = sum(int(row[col]) for col in cols)
        if arm == "critical" and level in ("2", "3") and votes <= 1:
            flagged.append(row["item_id"])
        elif arm == "s1" and level == "1" and votes >= 2:
            flagged.append(row["item_id"])
    return sorted(flagged)


def verifier_flags(
    verify_rows: list[dict[str, str]], levels: dict[str, str]
) -> list[str]:
    """Critical-arm items the verifier codes as not decision-changing."""
    return sorted(
        row["item_id"]
        for row in verify_rows
        if levels.get(row["item_id"]) in ("2", "3") and row["decision_changing"] == "0"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    analysis = REPO_ROOT / "artifacts" / "analysis"
    audit = REPO_ROOT / "artifacts" / "audit"
    verification = audit / "verification"

    g3 = json.loads((analysis / "g3_analysis.json").read_text(encoding="utf-8"))
    secondary = json.loads((analysis / "prereg_secondary.json").read_text(encoding="utf-8"))
    blind_result = json.loads((audit / "blind_audit_result.json").read_text(encoding="utf-8"))
    panel = json.loads((verification / "panel_record.json").read_text(encoding="utf-8"))

    levels = _load_levels(audit / "blind" / "severity_items.jsonl")
    sheet = _read_csv_rows(audit / "severity_audit_sheet.csv")
    visible = _read_csv_rows(verification / "severity_verification.csv")
    blind = _read_csv_rows(verification / "severity_verification_slices.csv")

    maj = majority_flags(sheet, levels, "critical")
    s1c = majority_flags(sheet, levels, "s1")
    vis = verifier_flags(visible, levels)
    bli = verifier_flags(blind, levels)

    # Cross-checks against the recorded audit gates (fail loudly on drift).
    assert len(maj) == 7, f"majority donor-unused changed: {len(maj)}"
    assert len(vis) == 11, f"visible-verifier donor-unused changed: {len(vis)}"
    assert len(bli) == 16, f"blind-verifier donor-unused changed: {len(bli)}"
    assert len(s1c) == 3, f"s1 contamination changed: {len(s1c)}"
    assert blind_result["severity"]["rates_majority"]["s23_decision_changing"] == 0.8833 or abs(
        blind_result["severity"]["rates_majority"]["s23_decision_changing"] - 53 / 60
    ) < 1e-9

    donor_unused = {
        name: {
            "k": len(ids),
            "n": 60,
            "by_level": {
                "s2": sum(1 for i in ids if levels[i] == "2"),
                "s3": sum(1 for i in ids if levels[i] == "3"),
            },
            "wilson95": wilson_ci(len(ids), 60),
            "items": ids,
        }
        for name, ids in (
            ("majority", maj),
            ("sheet_visible_verifier", vis),
            ("blind_verifier", bli),
        )
    }

    # Pooled marginal arm table from the frozen g3 analysis.
    arms: dict[str, dict[str, int]] = {"s0": {"any": 0, "n": 0}, "s1": {"any": 0, "n": 0},
                                      "s2": {"any": 0, "n": 0}, "s3": {"any": 0, "n": 0}}
    for key, cell in g3["arm_table"].items():
        arm = key.split("|", 1)[1]
        arms[arm]["any"] += int(cell["any"])
        arms[arm]["n"] += int(cell["n"])
    assert arms["s2"]["any"] + arms["s3"]["any"] == g3["silent_propagation"]["switched_n"] == 1964
    assert g3["silent_propagation"]["silent_n"] == 419

    rates = {arm: wilson_ci(v["any"], v["n"]) for arm, v in arms.items()}
    ref = arms["s0"]
    marginal_ors = {
        arm: marginal_or(v["any"], v["n"], ref["any"], ref["n"]) for arm, v in arms.items() if arm != "s0"
    }
    s1_s0 = newcombe_diff(arms["s1"]["any"], arms["s1"]["n"], ref["any"], ref["n"])

    # Dilution bounded sensitivity: donor-unused critical rows switch at s1 rate.
    p_ref = arms["s1"]["any"] / arms["s1"]["n"]
    dilution = []
    for name, ids in (("majority_7_60", maj), ("visible_11_60", vis), ("blind_16_60", bli)):
        m = len(ids) / 60.0
        row: dict[str, object] = {"pass": name, "m": m}
        for arm in ("s2", "s3"):
            p_obs = arms[arm]["any"] / arms[arm]["n"]
            row[arm] = dilution_adjusted_or(p_obs, m, p_ref, ref["any"], ref["n"])
        dilution.append(row)

    # s1 conditional record cited read-only from the frozen secondary analysis.
    pooled_tiers = secondary["tier_or"]["pooled"]["categorical_fit"]
    s1_conditional = {
        "or": pooled_tiers["or"][0],
        "wald_ci": [pooled_tiers["wald_ci_low"][0], pooled_tiers["wald_ci_high"][0]],
        "bootstrap_ci": [
            secondary["tier_or"]["pooled"]["bootstrap_or_ci_low"][0],
            secondary["tier_or"]["pooled"]["bootstrap_or_ci_high"][0],
        ],
        "p_value": pooled_tiers["p_value"][0],
        "n_groups": pooled_tiers["n_groups"],
        "n_rows": pooled_tiers["n_rows"],
        "source": "artifacts/analysis/prereg_secondary.json:tier_or.pooled (read-only; no refit)",
    }
    assert abs(s1_conditional["or"] - 1.2690324517800897) < 1e-9
    assert abs(s1_conditional["p_value"] - 0.019186692739831812) < 1e-12

    # Silent share: observed lower bound + recall adjustment + PPV bound.
    silent = g3["silent_propagation"]
    panel_outcome = panel["verifier_adjudicated_rates"]["outcome"]
    assert panel_outcome["confirmed"] == 9 and panel_outcome["verifier_only_yu"] is not None
    tp, extra = panel_outcome["confirmed"], len(panel_outcome["verifier_only_yu"])
    assert (tp, extra) == (9, 3)
    recall = wilson_ci(tp, tp + extra)
    assert recall["rate"] == 0.75
    recall_point = tp / (tp + extra)
    silent_report = {
        "observed": {"k": silent["silent_n"], "n": silent["switched_n"], "wilson95": wilson_ci(419, 1964)},
        "recall": {"tp": tp, "fn": extra, "wilson95": recall},
        "recall_adjusted": {
            "point": silent["silent_n"] / recall_point / silent["switched_n"],
            "over_recall_ci": sorted(
                silent["silent_n"] / bound / silent["switched_n"]
                for bound in (recall["hi"], recall["lo"])
            ),
            "method": "observed/recall; interval endpoints map the recall Wilson CI",
        },
        "ppv": {
            "k": 9,
            "n": 9,
            "point": 1.0,
            "exact_95_lower": exact_lower_bound(9, 9),
            "source": "blind_audit_result.json outcome.silent_ppv (read-only)",
        },
    }

    report = {
        "stage": "severity_sensitivity",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "provenance": PROVENANCE,
        "inputs": {
            "g3_analysis": {
                "silent": silent,
                "pooled_slope_rows": g3["n_slope_rows"],
            },
            "prereg_secondary_tier_or_pooled": pooled_tiers["or"],
            "blind_audit_gates": blind_result["severity"]["rates_majority"],
            "panel_outcome": panel_outcome,
        },
        "estimand": (
            "assigned-severity: tier ORs 1.27/4.60/11.21 are contrasts over "
            "assigned arms, not verified realized criticality; 12-27% of "
            "audited critical-arm stimuli are donor-unused, so the assigned "
            "ORs are attenuated (conservative) for the realized-criticality "
            "contrast under the dilution model below."
        ),
        "donor_unused_critical": donor_unused,
        "s1_contamination": {"k": len(s1c), "n": 30, "wilson95": wilson_ci(len(s1c), 30), "items": s1c},
        "marginal_arms": {
            arm: {"any": v["any"], "n": v["n"], "wilson95": rates[arm]} for arm, v in arms.items()
        },
        "marginal_tier_or_vs_s0": marginal_ors,
        "marginal_s1_minus_s0_pp": s1_s0,
        "dilution_sensitivity": {
            "assumption": (
                "donor-unused critical-arm rows switch at the pooled s1 rate "
                f"({p_ref:.4f}); point ORs only, CIs need a row-level refit"
            ),
            "rows": dilution,
        },
        "s1_control_conditional": s1_conditional,
        "silent_propagation": silent_report,
    }

    out = Path(args.out) if args.out else (analysis / "severity_sensitivity.json")
    write_json(out, report)
    print(f"[14_severity] donor-unused 7/11/16 of 60; s1 contamination {len(s1c)}/30")
    print(f"[14_severity] marginal s1-s0 {s1_s0['diff'] * 100:+.2f}pp "
          f"[{s1_s0['lo'] * 100:+.2f}, {s1_s0['hi'] * 100:+.2f}]")
    print(f"[14_severity] recall-adjusted silent "
          f"{silent_report['recall_adjusted']['point'] * 100:.2f}%")
    print(f"[14_severity] wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
