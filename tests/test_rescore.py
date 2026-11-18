"""Re-score tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from toolobs.infer.ledger import append_ledger_row, read_ledger
from toolobs.infer.parse_output import parse_decision, signature_hash
from toolobs.infer.rescore import rescore_rows
from toolobs.infer.runner import PARSER_VERSION
from toolobs.schemas import LedgerRow

REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPT = REPO_ROOT / "scripts" / "09c_rescore.py"
_spec = importlib.util.spec_from_file_location("rescore_script", _SCRIPT)
assert _spec and _spec.loader
rescore_script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rescore_script)


def test_rescore_recomputes_parser_fields() -> None:
    row = LedgerRow(
        run_id="cal",
        model_id="qwen",
        prefix_id="p0",
        arm="s0",
        step=0,
        prompt_hash="p",
        output_text='{"final_answer": "The reservation was cancelled."}',
        parsed=False,
        latency_ms=1.0,
        cost_usd=0.0,
        timestamp_utc="2026-11-15T00:00:00+00:00",
        parser_status="parse_error",
        signature_hash="old",
        parser_version="toolresult-parser-v1",
    )
    rescored = rescore_rows([row])[0]
    assert rescored.parsed is True
    assert rescored.parser_status == "ok"
    assert rescored.parser_version == PARSER_VERSION
    assert rescored.signature_hash == signature_hash(parse_decision(row.output_text))
    assert '"status":["cancelled"]' in rescored.decision_json
    assert '"action":"cancel"' in rescored.decision_json


def test_in_place_rescore_is_safe(tmp_path) -> None:
    """input == output with --force must not delete the ledger before reading it."""
    path = tmp_path / "ledger.jsonl"
    row = LedgerRow(
        run_id="cal",
        model_id="qwen",
        prefix_id="p0",
        arm="s0",
        step=0,
        prompt_hash="p",
        output_text='{"final_answer": "The reservation was cancelled."}',
        parsed=False,
        latency_ms=1.0,
        cost_usd=0.0,
        timestamp_utc="2026-11-15T00:00:00+00:00",
        parser_status="parse_error",
        signature_hash="old",
        parser_version="toolresult-parser-v1",
    )
    append_ledger_row(path, row)
    result = rescore_script.main(
        ["--input", str(path), "--output", str(path), "--force"]
    )
    assert result == 0
    rows = read_ledger(path)
    assert len(rows) == 1
    assert rows[0].parser_version == PARSER_VERSION
    assert rows[0].parsed is True
