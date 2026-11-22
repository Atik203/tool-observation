"""Tests for the stage-18 release builder/validator (P4.7/P5)."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "18_build_release.py"
_spec = importlib.util.spec_from_file_location("build_release_script", _SCRIPT)
assert _spec and _spec.loader
build_release = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_release)

_REPO = Path(__file__).resolve().parents[1]
_TEX = _REPO / "paper" / "toolresults.tex"
_BIB = _REPO / "paper" / "ref.bib"


def _tex() -> str:
    return _TEX.read_text(encoding="utf-8")


def test_stats_helpers_known_values() -> None:
    lo, hi = build_release.wilson(54, 221)
    assert abs(lo - 0.192) < 1e-3 and abs(hi - 0.305) < 1e-3
    lo, hi = build_release.wilson(72, 264)
    assert abs(lo - 0.2226) < 1e-3 and abs(hi - 0.3294) < 1e-3
    assert build_release.wilson(0, 0) == (0.0, 0.0)
    assert abs(build_release.mcnemar_exact_p(190, 50) - 2.1121e-20) / 2.1121e-20 < 1e-5
    assert abs(build_release.mcnemar_exact_p(5, 0) - 0.0625) < 1e-12
    assert abs(build_release.chi2_sf_1(10.31) - 1.323e-3) / 1.323e-3 < 1e-3
    # Full-precision tail check against the stored LRT cells (25.03/3.665e-6 in
    # prose are 2-decimal roundings of the stored values).
    import json as _json

    import pytest as _pytest

    _lrt_path = _REPO / "artifacts" / "analysis" / "inference_robustness.json"
    if not _lrt_path.is_file():
        _pytest.skip("inference_robustness.json absent")
    _lrt = _json.loads(_lrt_path.read_text(encoding="utf-8"))["lrt_robustness"]
    for _cell in _lrt.values():
        if not isinstance(_cell, dict):
            continue
        if "categorical_chi2" in _cell:
            _p = _cell["categorical_recomputed_p"]
            assert abs(build_release.chi2_sf_2(_cell["categorical_chi2"]) - _p) / _p < 1e-9
        if "quadratic_chi2" in _cell:
            _p = _cell["quadratic_recomputed_p"]
            assert abs(build_release.chi2_sf_1(_cell["quadratic_chi2"]) - _p) / _p < 1e-9
    assert abs(build_release.clopper_pearson_lower(9, 9) - 0.6637) < 5e-5
    assert build_release.clopper_pearson_lower(0, 9) == 0.0


def test_table_map_covers_all_labels() -> None:
    labels = sorted(set(re.findall(r"\\label\{(tab:[^}]+)\}", _tex())))
    mapped = sorted(row["label"] for row in build_release.TABLE_MAP)
    assert labels == mapped
    assert len(mapped) == 25


def test_every_float_cited() -> None:
    tex = _tex()
    for label in re.findall(r"\\label\{((?:tab|fig):[^}]+)\}", tex):
        assert tex.count(f"\\ref{{{label}}}") >= 1, label


def test_no_duplicate_labels() -> None:
    labels = re.findall(r"\\label\{([^}]+)\}", _tex())
    assert len(labels) == len(set(labels))


def test_cite_keys_resolve_and_bib_fully_cited() -> None:
    bib = _BIB.read_text(encoding="utf-8")
    entries = set(re.findall(r"@\w+\{([^,\s]+)", bib))
    cited = set(re.findall(r"\\cite\{([^}]+)\}", _tex()))
    used: set[str] = set()
    for group in cited:
        used.update(k.strip() for k in group.split(","))
    assert used <= entries, used - entries
    assert entries <= used, entries - used
    assert "[VERIFY CITATION]" not in bib


def test_amendments_record_integrity() -> None:
    """The prereg record lists every post-freeze amendment and one frozen hash."""
    import json

    amendments = (_REPO / "prereg" / "AMENDMENTS.md").read_text(encoding="utf-8")
    deposit = (_REPO / "prereg" / "DEPOSIT_NOTE.md").read_text(encoding="utf-8")
    manifest = json.loads(
        (_REPO / "data" / "manifests" / "toolresult800_v1.json").read_text(encoding="utf-8")
    )
    frozen = manifest["freeze"]["git_commit"]
    assert frozen == "1673856cc6cd335ae9fd8b0132343082f167077a"
    assert frozen in amendments
    assert frozen in deposit
    assert "commit `1675376`" not in deposit

    status = amendments.split("## Status", 1)[1].split("\n## ", 1)[0]
    for amendment in ("A-004", "A-006", "A-007", "A-008", "A-009", "A-010", "A-011"):
        assert amendment in status, amendment

    for amendment in ("A-007", "A-008", "A-009", "A-010", "A-011"):
        assert re.search(rf"^\| {amendment} \|", amendments, re.M), amendment

    # A-009 must keep the v1 hash-risk-set triple as reconciliation only, not
    # mislabel it as an H=4-censoring estimate, and must name the P6.2 primary.
    a009 = next(line for line in amendments.splitlines() if line.startswith("| A-009 |"))
    assert "v1 hash-risk-set crude triple 27.3/34.7/27.2" in a009
    assert "v2 semantic crude 24.4/32.9/21.3" in a009
    assert "H=4-censoring triple" not in a009


def test_keywords_within_limit() -> None:
    match = re.search(r"\\begin\{keywords\}(.*?)\\end\{keywords\}", _tex(), re.S)
    assert match is not None
    keywords = [k.strip() for k in match.group(1).split("\\sep")]
    assert 1 <= len(keywords) <= 6, keywords


def test_highlights_shape() -> None:
    highlights = (_REPO / "docs" / "submission" / "highlights.md").read_text(encoding="utf-8")
    bullets = [line for line in highlights.splitlines() if line.startswith("- ")]
    assert 3 <= len(bullets) <= 5
    for bullet in bullets:
        core = bullet[2:].strip()
        assert len(core) <= 85, core


def test_pii_scanner_buckets() -> None:
    scan = build_release._scan_text
    hits, placeholders, echoes = scan('{"a": "person_0f41e336893e"}', "x.json")
    assert (hits, placeholders, echoes) == ([], [], [])
    hits, placeholders, echoes = scan('contact atikurrahaman0305@gmail.com', "CITATION.cff")
    assert hits == [] and placeholders == [] and echoes == []
    hits, placeholders, echoes = scan('mail user@example.com here', "t.jsonl")
    assert hits == [] and len(placeholders) == 1
    hits, placeholders, echoes = scan('mail user_509bd4ca4b7c@email.com here', "t.jsonl")
    assert hits == [] and len(echoes) == 1
    hits, placeholders, echoes = scan('call +1 (555) 123-4567 now', "t.jsonl")
    assert hits == [] and any("fictional-phone" in p for p in placeholders)
    hits, _, _ = scan("mail real.person@corp-example.com now", "t.jsonl")
    assert len(hits) == 1
    hits, _, _ = scan('latency 520.01855999697 ms', "t.jsonl")
    assert hits == []
    hits, _, _ = scan('value 0.15659461843846492 ok', "t.jsonl")
    assert hits == []
    hits, _, _ = scan('phone 01777300192 x', "t.jsonl")
    assert len(hits) == 1
    hits, _, _ = scan('write to support@airline.com today', "t.jsonl")
    assert hits == []  # generic role address, noted as placeholder
    hits, _, _ = scan('orcid 0009-0008-2945-4117 listed', "CITATION.cff")
    assert hits == []  # public researcher identifier, masked by design


def test_stage_files_all_present() -> None:
    staged = build_release.stage_files()
    assert len(staged) > 100
    missing = [str(src) for src, _ in staged if not src.is_file()]
    assert missing == []


def test_validate_live_tree_no_rerun() -> None:
    result = build_release.validate_tree(_REPO, rerun=False)
    assert result["ok"], result["failed"]


def test_rerun_producer_list_matches_staged_outputs() -> None:
    staged_names = {dst for _, dst in build_release.stage_files() if dst.startswith("analysis/")}
    for _, out_name, _ in build_release.RERUN_PRODUCERS:
        assert f"analysis/{out_name}" in staged_names
