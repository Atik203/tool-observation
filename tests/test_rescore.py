"""Re-score tests."""

from __future__ import annotations

from toolobs.infer.parse_output import parse_decision, signature_hash
from toolobs.infer.rescore import rescore_rows
from toolobs.infer.runner import PARSER_VERSION
from toolobs.schemas import LedgerRow


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
    assert '"status":["cancel"]' in rescored.decision_json
