# Reference format — Elsevier CAS single column (`cas-sc`)

Format specification extracted from the read-only reference manuscript at
`G:\HaluRISC\Journal_Paper`. Every convention below cites the reference file and line where it
was observed. Nothing here is taken from memory of Elsevier's author guidelines; where a journal
requirement is not visible in the reference, it is marked `TBD`.

Files read for this document:

| File | Role |
|---|---|
| `halurisc.tex` (1,070 lines) | the reference manuscript; source of every claim below |
| `halurisc.abs` | abstract artifact written by the class at build time (see §6) |
| `ref.bib` | 38-entry bibliography, keys matched to `\cite{}` |
| `cas-sc.cls` | class, v2.3, 2021/05/11 |
| `cas-common.sty` | class internals, v2.3, 2021/05/11 |
| `figures/**/*.png` | 13 raster figures, 12 of them referenced |
| `out/halurisc.log`, `out/halurisc.blg` | measured page geometry and BibTeX style |

Local copies of the class files are in this directory: `cas-sc.cls`, `cas-common.sty`. They are
byte-identical to the reference (SHA-256 verified). No PDFs or figure images were copied.

---

## 1. Document class and page geometry

```latex
\documentclass[a4paper,fleqn]{cas-sc}
```
`halurisc.tex:2`

- Class: `cas-sc` v2.3 (2021/05/11) (`cas-sc.cls:20-22`), described as "Formatting class for CAS
  single column articles" (`cas-sc.cls:24-25`); it builds on `article` (confirmed in
  `out/halurisc.log`: `Document Class: article`).
- Options used: `a4paper`, `fleqn` (equations flush left). No `review` or `longmktitle` option is
  used.
- Measured text width: `\textwidth = 468.3324pt` = 6.480 in = 16.46 cm
  (`out/halurisc.log`, geometry verbose block). All figure widths below are relative to this.
- `\emergencystretch` is raised to `2em` (`halurisc.tex:42`).

## 2. Preamble

Load order as used (`halurisc.tex:4-41`):

```latex
\usepackage{float}
\usepackage[utf8]{inputenc}
\usepackage[numbers]{natbib}
\usepackage{tabularx}
\usepackage[english]{babel}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{hyperref}
\usepackage{subcaption}
\usepackage{algorithm}
\usepackage{algpseudocode}
\usepackage{color}
\usepackage{xcolor}
\usepackage{orcidlink}
\usepackage{lineno}
\usepackage{silence}
\WarningFilter{hyperref}{Ignoring empty anchor}
```

Notes that matter when reusing this preamble:

- `booktabs` is the only table-rule package; `multirow`, `tabularx`, and `subcaption` are loaded
  but **not used in the body** (grep of the body returns no `\multirow`, no `tabularx`
  environment, no `subfigure`). Keep them only if the new manuscript uses them. `algorithm` and
  `algpseudocode` *are* used, for the two `algorithmic` blocks (`halurisc.tex:332`, `420`).
- `\usepackage[numbers]{natbib}` plus `elsarticle-num` gives bracketed numeric citations (§11).
- `hyperref` is loaded without `hidelinks`, so links are coloured boxes by default; the reference
  does not add `colorlinks` (`halurisc.tex:32`).
- `lineno` is used for line numbering in review mode (§13).
- `silence` suppresses one specific hyperref warning (`halurisc.tex:40-41`).

### 2.1 Class patches carried by the reference

These are project decisions, not class defaults. Copy them only if the new manuscript needs the
same behaviour.

1. **Preprint footer** (`halurisc.tex:52-66`): redefines `\__first_footerline:` so the first-page
   footer reads "*Short authors*: *Preprint*" instead of "Submitted to Elsevier".
2. **No-logo mode** (`halurisc.tex:67-75`): sets `\g_stm_nologo_bool` true so the class does not
   look for `thumbnails/cas-email.jpeg`. Without it, the email footnote breaks in any upload that
   lacks the `thumbnails/` folder. **This is required for the local build to work**, because
   `paper/` has no `thumbnails/` directory.
3. **ORCID badge in the byline** (`halurisc.tex:76-188`): the class prints ORCID iDs only in a
   footnote; this block redefines `\author` to place the green `\orcidlink` badge after each name,
   before the affiliation mark. Then `\printorcid` is emptied (`halurisc.tex:189-191`) so the
   footnote does not repeat the numbers.
4. **Comma-separated author list** (`halurisc.tex:192-216`): `\stmauthors` redefined so the last
   two names are joined by ", " rather than "and", keeping a four-author byline on one line with
   the ORCID badges.

## 3. Float placement and caption spacing

Counters and fractions (`halurisc.tex:13-21`), sized for 21 tables plus 12 figures:

```latex
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{5}
\renewcommand{\topfraction}{0.95}
\renewcommand{\bottomfraction}{0.95}
\renewcommand{\textfraction}{0.05}
\renewcommand{\floatpagefraction}{0.7}
```

Spacing is set twice in the reference. The `\AtBeginDocument` block (`halurisc.tex:24-30`) runs
after the plain `\setlength` block (`halurisc.tex:44-46`), so **the `\AtBeginDocument` values are
the effective ones**. Verified by instrumenting a copy of the preamble and reading the log:

| Length | Effective value | Source |
|---|---|---|
| `\textfloatsep` | `10pt plus 2pt minus 2pt` | `halurisc.tex:25` |
| `\floatsep` | `8pt plus 2pt minus 2pt` | `halurisc.tex:26` |
| `\intextsep` | `8pt plus 2pt minus 2pt` | `halurisc.tex:27` |
| `\abovecaptionskip` | `6pt` | `halurisc.tex:28` |
| `\belowcaptionskip` | `2pt` | `halurisc.tex:29` |
| `\bibsep` | `0pt` (last assignment wins) | `halurisc.tex:1064` |

Use the `\AtBeginDocument` block as the canonical definition; drop the later 4pt block, which is
dead code.

Table cell styling (`halurisc.tex:48-50`):

```latex
\renewcommand{\arraystretch}{1.08}
\setlength{\tabcolsep}{5pt}
```

`\tabcolsep` is dropped to `4pt` locally for the eight-column judge table
(`halurisc.tex:945`).

## 4. Float syntax and environment options

- Figures: `\begin{figure}[pos=htbp]` (11 of 12), `[pos=ht]` once (`halurisc.tex:878`).
- Tables: `\begin{table}[pos=htbp]` (19 of 21), `[pos=b]` once (`halurisc.tex:386`), `[H]` once
  (`halurisc.tex:618`, requires `float`).
- Algorithms: `\begin{algorithm}[H]` (2 occurrences, `halurisc.tex:332`, `420`), with
  `\caption` above the `algorithmic` body and `\label` immediately after the caption.
- No `figure*`, `table*`, or `sidewaystable` anywhere: the layout is single column, so all floats
  are `\linewidth` or narrower.

## 5. Front matter

Order of commands (`halurisc.tex:227-288`):

```latex
\begin{document}
\let\WriteBookmarks\relax          % 228, hyperref bookmark workaround

\shorttitle{Evidence-Consistent XGBoost}                     % 231
\shortauthors{Rahaman et~al.}                                % 234
\title [mode = title]{...full title...}                      % 237

\author[1]{Md. Atikur Rahaman}[orcid=0009-0008-2945-4117]    % 240
\cormark[1]
\ead{mrahaman2310298@bscse.uiu.ac.bd}
\credit{Conceptualization, Data curation, ..., Writing - review \& editing}

\author[1]{Saiful Alam Sabbir}[orcid=0009-0009-8460-1295]
\ead{...}
\credit{Data curation, Validation, Writing - review \& editing}

... two more \author blocks ...

\affiliation[1]{organization={Computer Science and Engineering, United International University},
  city={Dhaka},
  citysep={},
  postcode={1212},
  country={Bangladesh}}                                       % 260-264

\cortext[cor1]{Corresponding author: Md. Atikur Rahaman}      % 266

\linenumbers                                                  % 269
\begin{abstract} ... \end{abstract}                           % 270-272
\begin{keywords} ... \end{keywords}                           % 276-278

\begingroup
\hfuzz=120pt
\maketitle
\endgroup                                                    % 280-283
\hypersetup{pdfauthor={...}, pdftitle={...}}                  % 284-287
\linenumbers                                                  % 288
```

Details:

- `\title[mode = title]` — `mode` is a choice key of the class (`cas-common.sty`, `stm / title`
  keys: `mode / title` sets `\LARGE`, upright, medium weight); the reference passes it explicitly.
- Every author is marked `[1]` (one shared affiliation) and carries `[orcid=...]`; only the
  supervisor has no `\ead` (`halurisc.tex:256-257`).
- `\cormark[1]` marks the corresponding author; `\cortext[cor1]` supplies the footnote text.
  The keys `1` and `cor1` are independent namespaces.
- `\credit{...}` uses the Elsevier CRediT phrasing with a hyphen and escaped ampersand:
  `Writing - original draft`, `Writing - review \& editing`. `\printcredits` emits the statements
  (§12).
- Affiliation keys: `organization`, `city`, `citysep`, `postcode`, `country`; `citysep={}` sets
  the punctuation between city and postcode to nothing (`citysep` maps to `\l_city_punc_tl`,
  `cas-common.sty:1125`).
- `\hfuzz=120pt` while `\maketitle` runs suppresses overfull-box warnings up to 120 pt in the
  title block (`halurisc.tex:280-283`).
- `\linenumbers` is issued twice: once before the abstract, once after `\maketitle`, so both the
  front matter and the body are numbered.

## 6. Abstract and keywords

```latex
\begin{abstract}
  ...
\end{abstract}

\begin{keywords}
  Distribution shift \sep Evidence-consistent XGBoost \sep Conformal prediction \sep
  Hallucination risk estimation \sep Probability calibration \sep Question answering \sep SHAP
\end{keywords}
```
`halurisc.tex:270-278`

- The abstract is written **inline** in the `.tex`, not `\input` from a separate file.
- One paragraph, no citations, no displayed math, no `\cite` (`halurisc.tex:271`).
- Keywords: seven items, separated by `\sep` with spaces around it, capitalised as phrases, no
  trailing `\sep`.
- The class writes the abstract to `<jobname>.abs` on every build (confirmed: a test document
  produced `fmt-smoke.abs` containing exactly its abstract text). `halurisc.abs` in the reference
  root is that artifact from an earlier build; its wording differs from `halurisc.tex:271`, so the
  `.tex` is authoritative. Do not treat a stray `.abs` file as source.

## 7. Section hierarchy

| Level | Used | Example |
|---|---|---|
| `\section{...}\label{sec:...}` | 6 numbered | `halurisc.tex:290` Introduction |
| `\subsection{...}` | 17 numbered | `halurisc.tex:300` Preliminaries |
| `\subsubsection` | 0 | — |
| `\section*{...}` | 2 unnumbered | `halurisc.tex:1043` Declarations, `1059` Acknowledgements |
| Appendix | none | — |

Body order: Introduction, Conventional Method, Proposed Method, Experiments, Results,
Conclusion, `\printcredits`, Declarations, Acknowledgements, bibliography.

- Labels are `sec:`-prefixed and attached on the section line, not on a following line.
- Section titles are in Title Case and noun phrases (`Conventional Method`, `Proposed Method`,
  `Calibration, Shift, and External Validity`); no numbering is hand-written.
- The reference has no appendix; supplementary material would be a new decision, not a copy of an
  existing convention (`TBD`).

## 8. Table conventions

21 tables, all single column.

Canonical shape (`halurisc.tex:349-366`):

```latex
\begin{table}[pos=htbp]
  \centering
  \caption{Base feature groups (26 features total).}
  \label{tab:features}
  \begin{tabular}{>{\raggedright\arraybackslash}p{2.1cm}>{\raggedright\arraybackslash}p{4.6cm}>{\raggedright\arraybackslash}p{4.4cm}}
    \toprule
    \textbf{Group} & \textbf{Features} & \textbf{Source} \\
    \midrule
    ...
    \bottomrule
  \end{tabular}
\end{table}
```

Rules observed across all 21 tables:

1. `\centering` on the first line of the float.
2. `\caption{...}` **above** the tabular, sentence case, ending in a full stop, no `Table 1:`
   prefix (the class numbers it).
3. `\label{tab:...}` immediately after `\caption`, before `\begin{tabular}`.
4. `booktabs` only: `\toprule`, `\midrule`, `\bottomrule`. No `\hline`, no vertical rules, no
   `\cline`. Group breaks inside a table use `\addlinespace` (`halurisc.tex:955`, `753`, `756`,
   `759`, `762`).
5. Column headers are `\textbf{...}`. Numeric columns are `r` or `c`; text columns are `p{..cm}`
   with `>{\raggedright\arraybackslash}`.
6. Numbers are aligned by column and printed to a fixed number of decimals (usually four, e.g.
   `0.9855`, `$-$0.0066`). Negative values use `$-$` in math mode, not a hyphen
   (`halurisc.tex:626-634`). Missing values are `---` (em dash, `halurisc.tex:1031`).
7. Captions carry units, sample size, seed aggregation, and markers: `(n = 3{,}000)`,
   `mean over seeds 42/123/456`, `$^{\dagger}$Reduced reimplementation of ...`,
   `$^{\ast}$Slope: ...` (`halurisc.tex:549`, `675`).
8. A sub-block inside a table is introduced by
   `\multicolumn{8}{l}{\emph{Length-matched HaluEval, 158 rows, 50\% positive}} \\`
   (`halurisc.tex:956`) — italic text, left aligned, spanning all columns.
9. Wide tables are made to fit by shrinking `\tabcolsep` locally (`halurisc.tex:945`) or by
   choosing `p{}` widths; `\resizebox` and `\small` are **not** used on tables anywhere.
10. Percentages are escaped: `41.4\%` (`halurisc.tex:950`).

## 9. Figure conventions

12 figures; 13 PNGs exist, so `figures/revision/shap_summary.png` is unreferenced (the referenced
SHAP plot is `m3_shap_summary.png`).

Canonical shape (`halurisc.tex:374-379`):

```latex
\begin{figure}[pos=htbp]
  \centering
  \includegraphics[width=0.98\linewidth]{revision/architecture-flow-large.png}
  \caption{End-to-end pipeline, deployment path, and evaluation corpora of EC-XGB.}
  \label{fig:pipeline}
\end{figure}
```

Rules observed:

1. `\centering`; no `\includegraphics` inside a `center` environment.
2. `\caption{...}` **below** the image, sentence case, full stop, no "Figure 1:" prefix.
3. `\label{fig:...}` immediately after `\caption`.
4. Width keys used:
   - `width=0.98\linewidth` — the two wide architecture diagrams (`halurisc.tex:376`, `473`).
   - `width=\linewidth` — 9 data plots (`halurisc.tex:574`, `644`, `666`, `694`, `736`, `805`,
     `880`, `934`, `1014`).
   - `width=0.62\linewidth` — the confusion matrix, to keep it from dominating the page
     (`halurisc.tex:987`).
   No `height=`, `scale=`, `angle=`, or `\resizebox`.
5. No subfigures: `subcaption` is loaded but no `subfigure` environment is used. Panels are
   composed inside the PNG, not with `\subfigure`.
6. `\graphicspath` lists four fallbacks so the build survives a different upload layout
   (`halurisc.tex:225`):

```latex
\graphicspath{{./figures/}{Journal_Paper/figures/}{../Journal_Paper/figures/}{../artifacts/figures/}}
```
   Figure paths in `\includegraphics` are relative sub-directories (`revision/...`, `b3/...`,
   `b4/...`), so files live at `figures/<subdir>/<name>.png`.
7. Captions are one sentence, descriptive, and name the model/seed/scope; long explanations stay
   in the body text.

## 10. Figure resolution rule (600+ DPI)

The reference ships every raster figure at **600–650 dpi nominal, or at a pixel width that
exceeds 600 dpi at its printed width**. Nominal PNG metadata is not the test; effective resolution
at print size is.

Measured with `System.Drawing.Image.HorizontalResolution` / `.Width` / `.Height`:

| File | Pixels | Nominal DPI | Print width | Effective DPI at print width |
|---|---|---|---|---|
| `revision/architecture-flow-large.png` | 5600×3150 | 96 | `0.98\linewidth` (6.35 in) | ~882 |
| `revision/system-architecture-large.png` | 5600×2800 | 96 | `0.98\linewidth` (6.35 in) | ~882 |
| `revision/confusion_matrix.png` | 2666×2210 | 650 | `0.62\linewidth` (4.02 in) | ~664 |
| `revision/roc_pr_curves.png` | 4030×3575 | 650 | `\linewidth` (6.48 in) | ~622 |
| `revision/per_seed_stability.png` | 4009×1969 | 650 | `\linewidth` | ~619 |
| `revision/shap_summary.png` (unreferenced) | 3942×2110 | 650 | — | ~608 if full width |
| `revision/length_analysis.png` | 3921×1652 | 650 | `\linewidth` | ~605 |
| `revision/m3_shap_summary.png` | 4160×2307 | 650 | `\linewidth` | ~642 |
| `revision/h200_efficiency.png` | 4200×1650 | 600 | `\linewidth` | ~648 |
| `revision/operating_point_label_budget.png` | 4290×1950 | 650 | `\linewidth` | ~662 |
| `b3/transfer_score_distributions.png` | 4290×3055 | 650 | `\linewidth` | ~662 |
| `b4/reliability_diagrams.png` | 4290×2047 | 650 | `\linewidth` | ~662 |
| `b4/calibration_shift.png` | 4290×2047 | 650 | `\linewidth` | ~662 |

Effective DPI = pixel width ÷ printed width in inches, with `\linewidth = 6.480 in` from §1.

Current state of `paper/figures/` (snapshot 2026-11-15): `fig-analysis.png` 9055×5133,
`fig-arms.png` 10944×6144, `fig-design.png` 9144×5664, `fig-pipeline.png` 10344×6144, all tagged
600 dpi. At `\linewidth` that is ~1400–1690 dpi effective, i.e. far above the floor and roughly
2.3× more pixels than the rule needs; halving each dimension would still clear 600 dpi and cut the
PDF size.

The implied production rule, stated as a rule for this project:

- Render each figure on a canvas whose physical width is **at or just above its printed width**
  (e.g. 4290 px at 650 dpi = 6.60 in canvas for a 6.48 in slot, a 98% scale). For that 650-dpi
  family the figure lands at ~1:1, so the font size chosen in the plotting code is the font size
  on the page.
- Keep effective resolution **≥ 600 dpi** after scaling. A figure tagged 96 dpi is acceptable
  only when its pixel width is large enough to clear 600 dpi at the printed width, as with the two
  5600-px architecture diagrams (those are downscaled to ~11% of canvas width, so their text must
  be authored correspondingly large).
- Do not upscale a small raster. If a figure is under 600 dpi at its slot width, re-render it
  larger rather than stretching it.
- Minimum body-text size in a figure: the reference states none. The practical requirement is that
  text stays legible at final size, which the near-1:1 canvas rule provides for the 650-dpi
  family. Any explicit minimum is `TBD`.

Verification command (PowerShell, no extra packages):

```powershell
Add-Type -AssemblyName System.Drawing
Get-ChildItem -Recurse -Include *.png paper\figures | ForEach-Object {
  $i = [System.Drawing.Image]::FromFile($_.FullName)
  "{0} {1}x{2} px {3} dpi" -f $_.Name, $i.Width, $i.Height, [math]::Round($i.HorizontalResolution)
  $i.Dispose()
}
```

## 11. Bibliography

```latex
\hbadness=10000
\sloppy
\setlength{\bibsep}{0pt}
\renewcommand{\bibfont}{\fontsize{8.5pt}{9pt}\selectfont}
\bibliographystyle{elsarticle-num}
\bibliography{ref}
```
`halurisc.tex:1062-1067`

- Style: `elsarticle-num.bst`, driven by `natbib` with `numbers` → bracketed numeric citations
  such as `[1]`, `[2,5]`. Confirmed in `out/halurisc.blg` ("The style file: elsarticle-num.bst").
- Database: `ref.bib`, 38 entries, all 38 used (`out/halurisc.blg`: "You've used 38 entries").
- Citation command: `\cite{...}` only. No `\citep`, `\citet`, `\citeauthor`, or `\citeyear`
  anywhere in the body.
- Bibliography font is 8.5 pt on 9 pt leading, with `\bibsep` at 0 — deliberately compact to fit
  the page budget.
- `\sloppy` plus `\hbadness=10000` before the bibliography absorb underfull lines caused by DOIs
  and URLs.
- Bib entry conventions (`ref.bib:9-24` and throughout): full author lists with `and`, `Last,
  First` name order, `booktitle = {Proceedings of EMNLP}`, `pages = {9004--9017}`, `year`,
  and a `doi` field when one exists. arXiv-only works use
  `journal = {arXiv preprint arXiv:NNNN.NNNNN}`. A header comment records the verification date
  of every entry.
- BibTeX emits "empty pages" warnings for entries without page ranges (`out/halurisc.blg`); these
  are tolerated in the reference. Resolve them only by finding real page numbers, never by
  inventing them.

## 12. Declarations, CRediT, acknowledgements

```latex
\printcredits                      % 1041, immediately after the Conclusion

\section*{Declarations}            % 1043
\begin{itemize}
  \setlength{\itemsep}{0pt}
  \setlength{\parsep}{0pt}
  \item \textbf{Funding:} ...
  \item \textbf{Conflicts of Interest:} ...
  \item \textbf{Data availability:} ...
  \item \textbf{Code availability:} ...
  \item \textbf{Ethical approval:} ...
\end{itemize}

\section*{Acknowledgements}        % 1059
```
`halurisc.tex:1041-1060`

- `\printcredits` prints the `\credit{}` lines collected in the front matter as an unnumbered
  section titled "CRediT authorship contribution statement" (defined in `cas-common.sty` as
  `\NewDocumentCommand \printcredits`, which emits `\section*{CRediT authorship contribution
  statement}` from `\g_stm_credits_seq`). It sits after the Conclusion and before the
  declarations (`halurisc.tex:1041`).
- Declarations are an unnumbered `\section*` containing one `itemize` with `\itemsep` and
  `\parsep` zeroed, five items, each opening with a bold label and a colon.
- Order: Funding, Conflicts of Interest, Data availability, Code availability, Ethical approval.
- Acknowledgements follow as a second unnumbered section, in prose, one paragraph.
- URLs use `\url{...}`, file or branch names `\texttt{...}` (`halurisc.tex:1053`).

## 13. Review-mode line numbers

`\linenumbers` (`lineno`) is issued before the abstract and again after `\maketitle`
(`halurisc.tex:269`, `288`), so the submitted PDF is line-numbered throughout. Remove both calls
for a camera-ready or arXiv version, or keep them if the venue asks for numbered lines (`TBD`
which the target journal requires).

## 14. Build

Reference build products live in `out/` (`halurisc.pdf`, `.aux`, `.bbl`, `.log`, `.fls`,
`.fdb_latexmk`), i.e. the reference is built with an output directory:

```powershell
latexmk -pdf -outdir=out halurisc.tex
```

The class needs `cas-sc.cls` and `cas-common.sty` beside the `.tex` (now copied into `paper/`), and
the no-logo patch from §2.1 to avoid the missing `thumbnails/` error. The local TeX Live is 2026
(`pdfTeX 3.141592653-2.6-1.40.29`), the same installation that built the reference.

Smoke test performed for this document: a minimal manuscript using the copied
`paper/cas-sc.cls` and `paper/cas-common.sty`, with title, ORCID author, `\cormark`, `\ead`,
`\credit`, affiliation, abstract, `\sep` keywords, `booktabs` table, `\includegraphics`,
`\printcredits`, and `elsarticle-num` bibliography. Result: 1 page, no errors, no undefined
citations or references after `bibtex` plus two `pdflatex` passes. The ORCID byline patch,
no-logo mode, and `\AtBeginDocument` spacing block all behaved as described above.

Build check of the real manuscript (snapshot 2026-11-15, while `toolresult800.tex` was still being
written by another task): `pdflatex` → `bibtex` → `pdflatex` ×2 with `BIBINPUTS` and `TEXINPUTS`
pointing at `paper/` produced 15 pages with **0 undefined citations, 0 undefined references, 0
missing files, 0 overfull hboxes**. The 4 figures in `paper/figures/` resolve through
`\graphicspath{{./figures/}{figures/}{paper/figures/}}` (`toolresult800.tex:243`). Note that
`latexmk -outdir` needs `BIBINPUTS` set when the `.bib` lives outside the output directory, or
`bibtex` is skipped and every citation stays undefined.

## 15. Checklist for `paper/toolresult800.tex`

1. `\documentclass[a4paper,fleqn]{cas-sc}`; keep `cas-sc.cls` and `cas-common.sty` in `paper/`.
2. Copy the preamble of §2 in the same order; keep `algorithm`/`algpseudocode` only if the body
   has algorithm floats, and add `multirow`, `tabularx`, or `subcaption` only if the body uses
   them.
3. Include the no-logo patch (required) and, if the byline needs ORCID badges, the `\author`
   patch of §2.1. Both are self-contained blocks.
4. Front matter in the order of §5: `\shorttitle`, `\shortauthors`, `\title[mode = title]`,
   author blocks, `\affiliation`, `\cortext`, `\linenumbers`, `abstract`, `keywords`,
   `\maketitle`, `\hypersetup`, `\linenumbers`.
5. Abstract inline, one paragraph, no citations. Seven `\sep`-separated keywords unless the venue
   caps them (`TBD`).
6. Tables: `booktabs`, caption above, `\label` after caption, `\addlinespace` for group breaks.
7. Figures: PNG at ≥ 600 dpi effective, caption below, `\label` after caption, `width` as
   `\linewidth` or `0.98\linewidth`; put files under `paper/figures/` and keep `\graphicspath`
   pointing there.
8. `\printcredits`, then `\section*{Declarations}` with the five labelled items, then
   `\section*{Acknowledgements}`.
9. `\bibliographystyle{elsarticle-num}` + `\bibliography{ref}`; `\cite{}` only.
10. Compile with `latexmk -pdf -outdir=out toolresult800.tex` from `paper/`.

## 16. Not decided by the reference

These are journal-side requirements that the reference does not demonstrate, so they must not be
copied or assumed:

- Article number, running-head length limits, and any `review`/`casreviewlayout` option — the
  reference uses the class defaults, with `casreviewlayout` and `casfinallayout` both false
  (`cas-sc.cls:34-35`).
- Highlights and graphical abstract environments — absent from `halurisc.tex`.
- Whether the venue requires the `.abs` sidecar, an editable source bundle, or a specific figure
  naming scheme.
- A stated minimum figure font size (§10).
- An appendix or supplementary-material convention.

Naming conflict to resolve outside this file: `paper/README.md:37-38` still lists `main.tex` and
`refs.bib` as the planned manuscript and bibliography, while the current layout uses
`toolresult800.tex` and `ref.bib`. One of the two is stale. `README.md` was not edited here.

Mark any of these `TBD` in the manuscript rather than inventing a rule.
