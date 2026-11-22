"""Tests for the stage-16 inference-robustness script (M1/M5/M7/M9)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "16_inference_robustness.py"
_spec = importlib.util.spec_from_file_location("inference_robustness_script", _SCRIPT)
assert _spec and _spec.loader
inference_robustness = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inference_robustness)


def test_exact_mcnemar_known_values() -> None:
    assert inference_robustness.exact_mcnemar_two_sided(0, 0) == 1.0
    # Pilot-style 5/0 split from the paper's pilot table.
    assert abs(inference_robustness.exact_mcnemar_two_sided(5, 0) - 0.0625) < 1e-12
    # Pooled s2-vs-s3 must reproduce the artifact's 2.1e-20.
    p = inference_robustness.exact_mcnemar_two_sided(190, 50)
    assert abs(p - 2.1121099267123406e-20) / 2.1121099267123406e-20 < 1e-9


def test_chi2_tails_known_values() -> None:
    assert abs(inference_robustness.chi2_p_df1(0.0) - 1.0) < 1e-12
    assert abs(inference_robustness.chi2_p_df1(3.841458820694124) - 0.05) < 1e-6
    assert abs(inference_robustness.chi2_p_df2(0.0) - 1.0) < 1e-12
    assert abs(inference_robustness.chi2_p_df2(5.991464547107979) - 0.05) < 1e-9
    # Pooled categorical LRT 25.03, df=2.
    assert abs(inference_robustness.chi2_p_df2(25.033368891114606)
               - 3.664991852964582e-06) < 1e-15


def test_stratified_and_deff_monotone() -> None:
    strat = inference_robustness.stratified_mcnemar([(47, 15), (73, 15), (70, 20)])
    assert strat["diff"] == 140.0
    assert strat["var"] == 240.0
    assert abs(strat["p_value"] - inference_robustness.chi2_p_df1(strat["chi2"])) < 1e-15
    grid = inference_robustness.deff_adjusted_pooled(190, 50, 3.0, [0.0, 0.1, 0.3, 0.5])
    assert [r["rho"] for r in grid] == [0.0, 0.1, 0.3, 0.5]
    assert grid[0]["deff"] == 1.0
    assert grid[-1]["deff"] == 2.0
    pvals = [r["p_value"] for r in grid]
    assert all(a < b for a, b in zip(pvals, pvals[1:], strict=False))  # weaker with more correlation
    assert all(p < 1e-9 for p in pvals)  # pooled s2-vs-s3 survives the grid


def test_provenance_string() -> None:
    assert inference_robustness.PROVENANCE == "multi-role agent panel, author-overseen"


def test_cli_smoke_on_repo_inputs() -> None:
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        capture_output=True, text=True, cwd=_SCRIPT.parents[1],
    )
    assert proc.returncode == 0, proc.stderr
    out = _SCRIPT.parents[1] / "artifacts" / "analysis" / "inference_robustness.json"
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["provenance"] == "multi-role agent panel, author-overseen"
    per_model = payload["mcnemar_s2_vs_s3"]
    for model in ("llama_3_1_8b_instruct_awq",
                  "ministral_3_8b_instruct_2512_awq",
                  "qwen3_5_9b_instruct_awq"):
        assert per_model[model]["match_within_1pct"] is True
    assert per_model["pooled"]["match_within_1pct"] is True
    # Bootstrap support: s2/s3 CIs exclude 1 everywhere.
    for _, block in payload["tier_bootstrap_support"].items():
        assert block["s2_s3_exclude_1"] is True
    # Recovery paired checks recomputed, none rejects.
    rec = payload["recovery_paired_vs_marginal"]
    for _, entry in rec.items():
        for _, cell in entry["paired_mcnemar_recomputed"].items():
            assert cell["recomputed_p"] > 0.05
    assert payload["hypotheses_h1_h7"]["H5"]["status"] == "supported"
    assert payload["hypotheses_h1_h7"]["H4"]["status"].startswith("FAIL")
