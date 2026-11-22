# `release/` — ToolResult-800 release

This directory holds the release checklist, packaging notes, and (locally) the built release
candidate. Built packages are gitignored; only this README is tracked.

## What the release contains

- `ToolResult-800-v1.0.1/` — frozen 800 prefixes (400 airline, 400 retail), reserve IDs, scrubbed
  observations, factual continuations, perturbation records, arm assignments, renderer version.
  The distributed copy is redacted (D-046); the frozen source is not distributed.
- `manifests/` — `toolresult800_v1.json`, `perturbations.jsonl`, model pins, field-registry hash,
  prereg hash, checksums.
- `traces/` — model continuations, decision signatures, recovery traces, ledger extracts.
- `labels/` — automatic and adjudicated labels, audit samples, κ/α reports.
- `DATA_CARD.md`, `ATTRIBUTION.md`, `DATA_LICENSE.md` — data card and consolidated notices.
- `licenses/` — upstream τ-bench MIT notice (verbatim) + model-output license verification.
- `SHA256SUMS`, `CITATION.cff`, `README.md`, `CHANGELOG.md`.

## Pre-release checklist (status 2026-11-23; v1.0.1 redaction rebuild)

- [x] G0, G1, G2, G3, G4 reports are present and unmodified.
- [x] The frozen manifest hash verifies against the analysis artifacts (`make validate-release`: manifest chain ok).
- [x] Automated PII re-scan passes: 0 identifier hits (`release/.../pii_rescan.json`; placeholders/echoes documented, redaction counts reported).
- [ ] Independent human PII re-scan — pending author action (see `docs/submission/checklist.md`).
- [x] Scrub report and 40-item audit are included (`labels/scrub_report.json`, `labels/g0_*`).
- [x] Upstream τ-bench MIT notice and attribution are preserved (`licenses/TAU_BENCH_LICENSE_MIT`, source pin).
- [x] `DATA_LICENSE.md`, `LICENSE`, and `LICENSE-DOCS` are included.
- [x] Model outputs comply with each model's license; no weights are included (`licenses/MODEL_OUTPUT_LICENSES.md`; Apache-2.0 ×2 + llama3.1 verified 2026-11-22).
- [x] Checksums are generated and verified from a clean copy (`SHA256SUMS` + `release_record.json`).
- [x] Data card is complete; DOI and release date recorded.
- [x] Preregistration and all amendments are included (`prereg/`).
- [x] The claim in the README/paper matches the gate outcomes (measurement framing, three failures stated).
- [x] DOI minted and recorded in `CITATION.cff` and the data card (10.5281/zenodo.24449467).
- [ ] Repository tag and GitHub release match the package version — pending author action.
- [ ] A second person reproduces the checksum verification — pending author action.

## What is gitignored

`release/ToolResult-800-*/`, `release/*.zip`, and `release/*.tar.gz` are ignored. Release packages are
built locally, verified, and uploaded to the DOI archive; they are not committed to git.

## Versioning

- `v1.0` — first public ToolResult-800 release with confirmatory results or a documented null.
- `v1.0.1` — PII redaction errata: the distributed copy replaces every match of the
  scrubber-artifact identity class with `person_redacted_0001`; the frozen source is
  unchanged. No result changes.
- `v1.1` — additive data or labels; requires a new manifest and changelog entry.
- Corrections that change a frozen record require a new major/minor version, never an in-place
  edit.

## Rollback

If a release contains PII or a licensing error: unpublish or tombstone the artifact, publish an
erratum, rotate any exposed credential, and issue a corrected version. Do not silently replace
files under the same version.
