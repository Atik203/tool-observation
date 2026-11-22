# P5 submission checklist — ToolResult-800 v1.0

Status 2026-11-22 (Task 7). Items marked [x] are complete and evidenced; items marked [ ]
require author action and name the artifact that unblocks them.

## Manuscript

- [x] Title/abstract/intro/results/conclusion use one measurement claim; no causal or
  content-sensitivity claim (C1; `tab:gate-status`, `tab:hypotheses`).
- [x] All three gate failures stated (parser 1.55%, severity 88.3%, crude recovery
  24.4/32.9/21.3% on the semantic risk set); G1 original criterion reported as failed (A-004/D-041).
- [x] 11 main-text and 14 supplementary tables all cited; 10 figures all cited; 0 undefined refs; 0 duplicate labels
  (`pytest tests/test_release.py`).
- [x] 69/69 bib entries cited; 9 author lists completed from arXiv (4 legacy
  `[VERIFY CITATION]` + tool_survey/agent_survey/helm + toolscan/toolbehonest);
  BFCL URL verified; only remaining "et al." is the 100+-author Llama herd.
- [x] 6 keywords (journal cap); 4 highlights ≤85 chars (`docs/submission/highlights.md`).
- [x] Fig. 4 is a labeled conceptual schematic (T5); no draft stamps; no `\pending{}` uses.
- [x] PDF metadata title matches; byline/ORCID/CRediT reconciled (pending signatures below).
- [ ] Clean-room compile from the 14-file Overleaf zip — **cannot run here (no TeX
  toolchain on this host)**. Zip built and checksummed
  (`dist/toolresults-overleaf.zip`, see report); compile must be confirmed on Overleaf
  before submission. Structural checks substitute locally: 75/75 labels defined, all
  floats cited, all cite keys resolve.

## Release / DOI

- [x] Release staged: `release/ToolResult-800-v1.0/` (123 files), manifest hash chain ok,
  SHA256SUMS verified, automated identifier re-scan clean (`pii_rescan.json`).
- [x] Table-to-artifact map covers all 25 table labels (11 main-text, 14 supplementary; `TABLE_MAP.md`).
- [x] One-command validation implemented and passing: `make validate-release` 17/17 L1,
  22/22 with `--rerun` (T4 inference regen included).
- [x] License verification recorded (`licenses/`, `docs/submission/license_verification.md`).
- [x] Data card corrected (no "human labels" claim; G0 provisional; release inventory).
- [x] AI disclosure names sessions/dates/prompts/interface/hypothesis-blinding + T6
  single-agent part (paper Declarations).
- [ ] DOI minted and recorded in `CITATION.cff` + data card — **author action**
  (deposit record ready: `docs/submission/doi_record.md`).
- [ ] Repository tag + GitHub release match v1.0 — **author action**.
- [ ] Second-person checksum verification — **author action**.

## Human-gated items (cannot be completed by the agent)

- [ ] Independent human PII re-scan of the release candidate (automated scan is clean;
  the v1.0.1 builder redacts the scrubber-artifact identity class on every build and
  `pii_rescan.json` reports zero hits plus `n_redactions`, so no fragment remains in the
  package).
- [ ] Human audit subset (G0 40-item + 60–120-item held-out) or accept the disclosed
  AI-only status quo for this venue.
- [ ] Ethics determination for the annotation procedure (paper cites as pending).
- [ ] Author list freeze: sign-off on order, spelling, e-mails, ORCIDs, CRediT
  (`docs/submission/authorship.md`).

## Author sign-off

| Item | M.A.R. | O.T. | Date |
|---|---|---|---|
| Byline / ORCID / CRediT freeze | _pending_ | _pending_ | |
| Ethics determination cited | _pending_ | _pending_ | |
| DOI + tag + release approved | _pending_ | _pending_ | |
| Submission approved | _pending_ | _pending_ | |
