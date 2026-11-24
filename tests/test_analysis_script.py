"""End-to-end test of the G3 analysis script on a synthetic ledger."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from toolobs.infer.ledger import append_ledger_row
from toolobs.infer.parse_output import parse_decision, signature_hash, signature_json
from toolobs.schemas import LedgerRow, PerturbationRecord
from _requires import requires_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

_REFERENCE = '{"tool": "get_order_details", "arguments": {"order_id": "#W1"}}'
_SWITCHED = '{"tool": "cancel_order", "arguments": {"order_id": "#W1"}}'


def _row(model: str, prefix: str, arm: str, decision_text: str) -> LedgerRow:
    parsed = parse_decision(decision_text)
    assert parsed.parsed
    return LedgerRow(
        run_id="test",
        model_id=model,
        prefix_id=prefix,
        arm=arm,
        step=0,
        prompt_hash="p",
        output_text=decision_text,
        parsed=True,
        latency_ms=1.0,
        cost_usd=0.0,
        timestamp_utc="2026-11-15T00:00:00+00:00",
        stage="main",
        parser_status="ok",
        signature_hash=signature_hash(parsed),
        decision_json=signature_json(parsed),
    )


@requires_yaml
def test_analysis_script_reports_slope(tmp_path) -> None:
    ledger_root = tmp_path / "runs"
    model_dir = ledger_root / "qwen"
    model_dir.mkdir(parents=True)
    ledger = model_dir / "ledger.jsonl"
    for prefix_index in range(4):
        prefix = f"p{prefix_index}"
        # p0 never switches; the other three switch from s=2 upward.
        for arm in ("V", "s0", "s1"):
            append_ledger_row(ledger, _row("qwen", prefix, arm, _REFERENCE))
        for arm in ("s2", "s3"):
            text = _REFERENCE if prefix_index == 0 else _SWITCHED
            append_ledger_row(ledger, _row("qwen", prefix, arm, text))

    perturbations = tmp_path / "perturbations.jsonl"
    with perturbations.open("w", encoding="utf-8") as handle:
        for prefix_index in range(4):
            for arm, severity in (("s1", 1), ("s2", 2), ("s3", 3)):
                record = PerturbationRecord(
                    prefix_id=f"p{prefix_index}",
                    arm=arm,
                    severity=severity,
                    json_path="$.x",
                    true_value=1,
                    false_value=2,
                    criticality="critical" if severity >= 2 else "noncritical",
                    expected_action_change=True,
                    renderer_version="test",
                )
                handle.write(json.dumps(record.to_dict()) + "\n")

    out = tmp_path / "analysis.json"
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "13_analyze.py"),
            "--models",
            "qwen",
            "--ledger-root",
            str(ledger_root),
            "--perturbations",
            str(perturbations),
            "--expected-rows",
            "20",
            "--bootstrap",
            "50",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["models"] == ["qwen"]
    assert report["coverage"]["qwen"]["complete"] is True
    assert report["n_slope_rows"] == 16
    assert report["pooled"]["beta"] > 0
    assert report["pooled"]["p_value"] < 0.05
    assert report["silent_propagation"]["silent_share_of_switch"] is not None
    assert report["bootstrap"]["ci_low"] < report["bootstrap"]["ci_high"]


@requires_yaml
def test_reserve_prefixes_are_excluded_by_default(tmp_path) -> None:
    ledger_root = tmp_path / "runs"
    model_dir = ledger_root / "qwen"
    model_dir.mkdir(parents=True)
    ledger = model_dir / "ledger.jsonl"
    prefixes = ("p0", "p1", "p2", "p3")  # p3 is the reserve prefix
    for prefix in prefixes:
        for arm in ("V", "s0", "s1"):
            append_ledger_row(ledger, _row("qwen", prefix, arm, _REFERENCE))
        for arm in ("s2", "s3"):
            text = _REFERENCE if prefix == "p0" else _SWITCHED
            append_ledger_row(ledger, _row("qwen", prefix, arm, text))

    perturbations = tmp_path / "perturbations.jsonl"
    with perturbations.open("w", encoding="utf-8") as handle:
        for prefix in prefixes:
            for arm, severity in (("s1", 1), ("s2", 2), ("s3", 3)):
                record = PerturbationRecord(
                    prefix_id=prefix,
                    arm=arm,
                    severity=severity,
                    json_path="$.x",
                    true_value=1,
                    false_value=2,
                    criticality="critical" if severity >= 2 else "noncritical",
                    expected_action_change=True,
                    renderer_version="test",
                )
                handle.write(json.dumps(record.to_dict()) + "\n")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"reserve_ids": ["p3"]}), encoding="utf-8")

    def _run(out: Path, *extra: str) -> dict:
        result = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "13_analyze.py"),
                "--models",
                "qwen",
                "--ledger-root",
                str(ledger_root),
                "--perturbations",
                str(perturbations),
                "--manifest",
                str(manifest),
                "--expected-rows",
                "20",
                "--bootstrap",
                "20",
                "--out",
                str(out),
                *extra,
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(out.read_text(encoding="utf-8"))

    default = _run(tmp_path / "default.json")
    assert default["analysis_prefixes"] == 3
    assert default["reserve_ids"] == 1
    assert default["n_slope_rows"] == 12  # 3 prefixes x 4 non-V arms

    with_reserve = _run(tmp_path / "with_reserve.json", "--include-reserve")
    assert with_reserve["analysis_prefixes"] == 4
    assert with_reserve["n_slope_rows"] == 16
