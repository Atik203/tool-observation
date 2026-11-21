# Paper Overleaf Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a clean, Overleaf-uploadable `toolresults` package that follows the author's calibrated voice and six-section journal format, with `fig1.png`–`fig10.png` and no non-essential files in `paper/`.

**Architecture:** First rename and relocate files without changing content, then apply the structural and voice rules section by section, then package only the LaTeX sources, class files, bibliography, and ten figures. Every task ends with a clean compile and a structural check.

**Tech Stack:** LaTeX (Elsevier `cas-sc` class), BibTeX, PowerShell, Python (Pillow, regex checks), Git.

**Spec:** `docs/superpowers/specs/2026-11-22-paper-overleaf-release-spec.md`

## Global Constraints

- Exactly six main sections: Introduction, Conventional Method, Proposed Method, Experiment, Results, Conclusion.
- Mandatory `\subsection{Evaluation Metrics}` inside Experiment.
- Conclusion is exactly one paragraph, 120–170 words.
- Body paragraphs target 120–250 words; no body paragraph below 80 words except equations, algorithms, tables, and one-line transitions.
- Every display equation is followed by a lowercase `where ...` definition sentence.
- No `Furthermore`, `Moreover`, `In conclusion`, `plays a pivotal role`, `delve`, `tapestry`, `testament`, `not only ... but also`.
- Ten figures named `fig1.png` … `fig10.png`, all at 600 DPI or higher, captions ≤ 25 words.
- `paper/` final contents: `toolresults.tex`, `ref.bib`, `cas-common.sty`, `cas-sc.cls`, `figures/fig1.png` … `fig10.png`.
- `dist/toolresults-overleaf.zip` contains exactly those 14 files and compiles from a clean extraction.
- No number, confidence interval, p-value, gate verdict, citation key, or claim strength changes.
- No new experiments, citations, or results.
- Work happens in a Git worktree, never directly on `main`.

## Review Focus

- Numeric drift during prose rewriting: every number in the abstract, text, tables, and conclusion must survive unchanged.
- Figure order after renaming: `fig1`–`fig10` must match order of appearance, and every `\figfile` path must exist.
- Citation and cross-reference breakage after the file rename: 56 cited keys, 21 tables, 10 figures, zero undefined.
- Overleaf portability: missing class/style file, absolute path, or `out/` dependency causes a clean-room failure.
- Paragraph consolidation: merged paragraphs must keep one claim per paragraph and must not merge observation, interpretation, and limitation into one undifferentiated block.

---

## Execution setup

- Create the worktree before Task 1:

```powershell
git worktree add ..\tool-observation-paper -b paper-overleaf
```

- Work from `..\tool-observation-paper` for every task. Do not edit `main`.
- Create the SDD ledger at `.superpowers/sdd/paper-overleaf/progress.md` with the first line naming this plan.
- Read `docs/superpowers/specs/2026-11-22-paper-overleaf-release-spec.md` before Task 1.
- Every task's review package uses the commit before the task as `BASE`, never `HEAD~1`.

---

## Pre-flight scan

| Shared interface | Producer | Consumer | Finding / ruling |
|---|---|---|---|
| `paper/toolresults.tex` | Task 2 | Tasks 3–7 | Single source path; Tasks 3–6 must not recreate `toolresult800.tex`. |
| `fig1.png`–`fig10.png` mapping | Task 3 | Tasks 4–7 | Mapping is fixed in the spec; no task may reorder figures. |
| κ/α/PPV/Wilson/MDE equations | Task 4 moves them | Tasks 5–6 prose | Labels `eq:kappa`, `eq:alpha`, `eq:ppv`, `eq:wilson`, `eq:mde` must survive; Task 4 compiles before prose edits. |
| `paper/out/` | Task 2 staging | Task 7 cleanup | Staging exception: `out/` exists only while building; Task 7 removes it. |
| `dist/` | Tasks 2 and 7 | Final delivery | `dist/` is gitignored; the PDF and zip are local deliverables, not commits. |
| Same-file prose edits | Task 5 | Task 6 | Tasks 5 and 6 are sequential; never dispatch two implementers on `toolresults.tex` in parallel. |
| Voice profile | Task 1 copy | Tasks 5–6 | The copied `writing-support/VOICE_PROFILE.md` is the in-repo authority after Task 1. |

No task changes a result, citation, or claim strength. The only planned content move is the metrics block from Proposed Method to the Experiment subsection, with labels preserved.

---

### Task 1: Voice profile and project brief

**Files:**
- Create: `writing-support/VOICE_PROFILE.md`
- Create: `writing-support/PROJECT_BRIEF.md`
- Read: `C:\Users\atiku\.config\opencode\skills\academic-writer-humanizer\writing-support\VOICE_PROFILE.md`
- Read: `paper/toolresult800.tex`, `artifacts/analysis/g3_analysis.json`, `artifacts/analysis/g4_recovery.json`, `artifacts/audit/blind_audit_result.json`

**Interfaces:**
- Consumes: the calibrated voice profile from the skill installation.
- Produces: `writing-support/VOICE_PROFILE.md` (verbatim copy) and `writing-support/PROJECT_BRIEF.md` with a claim–evidence map that Tasks 4–6 use as the non-negotiable content list.

- [ ] **Step 1: Copy the calibrated voice profile**

```powershell
New-Item -ItemType Directory -Force writing-support | Out-Null
Copy-Item "C:\Users\atiku\.config\opencode\skills\academic-writer-humanizer\writing-support\VOICE_PROFILE.md" writing-support\VOICE_PROFILE.md
```

- [ ] **Step 2: Write `writing-support/PROJECT_BRIEF.md`**

It must contain, with source pointers: problem, gap, objective, data, design, estimators, results index, claim–evidence map, terminology lock, and known conflicts. The claim–evidence map must include at least these rows:

| Claim | Value | Source |
|---|---|---|
| Pooled slope | 0.877 [0.770, 0.998] | `artifacts/analysis/g3_analysis.json` |
| Per-model slopes | 1.079 / 0.915 / 0.649 | same |
| Tier ORs | 1.27 / 4.60 / 11.21 | `artifacts/analysis/prereg_secondary.json` |
| Silent share | 419/1,964 = 21.3% | `artifacts/analysis/g3_analysis.json` |
| Recovery by H=4 | 32.4 / 47.6 / 28.2% | `artifacts/analysis/g4_recovery.json` |
| Parser failure | 205/13,200 = 1.55% | `artifacts/analysis/g3_report.md` |
| Severity s2/s3 gate | 53/60 = 88.3% (fail) | `artifacts/audit/blind_audit_result.json` |
| Severity α | .911 nominal / .959 interval | same |
| Outcome κ | .987 | same |
| Recovery κ | .920 step / .917 endpoint | same |
| Silent PPV / recall | 1.00 / .75 | same |
| Second-rater agreement | α .917, κ .942, κ .918/.907 | `artifacts/audit/second_rater_agreement.json` |

- [ ] **Step 3: Verify**

Run:

```powershell
Test-Path writing-support\VOICE_PROFILE.md
Select-String -Path writing-support\PROJECT_BRIEF.md -Pattern "0.877|88.3|1.55|56"
```

Expected: both files exist; the brief contains the four values.

- [ ] **Step 4: Commit**

```powershell
git add writing-support
git commit -m "docs: add voice profile and project brief for paper release"
```

---

### Task 2: Clean the paper tree and rename the source

**Files:**
- Rename: `paper/toolresult800.tex` → `paper/toolresults.tex`
- Move: `paper/EVIDENCE_MAP.md` → `docs/archive/paper/EVIDENCE_MAP.md`
- Move: `paper/README.md` → `docs/archive/paper/README.md`
- Move: `paper/REFERENCE_FORMAT.md` → `docs/archive/paper/REFERENCE_FORMAT.md`
- Move: `paper/proposal.tex` → `docs/archive/paper/proposal.tex`
- Move: `paper/figures/README.md` → `docs/archive/paper/figures-README.md`
- Move: `paper/scripts/` → `scripts/paper_figures/`
- Move: `paper/out/toolresult800.pdf` → `dist/toolresults.pdf` (create `dist/`)
- Remove: `paper/out/` after the PDF move

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: the new source path `paper/toolresults.tex`; all later tasks edit only this file.

- [ ] **Step 1: Move archive files with `git mv`**

```powershell
New-Item -ItemType Directory -Force docs\archive\paper | Out-Null
git mv paper\EVIDENCE_MAP.md docs\archive\paper\EVIDENCE_MAP.md
git mv paper\README.md docs\archive\paper\README.md
git mv paper\REFERENCE_FORMAT.md docs\archive\paper\REFERENCE_FORMAT.md
git mv paper\proposal.tex docs\archive\paper\proposal.tex
git mv paper\figures\README.md docs\archive\paper\figures-README.md
```

- [ ] **Step 2: Move scripts and rename the source and PDF**

```powershell
git mv paper\scripts scripts\paper_figures
git mv paper\toolresult800.tex paper\toolresults.tex
New-Item -ItemType Directory -Force dist | Out-Null
Copy-Item paper\out\toolresult800.pdf dist\toolresults.pdf -Force
git rm paper\out\toolresult800.pdf
Remove-Item -Recurse -Force paper\out
```

`dist/` is gitignored; the copied PDF and the final zip are local deliverables, not committed. The source and figures remain tracked.

- [ ] **Step 3: Update script docstrings and path assumptions**

In `scripts/paper_figures/make_figures.py`, change the docstring's command to `python scripts/paper_figures/make_figures.py` and keep `DEFAULT_OUTDIR = REPO_ROOT / "paper" / "figures"`. In `scripts/paper_figures/make_result_figures.py`, keep `ROOT = Path(__file__).resolve().parents[2]` and `FIG = ROOT / "paper" / "figures"`.

- [ ] **Step 4: Build the renamed source**

```powershell
cd paper
latexmk -g -pdf -interaction=nonstopmode -outdir=out toolresults.tex
```

Expected: `paper/out/toolresults.pdf` is written; no errors. Then copy it:

```powershell
Copy-Item paper\out\toolresults.pdf dist\toolresults.pdf -Force
```

- [ ] **Step 5: Verify the paper directory**

```powershell
Get-ChildItem paper | Select-Object Name
```

Expected: `cas-common.sty`, `cas-sc.cls`, `figures`, `ref.bib`, `toolresults.tex`, and `out` only until final packaging. No Markdown, no `proposal.tex`, no `toolresult800.tex`.

- [ ] **Step 6: Commit**

```powershell
git add -A
git commit -m "chore: rename paper source and archive non-essential files"
```

---

### Task 3: Rename figures to fig1–fig10

**Files:**
- Rename: `paper/figures/fig-design.png` → `fig1.png`
- Rename: `paper/figures/fig-arms.png` → `fig2.png`
- Rename: `paper/figures/fig-pipeline.png` → `fig3.png`
- Rename: `paper/figures/fig-analysis.png` → `fig4.png`
- Rename: `paper/figures/result-forest.png` → `fig5.png`
- Rename: `paper/figures/result-tiers.png` → `fig6.png`
- Rename: `paper/figures/result-dose.png` → `fig7.png`
- Rename: `paper/figures/result-fields.png` → `fig8.png`
- Rename: `paper/figures/result-recovery-s2s3.png` → `fig9.png`
- Rename: `paper/figures/result-sensitivity.png` → `fig10.png`
- Modify: `paper/toolresults.tex` (all `\figfile` paths)
- Modify: `scripts/paper_figures/make_figures.py` (output names)
- Modify: `scripts/paper_figures/make_result_figures.py` (output names)

**Interfaces:**
- Consumes: `paper/toolresults.tex` from Task 2.
- Produces: the canonical figure mapping that every later task uses.

- [ ] **Step 1: Rename all ten files**

```powershell
git mv paper\figures\fig-design.png paper\figures\fig1.png
git mv paper\figures\fig-arms.png paper\figures\fig2.png
git mv paper\figures\fig-pipeline.png paper\figures\fig3.png
git mv paper\figures\fig-analysis.png paper\figures\fig4.png
git mv paper\figures\result-forest.png paper\figures\fig5.png
git mv paper\figures\result-tiers.png paper\figures\fig6.png
git mv paper\figures\result-dose.png paper\figures\fig7.png
git mv paper\figures\result-fields.png paper\figures\fig8.png
git mv paper\figures\result-recovery-s2s3.png paper\figures\fig9.png
git mv paper\figures\result-sensitivity.png paper\figures\fig10.png
```

- [ ] **Step 2: Update every `\figfile` path in `paper/toolresults.tex`**

Use this exact mapping, preserving the existing width options:

```text
figures/fig-design.png            -> figures/fig1.png
figures/fig-arms.png              -> figures/fig2.png
figures/fig-pipeline.png          -> figures/fig3.png
figures/fig-analysis.png          -> figures/fig4.png
figures/result-forest.png         -> figures/fig5.png
figures/result-tiers.png          -> figures/fig6.png
figures/result-dose.png           -> figures/fig7.png
figures/result-fields.png         -> figures/fig8.png
figures/result-recovery-s2s3.png  -> figures/fig9.png
figures/result-sensitivity.png    -> figures/fig10.png
```

- [ ] **Step 3: Update the two figure scripts**

In `make_figures.py`, change the four `save(...)` targets to `fig1.png`, `fig2.png`, `fig3.png`, `fig4.png` and update the `verify()` expected list. In `make_result_figures.py`, change the six `savefig` targets to `fig5.png` … `fig10.png` in the order shown above.

- [ ] **Step 4: Regenerate and verify DPI**

```powershell
python scripts/paper_figures/make_figures.py
python scripts/paper_figures/make_result_figures.py
```

Then run a Pillow check over all ten files; expected: every file reports DPI ≥ 600 and width/height > 1500 px.

- [ ] **Step 5: Verify no old names remain**

```powershell
Select-String -Path paper\toolresults.tex -Pattern "fig-design|fig-arms|fig-pipeline|fig-analysis|result-forest|result-tiers|result-dose|result-fields|result-recovery|result-sensitivity"
```

Expected: no matches.

- [ ] **Step 6: Build and commit**

```powershell
cd paper
latexmk -g -pdf -interaction=nonstopmode -outdir=out toolresults.tex
cd ..
git add -A
git commit -m "docs: rename figures to fig1-fig10"
```

---

### Task 4: Six-section structure and Evaluation Metrics subsection

**Files:**
- Modify: `paper/toolresults.tex`

**Interfaces:**
- Consumes: the renamed source from Task 3.
- Produces: the final section/subsection skeleton. Tasks 5 and 6 edit prose inside this skeleton.

- [ ] **Step 1: Add the Evaluation Metrics subsection**

In the Experiment section, after the `Models and fit checks` table and before `Generation envelope`, add:

```latex
\subsection{Evaluation Metrics}
\label{sec:metrics}
```

Move the existing `Agreement and audit statistics` block (Cohen's κ, Krippendorff's α, PPV/recall, Wilson interval) from Proposed Method into this subsection. Move the MDE equation here as well, and replace its display in the Power paragraph with a one-sentence reference to `Equation~\ref{eq:mde}`. Do not duplicate any equation. The subsection must define every metric the Results section reports, and each display equation must be followed by a lowercase `where ...` sentence.

- [ ] **Step 2: Verify the section skeleton**

Run a Python check that counts `\section{` and `\subsection{` commands. Expected: 6 sections; no section has more than 5 subsections; exactly one `\subsection{Evaluation Metrics}`.

- [ ] **Step 3: Fix the conclusion and declarations block**

Ensure a blank line separates the conclusion paragraph from `\section*{Declarations}`. Split each `\item` onto its own line. The conclusion must remain exactly one paragraph.

- [ ] **Step 4: Compile and commit**

```powershell
cd paper
latexmk -g -pdf -interaction=nonstopmode -outdir=out toolresults.tex
cd ..
git add paper/toolresults.tex
git commit -m "docs: add evaluation metrics subsection and fix section formatting"
```

---

### Task 5: Voice pass — Introduction, Conventional Method, Proposed Method

**Files:**
- Modify: `paper/toolresults.tex` (only the first three sections)
- Read: `writing-support/VOICE_PROFILE.md`, `writing-support/PROJECT_BRIEF.md`

**Interfaces:**
- Consumes: the skeleton from Task 4 and the claim–evidence map from Task 1.
- Produces: the front half of the paper in the calibrated voice; Tasks 6 uses the same rules on the back half.

- [ ] **Step 1: Consolidate micro-paragraphs**

Merge the following short body paragraphs into their neighbouring substantive paragraphs, preserving each claim:

- the paragraph beginning “The manuscript reports the completed study” (merge with the next paragraph);
- “All arms use a real observation from the same prefix” (merge with the following arm-description paragraph);
- “Gates are sequential and frozen before the main run” (merge with the G0 paragraph);
- “G0 is CPU-only and costs \$0” (merge with the G0 implementation-status paragraph);
- “The pilot is not evidence for the confirmatory claim” (merge with the pilot-limits paragraph).

- [ ] **Step 2: Apply the voice profile**

Rewrite only where needed to satisfy: 120–250 word paragraphs; sentence-length variance; past tense for executed work and present tense for definitions; lowercase `where` after equations; no banned connectors or clichés. Keep the author's clear technical wording and every number/citation.

- [ ] **Step 3: Verify paragraph statistics for these sections**

Run a Python check over the text between `\section{Introduction}` and `\section{Experiment}`. Expected: no body paragraph below 80 words; paragraph mean 160–230 words; no more than 15% of body paragraphs below 120 words; zero banned phrases. Do not pad paragraphs to hit a number; merge or split only where the argument requires it.

- [ ] **Step 4: Compile and commit**

```powershell
cd paper
latexmk -g -pdf -interaction=nonstopmode -outdir=out toolresults.tex
cd ..
git add paper/toolresults.tex
git commit -m "docs: align introduction and method with author voice"
```

---

### Task 6: Voice pass — Experiment, Results, Conclusion; shorten captions

**Files:**
- Modify: `paper/toolresults.tex` (Experiment, Results, Conclusion)
- Read: `writing-support/VOICE_PROFILE.md`, `writing-support/PROJECT_BRIEF.md`

**Interfaces:**
- Consumes: the front-half voice decisions from Task 5.
- Produces: the back half in the same voice and the final caption set.

- [ ] **Step 1: Consolidate the remaining micro-paragraphs**

Merge the short paragraphs beginning:

- “The primary estimate is the pooled conditional-logistic slope” (merge with the estimate paragraph);
- “The G3 gate did not pass” (merge with the claim-boundary paragraph);
- “Table~\ref{tab:armrates} gives the descriptive per-arm switch rates” (merge with the arm-rate paragraph);
- “The decomposition changes the interpretation of a positive slope” (merge with the interpretation paragraph).

- [ ] **Step 2: Shorten every caption to ≤ 25 words**

Rewrite each `\caption{...}` so it states what the figure/table shows, not the analysis. Move trend statements, artifact paths, and caveats into the body paragraph that references the float. Keep the `\label{}` unchanged.

- [ ] **Step 3: Verify**

Run a Python check over all captions. Expected: every caption ≤ 25 words; no caption contains `artifacts/` or `Traced to`. Check the Experiment/Results text for no body paragraph below 80 words.

- [ ] **Step 4: Compile and commit**

```powershell
cd paper
latexmk -g -pdf -interaction=nonstopmode -outdir=out toolresults.tex
cd ..
git add paper/toolresults.tex
git commit -m "docs: align results and captions with author voice"
```

---

### Task 7: Overleaf package and clean-room verification

**Files:**
- Create: `dist/toolresults-overleaf.zip`
- Create: `dist/toolresults.pdf`
- Modify: `paper/toolresults.tex` only if the clean-room compile finds a missing path

**Interfaces:**
- Consumes: the final `paper/toolresults.tex`, `paper/ref.bib`, `paper/cas-common.sty`, `paper/cas-sc.cls`, `paper/figures/fig1.png` … `fig10.png`.
- Produces: the upload artifact.

- [ ] **Step 1: Build the zip with exactly 14 files**

```powershell
New-Item -ItemType Directory -Force dist | Out-Null
Compress-Archive -Path paper\toolresults.tex,paper\ref.bib,paper\cas-common.sty,paper\cas-sc.cls,paper\figures -DestinationPath dist\toolresults-overleaf.zip -Force
```

Verify the archive listing: four top-level files plus `figures/fig1.png` … `fig10.png`; no `out/`, no scripts, no Markdown.

- [ ] **Step 2: Clean-room compile**

```powershell
$tmp = Join-Path $env:TEMP "toolresults-overleaf-check"
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
Expand-Archive dist\toolresults-overleaf.zip -DestinationPath $tmp
Push-Location $tmp
latexmk -g -pdf -interaction=nonstopmode toolresults.tex
Pop-Location
```

Expected: `toolresults.pdf` exists; 0 errors; 0 undefined references; 0 undefined citations; 56 bibliography entries; 10 figures.

- [ ] **Step 3: Copy the final PDF and clean `paper/`**

```powershell
Copy-Item paper\out\toolresults.pdf dist\toolresults.pdf -Force
Remove-Item -Recurse -Force paper\out
Get-ChildItem paper | Select-Object Name
```

Expected: `cas-common.sty`, `cas-sc.cls`, `figures`, `ref.bib`, `toolresults.tex`.

- [ ] **Step 4: Commit and final review**

```powershell
git add -A
git commit -m "chore: package Overleaf release"
```

Dispatch the final whole-branch reviewer with the spec, plan, ledger, and the full diff. The reviewer must confirm: six sections, one Evaluation Metrics subsection, one-paragraph conclusion, 56 cited keys, 10 figures at 600 DPI, no old filenames, clean-room compile, no numeric drift.

---

## Self-review

- Spec coverage: R1 → Task 4; R2 → Tasks 5–6; R3 → Task 3; R4 → Task 2; R5 → Task 7; R6 → final review and every compile check.
- Interfaces: Task 2 produces `paper/toolresults.tex`; Task 3 produces the `figN` mapping; Task 4 produces the skeleton; Tasks 5–6 consume it; Task 7 consumes the final files.
- No task asks for a result or citation change.
- Every task ends with a compile or a checkable structural assertion.
