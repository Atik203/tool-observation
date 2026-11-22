# DOI deposit record — ToolResult-800 v1.0.1

**Status 2026-11-23: PUBLISHED.** DOI **`10.5281/zenodo.24449467`**
(resolver: <https://doi.org/10.5281/zenodo.24449467>), Zenodo record **24449467**
(concept record 24449466), version 1.0.1, publication date 2026-11-23.

The record holds the exact release archive plus the package `SHA256SUMS`. Zenodo caps a
record at 100 files, so the 138-file package is deposited as
`ToolResult-800-v1.0.1.zip` + `SHA256SUMS`; the archive's internal file list and checksums
are the same `SHA256SUMS` (136 entries). Verification evidence is in the mint log below.
The Zenodo token lives only in `.env` (key `zendo_token`, the account's actual key name) and
was read in-process at mint time; it was never printed, logged, echoed, or committed.

## Release evidence (2026-11-23)

- **Package:** `release/ToolResult-800-v1.0.1/` — 136 checksummed files (138 files
  including `SHA256SUMS` and `release_record.json`); `SHA256SUMS` verified against
  every file.
- **L1 validation:** `python scripts/18_build_release.py --validate --root
  release/ToolResult-800-v1.0.1` — **18/18** checks (manifest chain, checksums, v2
  semantic recovery triple + v1 reconciliation, v2 bridge/Wilson, severity 7/11/16,
  McNemar/LRT/H5, wrong-direction, g3 totals, utility, PPV bound, 11 ordered main +
  S1–S14 table coverage, renderer-2 ledger hashes, identifier re-scan). L1 uses the
  bundled `paper_audit.json`, so it needs no repository checkout.
- **L2 rerun:** `--validate --rerun` — **24/24**; six CPU-only producers rebuilt
  (`g4_recovery_v2`, `severity_sensitivity`, `rowlevel_refits`,
  `inference_robustness`, `wrong_direction`, `new_evidence`) and diffed against the
  released JSONs modulo `recorded_utc`/`git_commit`.
- **Clean-room compile:** the 14-file Overleaf zip (`toolresults.tex`, `ref.bib`,
  `cas-common.sty`, `cas-sc.cls`, `figures/fig1–fig10.png`) compiled with TeX Live
  2026 via `latexmk -pdf` in a fresh temp directory: **36 pages**, **0 undefined
  references, 0 undefined citations, 0 BibTeX warnings**, no absolute paths in the
  extracted sources. The paper's Data-availability bullet carries this DOI.
- **Redaction:** applied at build time (D-046); `pii_rescan.json` reports 0
  identifier hits and `n_redactions > 0`. The independent human re-scan remains an
  author-gated item (`docs/submission/checklist.md`).
- **Scope:** the confirmatory payload plus the exploratory P6.7 second-renderer artifact
  (`analysis/renderer2.json`, its three ledgers, and the rebuild code). The exploratory
  check is descriptive, point-estimate based, and never pooled with the confirmatory
  estimate (D-048).

## DataCite metadata (as deposited)

- **Title:** ToolResult-800: Counterfactual Tool-Observation Dataset, 800 Frozen
  Prefixes
- **Creators:**
  - Md. Atikur Rahaman (ORCID 0009-0008-2945-4117), United International University — Contact
  - Ohidujjaman Tuhin (ORCID 0000-0002-8776-7145), United International University
- **Publication date:** 2026-11-23 (DOI registration date; also `CITATION.cff`
  `date-released`)
- **Version:** 1.0.1 (builder `stage-18 v3`; commit recorded in
  `release_record.json`)
- **Resource type:** Dataset
- **Abstract:** Fixed-prefix counterfactual dataset for measuring whether the content of a
  real tool observation changes a language-model agent's next decision. 800 primary + 80
  reserve τ-bench prefixes (airline/retail), five observation arms (verbatim JSON, faithful
  prose, non-critical change, critical error, critical-plus-contradiction), frozen
  perturbation records, scrubbed decision/recovery/jitter ledgers from three open-weight
  8–9B models (21,611 confirmatory generations), audit packets/sheets, every analysis JSON
  behind the paper's 11 main and 14 supplementary tables, and the exploratory
  second-renderer artifact (2,250 generations on 150 prefixes) with its ledgers and rebuild
  code. Confirmatory analysis complete with three failed gate criteria reported;
  measurement framing, no causal claim; the second-renderer check is exploratory and
  unpooled.
- **Licenses (dual):**
  - **Data (project additions): CC BY 4.0** — `DATA_LICENSE.md`, also stated in the
    data card; selected as the Zenodo record license.
  - **Code (repository software): MIT** — `LICENSE`, `CITATION.cff`, and the record
    description/notes.
  - Upstream τ-bench: MIT (Sierra copyright), full text bundled in
    `licenses/TAU_BENCH_LICENSE_MIT`; model-output notices in
    `licenses/MODEL_OUTPUT_LICENSES.md` and `ATTRIBUTION.md`.
- **Related identifiers (deposited):**
  - Repository (code, MIT): https://github.com/Atik203/tool-observation
    (relation: *is supplemented by*)
  - Upstream dataset: https://github.com/sierra-research/tau-bench @
    `59a200c6d575d595120f1cb70fea53cef0632f6b` (relation: *is derived from*)
  - τ-bench paper: https://arxiv.org/abs/2406.12045 (relation: *references*)
  - Preregistration deposit: freeze commit `1673856`, tag `prereg-freeze-v1`, hash
    `e0d107c6`; `prereg/PREREGISTRATION.md` + `prereg/AMENDMENTS.md` (A-001–A-011) are
    bundled under `prereg/` (relation: *is documented by*)
  - Paper: Tool-Result Errors in Language-Model Agents (measurement study; under
    submission; the dataset is its supplement, described in the Data-availability bullet)
- **Manifest hash (authoritative):**
  `d6e034d7f1132b314ad1f82bf14faa0f6762975ee7b404b54cc365acfac5487a`
- **Package checksum:** `release/ToolResult-800-v1.0.1/SHA256SUMS` (136 entries;
  SHA-256 `8ce5248a44658e34dabb0fd7e4bd9a2c07ab4ee12d4ff258886ced33dd250f79`).
  Deposited archive `ToolResult-800-v1.0.1.zip` SHA-256
  `83fadce666d034b8c53bdfc3bfe4c10f1b684c421fb6090c5de96dd66c89fa85`
  (6,944,006 bytes, 138 entries).
- **Notable artifact provenance:** `analysis/rowlevel_refits.json` was generated at
  commit `8e6f536` (2026-11-23 02:24 +0600), SHA-256
  `965805eac2791a0d40757777d537db4205c4d4c046d6b2732c2f272c9dbedfcb`. Its
  `reconciliation.note` wording was corrected as a text-only fix later committed as
  `7f0169d` (prefix-resampling sensitivity, `design_valid=false`, not a cluster
  bootstrap); the wording was in the working tree at generation, so the recorded
  commit lags the note text. No number changed, and a rerun reproduces every field
  except `recorded_utc`/`git_commit` (`release_record.json`
  `artifact_provenance_notes`).

## Mint log

| Step | Status | Date/actor |
|---|---|---|
| Package staged + validated (18/18 L1, 24/24 with `--rerun`) | done (agent) | 2026-11-23 |
| Clean-room compile (36 pages, 0 undefined, 0 BibTeX warnings) | done (agent) | 2026-11-23 |
| Draft deposition created; DOI reserved (`10.5281/zenodo.24449467`) | done (agent) | 2026-11-23 |
| Archive + `SHA256SUMS` uploaded | done (agent) | 2026-11-23 |
| Uploaded file list / archive checksums verified against `SHA256SUMS` | done (agent) | 2026-11-23 |
| DOI minted by publishing the record | done (agent) | 2026-11-23 |
| DOI resolves (URL returns record) | done (agent) | 2026-11-23 |
| DOI recorded in CITATION.cff / data card / paper | done (agent) | 2026-11-23 |

### Verification details

- Record: <https://zenodo.org/records/24449467>; DOI
  <https://doi.org/10.5281/zenodo.24449467>; concept DOI
  <https://doi.org/10.5281/zenodo.24449466>. Resolver returned HTTP 200 at the
  record URL on 2026-11-23; DataCite CSL JSON content negotiation returned a
  `dataset` with the same title and DOI.
- Uploaded files: `ToolResult-800-v1.0.1.zip` (6,944,006 bytes, MD5
  `e8c361448d4b59a472942470cf333d00`) and `SHA256SUMS` (14,158 bytes, MD5
  `0842c738ab798791ec644dd5c6c2e81a`) — 2 files; Zenodo's 100-file record cap
  forces a single archive. Both downloads were re-hashed after upload and match
  the local bytes (SHA-256 and MD5).
- Archive verification: the zip was downloaded from Zenodo, extracted, and every one of
  its 136 checksummed entries was checked against the `SHA256SUMS` inside the archive
  and against the deposited top-level `SHA256SUMS`; 0 mismatches, 0 missing, 0 extra.
- Archive SHA-256: `83fadce666d034b8c53bdfc3bfe4c10f1b684c421fb6090c5de96dd66c89fa85`.
- Package build commit: `074d217` (the release-content commit; the package's
  `release_record.json` records this commit, `doi` field
  `10.5281/zenodo.24449467`, and 136 files). A rebuild at post-release commit
  `6b88f5e` produced the identical 138-file set with 0 non-volatile byte
  differences (only `created_utc`/`git_commit`, the generated timestamps, `README.md`,
  and the checksums covering them differ).
