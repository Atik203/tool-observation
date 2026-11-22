"""Tests for the stage-15 semantic recovery re-estimation."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from toolobs.schemas import LedgerRow, RecoveryEvent

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "15_recovery_reestimate.py"
_spec = importlib.util.spec_from_file_location("recovery_reestimate_script", _SCRIPT)
assert _spec and _spec.loader
recovery_reestimate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recovery_reestimate)


def _ledger_row(prefix_id: str, arm: str, step: int, **kwargs) -> LedgerRow:
    payload = {
        "run_id": "r",
        "model_id": "test-model",
        "prefix_id": prefix_id,
        "arm": arm,
        "step": step,
        "prompt_hash": "ph",
        "output_text": '{"tool": "t", "args": {}}',
        "parsed": True,
        "latency_ms": 1.0,
        "cost_usd": 0.0,
        "timestamp_utc": "2026-01-01T00:00:00+00:00",
        "parser_status": "ok",
        "signature_hash": f"h-{prefix_id}-{arm}-{step}",
        "decision_json": json.dumps({"tool": "t", "args": {}, "slots": {}, "verb": ""}),
    }
    payload.update(kwargs)
    return LedgerRow(**payload)


def _recover_event(prefix_id: str, recovered_step: int | None) -> RecoveryEvent:
    return RecoveryEvent(
        prefix_id=prefix_id,
        model_id="test-model",
        regime="transient",
        severity=3,
        horizon=4,
        recovered_step=recovered_step,
        endpoint="R1" if recovered_step is not None else "censored",
        censored=recovered_step is None,
        last_step=recovered_step or 4,
    )


def test_wilson_ci_known_values() -> None:
    empty = recovery_reestimate.wilson_ci(0, 0)
    assert empty == {"rate": None, "lo": None, "hi": None}
    result = recovery_reestimate.wilson_ci(80, 376)
    assert abs(result["rate"] - 0.2127659574468085) < 1e-12
    assert abs(result["lo"] - 0.1744102256234766) < 1e-6
    assert abs(result["hi"] - 0.25693168110817155) < 1e-6


def test_greenwood_ci_single_step() -> None:
    rows = recovery_reestimate.greenwood_ci(
        [{"step": 1, "at_risk": 10, "events": 1, "survival": 0.9}]
    )
    assert abs(rows[0]["greenwood_se"] - 0.9 * (1.0 / (10 * 9)) ** 0.5) < 1e-12
    assert rows[0]["ci95"][0] < 0.9 < rows[0]["ci95"][1]


def test_classify_censor_reasons() -> None:
    tool_json = json.dumps({"tool": "t", "args": {}, "slots": {}, "verb": ""})
    final_json = json.dumps({"tool": "", "args": {}, "slots": {}, "verb": "confirm"})
    parse_fail = [
        _ledger_row("p", "s3", 1, decision_json=tool_json),
        _ledger_row("p", "s3", 2, parsed=False, decision_json=""),
    ]
    assert recovery_reestimate.classify_censor(parse_fail) == "parse_fail"
    final_answer = [
        _ledger_row("p", "s3", 1, decision_json=tool_json),
        _ledger_row("p", "s3", 2, decision_json=final_json),
    ]
    assert recovery_reestimate.classify_censor(final_answer) == "final_answer"
    ran_to_h = [_ledger_row("p", "s3", step, decision_json=tool_json) for step in (1, 2, 3, 4)]
    assert recovery_reestimate.classify_censor(ran_to_h) == "ran_to_H"


def test_semantic_return_step_flag_precedence() -> None:
    reference = json.dumps({"tool": "t", "args": {}, "slots": {}, "verb": ""})
    other = json.dumps({"tool": "other", "args": {}, "slots": {}, "verb": ""})
    flagged = _ledger_row(
        "p", "s3", 1, decision_json=other, output_text="this looks wrong, verify it"
    )
    match = _ledger_row("p", "s3", 2, decision_json=reference)
    assert recovery_reestimate.semantic_return_step(reference, [flagged, match]) is None
    assert recovery_reestimate.semantic_return_step(reference, [match]) == 2
    unparsed = _ledger_row("p", "s3", 1, parsed=False, decision_json="")
    assert recovery_reestimate.semantic_return_step(reference, [unparsed, match]) is None


def test_persistent_selected_is_deterministic() -> None:
    prefixes = {
        f"p{i}": {"domain": "airline" if i % 2 else "retail", "split": "primary"}
        for i in range(10)
    }
    first = recovery_reestimate.persistent_selected(prefixes)
    second = recovery_reestimate.persistent_selected(prefixes)
    assert first == second == {f"p{i}" for i in range(10)}


def _write_jsonl(path: Path, rows: list) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row.to_dict()) + "\n")


def _decision(tool: str, args: dict | None = None) -> str:
    return json.dumps({"tool": tool, "args": args or {}, "slots": {}, "verb": ""})


def test_cli_semantic_risk_set_and_crude(tmp_path) -> None:
    ledger_root = tmp_path / "ledgers"
    event_root = tmp_path / "events"
    model_dir = ledger_root / "test-model"
    model_dir.mkdir(parents=True)
    (event_root / "test-model").mkdir(parents=True)
    ref = _decision("t", {"x": 1})
    switched = _decision("t", {"x": 2})

    step0 = [
        # p1: switcher, recovers (analysis)
        _ledger_row("p1", "V", 0, decision_json=ref, signature_hash="hV"),
        _ledger_row("p1", "s3", 0, decision_json=switched, signature_hash="hX"),
        # p2: switcher, censored ran-to-H (analysis)
        _ledger_row("p2", "V", 0, decision_json=ref, signature_hash="hV"),
        _ledger_row("p2", "s3", 0, decision_json=switched, signature_hash="hX"),
        # p3: switcher, censored final-answer (analysis)
        _ledger_row("p3", "V", 0, decision_json=ref, signature_hash="hV"),
        _ledger_row("p3", "s3", 0, decision_json=switched, signature_hash="hX"),
        # p4: hash-only paraphrase (same semantics, other hash) with a recovery event
        _ledger_row("p4", "V", 0, decision_json=ref, signature_hash="hV"),
        _ledger_row("p4", "s3", 0, decision_json=ref, signature_hash="hX-paraphrase"),
        # p5: flagged switcher at injection (h=0, excluded)
        _ledger_row("p5", "V", 0, decision_json=ref, signature_hash="hV"),
        _ledger_row(
            "p5", "s3", 0, decision_json=switched, signature_hash="hX",
            output_text="this looks wrong, verify it",
        ),
        # p6: switcher never run (no sequences)
        _ledger_row("p6", "V", 0, decision_json=ref, signature_hash="hV"),
        _ledger_row("p6", "s3", 0, decision_json=switched, signature_hash="hX"),
        # p7: V unparsed (funnel)
        _ledger_row("p7", "V", 0, parsed=False, decision_json=""),
        _ledger_row("p7", "s3", 0, decision_json=switched, signature_hash="hX"),
    ]
    _write_jsonl(model_dir / "ledger.jsonl", step0)

    tool_json = _decision("t")
    final_json = json.dumps({"tool": "", "args": {}, "slots": {}, "verb": "confirm"})
    rec_rows = [
        _ledger_row("p1", "s3", 1, decision_json=ref, signature_hash="hV"),
        *[_ledger_row("p2", "s3", step, decision_json=tool_json) for step in (1, 2, 3, 4)],
        _ledger_row("p3", "s3", 1, decision_json=tool_json),
        _ledger_row("p3", "s3", 2, decision_json=final_json),
        _ledger_row("p4", "s3", 1, decision_json=ref, signature_hash="hV"),
    ]
    _write_jsonl(model_dir / "recovery_transient.jsonl", rec_rows)

    events = [
        _recover_event("p1", 1),
        _recover_event("p2", None),
        _recover_event("p3", None),
        _recover_event("p4", 1),
    ]
    event_path = event_root / "test-model" / "transient.jsonl"
    with event_path.open("w", encoding="utf-8", newline="\n") as handle:
        for event in events:
            handle.write(json.dumps(event.to_dict()) + "\n")

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"reserve_ids": []}), encoding="utf-8")
    prefixes = tmp_path / "prefixes.jsonl"
    with prefixes.open("w", encoding="utf-8", newline="\n") as handle:
        for pid in ("p1", "p2", "p3", "p4", "p5", "p6", "p7"):
            handle.write(json.dumps(
                {"prefix_id": pid, "domain": "airline", "split": "primary"}
            ) + "\n")

    out = tmp_path / "g4_v2.json"
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--models",
            "test-model",
            "--ledger-root",
            str(ledger_root),
            "--event-root",
            str(event_root),
            "--manifest",
            str(manifest),
            "--prefixes",
            str(prefixes),
            "--g3",
            str(tmp_path / "no-g3.json"),
            "--g4",
            str(tmp_path / "no-g4.json"),
            "--bootstrap-reps",
            "50",
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["stage"] == "g4_recovery_v2"
    assert payload["provenance"] == "multi-role agent panel, author-overseen"
    assert payload["primary_passed"] is False

    name = "test-model|transient_s3"
    group = payload["groups"][name]
    assert group["n"] == 3
    assert group["events"] == 1
    assert abs(group["crude"]["rate"] - 1 / 3) < 1e-12
    assert group["censor_reasons"] == {"parse_fail": 0, "final_answer": 1, "ran_to_H4": 1}
    assert group["recovery_parse_fail_rate"] == 0.0
    assert group["never_run"] == 1

    cell = payload["overlap"][name]
    assert cell["hash_n"] == 4
    assert cell["both"] == 3
    assert cell["hash_only"] == 1
    assert cell["sem_only_flagged"] == 1
    assert cell["sem_only_nonflag_norun"] == 1
    assert cell["semantic_any"] is None  # no g3 fixture: tolerated, not fabricated

    bridge = payload["hash_bridge"][name]
    assert bridge["g4_n"] is None
    assert bridge["analysis_events"] == 1
    assert bridge["hash_only_events"] == 1
    assert bridge["bridge_n_sum"] == bridge["analysis_n"] + 1
    assert out.with_suffix(".md").exists()
