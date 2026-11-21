# Paper Overleaf Release — Specification

**Date:** 2026-11-22
**Status:** proposed
**Owner:** Md. Atikur Rahaman
**Target:** a clean, Overleaf-uploadable `toolresults` package that follows the calibrated author voice and the six-section journal format.

## 1. Objective

Turn `paper/toolresult800.tex` into `paper/toolresults.tex`, apply the author's calibrated voice and format rules from `academic-writer-humanizer`, rename all figures to `fig1.png` … `fig10.png`, remove non-essential files from `paper/`, and produce `dist/toolresults-overleaf.zip` that compiles from a clean extraction.

The scientific content, numbers, claims, citations, and gate outcomes do not change. This is a format, voice, packaging, and navigation change.

## 2. Required outcomes

### R1 — Six-section structure

- Exactly six numbered main sections in this order: Introduction, Conventional Method, Proposed Method, Experiment, Results, Conclusion.
- At most five core subsections per section; no `4.1–4.8` or `5.1–5.10` sprawl.
- A mandatory `\subsection{Evaluation Metrics}` inside the Experiment section, containing the formal metric definitions (switch rate, action switch, flag, silent propagation, PPV/recall, Cohen's κ, Krippendorff's α, Wilson interval, MDE).
- The Conclusion is exactly one paragraph, 120–170 words, with no bullets and no blank line inside it.
- `\section*{Declarations}` starts on a new paragraph after the Conclusion, and each declaration item is on its own line.

### R2 — Calibrated author voice

Source: `C:\Users\atiku\.config\opencode\skills\academic-writer-humanizer\writing-support\VOICE_PROFILE.md`.

- Substantive body paragraphs target 120–250 words; no body paragraph below 80 words except equations, algorithms, tables, and one-line transitions.
- High sentence-length variance: pair 6–10 word claims with 25–35 word compound sentences; do not impose a quota.
- Past tense for executed procedures and observed results; present tense for definitions, equations, and figure/table references.
- Every display equation is followed by a lowercase `where ...` sentence defining its symbols; never `here x = ...`.
- No `Furthermore`, `Moreover`, `In conclusion`, `plays a pivotal role`, `delve`, `tapestry`, `testament`, `not only ... but also`.
- First-person plural for author decisions; passive voice for data and mathematical procedures.
- Keep the author's clear wording where it already meets these rules; do not flatten distinctive phrasing.

### R3 — Figures

Ten figures, renamed in order of appearance:

| New name | Current file | Content |
|---|---|---|
| `fig1.png` | `fig-design.png` | fixed-prefix design |
| `fig2.png` | `fig-arms.png` | five-arm severity ladder |
| `fig3.png` | `fig-pipeline.png` | end-to-end pipeline |
| `fig4.png` | `fig-analysis.png` | analysis path |
| `fig5.png` | `result-forest.png` | per-model and pooled slopes |
| `fig6.png` | `result-tiers.png` | tier odds ratios |
| `fig7.png` | `result-dose.png` | dose-response switch rates |
| `fig8.png` | `result-fields.png` | field-type breakdown |
| `fig9.png` | `result-recovery-s2s3.png` | recovery at s=2 and s=3 |
| `fig10.png` | `result-sensitivity.png` | sensitivity and strata |

- All ten figures remain at 600 DPI or higher.
- Result figures keep the enlarged fonts already generated; schematic figures must be checked at print size and enlarged if any label is below approximately 7 pt effective size.
- Every caption is one or two lines (target ≤ 25 words) and states what the figure shows; trends, caveats, and artifact paths move to the body text.
- Every figure is referenced from the body text with `Figure~\ref{...}`.

### R4 — Paper directory contents

After the change, `paper/` contains only:

```
paper/
  cas-common.sty
  cas-sc.cls
  figures/
    fig1.png ... fig10.png
  ref.bib
  toolresults.tex
```

Everything else moves to `docs/archive/paper/`:

- `EVIDENCE_MAP.md`
- `README.md`
- `REFERENCE_FORMAT.md`
- `proposal.tex`
- `figures/README.md`

`paper/scripts/` moves to `scripts/paper_figures/` and continues to write `paper/figures/fig1.png` … `fig10.png`. `paper/out/` is removed from the paper directory; the compiled PDF moves to `dist/toolresults.pdf`.

### R5 — Overleaf package

`dist/toolresults-overleaf.zip` contains exactly:

```
toolresults.tex
ref.bib
cas-common.sty
cas-sc.cls
figures/fig1.png ... fig10.png
```

No `out/`, no scripts, no Markdown, no `proposal.tex`, no old figure names.

The archive must compile from a clean extraction with `latexmk -pdf toolresults.tex` (or `pdflatex` + `bibtex` + `pdflatex` twice) with:

- 0 errors;
- 0 undefined references;
- 0 undefined citations;
- 56 references in the bibliography;
- 10 figures included;
- no missing class or style file.

### R6 — Integrity

- No number, confidence interval, p-value, sample count, gate verdict, table value, or claim strength changes.
- All 56 citation keys remain cited.
- All 21 table and 10 figure cross-references remain valid.
- The paper still reports the three failed criteria (parser, severity s2/s3, recovery) and makes no content-sensitivity claim.
- No new citations, experiments, or results are added.

## 3. Non-goals

- No new experiments, model runs, or analyses.
- No changes to the frozen manifests, audit records, or result artifacts.
- No page-limit optimization; the paper may remain 25–30 pages.
- No change to the dataset name “ToolResult-800”; only the source file is renamed.

## 4. Acceptance checks

1. `Select-String` finds exactly six `\section{` commands and one `\subsection{Evaluation Metrics}`.
2. The conclusion block has no blank line between its first and last sentence.
3. No body paragraph outside equations/algorithms/tables is below 80 words.
4. `paper/` listing matches R4 exactly.
5. `paper/toolresults.tex` contains no `fig-design`, `fig-arms`, `fig-pipeline`, `fig-analysis`, `result-` figure paths, and no `toolresult800` filename references.
6. All `\figfile{figures/figN.png}` targets exist; all ten are 600 DPI.
7. `dist/toolresults-overleaf.zip` extracts to 14 files and compiles cleanly in a temporary directory.
8. `python scripts/metric_consistency.py` (if a manifest exists) or a manual number audit shows no changed values.
9. The final PDF is built from the renamed source and recorded at `dist/toolresults.pdf`.
