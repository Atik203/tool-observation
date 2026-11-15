"""Tests for the G3/G4 audit packet generator."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from toolobs.schemas import LedgerRow, PerturbationRecord

REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = REPO_ROOT / "scripts" / "08b_audit_packets.py"

_spec = importlib.util.spec_from_file_location("audit_packets_script", _SCRIPT)
assert _spec and _spec.loader
audit_packets = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit_packets)


def _perturbation(prefix: str, severity: int, record_id: str) -> dict:
    return {
        "prefix_id": prefix,
        "arm": f"s{severity}",
        "severity": severity,
        "json_path": "$.x",
        "true_value": 1,
        "false_value": 2,
        "criticality": "critical" if severity >= 2 else "noncritical",
        "criticality_2": "",
        "expected_action_change": severity >= 2,
        "plausibility_checks": [],
        "record_id": record_id,
    }


def test_build_severity_packet_balances_levels() -> None:
    perturbations = []
    for level in (1, 2, 3):
        for index in range(50):
            perturbations.append(
                _perturbation(f"p{level}-{index}", level, f"r{level}-{index}")
            )
    packet = audit_packets.build_severity_packet(perturbations, n_per_level=10)
    assert len(packet) == 40
    from collections import Counter

    assert Counter(item["severity_level"] for item in packet) == {0: 10, 1: 10, 2: 10, 3: 10}
    assert all(item["item_id"].startswith("SEV-") for item in packet)


def test_build_outcome_packet_selects_requested_count() -> None:
    ledgers: dict[str, list[LedgerRow]] = {}
    perturbations: list[PerturbationRecord] = []
    for _model_index, model in enumerate(("m0", "m1")):
        rows: list[LedgerRow] = []
        for prefix_index in range(6):
            prefix = f"{model}-p{prefix_index}"
            for arm, signature in (
                ("V", "v"),
                ("s0", "v"),
                ("s1", "v"),
                ("s2", "x"),
                ("s3", "x"),
            ):
                rows.append(
                    LedgerRow(
                        run_id="t",
                        model_id=model,
                        prefix_id=prefix,
                        arm=arm,
                        step=0,
                        prompt_hash="p",
                        output_text="{}",
                        parsed=True,
                        latency_ms=1.0,
                        cost_usd=0.0,
                        timestamp_utc="2026-11-15T00:00:00+00:00",
                        parser_status="ok",
                        signature_hash=signature,
                    )
                )
            for arm, severity in (("s1", 1), ("s2", 2), ("s3", 3)):
                perturbations.append(
                    PerturbationRecord(
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
                )
        ledgers[model] = rows

    packet, _ = audit_packets.build_outcome_packet(ledgers, perturbations, n_items=8)
    assert len(packet) == 8
    assert all(item["item_id"].startswith("OUT-") for item in packet)
    assert {item["model_id"] for item in packet} <= {"m0", "m1"}


def test_cli_generates_packets(tmp_path) -> None:
    audit_dir = tmp_path / "audit"
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--perturbations",
            str(REPO_ROOT / "data" / "manifests" / "perturbations.jsonl"),
            "--ledger-root",
            str(REPO_ROOT / "data" / "runs" / "main"),
            "--audit-dir",
            str(audit_dir),
            "--severity-items",
            "12",
            "--outcome-items",
            "8",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (audit_dir / "severity_audit_packet.csv").exists()
    assert (audit_dir / "severity_audit_sheet.csv").exists()
    assert (audit_dir / "outcome_audit_packet.csv").exists()
    assert (audit_dir / "outcome_audit_sheet.csv").exists()
    import csv

    severity_rows = list(csv.DictReader((audit_dir / "severity_audit_sheet.csv").open()))
    assert len(severity_rows) == 12
    outcome_rows = list(csv.DictReader((audit_dir / "outcome_audit_sheet.csv").open()))
    assert len(outcome_rows) == 8
