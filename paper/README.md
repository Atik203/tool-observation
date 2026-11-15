# `paper/` — manuscript

Manuscript source, CAS class files, bibliography, and generated figures. The
confirmatory results are still pending, so the manuscript is a **skeleton with explicit
`[PENDING: ...]` markers**; no result has been invented.

## Files

- `toolresult800.tex` — CAS manuscript skeleton (Elsevier `cas-sc`, single column).
- `ref.bib` — bibliography converted from `proposal.tex`; five entries carry
  `[VERIFY CITATION]` comments.
- `cas-sc.cls`, `cas-common.sty` — byte-identical copies of the reference journal class.
- `figures/` — 600 DPI schematics: `fig-design.png`, `fig-pipeline.png`, `fig-arms.png`,
  `fig-analysis.png`.
- `scripts/make_figures.py` — regenerates the schematics at 600 DPI with large fonts.
- `REFERENCE_FORMAT.md` — extracted format spec for the reference manuscript, with line
  citations.
- `proposal.tex` — the earlier research proposal (article class, separate build).

## Build

```powershell
cd paper
latexmk -pdf -outdir=out toolresult800.tex
```

The class files are local, so no TeX Live CAS package is required. If `latexmk` skips
BibTeX when using `-outdir`, run:

```powershell
pdflatex -output-directory=out toolresult800.tex
bibtex out/toolresult800
pdflatex -output-directory=out toolresult800.tex
pdflatex -output-directory=out toolresult800.tex
```

## Status

| Milestone | Status |
|---|---|
| Proposal | drafted 2026-11-11 (`proposal.tex`) |
| Manuscript skeleton | complete; 16 pages with figures, 0 undefined citations/references |
| G1 calibration | in progress |
| Results draft | blocked on G1/G2 |
| Internal review | not started |
| Submission | not started |

## Rules

- Every number cites a ledger row, manifest, or artifact; no hand-entered results.
- The pilot table is labeled screening-only and is not pooled with the main run.
- The claim is bounded; no universal law, model ranking, or frontier generalization.
- A null result is written as a null result, with the dataset contribution stated.
- Figures are generated from `paper/scripts/make_figures.py` at 600 DPI; result figures
  will be generated from `artifacts/analysis/`, not hand-drawn.
- The abstract states the model families, domains, sample size, and recovery horizon.
