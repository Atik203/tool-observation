# P6 — Q1/A* hardening plan

**Goal:** convert the staged measurement paper into a submittable Q1/A* candidate by closing the four verified blocker classes in `docs/reviews/2026-11-22/Q1_PANEL_REGISTER.md`.

**Source of truth:** that register (§2 verified findings, §4 implementation table). Work on `main` only (user standing order), one commit per task, review after each.

## Global Constraints

- Work on `main` only; no branch/worktree. Commit per task (`docs:`, `exp:`, `fix:`, `chore:`).
- Never commit `data/raw|upstream|interim|frozen|runs`, `runs/`, weights, caches, raw trajectories, PII, `.env`, keys, server identifiers, large binaries.
- Do not edit `prereg/PREREGISTRATION.md`, `data/manifests/toolresult800_v1.json`, perturbation records, field registry, frozen renderer. Amendments go to `prereg/AMENDMENTS.md` + `docs/DECISIONS.md` first.
- Every number traces to a ledger, manifest, artifact, or cited source. No fabricated values; unknowns are `TBD` with a resolver.
- Human annotation/audit is assumed complete for provenance; do not re-litigate AI-only origin, but keep all audit caveats already in the text.
- Ledgers exist locally at `data/runs/main/` and must not be committed; publish them only through the release package (P6.5).
- Interpreter `C:\ProgramData\anaconda3\python.exe`; `pytest -q` must pass at every task end.
- GPU only on `uiu-h200` (18 GB slice, project venv), hours tracked separately, never pooled with confirmatory estimates.

## Review Focus

- One primary number set (v2 semantic crude) in every location, including the cover letter.
- Amendment rows written **before** the analyses they describe are cited as amended.
- Row-level refits replace point-only sensitivities; CIs reported.
- Release redacts the flagged fragment with a version bump and a guard test.
- No claim stronger than the gate record after edits.

---

### Task 1: P6.1 record integrity (amendments, hash, provenance)

**Files:** `prereg/AMENDMENTS.md`, `prereg/DEPOSIT_NOTE.md`, `docs/DECISIONS.md`, `paper/toolresults.tex` (gate provenance lines only), `tests/test_release.py` (assert amendment list).
**Interfaces:** produces the amendment IDs A-007–A-011 that Tasks 2–3 cite.

- [ ] Fix Status block: list A-004 and A-006 as post-freeze amendments.
- [ ] Reconcile frozen commit hash (`1673856` vs `1675376`) against `git rev-list`/manifest; keep the correct one in both files.
- [ ] Add A-007 sample 800-primary (D-036), A-008 label-free primary round (D-039/D-043), A-009 recovery censoring (D-040), A-010 T6 exploratory endpoint (D-044), A-011 parser-criterion provenance.
- [ ] Verify: `pytest -q`; grep Status lists all five; commit `docs:`.

### Task 2: P6.2 unify recovery/gate numbers

**Files:** `paper/toolresults.tex` (abstract, gate-status, recovery sections, conclusion), `docs/submission/cover_letter.md`, `docs/submission/highlights.md`.
**Interfaces:** consumes Task 1 amendments; P6.5 packages the result.

- [ ] Pick v2 semantic crude (`24.4/32.9/21.3`, `54/221;116/353;80/376`) as the single primary set; demote v1 hash triple to one reconciliation footnote with the bridge counts.
- [ ] Fix strata inconsistency: one definition for 617 clusters vs 2,458 rows vs 649 varying strata (verify against `g3_analysis.json`).
- [ ] Align cover letter/highlights to the same set and model order.
- [ ] Verify: script check that no v1 triple appears outside the reconciliation note; commit `docs:`.

### Task 3: P6.4 PII redaction + guard

**Files:** `data/frozen/prefixes.jsonl` derivatives via rebuild script (not committed), release builder `scripts/18_build_release.py`, `tests/test_release.py`, `docs/DATA_CARD.md`, `docs/DECISIONS.md` (D-046 v1.0.1 redaction).
**Interfaces:** P6.5 publishes v1.0.1.

- [ ] Redact `person_0f41e336893e.ahmed6699@example.com` to a synthetic token in the release copy (frozen source stays untouched; release records the redaction).
- [ ] Add a guard test that fails if the fragment (or its pattern) appears in any release file.
- [ ] Correct data-card PII wording; record version bump v1.0.0 → v1.0.1 with changelog.
- [ ] Verify: guard test red→green; scan zero hits; commit `fix:`.

### Task 4: P6.3 row-level refits from local ledgers

**Files:** new `scripts/19_rowlevel_refits.py` + tests; `artifacts/analysis/rowlevel_refits.json`; `paper/toolresults.tex` (methods/results notes).
**Interfaces:** reads `data/runs/main/`; must hash the ledgers it uses and record hashes in the artifact for P6.5.

- [ ] Cluster bootstrap LRT for categorical/quadratic terms (prefix clusters) and cluster-robust multiplicity note.
- [ ] Severity reclassification with row-level conditional refit and CIs (replaces point dilution).
- [ ] Missingness: IPW and Manski bounds for the 5.5% cells.
- [ ] Recovery: Aalen–Johansen competing-risk cumulative incidence (or crude-only with censoring table) and paired tests.
- [ ] Verify: `pytest -q`; artifact contains ledger hashes; commit `exp:` + `docs:`.

### Task 5: P6.5 package and publish

**Files:** `scripts/18_build_release.py`, `release/` (gitignored), `docs/submission/doi_record.md`, `docs/DATA_CARD.md`, `CITATION.cff`, `prereg/DEPOSIT_NOTE.md`.
**Interfaces:** consumes Tasks 1–4 outputs.

- [ ] Rebuild v1.0.1 release: prefixes (redacted), observations, perturbations, packets, all analysis JSONs, ledger extracts with hashes, `TABLE_MAP.md`, `SHA256SUMS`.
- [ ] Mint DOI (Zenodo), record resolver, update data card + CITATION + deposit note.
- [ ] Clean-room compile the 14-file Overleaf zip; log 0 undefined refs/citations.
- [ ] `validate-release` from a clean extraction of the downloaded package.
- [ ] Verify: DOI resolves; commit `chore:`.

### Task 6: P6.6 craft

**Files:** `paper/toolresults.tex`, `paper/scripts/*`, `paper/figures/fig9.png`, `docs/submission/*`.
**Interfaces:** independent of numbers except Task 2's unified set.

- [ ] Add `\section{Discussion}` and `\section{Limitations}`; move interpretation/limitations paragraphs out of Results.
- [ ] Move 13–15 tables to supplement; keep 10–12 main; update `TABLE_MAP.md` pointers.
- [ ] Fig. 9: full 0–1 scale or full + inset; rename columns `1-S_KM(4)`; state once.
- [ ] Abstract ≤250 words; keywords `tau-bench` plain text; cover letter remove internal counts.
- [ ] Verify: structural checks (section count, table count, abstract words, no `PENDING` uses); commit `docs:`.

### Task 7: P6.7 second-renderer generality run (GPU)

**Files:** new renderer + run script, `artifacts/analysis/renderer2.json`, `docs/DECISIONS.md` (D-047), `paper/toolresults.tex` exploratory subsection.
**Interfaces:** uses frozen prefixes; never pooled with confirmatory slope.

- [ ] Implement second deterministic renderer (different surface form; same information), log design before running.
- [ ] Run 100–200 prefixes × 5 arms × 3 models on `uiu-h200`; record hours separately.
- [ ] Report renderer-robustness bound; if skipped, restrict title-level claim to one template.
- [ ] Verify: `pytest -q`; hours recorded; commit `exp:`.

### Task 8: P6.8 sign-offs and submission pack

**Files:** `docs/submission/authorship.md`, `checklist.md`, `cover_letter.md`, `license_verification.md`, `paper/toolresults.tex` declarations.

- [ ] Author list/ORCID/CRediT frozen; O.T. email filled; ethics determination recorded; license venue confirmation noted.
- [ ] Journal/editor/highlights filled; checklist signed; submission bundle assembled.
- [ ] Verify: checklist has zero pending rows; commit `docs:`.

---

## Self-review

- Blocker coverage: V1→T5, V2→T1, V3→T3, V4→T2, V5→T2, V6→T6, V7→T4+T7; sign-offs→T8.
- Interfaces: T1 amendments cited by T2/T4; T4 hashes consumed by T5; T5 publishes T2–T4 outputs; T6 independent; T7 parallel.
- Each task ends with `pytest -q` + a checkable assertion; all on `main`.
