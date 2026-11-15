"""Recovery runner tests with a fake environment."""

from __future__ import annotations

import json

from toolobs.hashing import canonical_json
from toolobs.infer.ledger import read_ledger
from toolobs.infer.parse_output import parse_decision, signature_hash
from toolobs.infer.recovery_run import run_recovery
from toolobs.infer.runner import FakeBackend
from toolobs.schemas import LedgerRow, PerturbationRecord


class _FakeReplay:
    def __init__(self, upstream_dir, domain) -> None:
        self.domain = domain

    def prepare_state(self, messages):
        return {}

    def invoke(self, data, name, arguments):
        return '{"value": "true"}'


def _base_row(prefix_id: str, arm: str, text: str) -> LedgerRow:
    parsed = parse_decision(text)
    return LedgerRow(
        run_id="base",
        model_id="qwen",
        prefix_id=prefix_id,
        arm=arm,
        step=0,
        prompt_hash="p",
        output_text=text,
        parsed=parsed.parsed,
        latency_ms=1.0,
        cost_usd=0.0,
        timestamp_utc="2026-11-15T00:00:00+00:00",
        parser_status=parsed.status,
        signature_hash=signature_hash(parsed),
    )


def test_recovery_marks_r1_on_signature_match(tmp_path) -> None:
    v_text = '{"final_answer": "The order was delivered."}'
    injected_text = '{"tool": "get_order_details", "arguments": {"order_id": "1"}}'
    prefixes = {
        "p0": {
            "domain": "airline",
            "messages": [
                {"role": "system", "content": "policy"},
                {"role": "tool", "name": "get_order_details", "content": "{}"},
            ],
        }
    }
    rendered = {
        ("p0", "s3"): {
            "messages_json": canonical_json(
                [
                    {"role": "system", "content": "policy"},
                    {"role": "tool", "name": "get_order_details", "content": '{"value": "wrong"}'},
                ]
            )
        }
    }
    base_rows = {
        ("p0", "V"): _base_row("p0", "V", v_text),
        ("p0", "s3"): _base_row("p0", "s3", injected_text),
    }
    perturbation = PerturbationRecord(
        prefix_id="p0",
        arm="s3",
        severity=3,
        json_path="$.value",
        true_value="true",
        false_value="wrong",
        criticality="critical",
        expected_action_change=True,
        renderer_version="test",
    )
    backend = FakeBackend([injected_text, v_text])
    stats = run_recovery(
        prefixes=prefixes,
        rendered=rendered,
        base_rows=base_rows,
        perturbations={("p0", "s3"): perturbation},
        backend=backend,
        model_id="qwen",
        regime="transient",
        upstream_dir="unused",
        ledger_path=tmp_path / "recovery.jsonl",
        event_path=tmp_path / "events.jsonl",
        manifest_hash="m" * 64,
        horizon=4,
        replay_factory=_FakeReplay,
        tools_by_domain={
            "airline": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_order_details",
                        "parameters": {"type": "object", "properties": {}},
                    },
                }
            ]
        },
    )
    assert stats.sequences == 1
    assert stats.recovered_r1 == 1
    assert stats.ledger_rows == 2
    assert len(read_ledger(tmp_path / "recovery.jsonl")) == 2
    event = json.loads((tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert event["recovered_step"] == 2
    assert event["endpoint"] == "R1"
    assert event["censored"] is False
