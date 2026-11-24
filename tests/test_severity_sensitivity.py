"""Tests for the stage-14 severity bounded-sensitivity script."""

from __future__ import annotations

from _requires import requires_files
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "14_severity_sensitivity.py"
_spec = importlib.util.spec_from_file_location("severity_sensitivity_script", _SCRIPT)
assert _spec and _spec.loader
severity_sensitivity = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(severity_sensitivity)


def test_wilson_ci_known_values() -> None:
    empty = severity_sensitivity.wilson_ci(0, 0)
    assert empty == {"rate": None, "lo": None, "hi": None}
    result = severity_sensitivity.wilson_ci(7, 60)
    assert abs(result["rate"] - 0.11666666666666667) < 1e-12
    assert abs(result["lo"] - 0.05767647403450049) < 1e-9
    assert abs(result["hi"] - 0.2217902059985814) < 1e-9
    silent = severity_sensitivity.wilson_ci(419, 1964)
    assert abs(silent["rate"] - 419 / 1964) < 1e-12
    assert abs(silent["lo"] - 0.1958) < 1e-3
    assert abs(silent["hi"] - 0.2320) < 1e-3


def test_exact_lower_bound_ppv() -> None:
    lower = severity_sensitivity.exact_lower_bound(9, 9)
    assert lower is not None
    assert abs(lower - 0.025 ** (1.0 / 9.0)) < 1e-9
    assert abs(lower - 0.6637) < 1e-3
    # General case stays inside the Wilson interval for 9/12 recall.
    recall_exact = severity_sensitivity.exact_lower_bound(9, 12)
    recall_wilson = severity_sensitivity.wilson_ci(9, 12)
    assert recall_exact is not None
    assert recall_wilson["lo"] is not None and recall_wilson["hi"] is not None
    assert abs(recall_exact - recall_wilson["lo"]) < 0.05


def test_marginal_or_known_values() -> None:
    result = severity_sensitivity.marginal_or(707, 2267, 684, 2274)
    assert abs(result["or"] - 1.0535031488978857) < 1e-9
    assert result["lo"] is not None and result["hi"] is not None
    assert result["lo"] < 1.0 < result["hi"]  # marginal s1-s0 not significant
    degenerate = severity_sensitivity.marginal_or(0, 100, 10, 100)
    assert degenerate == {"or": None, "lo": None, "hi": None}


def test_newcombe_diff_sign_and_coverage() -> None:
    diff = severity_sensitivity.newcombe_diff(707, 2267, 684, 2274)
    assert diff["diff"] is not None
    assert abs(diff["diff"] - 0.011074345344992298) < 1e-12
    assert diff["lo"] is not None and diff["hi"] is not None
    assert diff["lo"] < 0.0 < diff["hi"]  # honest null on the margin
    assert diff["lo"] > -0.05 and diff["hi"] < 0.05


def test_dilution_monotone_steepening() -> None:
    p_s1 = 707 / 2267
    p_s2, p_s3 = 911 / 2267, 1053 / 2267
    base_s2 = severity_sensitivity.dilution_adjusted_or(p_s2, 0.0, p_s1, 684, 2274)
    assert base_s2["or"] is not None
    assert abs(base_s2["or"] - 1.5617075505873828) < 1e-9  # m=0 reproduces observed
    prev_s2, prev_s3 = base_s2["or"], None
    for m in (7 / 60, 11 / 60, 16 / 60):
        adj_s2 = severity_sensitivity.dilution_adjusted_or(p_s2, m, p_s1, 684, 2274)
        adj_s3 = severity_sensitivity.dilution_adjusted_or(p_s3, m, p_s1, 684, 2274)
        assert adj_s2["or"] is not None and adj_s3["or"] is not None
        assert adj_s2["or"] > prev_s2  # correction steepens, never flattens
        assert prev_s3 is None or adj_s3["or"] > prev_s3
        prev_s2, prev_s3 = adj_s2["or"], adj_s3["or"]
    adj = severity_sensitivity.dilution_adjusted_or(p_s3, 16 / 60, p_s1, 684, 2274)
    assert adj["or"] is not None and abs(adj["or"] - 2.518177754327338) < 1e-9


def test_provenance_string() -> None:
    assert severity_sensitivity.PROVENANCE == "multi-role agent panel, author-overseen"


@requires_files("artifacts/analysis/prereg_secondary.json", "artifacts/audit/blind_audit_result.json")
def test_cli_smoke_on_repo_inputs(tmp_path: Path) -> None:
    out = tmp_path / "severity_sensitivity.json"
    completed = subprocess.run(
        [sys.executable, str(_SCRIPT), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["provenance"] == "multi-role agent panel, author-overseen"
    assert report["donor_unused_critical"]["majority"]["k"] == 7
    assert report["donor_unused_critical"]["sheet_visible_verifier"]["k"] == 11
    assert report["donor_unused_critical"]["blind_verifier"]["k"] == 16
    assert report["s1_contamination"]["k"] == 3
    assert report["silent_propagation"]["observed"] == {
        "k": 419,
        "n": 1964,
        "wilson95": severity_sensitivity.wilson_ci(419, 1964),
    }
    adjusted = report["silent_propagation"]["recall_adjusted"]["point"]
    assert abs(adjusted - 419 / 0.75 / 1964) < 1e-12
    ppv_lower = report["silent_propagation"]["ppv"]["exact_95_lower"]
    assert abs(ppv_lower - 0.6637) < 1e-3
    assert abs(report["s1_control_conditional"]["p_value"] - 0.019186692739831812) < 1e-12
    assert abs(report["marginal_s1_minus_s0_pp"]["diff"] - 0.011074345344992298) < 1e-12
