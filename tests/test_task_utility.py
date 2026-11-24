"""Tests for the stage-16 task-utility endpoint script."""

from __future__ import annotations

from _requires import requires_yaml
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "16_task_utility.py"
_spec = importlib.util.spec_from_file_location("task_utility_script", _SCRIPT)
assert _spec and _spec.loader
task_utility = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(task_utility)

_RETOP = Path(__file__).resolve().parents[1]
_EVIDENCE = _RETOP / "artifacts" / "analysis" / "new_evidence.json"


def test_wilson_ci_known_values() -> None:
    empty = task_utility.wilson_ci(0, 0)
    assert empty == {"rate": None, "lo": None, "hi": None}
    result = task_utility.wilson_ci(64, 115)
    assert result["rate"] == round(64 / 115, 6)
    assert abs(result["lo"] - 0.465356) < 1e-3
    assert abs(result["hi"] - 0.644033) < 1e-3


def test_mcnemar_exact_known_values() -> None:
    assert task_utility.mcnemar_exact(0, 0) is None
    # 42 vs 11 discordant: strongly significant.
    assert task_utility.mcnemar_exact(42, 11) == 2.2e-05
    # Perfect symmetry: p = 1.
    assert task_utility.mcnemar_exact(9, 9) == 1.0


def test_cohen_kappa_known_values() -> None:
    assert task_utility.cohen_kappa([], [])["kappa"] is None
    perfect = task_utility.cohen_kappa([2, 1, 0, 2], [2, 1, 0, 2])
    assert perfect["agreement"] == 1.0
    assert perfect["kappa"] == 1.0
    # 38/40 agreement case shape: kappa below 1 but high.
    partial = task_utility.cohen_kappa([2] * 30 + [0] * 8, [2] * 30 + [0] * 7 + [1])
    assert 0.9 < partial["kappa"] < 1.0


def test_donor_reference_parsing() -> None:
    tool = task_utility.donor_reference(
        json.dumps({"role": "assistant", "tool_calls": [{"function": {"name": "Search_Flight", "arguments": "{}"}}]})
    )
    assert tool == ("tool", "search_flight")
    text = task_utility.donor_reference(json.dumps({"role": "assistant", "content": "hello"}))
    assert text == ("text", None)
    assert task_utility.donor_reference("") == ("bad", None)
    assert task_utility.donor_reference("not json") == ("bad", None)


def test_model_decision_parsing() -> None:
    def row(parsed, decision_json, status="ok", output=""):
        return SimpleNamespace(parsed=parsed, decision_json=decision_json, parser_status=status, output_text=output)

    tool_row = row(True, json.dumps({"args": {}, "slots": {}, "tool": "Get_Order", "verb": "tool_call"}))
    assert task_utility.model_decision(tool_row) == ("tool", "get_order")
    # Parser v4 final-answer signature: empty tool + action verb.
    ans_row = row(True, json.dumps({"args": {}, "slots": {}, "tool": "", "verb": "book"}))
    assert task_utility.model_decision(ans_row) == ("answer", None)
    legacy = row(True, json.dumps({"final_answer": "done"}))
    assert task_utility.model_decision(legacy) == ("answer", None)
    assert task_utility.model_decision(row(False, "", status="parse_error")) == ("invalid", None)


def test_donor_match_logic() -> None:
    match = task_utility.donor_match
    assert match(("tool", "cancel_reservation"), ("tool", "cancel_reservation")) is True
    assert match(("tool", "cancel_reservation"), ("tool", "get_order")) is False
    assert match(("tool", "cancel_reservation"), ("answer", None)) is False
    assert match(("text", None), ("answer", None)) is True
    assert match(("text", None), ("tool", "x")) is False
    assert match(("bad", None), ("tool", "x")) is None
    assert match(("tool", "x"), ("invalid", None)) is None


def test_select_sample_deterministic_and_stratified() -> None:
    labels = [
        SimpleNamespace(prefix_id=f"{m}-{i:03d}", model_id=m, arm="s3", y_any=True)
        for m in ("b-model", "a-model", "c-model")
        for i in range(50)
    ]
    first = task_utility.select_sample(labels, per_model=40, seed=20261122)
    second = task_utility.select_sample(labels, per_model=40, seed=20261122)
    assert [(item.prefix_id, item.model_id) for item in first] == [
        (item.prefix_id, item.model_id) for item in second
    ]
    models = [item.model_id for item in first]
    assert sorted(models) == ["a-model"] * 40 + ["b-model"] * 40 + ["c-model"] * 40
    assert len({item.prefix_id for item in first}) == 120


def test_repo_evidence_cross_check() -> None:
    """Cross-check the generated endpoint JSON (regenerable artifact)."""
    if not _EVIDENCE.exists():
        import pytest

        pytest.skip("regenerable artifact not present; run scripts/16_task_utility.py analyze")
    report = json.loads(_EVIDENCE.read_text(encoding="utf-8"))
    assert report["stage"] == "task_utility"
    assert report["hours"]["gpu_hours"] == 0.0
    assert report["provenance"] == "single-agent blinded coding + script-computed endpoints, author-overseen"
    det = report["deterministic"]["pooled"]
    assert det["n"] == 1039
    assert abs(det["match_s0"]["rate"] - 0.290664) < 1e-6
    assert abs(det["match_s3"]["rate"] - 0.288739) < 1e-6
    assert report["agent_coding"]["n_prefixes"] == 120
    assert report["agent_coding"]["n_judgeable_pairs"] == 115
    assert report["agent_coding"]["paired_adequacy_mcnemar_p"] == 2.2e-05
    assert report["reliability"]["n"] == 38
    assert abs(report["reliability"]["kappa"] - 0.918803) < 1e-6


@requires_yaml
def test_cli_smoke_analyze_on_repo_inputs(tmp_path) -> None:
    needed = [
        "task_utility_packets.json",
        "task_utility_map.json",
        "task_utility_s0_packets.json",
        "task_utility_s0_map.json",
        "task_utility_codes.json",
        "task_utility_s0_codes.json",
        "task_utility_recodes_packets.json",
        "task_utility_recodes_map.json",
        "task_utility_recodes.json",
    ]
    missing = [name for name in needed if not (_RETOP / "artifacts" / "analysis" / name).exists()]
    if missing or not (_RETOP / "data" / "runs" / "main").exists():
        import pytest

        pytest.skip(f"repo inputs not present: {missing}")
    out = tmp_path / "new_evidence.json"
    base = _RETOP / "artifacts" / "analysis"
    proc = subprocess.run(
        [
            sys.executable, str(_SCRIPT), "analyze",
            "--packets", str(base / "task_utility_packets.json"),
            "--map", str(base / "task_utility_map.json"),
            "--s0-packets", str(base / "task_utility_s0_packets.json"),
            "--s0-map", str(base / "task_utility_s0_map.json"),
            "--codes", str(base / "task_utility_codes.json"),
            "--s0-codes", str(base / "task_utility_s0_codes.json"),
            "--recode-packets", str(base / "task_utility_recodes_packets.json"),
            "--recode-map", str(base / "task_utility_recodes_map.json"),
            "--recodes", str(base / "task_utility_recodes.json"),
            "--out", str(out),
        ],
        capture_output=True,
        text=True,
        cwd=str(_RETOP),
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["deterministic"]["pooled"]["n"] == 1039
    assert report["agent_coding"]["n_judgeable_pairs"] == 115
