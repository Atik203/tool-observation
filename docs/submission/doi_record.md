# DOI deposit record — ToolResult-800 v1.0.1

**Status 2026-11-23: PACKAGE READY — DOI NOT MINTED (Phase A complete).**
`release/ToolResult-800-v1.0.1/` is rebuilt, validated, and clean-room compiled. The
author uploads it to Zenodo and mints the DOI in Phase B; nothing here is published
yet. The Zenodo token lives only in `.env` and is read only at mint time (never
printed, logged, or committed).

## Phase A evidence (2026-11-23)

- **Package:** `release/ToolResult-800-v1.0.1/` — 127 checksummed files (129 files
  including `SHA256SUMS` and `release_record.json`); `SHA256SUMS` verified against
  every file.
- **L1 validation:** `python scripts/18_build_release.py --validate --root
  release/ToolResult-800-v1.0.1` — 17/17 checks (manifest chain, checksums, v2
  semantic recovery triple + v1 reconciliation, v2 bridge/Wilson, severity 7/11/16,
  McNemar/LRT/H5, wrong-direction, g3 totals, utility, PPV bound, 11 main + S1–S14
  table coverage, identifier re-scan).
- **L2 rerun:** `--validate --rerun` — 23/23; six CPU-only producers rebuilt
  (`g4_recovery_v2`, `severity_sensitivity`, `rowlevel_refits`,
  `inference_robustness`, `wrong_direction`, `new_evidence`) and diffed against the
  released JSONs modulo `recorded_utc`/`git_commit`.
- **Clean-room compile:** the 14-file Overleaf zip (`toolresults.tex`, `ref.bib`,
  `cas-common.sty`, `cas-sc.cls`, `figures/fig1–fig10.png`) compiled with TeX Live
  2026 via `latexmk -pdf`: **35 pages, 0 undefined references, 0 undefined
  citations, 0 BibTeX warnings**.
- **Redaction:** applied at build time (D-046); `pii_rescan.json` reports 0
  identifier hits and `n_redactions > 0`. The independent human re-scan remains an
  author-gated item (`docs/submission/checklist.md`).
- **Scope:** confirmatory payload only. The exploratory P6.7 second-renderer ledgers
  (`data/runs/renderer2/`, D-048) are excluded from this deposit; publishing them is a
  separate decision requiring their own analysis artifact.

## DataCite metadata (deposit as-is)

- **Title:** ToolResult-800: Counterfactual Tool-Observation Dataset, 800 Frozen
  Prefixes
- **Creators:**
  - Md. Atikur Rahaman (ORCID 0009-0008-2945-4117), United International University — Contact
  - Ohidujjaman Tuhin (ORCID 0000-0002-8776-7145), United International University
- **Publication date:** the DOI registration date (release date = registration date).
- **Version:** 1.0.1 (staged 2026-11-23; builder `stage-18 v2`, commit recorded in
  `release_record.json`)
- **Resource type:** Dataset
- **Abstract:** Fixed-prefix counterfactual dataset for measuring whether the content of a
  real tool observation changes a language-model agent's next decision. 800 primary + 80
  reserve τ-bench prefixes (airline/retail), five observation arms (verbatim JSON, faithful
  prose, non-critical change, critical error, critical-plus-contradiction), frozen
  perturbation records, scrubbed ledger extracts from three open-weight 8–9B models (21,611
  generations), audit packets/sheets, and all analysis JSONs. Confirmatory analysis complete
  with three failed gate criteria reported; measurement framing, no causal claim.
- **Licenses (dual):**
  - **Data (project additions): CC BY 4.0** — `DATA_LICENSE.md`, also stated in the
    data card.
  - **Code (repository software): MIT** — `LICENSE`, `CITATION.cff`.
  - Upstream τ-bench: MIT (Sierra copyright), full text bundled in
    `licenses/TAU_BENCH_LICENSE_MIT`; model-output notices in
    `licenses/MODEL_OUTPUT_LICENSES.md` and `ATTRIBUTION.md`.
  - Zenodo field: select **CC BY 4.0** for the record (the data deposit); the code
    license is carried in the record description and `CITATION.cff`.
- **Related identifiers:**
  - Repository (code, MIT): https://github.com/Atik203/tool-observation
  - Upstream dataset: https://github.com/sierra-research/tau-bench @
    `59a200c6d575d595120f1cb70fea53cef0632f6b` (relation: *is derived from*)
  - Preregistration deposit (in-repo until this DOI): freeze commit `1673856`,
    tag `prereg-freeze-v1`, hash `e0d107c6`; `prereg/PREREGISTRATION.md` +
    `prereg/AMENDMENTS.md` (A-001–A-011) are bundled under `prereg/` (relation:
    *is documented by*)
  - Paper: Tool-Result Errors in Language-Model Agents (measurement study; under
    submission; relation: *is supplement to*)
- **Manifest hash (authoritative):**
  `d6e034d7f1132b314ad1f82bf14faa0f6762975ee7b404b54cc365acfac5487a`
- **Package checksum:** see `release/ToolResult-800-v1.0.1/SHA256SUMS` (127 files).
- **Notable artifact provenance:** `analysis/rowlevel_refits.json` was generated at
  commit `8e6f536` (2026-11-23 02:24 +0600), SHA-256
  `965805eac2791a0d40757777d537db4205c4d4c046d6b2732c2f272c9dbedfcb`. Its
  `reconciliation.note` wording was corrected as a text-only fix later committed as
  `7f0169d` (prefix-resampling sensitivity, `design_valid=false`, not a cluster
  bootstrap); the wording was in the working tree at generation, so the recorded
  commit lags the note text. No number changed, and a rerun reproduces every field
  except `recorded_utc`/`git_commit` (`release_record.json`
  `artifact_provenance_notes`).

## Phase B mint procedure (author; do not run unattended)

1. Read `zendo_token` from `.env` into the process environment only. Never echo it,
   never pass it on a command line that is logged, never commit it.
2. Create the Zenodo deposition with the metadata above; upload the package archive
   (contents of `release/ToolResult-800-v1.0.1/`, including `SHA256SUMS` and
   `release_record.json`).
3. Publish, then record the DOI, resolver URL, and registration date here and in
   `CITATION.cff`, `docs/DATA_CARD.md`, and the paper's Data-availability bullet.
4. Verify the resolver returns the record and the record's file list matches
   `SHA256SUMS` (127 files).

## Mint log

| Step | Status | Date/actor |
|---|---|---|
| Package staged + validated (17/17 L1, 23/23 with `--rerun`) | done (agent) | 2026-11-23 |
| Clean-room compile (35 pages, 0 undefined, 0 BibTeX warnings) | done (agent) | 2026-11-23 |
| Upload to archive | pending (author) | |
| DOI minted | pending (author) | DOI: ______ |
| DOI resolves (URL returns record) | pending (author) | |
| DOI recorded in CITATION.cff / data card / paper | pending (author) | |
