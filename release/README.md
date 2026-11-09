# `release/` — CTO-800 release

This directory holds the release checklist, packaging notes, and (locally) the built release
candidate. Built packages are gitignored; only this README is tracked.

## What the release contains

- `CTO-800-v1.0/` — frozen 800 prefixes (400 airline, 400 retail), reserve IDs, raw observations
  (scrubbed), factual continuations, perturbation records, arm assignments, renderer version.
- `manifests/` — `cto800_v1.json`, `perturbations.jsonl`, model pins, field-registry hash,
  prereg hash, checksums.
- `traces/` — model continuations, decision signatures, recovery traces, ledger extracts.
- `labels/` — automatic and adjudicated labels, audit samples, κ/α reports.
- `docs/` — data card, protocol, gates, label rubric, runbook, decisions.
- `LICENSES/` — MIT (code), CC BY 4.0 (docs/data), upstream τ-bench MIT notice.
- `SHA256SUMS`, `CITATION.cff`, `README.md`, `CHANGELOG.md`.

## Pre-release checklist

- [ ] G0, G1, G2, G3, G4 reports are present and unmodified.
- [ ] The frozen manifest hash matches the analysis artifacts.
- [ ] PII re-scan passes: no names, emails, phones, addresses, payment identifiers, or raw
      trajectories. Profile-tool observations are absent.
- [ ] Scrub report and 40-item audit are included.
- [ ] Upstream τ-bench MIT notice and attribution are preserved.
- [ ] `DATA_LICENSE.md`, `LICENSE`, and `LICENSE-DOCS` are included.
- [ ] Model outputs comply with each model's license; no weights are included.
- [ ] Checksums are generated and verified from a clean copy.
- [ ] Data card is complete; every TBD is resolved or explicitly marked.
- [ ] Preregistration and all amendments are included.
- [ ] The claim in the README/paper matches the gate outcomes.
- [ ] A DOI is minted and recorded in `CITATION.cff` and the data card.
- [ ] Repository tag and GitHub release match the package version.
- [ ] A second person reproduces the checksum verification.

## What is gitignored

`release/CTO-800-*/`, `release/*.zip`, and `release/*.tar.gz` are ignored. Release packages are
built locally, verified, and uploaded to the DOI archive; they are not committed to git.

## Versioning

- `v1.0` — first public CTO-800 release with confirmatory results or a documented null.
- `v1.0.1` — metadata/errata only; no data changes.
- `v1.1` — additive data or labels; requires a new manifest and changelog entry.
- Corrections that change a frozen record require a new major/minor version, never an in-place
  edit.

## Rollback

If a release contains PII or a licensing error: unpublish or tombstone the artifact, publish an
erratum, rotate any exposed credential, and issue a corrected version. Do not silently replace
files under the same version.
