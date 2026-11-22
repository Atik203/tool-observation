# Preregistration freeze and deposit note (P4.4)

- **Frozen version:** commit `1673856cc6cd335ae9fd8b0132343082f167077a`
  (short `1673856`, 2026-11-15), tag `prereg-freeze-v1`, prereg hash
  `e0d107c6` (authoritative; the document header's DRAFT/TBD lines are stale
  and are not amended, per the no-edit rule). The tag object and the
  manifest's `freeze.git_commit` carry the same full hash; the earlier
  `1675376` here was a typo, corrected 2026-11-22 under P6.1.
- **External registry:** none. The deposit is in-repo until the release DOI
  (now minted: `10.5281/zenodo.24449467`, 2026-11-23): `prereg/PREREGISTRATION.md`
  (frozen) + `prereg/AMENDMENTS.md`
  (A-001–A-011) + `data/manifests/toolresult800_v1.json` (hash sidecar).
  A-007–A-011 record post-freeze analysis-record items (decisions and the
  A-011 provenance finding) and were entered on 2026-11-22 (D-036, D-039,
  D-040, D-043, D-044); see the amendment table for the entry-date
  convention.
- **This task (P4.4) itself adds no amendment**; A-007–A-011 were entered
  later under P6.1 and are listed above. Outcome-definition handling is by
  reported sensitivity, not by rule change: strict flag-excluding coding
  (≈ signature-only $Y$) leaves the slope unchanged (0.876 vs 0.877), and
  $Y^O$ is decomposed separately. See
  `artifacts/analysis/inference_robustness.json` (regenerable via
  `scripts/16_inference_robustness.py`).
- **Pre-fix record (M22):** the pre-fix automatic coder gave pooled
  $\hat\beta = 0.684$ [0.584, 0.797]; the artifact was not retained. The
  number is cited from A-006/ROADMAP and disclosed as pre-fix, not
  reconstructed.
- **Audit circularity (M9):** the post-fix coder was conformed on the same
  160 outcome items used to certify $\kappa=.987$/PPV=1.00 — the audit is
  in-sample. No fresh held-out audit exists; the held-out plan (reserve
  prefixes, 60–120-item human audit) is future work.
- **Provenance:** multi-role agent panel, author-overseen.

## P6.5 Phase A packaging note (2026-11-23)

- **Release rebuilt:** `release/ToolResult-800-v1.0.1/` — 127 checksummed files (129
  files including `SHA256SUMS` and `release_record.json`), built by
  `scripts/18_build_release.py --build` with release-copy redaction on (D-046). Adds
  `analysis/rowlevel_refits.json` (P6.3) and `traces/ledger_hashes.json` (SHA-256 +
  byte size of every distributed ledger extract, computed after redaction). The
  exploratory P6.7 second-renderer runs (D-048) are excluded pending a separate
  deposit decision.
- **Table map:** all 25 paper tables mapped as 11 main-text (1–11) and 14
  supplementary (S1–S14, the paper's `\section*{Supplementary tables}`).
  `tab:recovery` points at the v2 semantic risk set; the v1 hash set is the single
  reconciliation note (27.3/34.7/27.2 crude; 32.4/47.6/28.2 KM, decomposing as
  54+18=72, 116+25=141, 80+32=112).
- **Artifact provenance:** `analysis/rowlevel_refits.json` was generated at commit
  `8e6f536` (SHA-256 `965805ea…dbedfcb`); its `reconciliation.note` is the text-only
  correction later committed as `7f0169d`. No number changed; a rerun reproduces every
  field except `recorded_utc`/`git_commit`.
- **Validation:** 17/17 L1 on the staged package; 23/23 with `--rerun` (six CPU-only
  producers rebuilt: `g4_recovery_v2`, `severity_sensitivity`, `rowlevel_refits`,
  `inference_robustness`, `wrong_direction`, `new_evidence`). Automated identifier
  re-scan clean (0 hits); the independent human re-scan remains pending.
- **Clean-room compile:** the 14-file Overleaf zip compiled with TeX Live 2026 via
  `latexmk -pdf` — 35 pages, 0 undefined references, 0 undefined citations, 0 BibTeX
  warnings.
- **Licenses (dual):** data CC BY 4.0 (`DATA_LICENSE.md`); code MIT (`LICENSE`,
  `CITATION.cff`); upstream τ-bench MIT.
- **Related identifiers for the deposit:** repository
  https://github.com/Atik203/tool-observation; upstream τ-bench @
  `59a200c6d575d595120f1cb70fea53cef0632f6b`; this prereg freeze commit `1673856`,
  tag `prereg-freeze-v1`, hash `e0d107c6`, bundled under `prereg/` in the package.
- **DOI:** published **2026-11-23** as `10.5281/zenodo.24449467`
  (<https://doi.org/10.5281/zenodo.24449467>, Zenodo record 24449467). The record
  carries the v1.0.1 package archive, the package `SHA256SUMS`, and the DataCite
  metadata in `docs/submission/doi_record.md`. The token in `.env` was read only
  at mint time (in-process) and was never printed or committed.

## P6.5 Phase B publication note (2026-11-23)

- **Package:** `release/ToolResult-800-v1.0.1/` — 136 checksummed files (138 with
  `SHA256SUMS` and `release_record.json`). Adds the exploratory P6.7
  `analysis/renderer2.json`, its three renderer-2 ledgers under
  `traces/renderer2/`, and `code/` (parser-v4 rescore + second-renderer sources).
  `traces/ledger_hashes.json` now records 24 extracts (21 confirmatory + 3
  renderer-2).
- **Validation:** 18/18 L1 on the package alone (includes renderer-2 ledger hashes
  and an ordered main-text table check via `paper_audit.json`); 24/24 with
  `--rerun` (six CPU-only producers).
- **Clean-room compile:** 36 pages, 0 undefined references, 0 undefined citations,
  0 BibTeX warnings; the paper's Data-availability bullet carries the DOI.
- **DOI:** `10.5281/zenodo.24449467`; resolver verified. Zenodo caps a record at
  100 files, so the record holds the release archive + `SHA256SUMS`; every archive
  entry was re-checked against `SHA256SUMS` after download.

## T7 staging note (2026-11-22, P4.7/P5)

- **Release staged:** `release/ToolResult-800-v1.0/` (123 files) built by
  `scripts/18_build_release.py --build`: frozen manifest + sidecar, perturbation
  records, source pin, 880 scrubbed prefixes, scrubbed ledger extracts, audit
  packets/sheets/instructions + verification record, all 27 analysis JSONs, T6
  packets/maps/codes, prereg + amendments + this note, upstream MIT notice,
  model-output license verification, `TABLE_MAP.md`, `VALIDATION.md`,
  `SHA256SUMS`, `release_record.json`, `pii_rescan.json` (clean: 0 identifier
  hits; reserved-domain placeholders, synthetic-token echoes, and one
  scrubber-artifact name fragment noted; human re-scan pending).
- **Validation:** `make validate-release` — 17/17 L1 checks on the staged tree
  (manifest chain, SHA256SUMS, crude triple, v2 bridge + Wilson, severity
  7/11/16, McNemar/LRT/H5 recomputes, wrong-direction partition, g3 totals,
  utility counts, PPV bound, table-map coverage, PII re-scan) and 22/22 with
  `--rerun` (all five producers rebuilt bit-identical modulo
  `recorded_utc`/`git_commit` — this doubles as the T4 inference-JSON regen).
- **DOI:** still pending author upload (no external registry yet). Deposit record
  with DataCite metadata is in `docs/submission/doi_record.md`; the DOI lands
  here, in `CITATION.cff`, and in `docs/DATA_CARD.md` at release.
- **Provenance:** multi-role agent panel, author-overseen (T6 packet contents
  remain single-agent coded, author-overseen, as disclosed).
