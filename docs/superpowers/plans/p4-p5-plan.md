# P4/P5 Execution Plan — ToolResult-800 revision to submission

**Goal:** Close ROADMAP P4 workstreams P4.1–P4.7 and complete P5 release/submission, driven by `docs/reviews/2026-11-22/WEAKNESS_REGISTER.md` (C1–C14, M1–M22). All work on `main` per user instruction (no worktree/branch).

**Sources (read before Task 1):** `ROADMAP.md`, `docs/reviews/2026-11-22/WEAKNESS_REGISTER.md`, `docs/DECISIONS.md` (D-028–D-043), `docs/GATES.md`, `prereg/AMENDMENTS.md`, `paper/toolresults.tex`, `artifacts/analysis/g3_analysis.json`, `artifacts/analysis/g4_recovery.json`, `artifacts/audit/blind_audit_result.json`, `artifacts/audit/verification/panel_record.json`.

## Global Constraints

- Work on `main` only. No new branch, no worktree. Commit per task with Conventional Commits (`docs:`, `exp:`, `fix:`, `chore:`).
- Never commit `data/raw/`, `data/upstream/`, `data/interim/`, `data/frozen/`, `data/runs/`, `runs/`, model weights, HF caches, raw τ-bench trajectories, PII, `.env`, tokens, keys, server addresses/hostnames/usernames/account IDs, large binaries. `data/manifests/` only small non-PII JSON/YAML.
- Do not edit `prereg/PREREGISTRATION.md`, `data/manifests/toolresult800_v1.json`, perturbation records, field registry, frozen renderer version. Any deviation → `docs/DECISIONS.md` + `prereg/AMENDMENTS.md` before affected analysis.
- Every number traces to a raw run ledger, manifest, or cited external source. No fabricated results. Mark unknowns TBD. Report gate failures; do not smooth over.
- Pilot numbers stay exactly: 54/60 consult, 0/60 placebo jitter, 5/60 error switch, 8.3 pp [1.3, 15.3], McNemar p=.0625, N=60, qwen3.5:4b, synthetic prefixes.
- Local interpreter `C:\ProgramData\anaconda3\python.exe` (Python 3.12). Repo imports without numpy/pandas/yaml/torch/vLLM; keep heavyweight imports lazy. `pytest -q` must pass.
- Verification provenance: "multi-role agent panel, author-overseen" — never "author-verified" or human independence.
- Recovery gate uses crude Events/n (27.3/34.7/27.2%), KM 32.4/47.6/28.2% is secondary with competing-risk caveat.
- Scope: no paid APIs, no new model families without prereg amendment, no sample expansion beyond 800+80, no dashboard/leaderboard features.
- Definition of done per task: code + test + docs + ledger row; `pytest -q` clean.

## Review Focus

- Claim boundary: measurement estimate only; no causal/content-sensitivity wording beyond gates.
- Recovery estimand: crude primary, semantic risk set, censoring-reason table.
- Audit honesty: AI-only panel disclosed; severity mismeasurement bounded.
- Reproducibility: every table maps to an artifact; DOI package.

---

### Task 1: P4.1 claim/title/abstract + P4.4 gate/integrity text + P4.5 craft blockers

**Files:**
- Modify: `paper/toolresults.tex` (title, abstract, intro, results/conclusion claim sentences, H1–H7/gate-status table, G1/A-004 history paragraph, pending blocks, Fig.4 stamp, byline/CRediT, G1 table, recovery range, two-vs-three count, notation collisions flagged)
- Read: `docs/reviews/2026-11-22/WEAKNESS_REGISTER.md` (C1, C7, C14, M6–M8), `prereg/AMENDMENTS.md`, `docs/GATES.md`

**Interfaces:**
- Consumes: current `paper/toolresults.tex` on main.
- Produces: consistent measurement claim ("measured shift among movers", no "move/causal/content-sensitivity"), failure count used everywhere, no `\pending{}`, no Fig.4 "no study outcomes" stamp.

- [ ] Step 1: Retitle away from causal study; rewrite abstract to lead with measurement + three failures (parser 1.55%, severity s2/s3 88.3%, recovery crude 27.3/34.7/27.2%); use one claim everywhere.
- [ ] Step 2: Add/refresh gate-status table (G0 provisional, G1 amended post-freeze/not blind per D-041, G3 parser fail, G3 severity fail, G4 recovery fail + Weibull 2/3 rejected); report original V-vs-s0 format jitter 20.3/36.7/45.6% as failed; delete "no threshold was changed".
- [ ] Step 3: Add H1–H7 status table; report H5; reconcile three-vs-four failure count; use one number everywhere; fix G1 table, recovery range 28.2–47.6, intro two-vs-three.
- [ ] Step 4: Clear craft blockers: remove/replace Fig.4 stamp, clear all `\pending{}`, reconcile byline/CRediT, distinguish preregistered vs protocol parser criterion.
- [ ] Step 5: Verify: `pytest -q` (if touched code: none expected); compile check if latexmk available else Python structural check (no `\pending`, one title claim, gate table present); `git add` + `git commit -m "docs: ..."`.

---

### Task 2: P4.2 recovery re-estimation (semantic risk set, crude gate, censoring)

**Files:**
- Modify/add: `scripts/` recovery re-estimation (new script or stage, e.g. `scripts/13_recovery_reestimate.py`), `artifacts/analysis/g4_recovery_v2.json` (+ `.md` gate note), `paper/toolresults.tex` recovery section/table (crude + KM columns, RMST/t12 recomputed)
- Read: `src/toolobs/recovery*.py`, `scripts/recovery_run.py`, `artifacts/analysis/g4_recovery.json`, WEAKNESS_REGISTER C2–C4

**Interfaces:**
- Consumes: frozen ledgers + `g3_analysis.json` switch sets (semantic `signatures_differ` per v4/signature v2).
- Produces: `g4_recovery_v2.json` with crude Events/n primary, KM secondary, hash-vs-semantic overlap counts (Llama 412 vs 377, Ministral 406 vs 390, Qwen 264 vs 286 reconciled), censoring-reason table (parse-fail / final-answer / ran-to-H4), recovery parse-failure rate, RMST/t12 (note 3.9–8.0, most exceed H=4).

- [ ] Step 1: Rebuild risk set from semantic switch definition; report overlap table hash-vs-semantic per model.
- [ ] Step 2: Compute crude cumulative incidence as gate statistic; keep KM as secondary with competing-risk caveat; treat final answers as failures in co-primary, parse failures as failures in sensitivity.
- [ ] Step 3: Emit censoring-reason table + recovery parse-failure rate; recompute RMST/t12; remove "Ministral close" unless failure-treated estimate supports it.
- [ ] Step 4: Update paper recovery table (add crude column; define "Recovered" as crude Events/n), rewrite recovery paragraphs.
- [ ] Step 5: Verify: focused test for new script + `pytest -q`; numbers reconcile Events/n; commit `exp:` + `docs:`.

---

### Task 3: P4.3 severity reclassification + silent-share bounds + s1 control

**Files:**
- Modify/add: reclassification script (`scripts/14_severity_sensitivity.py`), `artifacts/analysis/severity_sensitivity.json`, `paper/toolresults.tex` severity/silent paragraphs + abstract caveats
- Read: `artifacts/audit/blind_audit_result.json`, `artifacts/audit/verification/panel_record.json`, WEAKNESS_REGISTER C5, C12–C13

**Interfaces:**
- Consumes: audit sheets/packets (7/11/16 of 60 donor-unused range), tier ORs 1.27/4.60/11.21, silent 419/1964=21.3%, PPV 9/9 lower bound .66, recall .75, s1 OR 1.27 + marginal +1.1pp.
- Produces: reclassified tier ORs sensitivity, assigned-vs-realized estimand label, silent lower-bound + recall-adjusted (~28.5%) + PPV lower-bound gate row.

- [ ] Step 1: Report 7/11/16 range in results + abstract; reclassify audit-flagged items, re-estimate tier ORs (bounded sensitivity).
- [ ] Step 2: Report silent share as lower bound; add recall-adjusted estimate with uncertainty; add PPV 95% lower bound .66 to gate table.
- [ ] Step 3: Report s1 OR 1.27 [1.04,1.55] p=.019 and marginal s1–s0 +1.1pp honestly; discuss s1 contamination / low-dose framing.
- [ ] Step 4: Verify: `pytest -q`; artifact JSON present; commit.

---

### Task 4: P4.4 inference robustness + audit circularity + prereg deposit

**Files:**
- Modify/add: inference script (`scripts/15_inference_robustness.py`), `artifacts/analysis/inference_robustness.json`, `paper/toolresults.tex` methods/results notes, `prereg/` deposit note, audit circularity disclosure
- Read: WEAKNESS_REGISTER M1, M5, M7, M9, `artifacts/analysis/prereg_secondary.json`, `g3_analysis.json`

**Interfaces:**
- Consumes: prefix×model pairs (2251), McNemar b=190/c=50, categorical LRT, log-rank vs paired tests.
- Produces: per-model McNemar primary + cluster-robust/stratified + bootstrap LRT; paired/stratified log-rank with marginal log-rank labeled descriptive; H1–H7 table completed; outcome-definition amendment or signature-only sensitivity; post-fix in-sample disclosure + pre/post-fix split (β .684 noted, artifact retained or removed with note).

- [ ] Step 1: Per-model tests primary; add cluster-robust/stratified McNemar + bootstrap LRT.
- [ ] Step 2: Paired recovery tests; label marginal log-rank descriptive.
- [ ] Step 3: H1–H7 table + H5; outcome-definition sensitivity; audit-circularity paragraph + held-out plan or in-sample label.
- [ ] Step 4: Freeze/deposit prereg note; verify `pytest -q`; commit.

---

### Task 5: P4.5 figures/tables/refs + P4.1 comparison table + P4.6 wrong-direction endpoint

**Files:**
- Modify: `paper/toolresults.tex` (floats, headings, notation, effective N 617 groups/423 prefixes, mover estimand, planned-vs-executed 34800 vs 21611 table, 8.9 GPU-h), `paper/ref.bib` (2025–26 adds), `paper/figures/*` (regen at print width ≥8pt), `paper/scripts/make_result_figures.py`
- Read: WEAKNESS_REGISTER C9–C11, M2–M4, M10–M17 + contribution review neighbor list (ToolMaze, Loud Failures, Fabrication After Tool Failure, Measuring What…, ToolScan, ToolSword, ToolBeHonest, Sclar et al.)

**Interfaces:**
- Consumes: Task 2–4 numbers (do not overwrite their tables; only cite/float hygiene + new comparison/wrong-direction content).
- Produces: comparison table + narrowed novelty; format sensitivity headline (V-vs-s0 20–46% + main-run 19.8–38.1%); second-renderer note or single-renderer bound; wrong-direction analysis from perturbation records (2-day path) with R1="reference decision" rename; figures ≥600 DPI at final width, Wald-vs-bootstrap labeled, y-axis disclosed, every float cited, headings ≤5 subsections/section.

- [ ] Step 1: Add 2025–26 citations + comparison table; narrow gap to combination (not vacuum); fix M17/M19 bib hygiene (model cards, prereg citation, truncation).
- [ ] Step 2: Regenerate figures at print width with effective-font check script; fix Wald/Bootstrap labels, half-life "3.9–8.0 most exceed H=4", field-taxonomy omitted rows, missingness table (model×arm×parse + 205/250/525 reconciliation).
- [ ] Step 3: Float citations for Table 10 + Figs 5/7/8; merge/drop redundant floats; fix notation collisions (~10 symbols) + missing definitions; headings cleanup.
- [ ] Step 4: Wrong-direction / utility endpoint from perturbation records (no new GPU); rename R1 reference decision.
- [ ] Step 5: Verify: font-size + DPI check, 0 undefined refs, `pytest -q`; commit.

---

### Task 6: P4.6 new evidence streams (task-success + second renderer + human audit + probe + frontier control)

**Files:**
- Add: `scripts/16_new_evidence.py` (or staged scripts), `artifacts/analysis/new_evidence.json`, `docs/DECISIONS.md` entries, `paper/toolresults.tex` exploratory section update
- Read: D-037 (exploratory H=8 + temperature authorized, no pooling), WEAKNESS_REGISTER P2 list

**Interfaces:**
- Consumes: 800+80 prefixes, toolresult-prose-v1 renderer, pinned 8–9B trio; GPU only on uiu-h200 slice, project-local venv, hours tracked separately.
- Produces: at least ONE new stream (else tighten every claim to current scope): 100–200 prefix task-success/utility OR second deterministic renderer 100–200 OR human audit 60–120 OR intervention probe 100–200 OR frontier/on-policy control; H=8/temperature only as D-037 exploratory with own hours.

- [ ] Step 1: Pick lowest-risk stream(s) given GPU/human budget; log design in DECISIONS before running.
- [ ] Step 2: Run on uiu-h200 (track GPU-h separately; never pool with confirmatory); emit `new_evidence.json` with hours.
- [ ] Step 3: Update paper exploratory section with hours + limits; if no stream possible, tighten claims instead.
- [ ] Step 4: Verify: `pytest -q`; commit `exp:`.

---

### Task 7: P4.7 reproducibility + P5 release/submission package

**Files:**
- Add/modify: release builder (`scripts/17_build_release.py`), `release/` staging (gitignored) + DOI deposit record, `docs/DATA_CARD.md` fixes, `paper/toolresults.tex` disclosure updates, `dist/toolresults-overleaf.zip` refresh, cover letter + highlights + checklist (`docs/submission/cover_letter.md`, `checklist.md`)
- Read: WEAKNESS_REGISTER C8, C14, M18–M22, `docs/DATA_CARD.md`

**Interfaces:**
- Consumes: outputs of Tasks 1–6 (final numbers/tables).
- Produces: scrubbed artifacts/ledger extracts + manifest + packets + analysis JSONs published with DOI; table-to-artifact map; "one-command validation" implemented or removed; PII re-scan (human) + license verification (τ-bench MIT + 3 model outputs); AI disclosure (models/versions/dates/prompts/interfaces, rater-hypothesis blinding); byline/ORCID/CRediT/ethics sign-off; 14-file Overleaf zip clean-room compile; keyword/highlights within limits; submission checklist signed.

- [ ] Step 1: Build scrubbed release package + table-to-artifact map; verify external reader can reproduce reported tables.
- [ ] Step 2: PII + license clearance; fix data card ("human labels" false); ethics determination + AI-use statement; reconcile M18–M21.
- [ ] Step 3: Refresh 14-file Overleaf zip; clean-room compile (0 undefined); write cover letter + highlights; freeze author list/ORCIDs/CRediT.
- [ ] Step 4: Mint DOI; record in docs; verify resolves; complete submission checklist.
- [ ] Step 5: Verify: `pytest -q`; final ledger entry; commit (`chore:`/`docs:`).

---

## Self-review

- Spec coverage: ROADMAP P4.1→T1+T5, P4.2→T2, P4.3→T3, P4.4→T1+T4, P4.5→T1+T5, P4.6→T5+T6, P4.7→T7; P5→T7.
- Interfaces: T2–T4 produce JSONs + paper edits on disjoint sections; T5 consumes numbers read-only; T6 independent exploratory; T7 packages all.
- Every task ends with `pytest -q` + commit on main; review package uses BASE=pre-task HEAD.
- Weakness coverage: P0 (C1–C9, C14, M18–M21) in T1–T5+T7; P1 (C10, C12–C13, M1–M7, M10–M17) in T3–T5; P2 (new evidence) in T6.
