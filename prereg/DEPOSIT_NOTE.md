# Preregistration freeze and deposit note (P4.4)

- **Frozen version:** commit `1673856cc6cd335ae9fd8b0132343082f167077a`
  (short `1673856`, 2026-11-15), tag `prereg-freeze-v1`, prereg hash
  `e0d107c6` (authoritative; the document header's DRAFT/TBD lines are stale
  and are not amended, per the no-edit rule). The tag object and the
  manifest's `freeze.git_commit` carry the same full hash; the earlier
  `1675376` here was a typo, corrected 2026-11-22 under P6.1.
- **External registry:** none. The deposit is in-repo until the release DOI
  (Task 7): `prereg/PREREGISTRATION.md` (frozen) + `prereg/AMENDMENTS.md`
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
