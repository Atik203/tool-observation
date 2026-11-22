# P5 submission checklist — ToolResult-800 v1.0.1

Status 2026-11-23 (Task 5, P6.5 Phase A). Items marked [x] are complete and evidenced; items
marked [ ] require author action (or remain human-gated) and name the artifact that unblocks
them.

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
- [x] Clean-room compile from the 14-file Overleaf zip with the installed TeX Live 2026:
  `latexmk -pdf -interaction=nonstopmode -halt-on-error toolresults.tex` in a fresh temp
  directory — 35 pages, 0 undefined references, 0 undefined citations, 0 BibTeX warnings
  (`dist/toolresults-overleaf.zip` refreshed from the current `paper/` tree).
  Structural checks also pass locally: 75/75 labels defined, all floats cited, all cite keys
  resolve (`pytest tests/test_release.py`).

## Release / DOI

- [x] Release staged: `release/ToolResult-800-v1.0.1/` (127 files), manifest hash chain ok,
  SHA256SUMS verified, automated identifier re-scan clean (`pii_rescan.json`).
- [x] Table-to-artifact map covers all 25 table labels (11 main-text, S1–S14 supplementary;
  `TABLE_MAP.md`), with `tab:recovery` on the v2 semantic set and one v1 note.
- [x] One-command validation implemented and passing: `make validate-release` 17/17 L1,
  23/23 with `--rerun` (six CPU-only producers, P6.3 refits included).
- [x] License verification recorded (`licenses/`, `docs/submission/license_verification.md`);
  dual license recorded (data CC BY 4.0, code MIT).
- [x] Data card corrected (no "human labels" claim; G0 provisional; release inventory).
- [x] AI disclosure names sessions/dates/prompts/interface/hypothesis-blinding + T6
  single-agent part (paper Declarations).
- [ ] DOI minted and recorded in `CITATION.cff` + data card — **author action**
  (deposit record prepared and ready: `docs/submission/doi_record.md`).
- [ ] Repository tag + GitHub release match v1.0.1 — **author action**.
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
