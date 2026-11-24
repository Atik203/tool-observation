"""Tests for the stage-17 wrong-direction endpoint script."""

from __future__ import annotations

from _requires import requires_yaml, requires_files
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "17_wrong_direction.py"
_spec = importlib.util.spec_from_file_location("wrong_direction_script", _SCRIPT)
assert _spec and _spec.loader
wrong_direction = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wrong_direction)

_REPO = Path(__file__).resolve().parents[1]
_JSON = _REPO / "artifacts" / "analysis" / "wrong_direction.json"


def test_wilson_ci_known_values() -> None:
    empty = wrong_direction.wilson_ci(0, 0)
    assert empty == {"rate": None, "lo": None, "hi": None}
    result = wrong_direction.wilson_ci(1258, 1964)
    assert result["rate"] == round(1258 / 1964, 6)
    assert abs(result["lo"] - 0.619052) < 1e-3
    assert abs(result["hi"] - 0.661458) < 1e-3


def test_classify_exclusive_partition() -> None:
    class Label:
        def __init__(self, action, flag, silent):
            self.y_action = action
            self.y_flag = flag
            self.y_silent = silent

    assert wrong_direction.classify(Label(True, True, False)) == "action"
    assert wrong_direction.classify(Label(False, True, False)) == "caught"
    assert wrong_direction.classify(Label(False, False, True)) == "silent"
    assert wrong_direction.classify(Label(False, False, False)) == "other"


def test_summarize_partition_sums() -> None:
    class Label:
        def __init__(self, action, flag, silent):
            self.y_action = action
            self.y_flag = flag
            self.y_silent = silent

    labels = [
        Label(True, False, False),
        Label(True, True, False),
        Label(False, True, False),
        Label(False, False, True),
        Label(False, False, False),
    ]
    summary = wrong_direction.summarize(labels)
    assert summary["switches"] == 5
    assert summary["wrong_direction"] == 3  # 2 action + 1 silent
    assert summary["caught"] == 1
    assert summary["other"] == 1
    assert summary["wrong_direction"] + summary["caught"] + summary["other"] == 5


def test_repo_inputs_cross_check() -> None:
    """Cross-check the generated JSON against the frozen g3 totals (T3 read-only)."""
    if not _JSON.exists():
        import pytest

        pytest.skip("regenerable artifact not present; run scripts/17_wrong_direction.py")
    report = json.loads(_JSON.read_text(encoding="utf-8"))
    assert report["critical_expected_action_change_true"] == report["critical_records"] == 1760
    assert report["critical_switches"] == 1964
    pooled = report["pooled"]
    assert pooled["silent"] == 419  # T3 silent total, read-only
    assert pooled["action"] + pooled["silent"] == pooled["wrong_direction"] == 1258
    assert pooled["wrong_direction"] + pooled["caught"] + pooled["other"] == 1964
    assert report["provenance"] == "multi-role agent panel, author-overseen"


@requires_yaml
@requires_files("data/runs/main")
def test_cli_smoke_on_repo_inputs(tmp_path) -> None:
    out = tmp_path / "wd.json"
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT), "--out", str(out)],
        capture_output=True,
        text=True,
        cwd=str(_REPO),
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["pooled"]["switches"] == 1964
    assert report["pooled"]["wrong_direction"] == 1258
