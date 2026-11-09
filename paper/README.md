# `paper/` — manuscript

Manuscript source and generated figures/tables. **No draft exists yet.** This directory explains
the intended structure so the analysis and writing stay aligned.

## Planned structure

1. **Introduction** — the reliability gap between end-to-end success and observation-level
   sensitivity; the pilot as motivation only.
2. **Related work** — τ-bench, tool-use benchmarks, counterfactual evaluation, silent error
   propagation, recovery.
3. **Design** — fixed prefixes, five arms, three models, paired within-prefix, 800/400/400.
4. **Manipulation and labels** — deterministic renderer, severity rubric, human audits.
5. **Outcomes and estimands** — Y/Y^U/Y^F/Y^A, conditional-logistic slope, recovery model.
6. **Results** — pooled and per-model slopes, silent propagation, s=3 vs s=1, recovery curves and
   t½ (or null/measurement result).
7. **Limitations** — contamination, donor off-policy, construct validity, model coverage,
   deterministic tools, four-step horizon.
8. **Data and ethics** — CTO-800, PII handling, licenses.
9. **Reproducibility** — environment, manifests, gates, commands.
10. **Appendix** — gate reports, amendments, prompt templates, full tables.

## Rules

- Every number cites a ledger row, manifest, or artifact; no hand-entered results.
- The pilot table is labeled screening-only and is not pooled with the main run.
- The claim is bounded; no "universal law", no model ranking, no frontier generalization.
- A null result is written as a null result, with the dataset contribution stated.
- Figures are generated from `artifacts/analysis/`, not hand-drawn.
- The abstract states the model families, domains, sample size, and the recovery horizon.

## Files

- `main.tex` / `main.md` — manuscript source (not yet created).
- `refs.bib` — bibliography (not yet created).
- `figures/` — generated figures (not yet created).
- `tables/` — generated tables (not yet created).

## Status

| Milestone | Status |
|---|---|
| Outline | not started |
| Methods draft | blocked on G0 |
| Results draft | blocked on G3/G4 |
| Internal review | not started |
| Submission | not started |

## Citation

Until the paper exists, cite the software metadata in `CITATION.cff`. Add the paper citation,
DOI, and venue here when available.
