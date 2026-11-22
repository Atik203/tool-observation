# DOI deposit record — ToolResult-800 v1.0.2

**Status 2026-11-23: PUBLISHED (v1.0.2 path-leak errata).** Version DOI
**`10.5281/zenodo.24449882`** (resolver:
<https://doi.org/10.5281/zenodo.24449882>), Zenodo record **24449882**, version 1.0.2,
publication date 2026-11-23. Concept DOI **`10.5281/zenodo.24449466`** (record
24449466), so the version lineage is preserved.

**Superseded:** v1.0.1, DOI `10.5281/zenodo.24449467` (record 24449467), remains
published and immutable but is superseded and must not be cited for the package bytes.
Its archive exposed absolute build-machine/server paths (16 occurrences in 8 files); the
errata are described in the record description, the package `CHANGELOG.md`, and D-050.

The record holds the exact release archive plus the package `SHA256SUMS`. Zenodo caps a
record at 100 files, so the 139-file package is deposited as
`ToolResult-800-v1.0.2.zip` + `SHA256SUMS`; the archive's internal file list and checksums
are the same `SHA256SUMS` (137 entries). Verification evidence is in the mint log below.
The Zenodo token lives only in `.env` (key `zendo_token`, the account's actual key name) and
was read in-process at mint time; it was never printed, logged, echoed, or committed.

## Release evidence (2026-11-23)

- **Package:** `release/ToolResult-800-v1.0.2/` — 137 checksummed files (139 files
  including `SHA256SUMS` and `release_record.json`); `SHA256SUMS` verified against
  every file. `SHA256SUMS` SHA-256:
  `c0bc4fd52447861fc904006054339ab057f4df7d813f0ac7967f8f99c10cd902`
  (14,242 bytes).
- **Path scrub (v1.0.2 fix):** 16 occurrences in 8 files replaced by `[repo]` at build
  time; `path_rescan.json` reports 0 residual hits. Affected v1.0.1 files:
  `labels/g0_report.md` and `analysis/g3_analysis*.json` (repository root),
  `labels/g1_calibration_v3.json` (server home directory), and the three
  `analysis/jitter_stability_*.json`. Generated source artifacts outside the release are
  unchanged.
- **Redaction:** applied at build time (D-046); 8 occurrences in 4 files;
  `pii_rescan.json` reports 0 identifier hits and `n_redactions > 0`. The independent
  human re-scan remains an author-gated item (`docs/submission/checklist.md`).
- **L1 validation:** `python scripts/18_build_release.py --validate --root
  release/ToolResult-800-v1.0.2` — **19/19** checks (manifest chain, checksums, v2
  semantic recovery triple + v1 reconciliation, v2 bridge/Wilson, severity 7/11/16,
  McNemar/LRT/H5, wrong-direction, g3 totals, utility, PPV bound, 11 ordered main +
  S1–S14 table coverage, renderer-2 ledger hashes, path re-scan, identifier re-scan).
  L1 uses the bundled `paper_audit.json`, so it needs no repository checkout.
- **L2 rerun:** `--validate --rerun` — **25/25**; six CPU-only producers rebuilt
  (`g4_recovery_v2`, `severity_sensitivity`, `rowlevel_refits`,
  `inference_robustness`, `wrong_direction`, `new_evidence`) and diffed against the
  released JSONs modulo `recorded_utc`/`git_commit`. Both levels were also run against
  the **extracted download** from Zenodo (19/19 and 25/25).
- **Clean-room compile:** the 14-file Overleaf zip (`toolresults.tex`, `ref.bib`,
  `cas-common.sty`, `cas-sc.cls`, `figures/fig1–fig10.png`) compiled with TeX Live
  2026 via `latexmk -pdf` in a fresh temp directory: **36 pages**, **0 undefined
  references, 0 undefined citations, 0 LaTeX warnings, 0 BibTeX warnings**; the
  remaining output is **2 font warnings** and **46 pdfTeX duplicate-destination
  notices**. No absolute paths in the extracted sources or the PDF. Zip SHA-256
  `cf3206a6746d6bd1812672ba1dbb739dd887c3bb7e1e3ccbac4be5ec3e12c3db`
  (3,391,334 bytes); combined 14-file manifest SHA-256
  `64a329cd2abf48ab70b5f7002dee7c49d66a679e3e74e6bfa8f70e6d2f0759e7`.
  PDF SHA-256 `c7ebc0c7821b02395604c48d2b81b28c8b567e45ef13777f3efa5265b12ea78e`
  (4,046,079 bytes). The paper's Data-availability bullet carries this version DOI and
  the concept DOI.
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
- **Version:** 1.0.2 (builder `stage-18 v4`; commit recorded in
  `release_record.json`)
- **Resource type / publisher:** Dataset / Zenodo
- **Abstract:** Fixed-prefix counterfactual dataset for measuring whether the content of a
  real tool observation changes a language-model agent's next decision. 800 primary + 80
  reserve τ-bench prefixes (airline/retail), five observation arms (verbatim JSON, faithful
  prose, non-critical change, critical error, critical-plus-contradiction), frozen
  perturbation records, scrubbed decision/recovery/jitter ledgers from three open-weight
  8–9B models (21,611 confirmatory generations), audit packets/sheets, every analysis JSON
  behind the paper's 11 main and 14 supplementary tables, and the exploratory
  second-renderer artifact (2,250 generations on 150 prefixes) with its ledgers and rebuild
  code. v1.0.2 removes absolute build-machine/server paths from the distributed copies;
  no number changes. Confirmatory analysis complete with three failed gate criteria
  reported; measurement framing, no causal claim; the second-renderer check is exploratory
  and unpooled.
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
- **Concept DOI (all versions):** `10.5281/zenodo.24449466`
- **Manifest hash (authoritative):**
  `d6e034d7f1132b314ad1f82bf14faa0f6762975ee7b404b54cc365acfac5487a`
- **Package checksum:** `release/ToolResult-800-v1.0.2/SHA256SUMS` (137 entries;
  SHA-256 `c0bc4fd52447861fc904006054339ab057f4df7d813f0ac7967f8f99c10cd902`).
  Deposited archive `ToolResult-800-v1.0.2.zip` SHA-256
  `e63e0c1313e15095619fad7950fd82291ed8b681bdcd961ef7e3a6b4d96ca113`
  (6,947,000 bytes, 139 entries; MD5 `1e3783f4ec5007c3a56a30d77b126e99`).
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
| v1.0.2 package staged + validated (19/19 L1, 25/25 with `--rerun`) | done (agent) | 2026-11-23 |
| Clean-room compile (36 pages, 0 undefined, 0 LaTeX warnings) | done (agent) | 2026-11-23 |
| New version draft created from record 24449467; version DOI reserved | done (agent) | 2026-11-23 |
| Metadata set (version 1.0.2, publication date, path-errata description) | done (agent) | 2026-11-23 |
| Archive + `SHA256SUMS` uploaded | done (agent) | 2026-11-23 |
| Uploaded file list / archive checksums verified against `SHA256SUMS` | done (agent) | 2026-11-23 |
| Version published (record 24449882) | done (agent) | 2026-11-23 |
| DOI resolves (HTTP 200 → record page) | done (agent) | 2026-11-23 |
| Downloaded archive re-verified (L1 19/19, L2 25/25, 137/137 checksums, 0 path hits) | done (agent) | 2026-11-23 |
| DOI recorded in CITATION.cff / data card / deposit note / paper | done (agent) | 2026-11-23 |

### Verification details

- Record: <https://zenodo.org/records/24449882>; version DOI
  <https://doi.org/10.5281/zenodo.24449882>; concept DOI
  <https://doi.org/10.5281/zenodo.24449466>. The resolver returned HTTP 200 and
  redirected to the record page on 2026-11-23. The API record reports
  `version 1.0.2`, `publication_date 2026-11-23`, `status published`, 2 files.
- Uploaded files: `ToolResult-800-v1.0.2.zip` (6,947,000 bytes, MD5
  `1e3783f4ec5007c3a56a30d77b126e99`) and `SHA256SUMS` (14,242 bytes, MD5
  `d967aeb63a903c92cab02cb58a9c9ad2`) — 2 files; Zenodo's 100-file record cap
  forces a single archive. Both downloads were re-hashed after upload and match
  the local bytes (SHA-256 and MD5).
- Archive verification: the zip was downloaded from Zenodo, extracted, and every one
  of its 137 checksummed entries was checked against the `SHA256SUMS` inside the
  archive and against the deposited top-level `SHA256SUMS` (byte-identical);
  **0 mismatches, 0 missing, 0 extra**. `release_record.json` re-hashes all 137 files
  with 0 mismatches.
- Path verification: the downloaded archive's text entries contain 0 matches for the
  server-home, workstation-home, or repository-root path patterns; the extracted tree
  passes the L1 `path-rescan` check.
- Archive SHA-256: `e63e0c1313e15095619fad7950fd82291ed8b681bdcd961ef7e3a6b4d96ca113`.
- Package build commit: `release_record.json` names `6510c4e` (the base commit; the
  release content was finalized in the working tree before the release-content commit
  `b4ea98c`). A rebuild at `b4ea98c` produced the same 139-file set with **0
  non-volatile byte differences**; only `created_utc`/`git_commit`, the generated
  timestamps (`README.md`, `path_rescan.json`, `pii_rescan.json`,
  `traces/ledger_hashes.json`), and `SHA256SUMS`/`release_record.json` covering them
  differ. `release_record.json` records `doi` `10.5281/zenodo.24449882`,
  `concept_doi` `10.5281/zenodo.24449466`, and 137 files.
- Metadata revision: a metadata-only edit (legacy deposition API, same DOI) restored the
  record license (`cc-by-4.0`), keywords, notes, language, and Zenodo publisher after the
  first publish; the files were not changed (identical sizes and checksums, verified via
  the API). Concept DOI `10.5281/zenodo.24449466` resolves (HTTP 200) to the latest
  version page.
- v1.0.1 record 24449467 is unchanged and still resolves; it is superseded, not
  deleted.
