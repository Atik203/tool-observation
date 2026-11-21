# Task 3 report — rename figures fig1–fig10 (branch `paper-overleaf`, BASE `e8bd1953`)

## 1. Steps performed
1. `git mv` of all 10 files under `paper/figures/` (note: the task text said `figures/…`;
   in this repo the directory is `paper/figures/`, and `\graphicspath` resolves `figures/…`
   relative to `paper/`):
   - `fig-design.png -> fig1.png`, `fig-arms.png -> fig2.png`,
     `fig-pipeline.png -> fig3.png`, `fig-analysis.png -> fig4.png`
   - `result-forest.png -> fig5.png`, `result-tiers.png -> fig6.png`,
     `result-dose.png -> fig7.png`, `result-fields.png -> fig8.png`,
     `result-recovery-s2s3.png -> fig9.png`, `result-sensitivity.png -> fig10.png`
2. `paper/toolresults.tex`: replaced all 10 `\figfile[…]{…}` paths per the mapping.
   Width options preserved exactly (`0.95\linewidth` ×7, `0.98\linewidth` ×3 for
   figs 6/9/10 as before). Captions, `\label`s, and body text untouched.
   `git diff` confirms exactly 10 changed lines (20 +++/−−−), path strings only.
3. `scripts/paper_figures/make_figures.py`: 4 `save()` targets → `fig1/fig3/fig2/fig4.png`
   (design→fig1, arms→fig2, pipeline→fig3, analysis→fig4) + `verify()` expected list.
   `scripts/paper_figures/make_result_figures.py`: 6 `savefig` targets →
   forest→fig5, tiers→fig6, dose→fig7, fields→fig8, recovery-s2s3→fig9,
   sensitivity→fig10. (Module docstring in `make_figures.py` still names the old
   schematic filenames — cosmetic only, left per minimal-scope instruction.)
4. Regeneration with `C:\ProgramData\anaconda3\python.exe` (default `python` is 3.14
   without matplotlib; conda env has matplotlib + Pillow):
   - `make_figures.py` → exit 0; wrote fig1–fig4 and its built-in `verify()` passed.
     Regenerated PNGs are byte-identical to the renamed originals (deterministic render).
   - `make_result_figures.py` → exit 1, `FileNotFoundError:
     artifacts/analysis/g3_analysis.json`. This repo carries only `.gitkeep` stubs under
     `artifacts/` (analysis JSONs are not vendored on this branch), so fig5–fig10 could
     not be redrawn here. They are the original 600-DPI renders, preserved byte-for-byte
     via `git mv` (diff shows `Bin`, 0 insertions/deletions). After the script targets are
     updated, a future run with the analysis artifacts present will write fig5–fig10.
5. Stale-name grep on `paper/toolresults.tex`
   (`fig-design|fig-arms|fig-pipeline|fig-analysis|result-forest|result-tiers|result-dose|`
   `result-fields|result-recovery|result-sensitivity`): **0 matches**. New `figures/figN`
   references present at lines 485, 648, 787, 1078, 1407, 1466, 1587, 1738, 1809, 1853 —
   ascending fig1→fig10 in appearance order, matching the spec table.
6. Build: `cd paper; latexmk -g -pdf -interaction=nonstopmode -outdir=out toolresults.tex`
   → clean, `Output written on out/toolresults.pdf (27 pages, 7496221 bytes)`,
   `All targets are up-to-date`; log has no `!` errors, no missing-file warnings.
   `Copy-Item paper\out\toolresults.pdf dist\toolresults.pdf -Force` done (7,496,221 B).
   `dist/` is git-ignored — `git status` shows no `dist/` entry; it was NOT staged.
7. `git add -A` (staged: 10 renames, tex, 2 scripts, rebuilt tracked `paper/out/toolresults.pdf`,
   plus this report under untracked `.superpowers/`); `git status` confirms no `dist/`;
   committed (see below).

## 2. DPI / dimension check (Pillow, all 10 files)
PNG `pHYs` stores px/m, so nominal 600 DPI reads back as 599.9988; the repo's own
`verify()` tolerance (`DPI − 0.5`) is used. Requirement: nominal 600 DPI and w,h > 1500 px.

| file | size | dpi | verdict |
|---|---|---|---|
| fig1.png | 9144×5664 | (600,600) | OK |
| fig2.png | 10944×6144 | (600,600) | OK |
| fig3.png | 10344×6144 | (600,600) | OK |
| fig4.png | 9055×5133 | (600,600) | OK |
| fig5.png | 4477×1852 | (600,600) | OK |
| fig6.png | 7442×2028 | (600,600) | OK |
| fig7.png | 4909×2274 | (600,600) | OK |
| fig8.png | 4671×2094 | (600,600) | OK |
| fig9.png | 6588×2152 | (600,600) | OK |
| fig10.png | 7081×2152 | (600,600) | OK |
ALL_PASS (10/10). Check script was a temp file under `.superpowers/`, removed after the run.

## 3. Build output (tail)
`Output written on out/toolresults.pdf (27 pages, 7496221 bytes)` …
`Latexmk: All targets (out/toolresults.pdf) are up-to-date`. No errors in
`paper/out/toolresults.log` (`File.*not found|LaTeX Error|Missing|! ` → no hits).

## 4. Commit
`docs: rename figures to fig1-fig10`, direct child of BASE `e8bd1953` (see `git log --oneline -2`).

## 5. Concerns / follow-ups
- `make_result_figures.py` cannot run on this branch (missing `artifacts/analysis/*.json`);
  fig5–fig10 are carried over byte-identical. Regenerate them wherever the analysis
  artifacts exist to confirm byte-stability under the new filenames.
- `make_figures.py` module docstring still lists the old schematic filenames (step-3 scope
  covered only `save()` targets + `verify()` list).
- No numeric, claim, caption, label, or citation text was changed; figure order in the tex
  is fig1→fig10 in appearance order (no reorder).
