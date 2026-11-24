"""Tests for the G4 recovery report."""

from __future__ import annotations

from _requires import requires_yaml
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from toolobs.schemas import RecoveryEvent

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "14_recovery_report.py"
_spec = importlib.util.spec_from_file_location("recovery_report_script", _SCRIPT)
assert _spec and _spec.loader
recovery_report_script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recovery_report_script)


def _event(index: int, *, recovered_step: int | None, censored: bool) -> RecoveryEvent:
    return RecoveryEvent(
        prefix_id=f"p{index}",
        model_id="qwen",
        regime="transient",
        severity=3,
        horizon=4,
        recovered_step=recovered_step,
        endpoint="R1" if recovered_step is not None else "censored",
        censored=censored,
    )


def test_group_report_computes_recovery_share() -> None:
    events = [
        _event(0, recovered_step=1, censored=False),
        _event(1, recovered_step=1, censored=False),
        _event(2, recovered_step=2, censored=False),
        _event(3, recovered_step=3, censored=False),
        _event(4, recovered_step=4, censored=False),
        _event(5, recovered_step=None, censored=True),
        _event(6, recovered_step=None, censored=True),
        _event(7, recovered_step=None, censored=True),
        _event(8, recovered_step=None, censored=True),
        _event(9, recovered_step=None, censored=True),
    ]
    report = recovery_report_script._group_report(events)
    assert report["n"] == 10
    # KM: 0.8, 0.7, 0.6, 0.5 -> recovered 0.5
    assert abs(report["recovered_by_h4"] - 0.5) < 1e-6
    assert report["gates"]["recovered_by_h4"] is True
    assert report["passed"] in (True, False)


@requires_yaml
def test_cli_writes_json_and_markdown(tmp_path) -> None:
    event_dir = tmp_path / "events" / "qwen"
    event_dir.mkdir(parents=True)
    with (event_dir / "transient.jsonl").open("w", encoding="utf-8") as handle:
        for index in range(6):
            handle.write(
                json.dumps(
                    _event(index, recovered_step=1 if index < 4 else None,
                           censored=index >= 4).to_dict()
                )
                + "\n"
            )
    out = tmp_path / "g4.json"
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--models",
            "qwen",
            "--event-root",
            str(tmp_path / "events"),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["stage"] == "g4_recovery"
    assert "qwen|transient_s3" in payload["groups"]
    assert out.with_suffix(".md").exists()
    assert "Recovered by H=4" in out.with_suffix(".md").read_text(encoding="utf-8")
