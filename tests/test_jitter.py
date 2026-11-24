"""Jitter shard tests."""

from __future__ import annotations

from _requires import requires_yaml
import importlib.util
from pathlib import Path
from types import SimpleNamespace

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "09d_jitter.py"
_spec = importlib.util.spec_from_file_location("jitter_script", _SCRIPT)
assert _spec and _spec.loader
jitter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jitter)


def _prefixes() -> dict[str, dict]:
    prefixes = {}
    for domain in ("airline", "retail"):
        for index in range(60):
            prefix_id = f"{domain}-p{index:03d}"
            prefixes[prefix_id] = {"domain": domain, "split": "primary"}
        prefixes[f"{domain}-reserve"] = {"domain": domain, "split": "reserve"}
    return prefixes


def test_selects_forty_per_domain_deterministically() -> None:
    prefixes = _prefixes()
    first = jitter.select_jitter_prefixes(prefixes)
    second = jitter.select_jitter_prefixes(prefixes)
    assert first == second
    assert len(first) == 80
    assert sum(1 for p in first if p.startswith("airline")) == 40
    assert sum(1 for p in first if p.startswith("retail")) == 40
    assert not any("reserve" in prefix_id for prefix_id in first)


def test_stability_counts_signature_matches() -> None:
    base = {
        ("p0", "V"): SimpleNamespace(parsed=True, signature_hash="a"),
        ("p0", "s3"): SimpleNamespace(parsed=True, signature_hash="a"),
        ("p1", "V"): SimpleNamespace(parsed=True, signature_hash="b"),
        ("p1", "s3"): SimpleNamespace(parsed=True, signature_hash="b"),
    }
    rows = [
        SimpleNamespace(prefix_id="p0", arm="V", parsed=True, signature_hash="a"),
        SimpleNamespace(prefix_id="p0", arm="s3", parsed=True, signature_hash="a"),
        SimpleNamespace(prefix_id="p1", arm="V", parsed=True, signature_hash="c"),
        SimpleNamespace(prefix_id="p1", arm="s3", parsed=True, signature_hash="b"),
        SimpleNamespace(prefix_id="p2", arm="V", parsed=True, signature_hash="d"),
        SimpleNamespace(prefix_id="p2", arm="s3", parsed=False, signature_hash=""),
    ]
    report = jitter.stability_report(base, rows)
    assert report["n"] == 4
    assert report["stable"] == 3
    assert report["rate"] == 0.75
    assert report["unparsed"] == 1
    assert report["missing_base"] == 1
    assert report["by_arm"]["V"] == {"n": 2, "stable": 1, "rate": 0.5}
    assert report["by_arm"]["s3"] == {"n": 2, "stable": 2, "rate": 1.0}


@requires_yaml
def test_report_only_recomputes_from_existing_ledgers(tmp_path) -> None:
    import json as _json
    import subprocess
    import sys

    from toolobs.infer.ledger import append_ledger_row
    from toolobs.schemas import LedgerRow

    def _row(prefix: str, arm: str, signature: str) -> LedgerRow:
        return LedgerRow(
            run_id="t",
            model_id="qwen3_5_9b_instruct_awq",
            prefix_id=prefix,
            arm=arm,
            step=0,
            prompt_hash="p",
            output_text="{}",
            parsed=True,
            latency_ms=1.0,
            cost_usd=0.0,
            timestamp_utc="2026-11-15T00:00:00+00:00",
            stage="main",
            parser_status="ok",
            signature_hash=signature,
        )

    base_path = tmp_path / "base.jsonl"
    jitter_path = tmp_path / "jitter.jsonl"
    for prefix, signature in (("p0", "a"), ("p1", "b")):
        append_ledger_row(base_path, _row(prefix, "V", signature))
        append_ledger_row(base_path, _row(prefix, "s3", signature))
    append_ledger_row(jitter_path, _row("p0", "V", "a"))
    append_ledger_row(jitter_path, _row("p1", "V", "b"))
    out = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--model-id",
            "qwen3_5_9b_instruct_awq",
            "--report-only",
            "--base-ledger",
            str(base_path),
            "--out",
            str(jitter_path),
            "--report",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=str(_SCRIPT.parent.parent),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = _json.loads(out.read_text(encoding="utf-8"))
    assert report["mode"] == "report_only"
    assert report["n"] == 2
    assert report["stable"] == 2
    assert report["rate"] == 1.0
    assert report["passed"] is True
