"""Jitter shard tests."""

from __future__ import annotations

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
