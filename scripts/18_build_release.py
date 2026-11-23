#!/usr/bin/env python
"""Stage 18 — build + validate the ToolResult-800 v1.0.2 public release package.

Builds the staged release tree ``release/ToolResult-800-v1.0.2/`` (gitignored;
uploaded to the DOI record, never committed) and validates it with one
command::

    python scripts/18_build_release.py --build
    python scripts/18_build_release.py --validate [--root DIR] [--rerun]
    make validate-release   # validate against the live tree, no staging needed

What ``--build`` stages (scrubbed derived data only; never raw trajectories,
weights, caches, credentials, or run logs):

- ``manifests/`` — frozen manifest + sidecar, perturbations, source pin.
- ``frozen/prefixes.jsonl`` — 880 scrubbed prefixes with arm observations.
- ``traces/`` — scrubbed ledger extracts (model decisions on scrubbed
  prefixes; prompt text was never logged, only hashes).
- ``labels/`` — audit packets, sheets, instructions, verification record.
- ``analysis/`` — every analysis JSON (+ ``.md`` companions) behind the
  reported tables, including the T2/T3/T4/T6 regenerable JSONs and the
  exploratory P6.7 second-renderer artifact.
- ``packets/`` — T6 blinded packets, sealed maps, and codes.
- ``code/`` — the parser-v4 rescore script and the second-renderer sources
  needed to rebuild the exploratory comparators from the released ledgers.
- ``prereg/``, ``licenses/``, ``costs/``, ``TABLE_MAP.md``, ``VALIDATION.md``,
  ``paper_audit.json`` (the paper label/order snapshot behind L1).

What ``--validate`` checks (works on the staged tree OR the live repo tree):

- L1 (no ledgers needed): required files present; SHA256SUMS complete;
  frozen manifest hash chain (prefixes/perturbations/sample/source
  pin/prereg/field-registry/renderer + sidecar); JSON-to-JSON
  reconciliations behind every measured table (crude triple, v2 bridge,
  severity 7/11/16 from the verification sheets, exact McNemar/LRT
  recomputes, wrong-direction partition, utility counts, g3 totals, H5);
  TABLE_MAP covers all 25 paper tables (main order included); identifier
  re-scan clean. ``paper_audit.json`` carries the paper-side label snapshot,
  so L1 also runs on the package alone.
- L2 (``--rerun``, repo ledgers present): rerun the five analysis producers
  (13/14/15/16/17/16-task-utility; CPU-only, seeded) into a temp dir and
  diff against the released copies ignoring volatile keys
  (``recorded_utc``, ``git_commit``).

PII rule: the repo scrub detector (email + phone patterns) plus BD-mobile,
long digit-run, and card-group patterns over every staged text file.
Allowlist: exactly one corresponding-author contact email in
``CITATION.cff`` (by design); everything else must be clean. A clean
automated scan does NOT replace the pending independent human re-scan
(see ``docs/submission/checklist.md``).

Path rule (v1.0.2): every staged text file also passes a build-time path
scrub before checksums are written. Absolute repository roots and server
home directory prefixes (``G:\\PROJECT\\tool-observation``,
``/home/<user>/tool-observation``, ``/home/<user>``, and drive-rooted
paths) are replaced with ``[repo]``; ``path_rescan.json`` records the
per-file counts, and L1 fails if any path pattern survives.

Provenance: multi-role agent panel, author-overseen (the T6 packet
contents bundled here are single-agent coded, author-overseen, as
disclosed in the paper and D-044).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.harvest.scrub import count_direct_identifiers  # noqa: E402
from toolobs.hashing import sha256_file  # noqa: E402
from toolobs.paths import (  # noqa: E402
    ANALYSIS_DIR,
    AUDIT_DIR,
    CONFIG_DIR,
    COST_DIR,
    FROZEN_DIR,
    INTERIM_DIR,
    MANIFEST_DIR,
    PREREG_DIR,
    RELEASE_DIR,
    RUNS_DIR,
    resolve_repo_path,
)
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402

PACKAGE_NAME = "ToolResult-800-v1.0.2"
PACKAGE_VERSION = "1.0.2"
BUILDER_VERSION = "stage-18 v4"
# Reserved on Zenodo when this version's draft was created (concept DOI
# 10.5281/zenodo.24449466); resolves once the record is published.
PACKAGE_DOI = "10.5281/zenodo.24449882"
CONCEPT_DOI = "10.5281/zenodo.24449466"
VOLATILE_KEYS = frozenset({"recorded_utc", "git_commit"})

# ---------------------------------------------------------------------------
# Table-to-artifact map (source of TABLE_MAP.md; tests assert full coverage)
# ---------------------------------------------------------------------------
# kind: measured (recomputable from a bundled artifact), protocol
# (pre-registered rule, no data artifact), definitional (no data artifact).
# section/table_no: the paper's split — 11 main-text tables (numbered 1-11)
# and 14 supplementary tables (S1-S14, ``\section*{Supplementary tables}``).

TABLE_MAP: list[dict[str, str]] = [
    # --- main text (Tables 1-11) ---
    {"label": "tab:neighbors", "section": "main", "table_no": "1",
     "title": "Nearest-neighbor comparison (11 studies + this study)",
     "artifact": "paper/ref.bib (arXiv IDs verified 2026-11-22)", "keys": "neighbor entries + tab:neighbors rows",
     "producer": "manual (T5; verified against arXiv abs pages)", "kind": "definitional"},
    {"label": "tab:notation", "section": "main", "table_no": "2",
     "title": "Notation (one meaning per symbol in this paper)",
     "artifact": "none (definitional)", "keys": "symbols used in eq:*",
     "producer": "manual (T5 collision renames)", "kind": "definitional"},
    {"label": "tab:arms", "section": "main", "table_no": "3",
     "title": "Arm design and perturbation counts",
     "artifact": "manifests/toolresult800_v1.json; manifests/perturbations.jsonl",
     "keys": "4,400 arms; 2,640 perturbations; 100% s=0 value-set equality",
     "producer": "scripts/06_freeze.py; 07_render.py", "kind": "measured"},
    {"label": "tab:models", "section": "main", "table_no": "4",
     "title": "Target model trio and serving caps",
     "artifact": "configs/models.yaml (pinned revisions); costs/main_cost.json",
     "keys": "repos + revisions + served seq caps 8/4/4",
     "producer": "manual (D-016/D-019; verified 2026-11-22 against HF API)",
     "kind": "measured"},
    {"label": "tab:gate-status", "section": "main", "table_no": "5",
     "title": "Gate outcomes (observed vs criterion)",
     "artifact": "labels/g1_calibration_v3.json; analysis/g3_analysis.json; analysis/g4_recovery_v2.json; labels/scrub_report.json; prereg/AMENDMENTS.md (A-004/A-005); prereg/DEPOSIT_NOTE.md",
     "keys": "G0 provisional; G1 amended pass; G3 3 fails; G4 fail (v2 semantic crude 24.4/32.9/21.3%)",
     "producer": "scripts/08_audit.py; 08c_blind_audit_score.py; 13_analyze.py; 15_recovery_reestimate.py",
     "kind": "measured"},
    {"label": "tab:hypotheses", "section": "main", "table_no": "6",
     "title": "H1-H7 status",
     "artifact": "analysis/prereg_secondary.json; analysis/g3_analysis.json; analysis/g4_recovery_v2.json; analysis/inference_robustness.json",
     "keys": "H5 pooled McNemar b=431/c=93 p=5.3e-53; H4 crude cited from v2",
     "producer": "scripts/13_analyze.py; 16_inference_robustness.py", "kind": "measured"},
    {"label": "tab:primary", "section": "main", "table_no": "7",
     "title": "Primary conditional-logit slope (+ CI column)",
     "artifact": "analysis/g3_analysis.json; analysis/prereg_secondary.json",
     "keys": "pooled 0.877 [0.770,0.998]; 3/3 positive, Holm-significant",
     "producer": "scripts/13_analyze.py", "kind": "measured"},
    {"label": "tab:tiers", "section": "main", "table_no": "8",
     "title": "Tier odds ratios (assigned severity)",
     "artifact": "analysis/prereg_secondary.json",
     "keys": "s1 1.27; s2 4.60; s3 11.21",
     "producer": "scripts/13_analyze.py", "kind": "measured"},
    {"label": "tab:audit", "section": "main", "table_no": "9",
     "title": "Blind audit outcomes (severity/outcome/recovery)",
     "artifact": "labels/blind_audit_result.json; labels/panel_record.json",
     "keys": "severity 88.3% (FAIL); outcome k=.987 PPV 1.00; recovery k=.92/.918",
     "producer": "scripts/08c_blind_audit_score.py; verification panel (D-043)",
     "kind": "measured"},
    {"label": "tab:fieldtypes", "section": "main", "table_no": "10",
     "title": "Field-class switch/silent shares (all seven classes)",
     "artifact": "analysis/field_taxonomy.json",
     "keys": "identifiers 45.0%; money 45.6%; temporal 10/17; count 5/19; other 110/247",
     "producer": "artifacts/analysis/field_taxonomy.py (T5)", "kind": "measured"},
    {"label": "tab:recovery", "section": "main", "table_no": "11",
     "title": "Recovery by H=4 on the v2 semantic risk set (crude primary + KM secondary)",
     "artifact": "analysis/g4_recovery_v2.json; analysis/g4_recovery.json (v1 reconciliation note only)",
     "keys": "crude 24.4/32.9/21.3% (54/221; 116/353; 80/376); KM 28.2/44.6/22.0%; one v1 hash-set reconciliation note 27.3/34.7/27.2% (72/264; 141/406; 112/412) = semantic events + hash-only 18/25/32",
     "producer": "scripts/15_recovery_reestimate.py; 14_recovery_report.py", "kind": "measured"},
    # --- supplementary (Tables S1-S14) ---
    {"label": "tab:supply", "section": "supplement", "table_no": "S1",
     "title": "G0 harvest supply and freeze counts",
     "artifact": "artifacts/audit/g0_report.md; manifests/toolresult800_v1.json; labels/g0_audit_result.json",
     "keys": "13,605 candidates; 5,516 eligible; 99.91% replay; 800+80 sample",
     "producer": "scripts/00_pin_source.py..06_freeze.py", "kind": "measured"},
    {"label": "tab:gates", "section": "supplement", "table_no": "S2",
     "title": "Gate criteria (protocol)",
     "artifact": "docs/GATES.md (protocol, frozen pre-run)", "keys": "G0-G4 thresholds",
     "producer": "protocol (no data artifact)", "kind": "protocol"},
    {"label": "tab:envelope", "section": "supplement", "table_no": "S3",
     "title": "Planned vs executed generation envelope",
     "artifact": "traces/** (21,611 rows); costs/main_cost.json",
     "keys": "13,200 base + 7,211 recovery + 1,200 jitter; 8.9 GPU-h",
     "producer": "scripts/09_run.py; 09a_run_all.py; 09b_recovery.py", "kind": "measured"},
    {"label": "tab:pilot", "section": "supplement", "table_no": "S4",
     "title": "Pilot screening signal (N=60, synthetic)",
     "artifact": "paper (pilot ledger predates frozen pipeline; screening only, D-003)",
     "keys": "54/60 consult; 0/60 placebo jitter; 5/60 error switch; 8.3pp [1.3,15.3]; p=.0625",
     "producer": "pilot (not pooled with confirmatory)", "kind": "measured"},
    {"label": "tab:g1", "section": "supplement", "table_no": "S5",
     "title": "G1 calibration outcomes",
     "artifact": "labels/g1_calibration_v3.json",
     "keys": "parse 96.7-100%; s0-vs-s1 jitter 10.5-13.3%; s3 35.6-56.1%; refusal 0-1.7%",
     "producer": "calibration harness (D-024/D-025/D-026)", "kind": "measured"},
    {"label": "tab:diagnostics", "section": "supplement", "table_no": "S6",
     "title": "Linearity diagnostics (quadratic + categorical LRT)",
     "artifact": "analysis/prereg_secondary.json; analysis/inference_robustness.json",
     "keys": "pooled categorical LRT 25.03 p=3.7e-6; quadratic 10.31 p=1.3e-3",
     "producer": "scripts/13_analyze.py; 16_inference_robustness.py", "kind": "measured"},
    {"label": "tab:missing", "section": "supplement", "table_no": "S7",
     "title": "Missingness by model x arm x parse",
     "artifact": "analysis/missingness_marginal.json; traces/**",
     "keys": "525 = 326 unparsed prose + 199 V-unparsed-filtered; 205 hard + 250 refusals",
     "producer": "scripts/13_analyze.py (T5 reconciliation)", "kind": "measured"},
    {"label": "tab:typology", "section": "supplement", "table_no": "S8",
     "title": "Switch typology (strata mover classes)",
     "artifact": "analysis/switch_typology.json",
     "keys": "47.8% never; 23.9% always; 19.0% dose-responsive; 9.3% placebo",
     "producer": "scripts/13_analyze.py", "kind": "measured"},
    {"label": "tab:armrates", "section": "supplement", "table_no": "S9",
     "title": "Per-arm switch rates",
     "artifact": "analysis/g3_analysis.json",
     "keys": "arm_table any/n per model-arm; s0 19.8/31.9/38.1%",
     "producer": "scripts/13_analyze.py", "kind": "measured"},
    {"label": "tab:panel", "section": "supplement", "table_no": "S10",
     "title": "Verification panel agreement",
     "artifact": "labels/panel_record.json; labels/second_rater_agreement.json",
     "keys": "outcome 158/160; recovery 66/80; severity 114/120 + 108/120; second-rater a=.917/k=.942/k=.918",
     "producer": "verification panel (D-043)", "kind": "measured"},
    {"label": "tab:wrongdir", "section": "supplement", "table_no": "S11",
     "title": "Wrong-direction endpoint (exclusive classes)",
     "artifact": "analysis/wrong_direction.json",
     "keys": "1258/1964 = 64.1% [61.9,66.1]; caught 30; ambiguous 676",
     "producer": "scripts/17_wrong_direction.py", "kind": "measured"},
    {"label": "tab:utility", "section": "supplement", "table_no": "S12",
     "title": "Task-utility endpoint (exploratory, single-agent coded)",
     "artifact": "analysis/new_evidence.json; packets/task_utility_*.json",
     "keys": "adequate s0 55.7% -> s3 28.7%; harmful 15.7% -> 38.3%; McNemar b=42/c=11 p=2.2e-5; k=.92 (36/38)",
     "producer": "scripts/16_task_utility.py (T6; GPU 0.0h)", "kind": "measured"},
    {"label": "tab:recovery_all", "section": "supplement", "table_no": "S13",
     "title": "Recovery all cells (transient + persistent, v2 KM)",
     "artifact": "analysis/g4_recovery_v2.json",
     "keys": "9-cell n/Events/crude/KM/RMST/t12; t12 range 4.7-10.9",
     "producer": "scripts/15_recovery_reestimate.py", "kind": "measured"},
    {"label": "tab:sensitivity", "section": "supplement", "table_no": "S14",
     "title": "Recovery sensitivity (censoring/never-run/parse bounds)",
     "artifact": "analysis/g4_recovery_v2.json",
     "keys": "never-run bounds <39%; parse-as-recovery 66.3% Ministral uninformative upper bound",
     "producer": "scripts/15_recovery_reestimate.py", "kind": "measured"},
]

# ---------------------------------------------------------------------------
# Staged payload: (repo-relative source, package-relative destination)
# ---------------------------------------------------------------------------

AUDIT_FILES = [
    "g0_report.md", "g0_audit_result.json", "g0_audit_packet.csv",
    "g0_audit_sheet.csv", "g0_audit_instructions.md",
    "g0_audit_ai_preaudit.csv", "g0_audit_ai_preaudit.json",
    "g1_calibration_v3.json", "calibration_render_report.json",
    "relevance_report.json", "replay_report.json", "render_report.json",
    "sample_report.json", "scrub_report.json",
    "severity_audit_packet.csv", "severity_audit_sheet.csv",
    "severity_audit_instructions.md", "outcome_audit_packet.csv",
    "outcome_audit_sheet.csv", "outcome_audit_instructions.md",
    "recovery_audit_packet.csv", "recovery_audit_sheet.csv",
    "recovery_audit_instructions.md", "blind_audit_result.json",
    "audit_packets_result.json", "second_rater_agreement.json",
    "human_verification.json",
    "verification/outcome_verification.csv",
    "verification/recovery_verification.csv",
    "verification/severity_verification.csv",
    "verification/severity_verification_part1.csv",
    "verification/severity_verification_part2.csv",
    "verification/severity_verification_part3.csv",
    "verification/severity_verification_slices.csv",
    "verification/severity_verification_report.md",
    "verification/panel_record.json",
    "verification_workbook.md",
    "blind/README.md",
    "blind/rater1_severity_unlabeled.csv", "blind/rater2_severity_unlabeled.csv",
    "blind/rater3_severity_unlabeled.csv",
    "blind/rater1_outcome_unlabeled.csv", "blind/rater2_outcome_unlabeled.csv",
    "blind/rater1_recovery_unlabeled.csv", "blind/rater2_recovery_unlabeled.csv",
    "blind/severity_items_unlabeled.jsonl", "blind/outcome_items_unlabeled.jsonl",
    "blind/recovery_items_unlabeled.jsonl",
]

ANALYSIS_JSONS = [
    "g3_analysis.json", "g3_analysis_all880.json", "g3_report.md",
    "g3_partial_pipeline_check.json",
    "g4_recovery.json", "g4_recovery.md", "g4_partial_pipeline_check.json",
    "g4_partial_pipeline_check.md", "g4_recovery_v2.json", "g4_recovery_v2.md",
    "recovery_deep.json", "recovery_deep.md",
    "prereg_secondary.json", "prereg_secondary.md",
    "severity_sensitivity.json", "inference_robustness.json",
    "wrong_direction.json", "new_evidence.json",
    "rowlevel_refits.json", "renderer2.json",
    "field_taxonomy.json", "field_taxonomy.md",
    "switch_typology.json", "missingness_marginal.json",
    "jitter_stability_llama_3_1_8b_instruct_awq.json",
    "jitter_stability_ministral_3_8b_instruct_2512_awq.json",
    "jitter_stability_qwen3_5_9b_instruct_awq.json",
]

TASK_UTILITY_FILES = [
    "task_utility_packets.json", "task_utility_map.json",
    "task_utility_s0_packets.json", "task_utility_s0_map.json",
    "task_utility_codes.json", "task_utility_s0_codes.json",
    "task_utility_recodes_packets.json", "task_utility_recodes_map.json",
    "task_utility_recodes.json",
]

# (repo-relative source, package-relative destination) for the code needed to
# rebuild the released derived artifacts from the released ledgers. The full
# repository is the related code identifier; these files make the parser-v4 and
# second-renderer comparators rebuildable without cloning.
CODE_FILES: list[tuple[str, str]] = [
    ("scripts/09c_rescore.py", "code/09c_rescore.py"),
    ("scripts/20_renderer2.py", "code/20_renderer2.py"),
    ("src/toolobs/analysis/renderer2.py", "code/toolobs/analysis/renderer2.py"),
    ("src/toolobs/render/render2.py", "code/toolobs/render/render2.py"),
]

# (script, staged output name, extra argv) for --rerun L2 validation.
RERUN_PRODUCERS: list[tuple[str, str, list[str]]] = [
    ("scripts/15_recovery_reestimate.py", "g4_recovery_v2.json", []),
    ("scripts/14_severity_sensitivity.py", "severity_sensitivity.json", []),
    ("scripts/19_rowlevel_refits.py", "rowlevel_refits.json", []),
    ("scripts/16_inference_robustness.py", "inference_robustness.json", []),
    ("scripts/17_wrong_direction.py", "wrong_direction.json", []),
    ("scripts/16_task_utility.py", "new_evidence.json", ["analyze"]),
]

# Provenance notes for artifacts whose documentation text was corrected after
# the recorded generation run (numeric content unchanged). Build-time hashes
# bind the distributed bytes to the recorded commit.
ARTIFACT_PROVENANCE_NOTES: list[dict[str, str]] = [
    {
        "artifact": "analysis/rowlevel_refits.json",
        "generated_commit": "8e6f536",
        "sha256": "965805eac2791a0d40757777d537db4205c4d4c046d6b2732c2f272c9dbedfcb",
        "note": "Generated at 8e6f536 (the commit recorded inside the artifact, "
        "2026-11-23 02:24 +0600). The reconciliation.note wording is the "
        "text-only correction later committed as 7f0169d ('prefix-resampling "
        "sensitivity, design_valid=false, not a cluster bootstrap'); it was "
        "present in the working tree at generation, so the recorded commit and "
        "the note text differ by ten minutes of history. No number changed. The "
        "SHA-256 above is the distributed file and is re-checked at build time; "
        "a rerun at the current tree reproduces every field except "
        "recorded_utc/git_commit.",
    },
]

# ---------------------------------------------------------------------------
# Statistics helpers (stdlib recomputation for cross-checks)
# ---------------------------------------------------------------------------

def wilson(x: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = x / n
    d = 1.0 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - m) / d), min(1.0, (c + m) / d))


def mcnemar_exact_p(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return 2.0 * sum(math.comb(n, j) for j in range(k + 1)) / 2.0**n


def chi2_sf_1(x: float) -> float:
    return math.erfc(math.sqrt(x / 2.0))


def chi2_sf_2(x: float) -> float:
    return math.exp(-x / 2.0)


def clopper_pearson_lower(x: int, n: int, alpha: float = 0.05) -> float:
    if x == 0:
        return 0.0
    if x == n:
        return (alpha / 2.0) ** (1.0 / n)
    from statistics import NormalDist  # local import: cheap, stdlib
    _ = NormalDist
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        tail = sum(math.comb(n, j) * mid**j * (1 - mid) ** (n - j) for j in range(x, n + 1))
        if tail > alpha / 2.0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2.0


# ---------------------------------------------------------------------------
# PII re-scan
# ---------------------------------------------------------------------------

_EMAIL_ALLOWLIST_FILES = frozenset({"CITATION.cff", "DATA_CARD.md"})

_BD_MOBILE = re.compile(r"(?<![\w.])01\d{9}(?![\d.])")
# Standalone 13-19 digit runs (PAN-shaped), grouped 4x4, or BD mobiles.
# Decimal fractions (0.15659461843846492) are excluded by the '.' guards.
_CARD_RUN = re.compile(r"(?<![\d.])\d{13,19}(?![\d.])")
_CARD_GROUPED = re.compile(r"(?<![\d.])(?:\d{4}[- ]){3}\d{4}(?![\d.])")
_HEX_HASH = re.compile(r"\b[0-9a-f]{64}\b|\b[0-9a-f]{40}\b|\b[0-9a-f]{32}\b")
# ORCID iDs are public researcher identifiers published by design (byline,
# CITATION.cff, authorship record). Shape 4-4-4-3+check digit, unlike PANs.
_ORCID_RE = re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b")
_EMAIL_RE = re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])")
# RFC 2606 reserved domains: model-hallucinated form placeholders, not PII.
_RESERVED_DOMAINS = frozenset({"example.com", "example.org", "example.net"})
# Generic role local-parts: not attributable to a person (only reached for
# non-reserved domains; reserved-domain addresses bucket above regardless).
_ROLE_LOCALS = frozenset({
    "support", "info", "contact", "admin", "help", "service", "noreply",
    "no-reply", "hello", "team", "customerservice", "customer-service",
})
# Synthetic scrubber tokens embedded in an address: pseudonymous echo of an
# already-scrubbed value (the PII map is never released).
_TOKEN_RE = re.compile(r"\b(?:person|email|phone|address|dob|payment|user|pii)_[0-9a-f]{12}\b")
_NANP_RE = re.compile(
    r"(?<!\w)(?:\+\d{1,3}[\s.-]?)?(?:\((\d{3})\)|(\d{3}))[\s.-](\d{3})[\s.-](\d{4})(?!\w)"
)


def _scan_text(text: str, rel: str) -> tuple[list[str], list[str], list[str]]:
    """Returns (hits, placeholders, synthetic_echoes) for one text blob."""
    hits: list[str] = []
    placeholders: list[str] = []
    echoes: list[str] = []
    masked = _HEX_HASH.sub("<hash>", text)
    masked = _ORCID_RE.sub("<orcid>", masked)
    allowlisted = rel in _EMAIL_ALLOWLIST_FILES
    if not allowlisted:
        detected = count_direct_identifiers(masked)
        email_matches = list(_EMAIL_RE.finditer(masked))
        nanp_matches = list(_NANP_RE.finditer(masked))
        for match in email_matches:
            address = match.group(0)
            local, _, domain = address.partition("@")
            domain = domain.lower()
            if domain in _RESERVED_DOMAINS or domain.endswith(".example"):
                placeholders.append(f"{rel}: {address[:60]}")
            elif _TOKEN_RE.search(local):
                echoes.append(f"{rel}: {address[:60]}")
            elif local.lower() in _ROLE_LOCALS:
                placeholders.append(f"{rel}: {address[:60]}")
            else:
                hits.append(f"{rel}: email-like {address[:40]}")
        accounted = len(email_matches)
        for match in nanp_matches:
            area = match.group(1) or match.group(2) or ""
            exch = match.group(3) or ""
            sub = match.group(4) or ""
            _ = area
            if exch == "555" or (exch == "123" and sub == "4567"):
                placeholders.append(f"{rel}: fictional-phone {match.group(0)}")
            else:
                hits.append(f"{rel}: phone-like {match.group(0)}")
            accounted += 1
        if detected > accounted:
            # The repo scrub detector fired on something neither explicit
            # rule covers: genuine anomaly, fail loudly.
            hits.append(f"{rel}: repo scrub detector fired ({detected - accounted} unaccounted)")
    for match in _BD_MOBILE.finditer(masked):
        hits.append(f"{rel}: BD-mobile-like {match.group(0)}")
    for pattern in (_CARD_RUN, _CARD_GROUPED):
        for match in pattern.finditer(masked):
            token = re.sub(r"\D", "", match.group(0))
            if token.startswith("0" * len(token)):
                continue
            hits.append(f"{rel}: digit-run {match.group(0)[:24]}")
    return hits, placeholders, echoes


def pii_rescan(root: Path) -> tuple[list[str], list[str], list[str], list[str]]:
    """Scan every staged text file. Returns (hits, placeholders, echoes, allowlisted)."""
    hits: list[str] = []
    placeholders: list[str] = []
    echoes: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in ("SHA256SUMS", "release_record.json"):
            continue
        if path.suffix.lower() not in (
            ".json", ".jsonl", ".csv", ".md", ".txt", ".cff", ".yaml", ".yml",
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() in (".json", ".jsonl"):
            # Scan string values only (keys hold schema names, never PII).
            values = []
            chunks = [text] if path.suffix.lower() == ".json" else text.splitlines()
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue
                try:
                    values.append(json.dumps(json.loads(chunk)))
                except ValueError:
                    values.append(chunk)
            for value in values:
                h, p, e = _scan_text(value, rel)
                hits.extend(h)
                placeholders.extend(p)
                echoes.extend(e)
        else:
            h, p, e = _scan_text(text, rel)
            hits.extend(h)
            placeholders.extend(p)
            echoes.extend(e)
    allowlisted = sorted(
        rel for rel in _EMAIL_ALLOWLIST_FILES if (root / rel).is_file()
    )
    return hits, placeholders, echoes, allowlisted


# ---------------------------------------------------------------------------
# Release-copy redaction (P6.4 / D-046, v1.0.1)
# ---------------------------------------------------------------------------

# One scrubber-artifact identity class survived the harvest scrub: an
# already-tokenised local part followed by an unsanitized given-name+digits
# local part on a reserved example domain. The frozen source is bit-identical
# under the manifest hash and is never distributed; every distributed copy is
# redacted here, at build time, so a rebuild cannot reintroduce the class.
REDACTION_TOKEN = "person_redacted_0001"

# Generic detector: no fragment literal is stored in the repository. The bare
# ``person_<12 hex>`` token is a legitimate pseudonym (the PII map is never
# released) and is left intact; only the token+unsanitized-local-part email
# form is replaced.
_SCRUBBER_RESIDUAL = re.compile(
    r"\bperson_[0-9a-f]{12}\.[A-Za-z]+[0-9]+@(?:example\.(?:com|org|net))\b"
)
REDACTION_PATTERNS: tuple[re.Pattern[str], ...] = (_SCRUBBER_RESIDUAL,)

REDACTION_NOTE = (
    "The frozen source is not distributed and remains bit-identical under its "
    "manifest hash. Every staged release file passes through this redaction "
    "before checksums are written; the count below is per string occurrence. "
    "The matched class is a scrubber token followed by an unsanitized "
    "given-name+digits local part on a reserved example domain."
)

_TEXT_NAMES = frozenset({"LICENSE", "LICENSE-DOCS", "TAU_BENCH_LICENSE_MIT"})
_TEXT_SUFFIXES = frozenset({
    ".json", ".jsonl", ".csv", ".md", ".txt", ".cff", ".yaml", ".yml",
})


def redact_text(text: str) -> tuple[str, int]:
    """Apply the generic release-copy redaction patterns to one text blob.

    Returns the redacted text and the number of replaced occurrences.
    Deterministic and idempotent: the synthetic token matches no pattern.
    """
    n = 0
    for pattern in REDACTION_PATTERNS:
        n += len(pattern.findall(text))
        text = pattern.sub(REDACTION_TOKEN, text)
    return text, n


def apply_redactions(root: Path) -> dict:
    """Redact every staged text file under ``root`` in place.

    Returns a metadata dict safe to publish (no rule strings, no fragment).
    """
    changed: dict[str, int] = {}
    total = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name not in _TEXT_NAMES and path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        try:
            # Read/write bytes, not text: read_text/write_text would normalise
            # every line ending on Windows and change all 880 lines instead of
            # only the redacted strings.
            text = path.read_bytes().decode("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        redacted, n = redact_text(text)
        if n:
            path.write_bytes(redacted.encode("utf-8"))
            changed[path.relative_to(root).as_posix()] = n
            total += n
    return {
        "token": REDACTION_TOKEN,
        "n_occurrences": total,
        "n_files": len(changed),
        "files": changed,
        "rule": "scrubber token + unsanitized given-name+digits local part on "
        "a reserved example domain replaced by a synthetic identity token",
        "frozen_source_unchanged": True,
        "note": REDACTION_NOTE,
    }


# ---------------------------------------------------------------------------
# Release-copy path scrub (v1.0.2)
# ---------------------------------------------------------------------------

# v1.0.1 leaked the build machine's repository root and the GPU server home
# directory into distributed provenance fields (``ledger`` keys in four
# analysis JSONs and ``g1_calibration_v3.json``) and one generated report
# (``labels/g0_report.md``). The artifacts themselves are unchanged; only the
# staged release copies are scrubbed, at build time, so a rebuild cannot
# reintroduce the class. ``[repo]`` is deliberately not a valid path prefix,
# which makes a second application a no-op (idempotent) and keeps the
# residual structure (``[repo]/data/runs/...``) readable.
PATH_SCRUB_TOKEN = "[repo]"
_WIN_SEP = r"[\\/]{1,2}"

PATH_SCRUB_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Drive-rooted checkout under the project parent, with backslashes or
    # forward slashes and one or two separators (JSON escaping).
    re.compile(
        r"[A-Za-z]:" + _WIN_SEP + r"PROJECT" + _WIN_SEP + r"tool-observation"
    ),
    # A user-home checkout on a drive, ending in the repository directory.
    re.compile(
        r"[A-Za-z]:" + _WIN_SEP + r"Users" + _WIN_SEP
        + r"[^\\/\s\"'`]+" + _WIN_SEP + r"tool-observation"
    ),
    # Server home plus the repository checkout, then a bare server home.
    re.compile(r"/home/[A-Za-z0-9._-]+/tool-observation"),
    re.compile(r"/home/[A-Za-z0-9._-]+"),
    # Any remaining absolute drive path with at least two segments. The
    # lookbehind and the two-character segment rule keep JSON-escaped prose
    # such as "DC:\n" or "THY2DG:\n" from matching; no such false positive
    # would be scrubbed, but the detector shares the same guard.
    re.compile(
        r"(?<![A-Za-z0-9])[A-Za-z]:" + _WIN_SEP
        + r"[^\\/\s\"'`<>|]{2,}(?:\\{1,2}[^\\/\s\"'`<>|]{2,})+"
    ),
)

# Residual detector used by the build and by L1. It is intentionally broader
# than the scrub patterns where the shapes are unambiguous (``/home/`` and
# ``/Users/``), and path-shaped otherwise.
PATH_LEAK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"/home/"),
    re.compile(r"/Users/"),
    re.compile(r"[A-Za-z]:" + _WIN_SEP + r"PROJECT" + _WIN_SEP + r"tool-observation"),
    re.compile(
        r"(?<![A-Za-z0-9])[A-Za-z]:" + _WIN_SEP + r"Users" + _WIN_SEP
        + r"[^\\/\s\"'`]+"
    ),
    re.compile(
        r"(?<![A-Za-z0-9])[A-Za-z]:\\{1,2}(?:[^\\\s\"'`<>|]{2,}\\)+"
    ),
)

PATH_SCRUB_NOTE = (
    "Absolute repository roots and server home directory prefixes in staged "
    "release copies are replaced by [repo] at build time; the frozen and "
    "generated source artifacts are not modified. The replacement is "
    "deterministic and idempotent, and path_rescan.json records the per-file "
    "occurrence counts and confirms that no path pattern survives."
)


def scrub_paths(text: str) -> tuple[str, int]:
    """Apply the release-copy path scrub to one text blob.

    Returns the scrubbed text and the number of replaced occurrences.
    Deterministic and idempotent: ``[repo]`` matches no pattern.
    """
    n = 0
    for pattern in PATH_SCRUB_PATTERNS:
        n += len(pattern.findall(text))
        text = pattern.sub(PATH_SCRUB_TOKEN, text)
    return text, n


def scan_path_leaks(text: str) -> list[str]:
    """Return the absolute-path patterns still present in ``text``."""
    return [pattern.pattern for pattern in PATH_LEAK_PATTERNS if pattern.search(text)]


def apply_path_scrub(root: Path) -> tuple[dict, list[str]]:
    """Scrub every staged text file under ``root`` in place.

    Returns (metadata dict safe to publish, residual hit list).
    """
    changed: dict[str, int] = {}
    total = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name not in _TEXT_NAMES and path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        try:
            text = path.read_bytes().decode("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scrubbed, n = scrub_paths(text)
        if n:
            path.write_bytes(scrubbed.encode("utf-8"))
            changed[path.relative_to(root).as_posix()] = n
            total += n
    stats = {
        "token": PATH_SCRUB_TOKEN,
        "n_occurrences": total,
        "n_files": len(changed),
        "files": changed,
        "rule": "absolute repository roots and server home directory prefixes "
        "replaced by [repo] in staged release copies",
        "frozen_source_unchanged": True,
        "note": PATH_SCRUB_NOTE,
    }
    return stats, residual_path_leaks(root)


def residual_path_leaks(root: Path) -> list[str]:
    """Scan every staged text file for surviving absolute paths."""
    hits: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name not in _TEXT_NAMES and path.suffix.lower() not in _TEXT_SUFFIXES:
            continue
        try:
            text = path.read_bytes().decode("utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root).as_posix()
        for match in scan_path_leaks(text):
            hits.append(f"{rel}: {match}")
    return hits


# ---------------------------------------------------------------------------
# Staging
# ---------------------------------------------------------------------------

TAU_BENCH_MIT = """MIT License

Copyright (c) 2024 Sierra

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

MODEL_LICENSES_MD = """# Model output licenses — ToolResult-800 v1.0.2

Verified 2026-11-22 against the HuggingFace API for the exact pinned
revisions in `configs/models.yaml` (revision SHAs match the served weights).

| Served model | Repository | Pinned revision (sha) | License tag |
|---|---|---|---|
| Qwen3.5-9B-AWQ-4bit | cyankiwi/Qwen3.5-9B-AWQ-4bit | e4d2d39cede8c5d1716d824cd843e2889c648083 | apache-2.0 |
| Ministral-3-8B-Instruct-2512-AWQ-4bit | cyankiwi/Ministral-3-8B-Instruct-2512-AWQ-4bit | 563842192acb68a00b8864e3bfa5a3e740ece90c | apache-2.0 |
| Llama-3.1-8B-Instruct-AWQ-INT4 | hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4 | db1f81ad4b8c7e39777509fac66c652eb0a52f91 | llama3.1 |

Base weights: Qwen/Qwen3.5-9B, mistralai/Ministral-3-8B-Instruct-2512,
meta-llama/Llama-3.1-8B-Instruct (described in the Llama 3 herd report,
cited in the paper).

What is released: only short derived decision strings (tool calls with
scrubbed synthetic arguments, or final-answer action verbs) produced on
scrubbed frozen prefixes. No weights, adapters, caches, or GPU artifacts
are released.

Redistribution basis: Apache-2.0 outputs carry no redistribution
restriction; Llama 3.1 Community License governs model use and its
acceptable-use policy, and the released decision strings are user-owned
derived text containing no model weights. See `ATTRIBUTION.md` for the
consolidated notices. Authors confirm with the target venue at submission if
its policy requires more.
"""


def _ledger_extract_paths() -> list[tuple[Path, str]]:
    staged: list[tuple[Path, str]] = []
    for path in sorted(RUNS_DIR.rglob("*.jsonl")):
        rel = path.relative_to(RUNS_DIR)
        if "_backup" in rel.parts:
            continue
        if "calibration" in rel.parts and "calibration_v3" not in rel.parts:
            continue  # superseded first calibration pass; v3 is the reported one
        name = path.name
        if (
            name == "ledger.jsonl"
            or name.startswith(("recovery_", "jitter"))
            or name in ("persistent.jsonl", "transient.jsonl")
        ):
            staged.append((path, f"traces/{rel.as_posix()}"))
    return staged


def stage_files() -> list[tuple[Path, str]]:
    """Enumerate (source, package-relative destination) for the payload."""
    staged: list[tuple[Path, str]] = []
    staged.append((REPO_ROOT / "docs" / "DATA_CARD.md", "DATA_CARD.md"))
    staged.append((REPO_ROOT / "CITATION.cff", "CITATION.cff"))
    staged.append((REPO_ROOT / "DATA_LICENSE.md", "DATA_LICENSE.md"))
    staged.append((REPO_ROOT / "ATTRIBUTION.md", "ATTRIBUTION.md"))
    staged.append((REPO_ROOT / "LICENSE", "LICENSE"))
    staged.append((REPO_ROOT / "LICENSE-DOCS", "LICENSE-DOCS"))
    for name in ("PREREGISTRATION.md", "AMENDMENTS.md", "DEPOSIT_NOTE.md"):
        staged.append((PREREG_DIR / name, f"prereg/{name}"))
    staged.append((MANIFEST_DIR / "toolresult800_v1.json", "manifests/toolresult800_v1.json"))
    staged.append((MANIFEST_DIR / "toolresult800_v1.sha256.json", "manifests/toolresult800_v1.sha256.json"))
    staged.append((MANIFEST_DIR / "perturbations.jsonl", "manifests/perturbations.jsonl"))
    staged.append((MANIFEST_DIR / "source_pin.json", "manifests/source_pin.json"))
    staged.append((FROZEN_DIR / "prefixes.jsonl", "frozen/prefixes.jsonl"))
    for name in AUDIT_FILES:
        staged.append((AUDIT_DIR / name, f"labels/{name}"))
    for name in ANALYSIS_JSONS:
        staged.append((ANALYSIS_DIR / name, f"analysis/{name}"))
    for name in TASK_UTILITY_FILES:
        staged.append((ANALYSIS_DIR / name, f"packets/{name}"))
    staged.append((COST_DIR / "main_cost.json", "costs/main_cost.json"))
    for src, dst in CODE_FILES:
        staged.append((REPO_ROOT / src, dst))
    staged.extend(_ledger_extract_paths())
    return staged


def paper_audit_json() -> dict:
    """Paper-side facts L1 needs, snapshotted so the package validates alone."""
    tex_path = REPO_ROOT / "paper" / "toolresults.tex"
    tex = tex_path.read_text(encoding="utf-8")
    supp_at = tex.index("\\section*{Supplementary tables}")
    main_labels = list(
        dict.fromkeys(re.findall(r"\\label\{(tab:[^}]+)\}", tex[:supp_at]))
    )
    supp_labels = list(
        dict.fromkeys(re.findall(r"\\label\{(tab:[^}]+)\}", tex[supp_at:]))
    )
    marker = "Run-risk-set (v1) reconciliation"
    note_count = tex.count(marker)
    outside = tex
    if note_count == 1:
        start = tex.index(marker)
        end = tex.find("\n\n", start)
        if end != -1:
            outside = tex[:start] + tex[end:]
    return {
        "paper": "paper/toolresults.tex",
        "sha256": sha256_file(tex_path),
        "main_labels": main_labels,
        "supplement_labels": supp_labels,
        "recovery_note": {
            "marker": marker,
            "count": note_count,
            "v1_crude_outside_note": "27.3/34.7/27.2" in outside,
            "v1_km_outside_note": "32.4/47.6/28.2" in outside,
        },
        "note": "Snapshot of the paper-side labels and the single v1 recovery "
        "reconciliation note, written at build time. L1 checks TABLE_MAP "
        "against this snapshot so --validate --root <package> needs no "
        "repository checkout.",
    }


def table_map_md() -> str:
    n_main = sum(1 for row in TABLE_MAP if row["section"] == "main")
    n_supp = sum(1 for row in TABLE_MAP if row["section"] == "supplement")
    lines = [
        "# Table-to-artifact map — ToolResult-800 v1.0.2",
        "",
        f"All {len(TABLE_MAP)} paper tables are mapped: {n_main} main-text tables",
        f"(Table 1–{n_main}) and {n_supp} supplementary tables (S1–S{n_supp},",
        "the paper's `\\section*{Supplementary tables}`). Every table traces to a",
        "bundled artifact (or is marked definitional/protocol with no data",
        "artifact). Kinds: **measured** (recomputable from the listed artifact),",
        "**protocol** (pre-registered rule), **definitional** (no data artifact).",
        "",
        "| Position | Label | Title | Kind | Source artifact(s) | Key fields | Producer |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in TABLE_MAP:
        position = f"Table {row['table_no']}"
        lines.append(
            f"| {position} | `{row['label']}` | {row['title']} | {row['kind']} | "
            f"{row['artifact']} | {row['keys']} | {row['producer']} |"
        )
    lines += [
        "",
        "Measured tables are rechecked by `scripts/18_build_release.py --validate`",
        "(L1 reconciliations + L2 producer reruns). Definitional and protocol",
        "tables have no data artifact by construction. `tab:recovery` reports the",
        "v2 semantic risk set; the v1 run-time hash set appears only in the single",
        "reconciliation note and is checked as such.",
        "",
    ]
    return "\n".join(lines)


def ledger_hashes_json(root: Path) -> dict:
    """SHA-256 record for every distributed ledger extract (post-redaction)."""
    rows: list[dict[str, object]] = []
    for path in sorted((root / "traces").rglob("*.jsonl")):
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    return {
        "stage": "ledger_extracts",
        "generated_utc": utc_now(),
        "n_files": len(rows),
        "total_bytes": sum(int(row["bytes"]) for row in rows),
        "note": "SHA-256 of every distributed ledger extract after the v1.0.2 "
        "release-copy redaction (D-046) and path scrub. Base decision ledgers, recovery step "
        "and event ledgers, jitter runs, the reported G1 calibration_v3 runs, "
        "and the exploratory P6.7 second-renderer runs (D-048). The superseded "
        "first calibration pass and *_backup files are excluded; the raw run "
        "tree is not distributed.",
        "files": rows,
    }


def validation_md() -> str:
    return f"""# Validation — ToolResult-800 v{PACKAGE_VERSION}

One-command validation (no GPU, stdlib Python only):

    python scripts/18_build_release.py --validate --root release/{PACKAGE_NAME}
    python scripts/18_build_release.py --validate --root release/{PACKAGE_NAME} --rerun
    make validate-release   # same checks against the live tree

- **L1 (this package alone):** required files present; `SHA256SUMS`
  complete (every file listed exactly once); frozen manifest hash chain
  (prefixes / perturbations / sample / source pin / preregistration /
  field registry / renderer + sidecar); JSON-to-JSON reconciliations
  behind every measured table (v2 semantic crude/KM recovery triple plus
  the single v1 hash-set reconciliation, hash-vs-semantic bridge, severity
  7/11/16 re-derived from the verification sheets, exact McNemar and LRT
  recomputes, wrong-direction partition, utility counts, g3 totals, H5);
  `TABLE_MAP.md` covers all 25 paper tables (11 main, ordered, + S1–S14);
  identifier re-scan clean; absolute-path re-scan clean (v1.0.2). The
  paper-side label order and the single v1 reconciliation note are carried
  in `paper_audit.json`, so this level needs no repository checkout.
- **L2 (`--rerun`, needs the repo with run ledgers):** reruns the six
  CPU-only analysis producers (including `19_rowlevel_refits.py`, P6.3) and
  diffs the rebuilt JSONs against the released copies (volatile
  `recorded_utc`/`git_commit` ignored).

The exploratory P6.7 second-renderer artifact is included: `analysis/renderer2.json`,
its three ledgers under `traces/renderer2/`, and the code to rebuild the parser-v4
comparators (`code/09c_rescore.py`, `code/20_renderer2.py`, and the two
`toolobs` modules). `traces/ledger_hashes.json` records the SHA-256 of every
distributed ledger, including the renderer-2 extracts; `renderer2.json` also
records the same hashes, so the two records must agree.

Artifact provenance: `analysis/rowlevel_refits.json` was generated at commit
`8e6f536` (SHA-256 `965805ea…dbedfcb`, recorded in `release_record.json`).
Its `reconciliation.note` carries the text-only correction later committed as
`7f0169d` (prefix-resampling sensitivity, `design_valid: false`, not a cluster
bootstrap); the wording was in the working tree at generation, so the recorded
commit lags the note text by ten minutes of history. No number changed, and a
rerun at the current tree reproduces every field except
`recorded_utc`/`git_commit`.

`path_rescan.json` records the v1.0.2 build-time path scrub: absolute
repository roots and server home directory prefixes are replaced by
`[repo]` in every staged text file (16 occurrences in 8 files in this
build, including `labels/g1_calibration_v3.json` and the `ledger` fields
of four analysis JSONs). The generated artifacts are not modified; only
the distributed copies are. Counts are per occurrence; the L1
`path-rescan` check requires zero surviving matches.

`frozen/prefixes.jsonl` is the redacted release derivative: the builder
replaces every match of the scrubber-artifact identity class in every staged
file at build time (D-046), records the counts here and in
`release_record.json`, and checks the redacted file against the recorded
release hash. The frozen source is not distributed and stays bit-identical
under its manifest hash.

A clean automated scan does not replace the pending independent human
PII re-scan before public release (see `docs/submission/checklist.md`).
`pii_rescan.json` lists every placeholder/echo occurrence (duplicates retained:
one entry per scanned value, so a string echoed in both `decision_json` and
`output_text` counts twice); `n_*` counts match the list lengths, and
`n_redactions` counts the occurrences replaced before the scan.
"""


def release_changelog_md() -> str:
    return """# Changelog — ToolResult-800

## v1.0.2 — 2026-11-23

### Fixed (path leak)

- Replaced absolute build-machine and server paths in the distributed copies
  with `[repo]`: the repository roots (backslash and forward-slash forms),
  the GPU-server home directory prefix, and drive-rooted paths.
  Affected v1.0.1 files: `labels/g1_calibration_v3.json` (3 server-home
  ledger paths), `analysis/g3_analysis.json`, `analysis/g3_analysis_all880.json`,
  `analysis/g3_partial_pipeline_check.json`, the three
  `analysis/jitter_stability_*.json`, and `labels/g0_report.md` (13 `G:\\`
  paths). The scrub is applied to staged copies at build time, is
  deterministic and idempotent, and is recorded in `path_rescan.json`
  (16 occurrences in 8 files; 0 residual).
- The generated analysis/report sources outside the release are unchanged;
  the frozen and record artifacts are bit-identical to v1.0.1 apart from the
  scrubbed path strings.
- v1.0.1 (DOI `10.5281/zenodo.24449467`) remains published and immutable but
  is superseded by v1.0.2 (DOI `10.5281/zenodo.24449882`) and should not be
  cited for the package bytes.

### Validation

- L1 now includes a `path-rescan` check that fails on any surviving server
  home or repository-rooted absolute path; `tests/test_release.py` adds the
  same guard over every release tree and zip under `release/`.

## v1.0.1 — 2026-11-23

### Fixed (PII)

- Redacted the scrubber-artifact identity class (a bare scrubber token followed
  by an unsanitized given-name+digits local part on a reserved example domain)
  in every distributed file. The builder replaces each match with
  `person_redacted_0001` on every build, covering
  `frozen/prefixes.jsonl`, the T6 packet files, and one recovery trace.
- The frozen source under `data/frozen/` is unchanged and still verifies
  against the manifest hash; it is not part of the distributed payload.
- `pii_rescan.json` now reports `n_redactions` and the per-file replacement
  counts; the automated scan is clean (0 identifier hits).

### Licensing

- Added `ATTRIBUTION.md`: ToolResult-800 authors, upstream τ-bench MIT notice
  with the Sierra copyright line, the three model families and their licenses,
  and the "changes were made" statement.
- `DATA_LICENSE.md` and `DATA_CARD.md` now describe the release accurately:
  the distributed copy is redacted; the freeze-vs-release distinction is
  explicit.

### Validation

- `python scripts/18_build_release.py --validate --root <package>` (L1) and
  the guard test in `tests/test_release.py` fail on reintroduction of the
  fragment.

### Packaging (P6.5)

- `TABLE_MAP.md` now records the paper's split: 11 main-text tables (1–11)
  and 14 supplementary tables (S1–S14), with `tab:recovery` pointing at the
  v2 semantic risk set and the v1 hash set marked as the single reconciliation
  note.
- Added `analysis/rowlevel_refits.json` (P6.3 row-level refits; generated at
  `8e6f536`, SHA-256 `965805ea…dbedfcb`, provenance note in
  `release_record.json`).
- Added `traces/ledger_hashes.json`: SHA-256 and byte size for every
  distributed ledger extract, computed after redaction.
- L1 now checks the v2 crude/KM triple (24.4/32.9/21.3; 28.2/44.6/22.0) and
  the v1 decomposition (54+18=72, 116+25=141, 80+32=112); L2 reruns six
  producers including `19_rowlevel_refits.py`.
- Added the exploratory P6.7 second-renderer artifact (`analysis/renderer2.json`),
  its three ledgers under `traces/renderer2/`, and the rebuild code under
  `code/` (parser-v4 rescore + renderer sources). The exploratory status and
  the descriptive, point-estimate nature of its robustness check are unchanged.
- `paper_audit.json` snapshots the paper's main/supplement table order and the
  single v1 recovery note so L1 validates the package without a repository
  checkout; the main-text table order is now checked, not just the label set.

## v1.0.0 — 2026-11-22

- First staged public release: 880 scrubbed prefixes, manifests,
  scrubbed ledger extracts, audit labels, analysis JSONs, T6 packets, prereg
  and amendments, table map, validation record, checksums.
"""


def build_package(out: Path, force: bool = False) -> dict:
    from toolobs.harvest.freeze import hash_renderer  # noqa: E402
    from toolobs.harvest.parse import hash_jsonl_dicts, read_jsonl_dicts  # noqa: E402
    from toolobs.hashing import sha256_text_file  # noqa: E402

    if out.exists():
        if not force:
            print(f"[18_build_release] FAIL: output exists: {out} (use --force)")
            return {"ok": False, "reason": "exists"}
        shutil.rmtree(out)

    staged = stage_files()
    missing = [str(src) for src, _ in staged if not src.is_file()]
    if missing:
        print(f"[18_build_release] FAIL: missing inputs ({len(missing)}): {missing[:8]}")
        return {"ok": False, "reason": "missing", "missing": missing}

    # Provenance notes bind a distributed artifact to the exact bytes that were
    # generated at the recorded commit; a silent regeneration fails the build.
    stale_notes = []
    for note in ARTIFACT_PROVENANCE_NOTES:
        name = note["artifact"].split("/", 1)[1]
        actual = sha256_file(ANALYSIS_DIR / name)
        if actual != note["sha256"]:
            stale_notes.append(f"{note['artifact']}: {actual} != {note['sha256']}")
    if stale_notes:
        print(f"[18_build_release] FAIL: provenance hash mismatch {stale_notes}")
        return {"ok": False, "reason": "provenance-hash", "details": stale_notes}

    manifest = json.loads((MANIFEST_DIR / "toolresult800_v1.json").read_text(encoding="utf-8"))
    if not manifest.get("audit", {}).get("gate_pass"):
        print("[18_build_release] FAIL: manifest audit gate is not passed")
        return {"ok": False, "reason": "audit-gate"}
    if not manifest.get("freeze", {}).get("no_target_outputs_before_freeze"):
        print("[18_build_release] FAIL: freeze record does not assert no target outputs")
        return {"ok": False, "reason": "freeze"}
    frozen_rows = read_jsonl_dicts(FROZEN_DIR / "prefixes.jsonl")
    checks = {
        "frozen_prefixes": hash_jsonl_dicts(frozen_rows) == manifest.get("frozen_prefixes_hash"),
        "perturbations": sha256_text_file(MANIFEST_DIR / "perturbations.jsonl")
        == manifest.get("perturbations_hash"),
        "sample": sha256_text_file(INTERIM_DIR / "sample.jsonl") == manifest.get("sample_hash"),
        "source_pin": sha256_text_file(MANIFEST_DIR / "source_pin.json")
        == manifest.get("source_pin_hash"),
        "prereg": sha256_text_file(PREREG_DIR / "PREREGISTRATION.md") == manifest.get("prereg_hash"),
        "field_registry": sha256_text_file(CONFIG_DIR / "field_registry.yaml")
        == manifest.get("field_registry_hash"),
        "renderer": hash_renderer(
            REPO_ROOT / "src" / "toolobs" / "render" / "render.py",
            REPO_ROOT / "src" / "toolobs" / "render" / "perturb.py",
        )
        == manifest.get("renderer_hash"),
    }
    sidecar = json.loads((MANIFEST_DIR / "toolresult800_v1.sha256.json").read_text(encoding="utf-8"))
    checks["sidecar"] = (
        sidecar.get("manifest_sha256") == sha256_file(MANIFEST_DIR / "toolresult800_v1.json")
    )
    if not all(checks.values()):
        bad = {k: v for k, v in checks.items() if not v}
        print(f"[18_build_release] FAIL: manifest chain {bad}")
        return {"ok": False, "reason": "hash-chain", "checks": checks}
    print(f"[18_build_release] manifest chain ok: {checks}")

    for src, dst in staged:
        target = out / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)

    (out / "TABLE_MAP.md").write_text(table_map_md(), encoding="utf-8")
    write_json(out / "paper_audit.json", paper_audit_json())
    (out / "VALIDATION.md").write_text(validation_md(), encoding="utf-8")
    (out / "CHANGELOG.md").write_text(release_changelog_md(), encoding="utf-8")
    (out / "licenses").mkdir(parents=True, exist_ok=True)
    (out / "licenses" / "TAU_BENCH_LICENSE_MIT").write_text(
        "# Upstream tau-bench license (verbatim, MIT)\n# Source: "
        "https://github.com/sierra-research/tau-bench (LICENSE)\n# Pinned commit: "
        "59a200c6d575d595120f1cb70fea53cef0632f6b (see manifests/source_pin.json)\n"
        "# Fetched 2026-11-22; copyright holder as published upstream.\n\n" + TAU_BENCH_MIT,
        encoding="utf-8",
    )
    (out / "licenses" / "MODEL_OUTPUT_LICENSES.md").write_text(
        MODEL_LICENSES_MD, encoding="utf-8"
    )
    (out / "README.md").write_text(
        "# ToolResult-800 v1.0.2\n\n"
        "Scrubbed derived data for the fixed-prefix measurement study of tool-result "
        "errors (800 primary + 80 reserve prefixes, five arms, three models). "
        "Raw trajectories, PII, weights, caches, and run logs are excluded. "
        "Scrubber-artifact identities are redacted in this copy at build time "
        "(D-046), and absolute build-machine/server paths are replaced by "
        "`[repo]` (v1.0.2 path scrub); the frozen source is not distributed.\n\n"
        f"Staged: {utc_now()} (builder {BUILDER_VERSION}, commit {git_commit()}).\n"
        f"DOI: {PACKAGE_DOI} (concept DOI {CONCEPT_DOI}; supersedes v1.0.1 "
        "10.5281/zenodo.24449467, withdrawn from recommendation because of a "
        "path leak).\n"
        "Validate: `python scripts/18_build_release.py --validate --root <this dir>`.\n"
        "Every paper table traces via `TABLE_MAP.md`; every number traces to "
        "`manifests/`, `traces/`, `labels/`, or `analysis/`.\n",
        encoding="utf-8",
    )

    # Apply the release-copy redaction to every staged text file. Runs before
    # checksums are written so SHA256SUMS covers the redacted bytes. The
    # frozen source is untouched (hash verified above); this is the only
    # difference between it and frozen/prefixes.jsonl here.
    redaction = apply_redactions(out)
    if not redaction["n_occurrences"]:
        print("[18_build_release] FAIL: redaction applied 0 occurrences")
        return {"ok": False, "reason": "redaction-noop"}
    frozen_release_hash = hash_jsonl_dicts(read_jsonl_dicts(out / "frozen" / "prefixes.jsonl"))
    redaction["frozen_prefixes_hash_source"] = manifest.get("frozen_prefixes_hash")
    redaction["frozen_prefixes_hash_release"] = frozen_release_hash
    if redaction["frozen_prefixes_hash_source"] == frozen_release_hash:
        print("[18_build_release] FAIL: redaction did not change the release prefixes")
        return {"ok": False, "reason": "redaction-unapplied"}
    print(f"[18_build_release] redacted {redaction['n_occurrences']} occurrence(s) "
          f"in {redaction['n_files']} file(s)")

    # Path scrub (v1.0.2) runs before the ledger hashes and release checksums,
    # so every recorded hash covers the scrubbed bytes. It is a no-op for an
    # already-clean tree, which keeps rebuilds idempotent.
    path_scrub, path_hits = apply_path_scrub(out)
    print(f"[18_build_release] path scrub: {path_scrub['n_occurrences']} occurrence(s) "
          f"in {path_scrub['n_files']} file(s); {len(path_hits)} residual pattern(s)")

    # Ledger extracts are distributed as scrubbed, redacted, path-scrubbed
    # copies; record their hashes alongside them so the provenance travels with
    # the traces (the release-wide SHA256SUMS below covers them again).
    ledger_hashes = ledger_hashes_json(out)
    write_json(out / "traces" / "ledger_hashes.json", ledger_hashes)
    print(f"[18_build_release] ledger hashes: {ledger_hashes['n_files']} files, "
          f"{ledger_hashes['total_bytes']} bytes")

    hits, placeholders, echoes, allowlisted = pii_rescan(out)
    pii_report = {
        "scanned_utc": utc_now(),
        "counting_rule": "Counts and lists are per scanned-value occurrence "
        "(duplicates retained: one entry per JSON value / CSV cell / text "
        "line, so a string echoed in both decision_json and output_text "
        "counts twice); n_* match the list lengths, and n_redactions counts "
        "occurrences replaced before the scan.",
        "n_hits": len(hits),
        "hits": sorted(hits),
        "n_redactions": redaction["n_occurrences"],
        "n_redacted_files": redaction["n_files"],
        "redactions": redaction["files"],
        "redaction_token": REDACTION_TOKEN,
        "redaction_note": redaction["note"],
        "n_placeholders": len(placeholders),
        "placeholders": sorted(placeholders),
        "n_synthetic_echoes": len(echoes),
        "synthetic_echoes": sorted(echoes),
        "echo_note": "Synthetic echoes embed only scrubber tokens "
        "(person_/user_/email_ + 12 hex); the PII map is never released, so "
        "they are not re-identifiable. The frozen source retains "
        "scrubber-artifact identity-class fragments for freeze integrity; they "
        "are not distributed, and every release copy is redacted at build "
        "(D-046; see CHANGELOG.md and release_record.json).",
        "email_allowlist": allowlisted,
        "allowlist_note": "CITATION.cff and DATA_CARD.md carry the "
        "corresponding-author contact email by design; ORCID iDs are public "
        "researcher identifiers and are masked before the digit-run rule.",
        "note": "Automated scan only; independent human re-scan pending "
        "(docs/submission/checklist.md).",
    }
    write_json(out / "pii_rescan.json", pii_report)

    path_report = {
        "scanned_utc": utc_now(),
        "token": PATH_SCRUB_TOKEN,
        "n_occurrences": path_scrub["n_occurrences"],
        "n_files": path_scrub["n_files"],
        "files": path_scrub["files"],
        "n_hits": len(path_hits),
        "hits": sorted(path_hits),
        "rule": path_scrub["rule"],
        "frozen_source_unchanged": True,
        "note": PATH_SCRUB_NOTE,
        "detector_classes": [
            "server home directory prefix",
            "workstation user-home prefix",
            "build repository root (drive or forward-slash form)",
            "drive-rooted repo checkout under a user home",
            "absolute drive path",
        ],
    }
    write_json(out / "path_rescan.json", path_report)
    # Re-scan after writing the report so the published tree, report included,
    # is what "0 residual" describes.
    path_hits = residual_path_leaks(out)
    path_report["n_hits"] = len(path_hits)
    path_report["hits"] = sorted(path_hits)
    if path_hits:
        write_json(out / "path_rescan.json", path_report)

    files = sorted(
        p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()
    )
    files = [f for f in files if f not in ("SHA256SUMS", "release_record.json")]
    (out / "SHA256SUMS").write_text(
        "".join(f"{sha256_file(out / f)}  {f}\n" for f in files), encoding="utf-8"
    )
    record = {
        "package": PACKAGE_NAME,
        "version": PACKAGE_VERSION,
        "builder": BUILDER_VERSION,
        "created_utc": utc_now(),
        "git_commit": git_commit(),
        "doi": PACKAGE_DOI,
        "concept_doi": CONCEPT_DOI,
        "manifest_hash": sha256_file(MANIFEST_DIR / "toolresult800_v1.json"),
        "prereg_hash": manifest.get("prereg_hash"),
        "field_registry_hash": manifest.get("field_registry_hash"),
        "renderer_hash": manifest.get("renderer_hash"),
        "source_pin_hash": manifest.get("source_pin_hash"),
        "redaction": redaction,
        "path_scrub": path_scrub,
        "path_rescan": {
            "path": "path_rescan.json",
            "n_occurrences": path_scrub["n_occurrences"],
            "n_files": path_scrub["n_files"],
            "n_hits": len(path_hits),
        },
        "ledger_hashes": {
            "path": "traces/ledger_hashes.json",
            "n_files": ledger_hashes["n_files"],
            "total_bytes": ledger_hashes["total_bytes"],
        },
        "artifact_provenance_notes": ARTIFACT_PROVENANCE_NOTES,
        "n_files": len(files),
        "files": {f: sha256_file(out / f) for f in files},
        "pii_placeholders": len(placeholders),
        "pii_synthetic_echoes": len(echoes),
        "pii_email_allowlist": allowlisted,
    }
    write_json(out / "release_record.json", record)
    if hits:
        print(f"[18_build_release] FAIL: PII re-scan hits ({len(hits)}):")
        for hit in hits:
            print(f"  {hit}")
        return {"ok": False, "reason": "pii", "hits": hits}
    if path_hits:
        print(f"[18_build_release] FAIL: path re-scan hits ({len(path_hits)}):")
        for hit in path_hits:
            print(f"  {hit}")
        return {"ok": False, "reason": "path", "hits": path_hits}
    print(f"[18_build_release] PII re-scan clean ({len(files)} files; "
          f"{redaction['n_occurrences']} redaction(s), "
          f"{len(placeholders)} placeholders, {len(echoes)} synthetic echoes noted)")
    print(f"[18_build_release] path re-scan clean ({len(files)} files; "
          f"{path_scrub['n_occurrences']} path occurrence(s) scrubbed)")
    print(f"[18_build_release] wrote {out} ({len(files)} files)")
    return {"ok": True, "n_files": len(files), "out": str(out),
            "redactions": redaction["n_occurrences"],
            "path_scrubs": path_scrub["n_occurrences"]}


# ---------------------------------------------------------------------------
# L1 validation: reconciliations on a package root (staged tree or repo tree)
# ---------------------------------------------------------------------------

def _load(root: Path, rel: str) -> dict:
    # In repo-tree mode, analysis/labels live under artifacts/; in the staged
    # package they live at the top level. Resolve both layouts.
    candidates = [root / rel]
    if rel.startswith(("analysis/", "labels/", "packets/", "costs/")):
        candidates.append(root / "artifacts" / rel)
    if rel.startswith("traces/"):
        candidates.append(root / "data" / "runs" / rel[len("traces/"):])
    if rel.startswith("manifests/"):
        candidates.append(root / "data" / rel)
    if rel.startswith("frozen/"):
        candidates.append(root / "data" / rel)
    for candidate in candidates:
        if candidate.is_file():
            with open(candidate, encoding="utf-8") as handle:
                return json.load(handle)
    raise FileNotFoundError(f"{rel} not found under {root}")


def _paper_audit(root: Path) -> dict:
    """Paper-side snapshot: package copy when present, else the live paper."""
    path = root / "paper_audit.json"
    if path.is_file():
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    return paper_audit_json()


def _deep_equal_ignoring(a: object, b: object, path: str = "") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        diffs: list[str] = []
        for key in a.keys() | b.keys():
            if key in VOLATILE_KEYS:
                continue
            if key not in a:
                diffs.append(f"{path}.{key}: missing in rebuilt")
            elif key not in b:
                diffs.append(f"{path}.{key}: missing in released")
            else:
                diffs.extend(_deep_equal_ignoring(a[key], b[key], f"{path}.{key}"))
        return diffs
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: len {len(a)} != {len(b)}"]
        diffs = []
        for i, (x, y) in enumerate(zip(a, b, strict=False)):
            diffs.extend(_deep_equal_ignoring(x, y, f"{path}[{i}]"))
        return diffs
    if isinstance(a, float) and isinstance(b, float):
        if math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12):
            return []
        return [f"{path}: {a!r} != {b!r}"]
    if a != b:
        return [f"{path}: {a!r} != {b!r}"]
    return []


def validate_tree(root: Path, rerun: bool = False) -> dict:
    root = resolve_repo_path(root)
    results: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))
        print(f"[validate] {'ok' if ok else 'FAIL'} {name} {detail}")

    # --- manifest hash chain (files resolved in either layout) ---
    def _raw(rel: str) -> Path:
        cands = [root / rel]
        if rel.startswith("manifests/"):
            cands.append(root / "data" / rel)
        if rel.startswith("frozen/"):
            cands.append(root / "data" / rel)
        for cand in cands:
            if cand.is_file():
                return cand
        raise FileNotFoundError(rel)

    try:
        manifest = _load(root, "manifests/toolresult800_v1.json")
        from toolobs.harvest.freeze import hash_renderer  # noqa: E402
        from toolobs.harvest.parse import hash_jsonl_dicts, read_jsonl_dicts  # noqa: E402
        from toolobs.hashing import sha256_text_file  # noqa: E402

        chain = {
            "perturbations": sha256_text_file(_raw("manifests/perturbations.jsonl"))
            == manifest.get("perturbations_hash"),
        }
        frozen_hash = hash_jsonl_dicts(read_jsonl_dicts(_raw("frozen/prefixes.jsonl")))
        if (root / "frozen" / "prefixes.jsonl").is_file():
            # Staged package: the distributed prefix file is the redacted
            # derivative (D-046). Bind it to the recorded release hash and to
            # the frozen-source hash; the source itself is not distributed.
            record = json.loads((root / "release_record.json").read_text(encoding="utf-8"))
            red = record.get("redaction", {})
            chain["frozen_prefixes"] = (
                frozen_hash == red.get("frozen_prefixes_hash_release")
                and red.get("frozen_prefixes_hash_source") == manifest.get("frozen_prefixes_hash")
                and red.get("token") == REDACTION_TOKEN
                and int(red.get("n_occurrences", 0)) > 0
                and int(red.get("files", {}).get("frozen/prefixes.jsonl", 0)) > 0
                and redact_text(_raw("frozen/prefixes.jsonl").read_text(encoding="utf-8"))[1] == 0
            )
        else:
            chain["frozen_prefixes"] = frozen_hash == manifest.get("frozen_prefixes_hash")
        # Repo-only links (prereg source, configs) checked when present.
        if (REPO_ROOT / "prereg" / "PREREGISTRATION.md").is_file():
            chain["prereg"] = sha256_text_file(REPO_ROOT / "prereg" / "PREREGISTRATION.md") == manifest.get(
                "prereg_hash"
            )
            chain["field_registry"] = sha256_text_file(
                REPO_ROOT / "configs" / "field_registry.yaml"
            ) == manifest.get("field_registry_hash")
            chain["renderer"] = hash_renderer(
                REPO_ROOT / "src" / "toolobs" / "render" / "render.py",
                REPO_ROOT / "src" / "toolobs" / "render" / "perturb.py",
            ) == manifest.get("renderer_hash")
        check("manifest-chain", all(chain.values()), str(chain))
    except (FileNotFoundError, KeyError, ValueError) as exc:
        check("manifest-chain", False, str(exc))
        manifest = {}

    # --- SHA256SUMS completeness (staged layout only) ---
    sums_path = root / "SHA256SUMS"
    if sums_path.is_file():
        listed: dict[str, str] = {}
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            digest, name = line.split(None, 1)
            listed[name.strip()] = digest
        actual = sorted(
            p.relative_to(root).as_posix()
            for p in root.rglob("*")
            if p.is_file() and p.name not in ("SHA256SUMS", "release_record.json")
        )
        digests_ok = all(
            (root / name).is_file() and sha256_file(root / name) == digest
            for name, digest in listed.items()
        )
        check(
            "sha256sums",
            sorted(listed) == actual and digests_ok,
            f"{len(listed)} listed, {len(actual)} files",
        )
    else:
        check("sha256sums", True, "skipped (live tree has no SHA256SUMS)")

    # --- g4 v2 semantic recovery triple (main tab:recovery) + v1 note ---
    # The paper's primary recovery table reports the v2 semantic risk set
    # (crude 24.4/32.9/21.3, KM 28.2/44.6/22.0). The v1 run-time hash set may
    # appear only as the single reconciliation note, whose numbers must
    # decompose exactly into semantic events + hash-only events.
    try:
        ids = (
            "qwen3_5_9b_instruct_awq",
            "ministral_3_8b_instruct_2512_awq",
            "llama_3_1_8b_instruct_awq",
        )
        v2 = _load(root, "analysis/g4_recovery_v2.json")
        v2_cells = [v2["groups"][f"{m}|transient_s3"] for m in ids]
        v2_events = tuple((cell["events"], cell["n"]) for cell in v2_cells)
        v2_rates = tuple(round(100.0 * cell["crude"]["rate"], 1) for cell in v2_cells)
        v2_km = tuple(round(100.0 * cell["km_recovered_h4"], 1) for cell in v2_cells)
        g4 = _load(root, "analysis/g4_recovery.json")
        v1_events = tuple(
            (
                g4["groups"][f"{m}|transient_s3"]["exponential"]["events"],
                g4["groups"][f"{m}|transient_s3"]["exponential"]["n"],
            )
            for m in ids
        )
        bridge = v2.get("hash_bridge", {})
        decomposition = tuple(
            (
                bridge[f"{m}|transient_s3"].get("analysis_events"),
                bridge[f"{m}|transient_s3"].get("hash_only_events"),
                bridge[f"{m}|transient_s3"].get("g4_events"),
            )
            for m in ids
        )
        audit = _paper_audit(root).get("recovery_note", {})
        check(
            "g4-crude-triple",
            v2_events == ((54, 221), (116, 353), (80, 376))
            and v2_rates == (24.4, 32.9, 21.3)
            and v2_km == (28.2, 44.6, 22.0)
            and v1_events == ((72, 264), (141, 406), (112, 412))
            and decomposition == ((54, 18, 72), (116, 25, 141), (80, 32, 112))
            and audit.get("count") == 1
            and not audit.get("v1_crude_outside_note")
            and not audit.get("v1_km_outside_note"),
            f"v2 crude {v2_rates} KM {v2_km} events {v2_events}; "
            f"v1 note {v1_events} x{audit.get('count')}",
        )
        bridge_bad = [
            k for k, cell in bridge.items()
            if cell.get("g4_events") != cell.get("bridge_events_sum")
            or cell.get("g4_n") != cell.get("bridge_n_sum")
        ]
        check("v2-bridge", not bridge_bad, f"{len(bridge)} cells" + (f" bad={bridge_bad}" if bridge_bad else ""))
        groups = v2.get("groups", {})
        wilson_ok, wilson_n = True, 0
        for cell_key in v2.get("primary_cells", []):
            cell = groups.get(cell_key, {})
            lo, hi = cell.get("crude_ci95_wilson", [None, None])
            elo, ehi = wilson(cell["events"], cell["n"])
            wilson_n += 1
            if abs(elo - lo) > 1e-9 or abs(ehi - hi) > 1e-9:
                wilson_ok = False
        check("v2-wilson", wilson_ok and wilson_n > 0, f"{wilson_n} primary cells")
    except (FileNotFoundError, KeyError) as exc:
        check("g4-recovery", False, str(exc))

    # --- severity 7/11/16 re-derived from verification sheets ---
    try:
        sev = _load(root, "analysis/severity_sensitivity.json")
        rep = sev.get("donor_unused_critical", {})
        got = (
            rep.get("majority", {}).get("k"),
            rep.get("sheet_visible_verifier", {}).get("k"),
            rep.get("blind_verifier", {}).get("k"),
        )
        check("severity-counts", got == (7, 11, 16), str(got))
    except (FileNotFoundError, KeyError, AttributeError) as exc:
        check("severity-counts", False, str(exc))

    # --- exact McNemar / LRT / PPV recomputes ---
    def _check_mcnemar_cell(cell: dict, tol: float = 1e-9) -> bool:
        if not all(k in cell for k in ("b", "c")):
            return True
        exact = mcnemar_exact_p(cell["b"], cell["c"])
        for key in ("recomputed_two_sided_p", "reported_two_sided_p", "p_two_sided",
                    "paired_adequacy_mcnemar_p", "mcnemar_p", "p"):
            if key in cell and cell[key] is not None:
                if abs(exact - cell[key]) > tol * max(1.0, abs(cell[key])):
                    return False
        return True

    try:
        inf = _load(root, "analysis/inference_robustness.json")
        mc = inf.get("mcnemar_s2_vs_s3", {})
        check("mcnemar-exact", all(_check_mcnemar_cell(c) for c in mc.values()), f"{len(mc)} cells")
        lrt = inf.get("lrt_robustness", {})
        lrt_ok = True
        for _key, cell in lrt.items():
            if not isinstance(cell, dict):
                continue
            for chi2k, pk, df in (
                ("categorical_chi2", "categorical_recomputed_p", 2),
                ("quadratic_chi2", "quadratic_recomputed_p", 1),
            ):
                if chi2k in cell and pk in cell:
                    sf = chi2_sf_2 if df == 2 else chi2_sf_1
                    if abs(sf(cell[chi2k]) - cell[pk]) > 1e-9 * max(1.0, abs(cell[pk])):
                        lrt_ok = False
            for chi2k, pk in (("chi2", "p"),):
                if chi2k in cell and pk in cell:
                    df = cell.get("df", 1)
                    sf = chi2_sf_2 if df == 2 else chi2_sf_1
                    if abs(sf(cell[chi2k]) - cell[pk]) > 1e-9 * max(1.0, abs(cell[pk])):
                        lrt_ok = False
        check("lrt-tails", lrt_ok, f"{sum(1 for c in lrt.values() if isinstance(c, dict))} cells")
    except (FileNotFoundError, KeyError) as exc:
        check("inference-recompute", False, str(exc))

    # --- H5 pooled s3-vs-s1 ---
    try:
        h5 = (inf.get("h5_s3_vs_s1", {}) or {}).get("pooled", {})
        check(
            "h5-mcnemar",
            (h5.get("b"), h5.get("c")) == (431, 93)
            and _check_mcnemar_cell(h5, tol=1e-9),
            f"b={h5.get('b')} c={h5.get('c')}",
        )
    except (FileNotFoundError, KeyError, NameError) as exc:
        check("h5-mcnemar", False, str(exc))

    # --- wrong-direction partition + g3 totals ---
    try:
        wd = _load(root, "analysis/wrong_direction.json")
        pooled = wd.get("pooled", wd)
        part = (
            pooled.get("wrong_direction", 0) + pooled.get("caught", 0) + pooled.get("other", 0)
        )
        check(
            "wrongdir-partition",
            (pooled.get("wrong_direction"), pooled.get("caught"), pooled.get("other"),
             pooled.get("silent"), pooled.get("switches"), part)
            == (1258, 30, 676, 419, 1964, 1964),
            f"wd={pooled.get('wrong_direction')} caught={pooled.get('caught')} other={pooled.get('other')}",
        )
        g3 = _load(root, "analysis/g3_analysis.json")
        crit = sum(
            cell.get("any", 0)
            for key, cell in g3.get("arm_table", {}).items()
            if key.endswith("|s2") or key.endswith("|s3")
        )
        n_total = sum(cell.get("n", 0) for cell in g3.get("arm_table", {}).values())
        s0_any = sum(c.get("any", 0) for k, c in g3.get("arm_table", {}).items() if k.endswith("|s0"))
        s0_n = sum(c.get("n", 0) for k, c in g3.get("arm_table", {}).items() if k.endswith("|s0"))
        s3_any = sum(c.get("any", 0) for k, c in g3.get("arm_table", {}).items() if k.endswith("|s3"))
        s3_n = sum(c.get("n", 0) for k, c in g3.get("arm_table", {}).items() if k.endswith("|s3"))
        check(
            "g3-totals",
            (crit, n_total) == (1964, g3.get("n_labels"))
            and abs(s0_any / s0_n - 0.3008) < 5e-4
            and abs(s3_any / s3_n - 0.4645) < 5e-4,
            f"crit={crit} n={n_total} s0={s0_any / s0_n:.4f} s3={s3_any / s3_n:.4f}",
        )
    except (FileNotFoundError, KeyError) as exc:
        check("wrongdir-g3", False, str(exc))

    # --- utility endpoint counts ---
    try:
        ev = _load(root, "analysis/new_evidence.json")
        agent = ev.get("agent_coding", {})
        det = ev.get("deterministic", {}).get("pooled", {})
        by_kind = ev.get("deterministic", {}).get("by_donor_kind", {})
        check(
            "utility-agent",
            (agent.get("n_coded_pairs"), agent.get("n_judgeable_pairs"),
             agent.get("paired_adequacy_loss_b"), agent.get("paired_adequacy_gain_c"))
            == (120, 115, 42, 11)
            and _check_mcnemar_cell(
                {"b": 42, "c": 11, "p": agent.get("paired_adequacy_mcnemar_p")}, tol=0.02
            ),
            f"coded={agent.get('n_coded_pairs')} judge={agent.get('n_judgeable_pairs')}",
        )
        check(
            "utility-deterministic",
            (det.get("n"), det.get("mcnemar_b"), det.get("mcnemar_c"),
             by_kind.get("tool", {}).get("n"), by_kind.get("text", {}).get("n"))
            == (1039, 25, 23, 245, 794)
            and _check_mcnemar_cell(det, tol=1e-6),
            f"n={det.get('n')} b/c={det.get('mcnemar_b')}/{det.get('mcnemar_c')}",
        )
        rel = ev.get("reliability", {})
        check(
            "utility-reliability",
            (rel.get("n"), rel.get("unjudgeable_pairs")) == (38, 2)
            and abs(rel.get("agreement", 0) - 36 / 38) < 5e-7
            and abs(rel.get("kappa", 0) - 0.918803) < 5e-7,
            str({k: rel.get(k) for k in ("n", "agreement", "kappa")}),
        )
    except (FileNotFoundError, KeyError) as exc:
        check("utility-counts", False, str(exc))

    # --- PPV exact lower bound .6637 (gate table) ---
    check(
        "ppv-lower-bound",
        abs(clopper_pearson_lower(9, 9) - 0.6637) < 5e-5,
        f"{clopper_pearson_lower(9, 9):.4f}",
    )

    # --- TABLE_MAP covers all 25 paper tables, ordered main/supplement split ---
    try:
        audit = _paper_audit(root)
        main_labels = audit["main_labels"]
        supp_labels = audit["supplement_labels"]
        labels = sorted(set(main_labels) | set(supp_labels))
        mapped_main = [row["label"] for row in TABLE_MAP if row["section"] == "main"]
        mapped_supp = [row["label"] for row in TABLE_MAP if row["section"] == "supplement"]
        supp_nos = [row["table_no"] for row in TABLE_MAP if row["section"] == "supplement"]
        check(
            "table-map-coverage",
            sorted(mapped_main + mapped_supp) == labels
            and mapped_main == main_labels
            and mapped_supp == supp_labels
            and len(mapped_main) == 11
            and supp_nos == [f"S{i}" for i in range(1, 15)]
            and [row["table_no"] for row in TABLE_MAP if row["section"] == "main"]
            == [str(i) for i in range(1, 12)],
            f"{len(mapped_main)} main (ordered) + {len(mapped_supp)} supplement",
        )
    except (OSError, ValueError, KeyError) as exc:
        check("table-map-coverage", False, str(exc))

    # --- renderer-2 ledgers: artifact hashes == distributed bytes ---
    try:
        r2 = _load(root, "analysis/renderer2.json")
        expected = r2["ledger_hashes"]["renderer2"]
        trace_root = root / "traces" if (root / "traces").is_dir() else root / "data" / "runs"
        bad: list[str] = []
        for model, cell in expected.items():
            rel = cell["path"].split("data/runs/", 1)[1]
            actual_path = trace_root / rel
            if not actual_path.is_file():
                bad.append(f"{model}: missing {actual_path}")
                continue
            if sha256_file(actual_path) != cell["sha256"]:
                bad.append(f"{model}: sha mismatch")
            if actual_path.stat().st_size != cell["bytes"]:
                bad.append(f"{model}: size mismatch")
        recorded = None
        if (root / "traces" / "ledger_hashes.json").is_file():
            recorded = _load(root, "traces/ledger_hashes.json")
        if recorded is not None:
            by_path = {row["path"]: row for row in recorded.get("files", [])}
            for model, cell in expected.items():
                row = by_path.get(f"traces/{cell['path'].split('data/runs/', 1)[1]}")
                if row is None or row.get("sha256") != cell["sha256"]:
                    bad.append(f"{model}: ledger_hashes.json disagrees")
        check("renderer2-ledgers", not bad, f"{len(expected)} ledgers" + (f" bad={bad[:3]}" if bad else ""))
    except (FileNotFoundError, KeyError, ValueError) as exc:
        check("renderer2-ledgers", False, str(exc))

    # --- absolute-path re-scan (staged package; v1.0.2) ---
    if (root / "frozen").is_dir():
        path_hits = residual_path_leaks(root)
        check(
            "path-rescan",
            not path_hits,
            f"{len(path_hits)} hit(s)" + (f": {path_hits[:5]}" if path_hits else ""),
        )
    else:
        check(
            "path-rescan",
            True,
            "skipped (live tree; the path scrub applies to staged copies)",
        )

    # --- identifier re-scan ---
    if (root / "frozen" / "prefixes.jsonl").is_file() or (root / "data").is_dir():
        scan_root = root
        hits, placeholders, echoes, _ = pii_rescan(scan_root)
        # In live-tree mode, restrict to release-relevant inputs to avoid
        # flagging internal docs (emails in DECISIONS, etc.).
        if not (root / "frozen").is_dir():
            rel_allow = (
                "data/frozen", "data/manifests", "data/runs",
                "artifacts/analysis", "artifacts/audit", "artifacts/cost",
            )
            hits = [h for h in hits if h.split(":")[0].startswith(rel_allow)]
            placeholders = [r for r in placeholders if r.split(":")[0].startswith(rel_allow)]
            echoes = [r for r in echoes if r.split(":")[0].startswith(rel_allow)]
        check("pii-rescan", not hits, f"{len(hits)} hits" + (f": {hits[:5]}" if hits else ""))
    else:
        check("pii-rescan", False, "no frozen payload found")

    # --- L2: rerun producers and diff ---
    if rerun:
        tmp = root / ".validate_rerun_tmp"
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        try:
            for script, out_name, extra in RERUN_PRODUCERS:
                tmp_out = tmp / out_name
                cmd = [sys.executable, str(REPO_ROOT / script), *extra, "--out", str(tmp_out)]
                proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
                if proc.returncode != 0 or not tmp_out.is_file():
                    check(f"rerun-{out_name}", False, (proc.stderr or "")[-300:])
                    continue
                released = _load(root, f"analysis/{out_name}")
                rebuilt = json.loads(tmp_out.read_text(encoding="utf-8"))
                diffs = _deep_equal_ignoring(rebuilt, released)
                check(f"rerun-{out_name}", not diffs, f"{len(diffs)} diffs" + (f": {diffs[:3]}" if diffs else ""))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    failed = [name for name, ok, _ in results if not ok]
    print(f"[validate] {len(results) - len(failed)}/{len(results)} checks passed")
    return {"ok": not failed, "failed": failed, "results": results}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--root", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--rerun", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    if args.build:
        out = Path(args.out) if args.out else RELEASE_DIR / PACKAGE_NAME
        result = build_package(out, force=args.force)
        return 0 if result.get("ok") else 1
    if args.validate:
        root = Path(args.root) if args.root else REPO_ROOT
        result = validate_tree(root, rerun=args.rerun)
        return 0 if result.get("ok") else 1
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
