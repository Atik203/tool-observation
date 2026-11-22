# Reviewer 3 — Paper craft, editorial quality, figures/tables, Overleaf readiness

- **Date:** 2026-11-22
- **Manuscript:** `paper/toolresults.tex` (1,945 lines), `paper/ref.bib` (56 entries),
  `paper/figures/fig1.png`–`fig10.png`, `paper/out/toolresults.pdf` (26 pp).
- **Read:** the complete `.tex`, the complete `.bib`, all ten figures at native resolution,
  the 26-page PDF, `writing-support/VOICE_PROFILE.md`, `AGENTS.md`, and the figure-generation
  scripts in `scripts/paper_figures/`.
- **Mode:** read-only. I did not edit the paper, figures, artifacts, or build files. I compiled
  scratch copies under the OS temp directory to test the submission package. The only write is
  this report.
- **Boundary:** statistical substance is owned by R1 and R4. Where a finding is primarily
  statistical, I cross-reference it and address only its prose, table, figure, or package surface.

---

## 1. Verdict

**Major revision. The manuscript is not submission-ready, and the craft defects alone would draw
a major-revision decision before the science is assessed.**

The paper is unusually candid about its failures, the core numbers are mostly traceable, and the
prose is generally clear. But the package a reviewer receives contains a figure that says *no study
outcomes have been generated*, three red `[PENDING]` blocks, an internal note that the CRediT
statement “must be confirmed by every author,” a credit list naming two people who are not on the
byline, a gate table that reports a G1 criterion the study did not pass, and an abstract/conclusion
recovery range that omits the worst model. Those are not polish issues; they are credibility
signals on the first two pages and the last two pages.

The good news is that none of the craft findings require new experiments or new numbers. They
require two or three days of disciplined editing: regenerate the figures at print size, restructure
40 run-in headings, reconcile about a dozen table/text denominators, refresh the references, and
clear the declarations. If R4's integrity blockers (release evidence, preregistration status, G1
amendment) are also resolved, the underlying measurement paper is publishable.

### Readiness by dimension

| Dimension | Status | Main reason |
|---|---|---|
| Section structure | Not ready | Six sections exist, but 40 bold run-in pseudo-headings; the Discussion is buried inside Results; 4.1 appears after the unnumbered gate/environment/fit material, and 5.1 is followed by ten unnumbered siblings. |
| Voice vs `VOICE_PROFILE.md` | Needs work | 41.5% of sentences open with “The”; one “we” in 9.2k words; subordinating connectors are nearly absent; large parts of the Discussion are still in pre-results conditional/future tense. |
| Figures | Not ready | Effective type is ~4.6–5.8 pt in Figs 1–4, 6, 9, 10; Fig 4 announces “no study outcomes”; Fig 5 plots a Wald interval while the text reports a bootstrap interval. |
| Tables | Needs work | 21 tables for ~9.2k words; 6–8 are supplementary-grade; four tables are not self-contained; three do not reconcile with the text. |
| Equations / notation | Needs work | Ten symbol collisions despite Table 1 claiming one meaning per symbol; ~20 symbols used but never defined; 21 of 27 equation labels are never referenced. |
| Citations | Needs work | 36/56 are arXiv-only, nothing after 2024 at a Nov-2026 submission, no model cards or model revisions, no preregistration citation. |
| Overleaf / build | Ready with fixes | Exactly 14 files compile clean-room in three passes, 26 pp, zero errors, zero overfull boxes; 31 duplicate hyperref destinations, no bookmarks, template metadata. |
| Declarations | Not ready | Ghost authors, three pending items, ethics wording contradicts the AI-use statement, DOI missing. |

---

## 2. What is working

These are real strengths and should survive the revision.

- **The abstract is the right length and mostly the right shape.** 227 words, one paragraph,
  concrete numbers, no “delve/crucial/landscape” vocabulary. All ten figure and 21 table captions
  are at or under 25 words (maximum 24).
- **The visual assets are technically high-resolution.** All ten PNGs carry a 600 DPI `pHYs`
  chunk; no image is below 4,400 px wide. The problem is layout scale, not file resolution
  (Section 7).
- **The bibliography is clean at the BibTeX level.** 56 entries, 56 cited, zero uncited entries,
  zero missing keys, zero duplicate keys, zero BibTeX warnings. The statistical references are
  canonical (Chamberlain 1980, Cameron 2015, Efron 1979, Holm 1979, Wilson 1927, Krippendorff
  2004).
- **The build is portable.** The `.tex` and `.bib` are pure ASCII; there are no `\input` files,
  no absolute paths, and exactly 14 files in the package. A clean-room TeX Live 2026 compile
  succeeds (Section 11).
- **There are zero overfull boxes and no undefined references.** Only two underfull boxes, both
  in the supply paragraph.
- **The paper does not hide its failures.** The prose is explicit about the parser failure, the
  severity audit miss, the recovery gate, and the audit's AI provenance. That is rare and should
  be preserved.
- **The tables use `booktabs`, no vertical rules, and no colour.** They are visually calm and
  consistent in style.

---

## 3. Severity-ranked findings

**Legend.** S1 = blocking (fix before submission); S2 = major (reviewer-visible, affects
credibility or readability); S3 = moderate (polish with substantive effect); S4 = minor.
“Confirmed” means I read it in the source, the PDF, the log, or the figure script. “Speculative”
means the mechanism is plausible but not demonstrated. Line numbers refer to
`paper/toolresults.tex` unless stated otherwise.

### 3.1 Blocking (S1)

| ID | Location | Finding | Why it matters | Fix | Status |
|---|---|---|---|---|---|
| **S1-1** | Fig. 4, `:998-1005`; `out/toolresults.pdf` p. 11; `scripts/paper_figures/make_figures.py:972-1012` | Figure 4 is a conceptual schematic stamped **“ILLUSTRATIVE — NOT DATA — no study outcomes have been generated; axes are unnumbered by design.”** The caption does not disclose that it is not a result. | This is the single most damaging artefact in the package. A reviewer sees a paper reporting a completed 13,200-generation study and a figure that says no outcomes exist. It reads as an unrevised pre-run draft or as a contradiction. | Remove Fig. 4 from the main text, or replace it with a results panel (e.g., the observed typology). If a conceptual figure is retained, delete the “no study outcomes” sentence, relabel the axes with real categories, and state “conceptual, not a result” in the caption. | Confirmed (image text + script) |
| **S1-2** | Byline `:254-272`; CRediT `:1920-1925`; comment `:206-207`; short authors `:241` | The byline has **two** authors (Rahaman, Tuhin). The Author contributions item credits **“S.A.S. and M.M.A.”** for data curation, validation, and writing. A source comment still says the patch exists “so the four-author line fits on one line.” `\shortauthors` says “Rahaman et al.” for a two-author paper. | Authorship and credit are integrity issues, not production details. An editor will query the ghost names; a reader will wonder who did the work. “et al.” with two authors is also wrong. | Decide the author list, then make byline, ORCIDs, emails, `\shortauthors`, `\credit`, and the Author contributions item agree. Delete the “carried over from the companion manuscript” sentence. | Confirmed |
| **S1-3** | `:1315`, `:1913`, `:1919`; visible note `:1924-1925`; PDF pp. 15, 24 | Three red `\pending{}` blocks are printed in the PDF: the G0 author-verification date, the release DOI/manifest hash, and the ethics determination. The CRediT item also prints “must be confirmed by every author before submission.” | A submission with red placeholders and an internal instruction in the body signals that the manuscript is a draft. Two of the three are declarations that journals require before review. | Resolve or remove all three. If the ethics determination or DOI cannot be obtained before submission, state the status in neutral prose rather than a red placeholder, and remove the internal confirmation sentence. | Confirmed (red text found in PDF) |
| **S1-4** | Table 5 `:1027-1031`; G1 text `:1054-1066`; Fig. 3 pipeline panel; PDF p. 12 | Table 5 lists G1's pass criterion as “**placebo jitter at most 20%**”; the text records G1 as passed. The text says the original V-vs-s0 criterion **failed at 20.3–45.6%** and that G1 passed only under the amended **s0-vs-s1** criterion (A-004, 10.5–13.3%). Fig. 3 repeats “placebo jitter ≤ 20%.” | A reader who checks the table computes 45.6% > 20% and concludes G1 failed. The paper's central credibility device is a gate sequence; if the gate table cannot reproduce the pass, the sequence looks retrofitted. (R4 C2 owns the amendment-integrity issue; this is the documentation defect.) | Put both criteria in Table 5: “V-vs-s0 format jitter (reported, not gated)” and “s0-vs-s1 negative control ≤20% (A-004).” Update Fig. 3's G1 panel. State that the original criterion failed. | Confirmed |
| **S1-5** | Abstract `:289-290`; Conclusion `:1893`; limitations `:1877`; Results `:1686`; Table 19 `:1712-1717` | The paper reports recovery as **32.4–47.6%** in the abstract, conclusion, and limitations. The three primary s=3 estimates are **32.4% (Qwen), 47.6% (Ministral), 28.2% (Llama)**. The interval omits Llama's 28.2%. | This understates the headline failure: the worst model is 21.8 points below the gate, not 2.4. A reviewer who checks Table 19 sees an interval that cannot be derived from it. (R4 C1 owns the KM-vs-crude estimand; this is a separate prose/table inconsistency.) | Make the interval cover all three reported values (28.2–47.6), or state explicitly that the interval is for the two models above 30% and say why Llama is excluded. Do not change the underlying estimates. | Confirmed |
| **S1-6** | Introduction `:383-384` vs `:291`, `:1266`, `:1875`, `:1891` | The Introduction says “**Two** preregistered criteria failed.” The abstract, Results, limitations, and conclusion all say **three** (parser failure, severity s2/s3 share, recovery). | A direct internal contradiction about the paper's own gate accounting, on the first page and in the conclusion. Readers remember the count. | Use “three” and list them, or reconcile the count with the gate definitions after R4's G1/Weibull discussion. | Confirmed (R4 H1 also) |
| **S1-7** | Fig. 3, freeze panel, `:1049-1052`, `:1311-1314` | The pipeline figure's freeze box says “**40-item human audit, pass at ≥ 36/40**.” The text says the sheet is filled by an **AI-assisted mechanical pre-audit at 40/40**, with the human verification deferred and reported as a deviation. | The figure asserts a human check the paper says has not happened. This is exactly the kind of detail an integrity reviewer checks first. | Relabel the box: “40-item audit (AI pre-audit 40/40; human verification pending)” or remove the audit from the figure. | Confirmed |

### 3.2 Major (S2)

| ID | Location | Finding | Why it matters | Fix | Status |
|---|---|---|---|---|---|
| **M1** | Whole manuscript; 40 `\noindent\textbf{}` headings; merged at `:429, :607, :730, :840, :1035, :1304`; visible on PDF p. 5 | **Heading architecture is flat and fragmented.** Six numbered subsections plus **40 bold run-in pseudo-headings**, roughly one per 200 words overall and one per 115 in Section 4: Method has 12 run-ins in 3.0k words; Experiment has 10 in 1.3k. Six run-ins have no paragraph break, so they render **mid-sentence**: p. 5 reads “…before attrition. **Arms and rendering.** All arms use…” All 40 are bold body-size lines, not subsection-size; they are not numbered, not in the PDF outline, and not addressable. | The reader cannot tell hierarchy from emphasis, and the paper looks like an outline exported to prose. The mid-line headings are the most visible formatting defect after the figures. | Keep at most 5 numbered subsections per section; demote the rest to ordinary paragraphs (or `\paragraph` if a label is essential). Add the missing blank lines. Never let a run-in heading share a line with the preceding paragraph. | Confirmed (6 merged; count from source) |
| **M2** | `:1786-1851`; Section 5 | **The Discussion is inside Results.** “Conditional interpretation,” “Engineering implications,” “Evaluation practice,” and “What would change the claim,” plus the limitations paragraphs, are ~1,200 words at the end of Section 5 with no Discussion heading. Meanwhile 4.1 "Evaluation Metrics" is the only numbered subsection in Section 4 and appears after the unnumbered gate/environment material. | A Q1 referee expects Results to report and Discussion to interpret. Burying interpretation in Results makes the Results section read as long and the paper as argumentative. The numbered-subsection scheme also misdescribes the content. | Rename Section 5 “Results and Discussion” (keeps the six-section frame), or add a seventh Discussion section with author approval. In Section 4, make 4.1 the first subsection or renumber it. | Confirmed |
| **M3** | Figs 1–4, 6, 9, 10; `scripts/paper_figures/make_figures.py:273,469,723,972`; `make_result_figures.py:62,182,229,309` | **The figures are designed at 15–18 in and printed at 6.2 in, so their type shrinks by 2.5–3×.** Estimated smallest effective sizes: Fig. 1 5.8 pt, Fig. 2 5.1, Fig. 3 4.8, Fig. 4 5.4, Fig. 6 4.6, Fig. 9 5.1, Fig. 10 4.8. Only Fig. 5 (8.1 pt) meets a typical 8 pt journal minimum; Fig. 7 (7.4) and Fig. 8 (7.7) are borderline. The QC script's docstring claims “base font of at least 14 pt” and `--verify-only` checks DPI and pixel dimensions, not effective type size. | “600 DPI” is satisfied but irrelevant: a 14 pt label on an 18-inch canvas is 4.8 pt on the page. At print, the pipeline boxes and the Fig. 4 axis are hard to read; at review, they look amateur. | Regenerate Figs 1–4, 6, 9, 10 with `figsize` near the final physical width (≈6.3–6.5 in) and fonts ≥8 pt, or split multi-panel figures. Add an effective-font-size check to `--verify-only`. Keep 600 DPI at final size (≈3,800 px wide), which also cuts the PDF size. | Confirmed (canvas and font sizes from scripts; page renders) |
| **M4** | Fig. 5; `make_result_figures.py:96-125`, line 107; text `:1373-1375`; Table 10 `:1352-1359` | **Fig. 5 plots Wald intervals, not the reported bootstrap intervals.** The script computes `beta ± 1.96*se`, so the pooled label is **0.88 [0.76, 0.99]**. The text and Table 10 report the prefix-cluster bootstrap **[0.770, 0.998]**. The figure caption says only “95% confidence intervals.” The per-model labels also show 0.91 for 0.915 (floating-point formatting). | The primary estimate now has two different 95% intervals a page apart. A referee will treat that as a reproducibility failure even though both are computable. | Either plot the bootstrap interval used in the text or label the figure “Wald 95% CI” and report the bootstrap interval alongside. Do not show a different interval from the one the paper calls primary. | Confirmed (script) |
| **M5** | Table 10 `:1345`; Figs 5 `:1363`, 7 `:1531`, 8 `:1674`; PDF pp. 11, 18, 21 | **Four floats are never cited in the body.** Table 10 (primary estimates), Fig. 5 (forest), Fig. 7 (switch rates), and Fig. 8 (field types) have no `\ref` anywhere. Separately, the float program produces **plate pages**: p. 21 contains Fig. 8, Table 19, Table 20 and Fig. 9 with **zero body text**; p. 11 contains Algorithm 1 and Fig. 4 with almost none; p. 18 has three tables plus Fig. 7 and five lines. The Recovery paragraph is on p. 20, but its Table 19/20 and Fig. 9 are on p. 21. | Journals require every float to be cited. A plate page with four floats and no argument reads as a layout accident, and the recovery evidence is separated from the paragraph that interprets it. | Add callouts for the four floats. Merge Table 20 into Table 19; move 6–8 tables to supplementary material (Section 8); let Fig. 9 sit with the Recovery paragraph. Reduce the float density so no page is pure plate. | Confirmed (reference scan + PDF) |
| **M6** | Table 1 `:522-545`; equations (1)–(27) | **The notation table's caption is false: “The same symbol is used with the same meaning throughout the paper.”** At least ten symbols are overloaded: `S` (success, survival, subset), `α` (intercept, significance level, Krippendorff's alpha), `β` (slope, power in `z_{1-β}`, quadratic `β_2`), `κ` (Cohen's kappa, Weibull shape), `h` (recovery step, hazard `h_W`), `U` (`Y^U`, score `U_g`), `V` (verbatim arm, variance `V_g`), `p` (prefix, p-value, `p_o/p_e`), `H` (horizon, `H_1`), `k` (`k_g`, binomial index, `δ²(c,k)`). The table also omits ~20 symbols used in the equations: `Π_s`, `T_prose`, `f_m`, `γ_k`, `Λ`, `κ`, `λ`, `θ_e2e`, `G_τ`, `z_T`, `v*`, `𝒱(d)`, `F`, `C^A…`, `n_a`, `E_g`, `U_g`, `V_g`, `S_W`, `h_W`, `RMST`. | A methods paper is read through its notation. The caption invites the reader to trust a uniqueness that the equations immediately break, and the missing symbols force reverse-engineering. | Either make the caption true (“symbols used in the primary estimand”) and add a second notation block for the statistical appendix, or rename the collisions (survival `R(h)`, hazard `λ_W(t)`, score `s_g(β)`, variance `W_g`, power `1-π`). Add the omitted symbols or delete the claim of completeness. | Confirmed |
| **M7** | `:383`, `:1794`, `:1816`, `:1822`, `:1825`, `:1840`, `:1843`, `:1855` | **Registered-report residue.** The Discussion still speaks in future/conditional tense about a completed study: “the paper will say so” (1816), “The result will inform choices” (1822), “If the slope is flat, those checks may be less urgent” (1825), “The limitations are known in advance” (1855), “The dataset is also a null-result asset” (1840), “What would change the claim” (1843). The Introduction says the results “replace the earlier placeholders” (383). | The paper's own tense says it has not been written yet. A reader concludes the Discussion was not revised after the run, which undermines confidence in the parts that *were* revised. The “null-result asset” sentence is also stale: the observed slope is positive and the paper reports a measurement estimate, not a null. | Rewrite the Discussion in past/present indicative: what was found, what it means, what remains uncertain. Keep the robustness list as “sensitivity” or “what would have changed the verdict,” not as a conditional future. Delete “replace the earlier placeholders.” | Confirmed |
| **M8** | Abstract `:289-291`, `:294`; Table 15 `:1520-1529`; Table 9 `:1332-1340`; Table 12 `:1452-1462` | **Two abstract claims do not match the body's own tables.** (a) “Re-serializing the same observation already moves **20–46%** of decisions” is the G1 calibration range (20.3/36.7/45.6 on 60 prefixes, Table 9); the main-matrix s0 rates are **19.8/31.9/38.1** (Table 15). The two ranges are never reconciled, and the abstract quotes the larger. (b) “Linearity is rejected” is true pooled (χ²(2)=25.03) but **not for Llama (p=.274)**; the per-model diagnostics say so. | The abstract is the most-read text. Both sentences generalize beyond the table a reader will check. The format range is especially misleading because the main run is the paper's own sample. | (a) Say which sample each range comes from, or use the main-run range and cite the calibration separately. (b) Say “pooled linearity is rejected; the per-model tests reject for Qwen and Ministral, not Llama.” No numbers change. | Confirmed |
| **M9** | Methods `:1203-1212`; Table 8 `:1215-1232`; Results `:1260`, `:1372`; Table 6 `:1126-1140`; limitations `:1874` | **Planned and executed arithmetic are mixed without labels.** Table 8 and Fig. 1 use 800×5×3 = **12,000** base generations and a **34,800** envelope. Results report the “full 880-prefix matrix” of **13,200** base generations. Methods says “The main run is fully crossed: **800** prefixes.” The executed envelope is therefore 13,200+19,200+2,400+1,200 = **36,000**, not 34,800. Separately, Table 6 says batch 4 / max seqs 8 for all models, while the run used **4** concurrent sequences for Ministral and Llama after OOM, and the limitations say “batch 4 rather than the **planned batch 8**” although no batch-8 plan appears anywhere. | The reader cannot tell what was planned, what was run, and what was analysed. The batch/sequence discrepancy is a reproducibility gap: the served configuration is not the one in the table. | Label Table 8 and Fig. 1 “planned (800 primary)” and add the executed totals, or state that the envelope excludes the 80 reserve. Make Table 6 report the **served** per-model caps (8/4/4) and delete or source “planned batch 8.” | Confirmed |
| **M10** | `:1380-1385`, `:1469-1470`, `:1478`; Table 13 `:1486-1494`; Table 18 `:1660-1671`; Table 19 `:1710-1717` | **Four denominator/row-arithmetic inconsistencies.** (a) “617 strata that vary across arms (28.3% of the 2,297 strata)”: 617/2,297 = **26.9%**; 28.3% is 649/2,297, the typology's dose-responsive + placebo total. (b) “Rates use **741–770** labeled rows per arm,” but Table 13's arm coverage is 97.0–98.6% of 800 = **776–789**; the gap is presumably the V-unparsed filter, which the text does not state. (c) Table 18's four classes sum to **1,984**, but the “All s=2” row is **2,267**; R1 M6 identifies the omitted classes (other 247, temporal 17, count 19). (d) Table 19's “Recovered” is a KM `1−S(4)` estimate (71/239 = 29.7% crude vs 35.0% KM; 141/406 = 34.7% vs 47.6%), not `Events/n`. | These are the numbers a referee recomputes first. Each is individually small; four in one paper read as a table-generation problem. (R1 M6/M14 and R4 C1 own the substantive implications; this is the craft surface.) | Reconcile each sentence against the artifact and state the denominator: 26.9% vs 649/2,297; the 741–770 base; the 283 omitted field rows; and label Table 19's column “KM recovery by H=4 (1−S)” with the crude share in a note. | Confirmed |
| **M11** | `paper/ref.bib`; reference list PDF pp. 25-26 | **The reference base is stale and heavily preprint.** 36/56 entries (64%) are `arXiv preprint` records, 22 are dated 2023, and the **maximum year is 2024** — at a November 2026 submission. Several 2023 preprints have likely since appeared at peer-reviewed venues; the list still cites the preprints. Author truncation is inconsistent: [1] lists seven authors, [3] and [4] print “X. Liu, et al.” because the `.bib` uses `and others`. There are no citations for the three target models or their revisions, no citation for the renderer/parser, and no citation for the preregistration. `bfcl` is a bare leaderboard URL. | A Q1 referee in 2026 expects 2025–26 agent-reliability work and published versions of the benchmarks. The absence is read as a literature gap, not a style choice. The missing model revisions are also a reproducibility gap. | Add 2025–26 work (verify specific records), update published versions of the 2023–24 benchmarks, unify author truncation, add model cards/revision hashes, cite the preregistration deposit, and give BFCL an access date (it has one in the `.bbl`; keep it). | Confirmed for counts/years; publication status per entry speculative |
| **M12** | Abstract `:294-295`; declarations `:1926-1935`; Methods `:685-690` | **The abstract's audit sentence is stronger than the audit.** “Audits were blind-rated label-free and checked by an agent verification panel” reads as human, independent verification. The body says the raters were AI-agent sessions sharing one model family, two severity sessions were identical on 116/120 items, and the panel is an agent panel. R4 C4 owns the integrity argument; the craft issue is that the abstract withholds the qualifier that makes the sentence true. | The paper's most careful disclosure is in the body; the abstract's compression removes exactly the limitation that matters. A reader who stops at the abstract overestimates the audit. | Add four words: “AI-operated blind raters, checked by an agent panel,” or move the limitation into the abstract's last sentence. | Confirmed |

### 3.3 Moderate (S3)

| ID | Location | Finding | Why it matters | Fix | Status |
|---|---|---|---|---|---|
| **D1** | `:1370-1400` | One **~420-word paragraph** (≈398 excluding numerals) merges the primary estimate, the typology, the coder-change history (0.684 → 0.867), the audit fix, and the G3 failure. It is roughly 1.7× the 250-word ceiling. | The most important result in the paper is the hardest paragraph to read. The coder history interrupts the estimate; the gate failure arrives after four unrelated sentences. | Split at “The switch typology…” and again at “The G3 gate did not pass…”. Keep the estimate and its CI together; move provenance to a short “Analysis history” paragraph or footnote. | Confirmed |
| **D2** | `:1045-1048`; `:1747-1749`; G0 in `:1035-1052`, `:1304-1315`, Table 2 | **Duplicated sentences and sections.** “The freeze dry-run validates…” and “The freeze is complete…” repeat the same 800+80 / 4,400 / 2,640 / 60 list in adjacent sentences. “The pre-registered sensitivity analyses exclude…” is immediately followed by “The pre-registered sensitivity analyses are complete.” The G0 counts appear in Table 2, Section 3.1, Section 4, and Results. | Repetition is the main reason the paper feels longer than its 9.2k words. It also makes the Results section look padded. | Delete the repeated freeze sentence, merge the two sensitivity sentences, and state the G0 counts once (Table 2) with Results pointing to the status only. | Confirmed |
| **D3** | `eq:decision` `:508-512`; `eq:render` `:499-507`; `eq:recovery` `:925-930`; `eq:ppv` `:1173-1179`; labels | **Equation hygiene.** The decision display ends with a period and is followed by lowercase “where” (`f_m(...).` then “where the design holds…”). The render display ends mid-sentence and the next clause begins “and target model `m` returns…”. The recovery display is spliced: "with interval censoring (Equation 20), [display] over H=4." The PPV where-clause is missing a verb: “where `TP` the automatic silent labels…”. **21 of 27 equation labels are never referenced**; only `eq:switch`, `eq:partition`, `eq:primary`, `eq:clogit`, `eq:recovery`, and `eq:mde` are cited. | These are small grammar faults with a large cumulative effect: the mathematical section reads as unproofed. Unreferenced displays are not wrong, but they add to the sense that the equations are decorative. | Remove the period before “where”; complete or split the render/decision sentence; make the recovery sentence one clause; add “are” after `TP`. Reference the displays the argument actually uses, or convert the rest to inline math. | Confirmed |
| **D4** | Table 16 `:1559-1569`; Table 19 `:1710`; Table 11 `:1410`; Table 2 `:579`; Table 10 `:1352`; Table 13 `:1488` | **Tables are not self-contained.** Table 16 prints “.911 / .959” and “.920 / .917” with no legend for nominal/interval or step/endpoint. Table 19 mixes an estimate and a p-value in one column (“`t_{1/2}` (Weibull `p`)”) and does not define “Recovered.” Table 11's “`n` groups/rows” uses a slash to mean two counts. Table 2 puts “87.39%” in a column headed “Count.” Table 10 has no CI column for a primary estimate. Table 13's “V-unparsed” has no `%` in the header though the cells are percentages. | A Q1 table must be readable without the body. Four of these require the reader to hunt for a definition; one (Table 19) invites a wrong recomputation. | Add table notes: KM vs crude; nominal vs interval α; step vs endpoint κ; groups vs rows; the 741–770 denominator. Add a 95% CI column to Table 10. Put the percentage in Table 2's note, not the Count column. | Confirmed |
| **D5** | `:1377-1378`, `:1394`, `:1578`, `:1598`, `:604`, `:1179` | **Grammar and antecedent faults.** “The slope is the log odds…, so an odds ratio of e^0.877 ≈ 2.40 per level, but that summary hides the shape” lacks a verb (“so [it corresponds to] an odds ratio”). “All three are positive and all are reported” (1394) has no clear antecedent after three different estimates. “In at least three, the design's automatic usage test matched…” (1578) never says three of what. “Two second raters independently re-rated…” (1598) is ambiguous. “The airline arm is the binding supply constraint” (604) misuses “arm” for “domain.” | These are the sentences a copy-editor would mark, and each one sits in a critical passage (primary estimate, audit, sample). | Rewrite the six sentences. In particular, replace “airline arm” with “airline domain” and “Two second raters” with “A second-rater pair.” | Confirmed |
| **D6** | Whole manuscript | **Terminology variants.** `pre-registered` 19× vs `preregistered` 1×; `pre-registration` 1× vs `preregistration` 9×. `s0` bare 9×, `$s0$` 8×, `$s=0$` 10×; table headers mix “s0” and “$s=0$.” `prefix-by-model` 3× vs `prefix$\times$model` 2×. `GPU-hours` 6× vs `GPU hours` 1×. `vs` and `versus` both used. “Sampling seed” describes a greedy rerun (1749) though decoding is “greedy with a fixed seed” (743). “Reliance” appears only in the title. | Inconsistent notation is the most common copy-edit note in Q1 reviews, and here it affects the paper's central factor (`s`). The title's “Reliance” is never operationalized; the paper measures switch/silent propagation, not reliance. | Pick one form of each term and apply it globally: `$s=0$`…`$s=3$` in text, tables, and figures; “pre-registered”; “GPU-hours”; “prefix-by-model”; “serving seed” or “repeat run.” Drop “Reliance” from the title or define it in the Introduction. | Confirmed (counts from source) |
| **D7** | `:1800-1811` | The paragraph announces “**Two** statistical properties bound the interpretation. First… Second…” and then continues with a **third**, unrelated argument (“The decomposition changes the interpretation of a positive slope”) for four more sentences. | The paragraph promises a structure it does not deliver, and the decomposition point is important enough to deserve its own paragraph. | End the paragraph after “calibrated dose–response law.” Start a new paragraph for the decomposition/detection contrast. | Confirmed |
| **D8** | `:1884-1896` | The Conclusion is **184 words** (profile target 120–160) in one paragraph, and says the audit “caught a labeling defect **before analysis**.” The earlier pre-fix analysis (β=0.684) is reported at `:1390-1394`, so the defect was caught after an analysis, not before. (R4 H3 owns the integrity reading.) | The conclusion is the last thing an editor reads; an inaccurate phrase there is costly. The length is minor but easy to fix. | Trim to ~150 words. Replace “before analysis” with “during the audit, before the reported estimate” or the accurate sequence. | Confirmed |
| **D9** | `:1822`, `:1888`, `:1894` | “The result will inform choices…” (future), “ran at **$0 cash**” (journal voice), and “the contribution is the dataset…” (singular, while four items follow). | These are tone slips in the closing pages: one future tense, one colloquialism, one singular/plural mismatch. | Use present/past indicative; “at no cash cost” or “without paid compute”; “the contributions are…”. | Confirmed |

### 3.4 Minor (S4)

| ID | Location | Finding | Fix | Status |
|---|---|---|---|---|
| **N1** | `:15-16`, `:56-58` | Stale source comments: “the manuscript carries 15 tables and 8 figures” (actual 21 and 10); “The four figures are generated by `paper/scripts/make_figures.py`” (actual ten figures; scripts live in `scripts/paper_figures/`, two files). | Update the comments; they mislead maintainers and Overleaf packagers. | Confirmed |
| **N2** | `:3-14`, `:26-45`, `:1941`; preamble | Dead or duplicated preamble: `tabularx` and `multirow` are loaded but never used; `color` duplicates the class's `xcolor`; `amsmath/amsfonts/amssymb` and `booktabs/array` are loaded again though the class loads them; the 4 pt float lengths at `:42-44` are overridden by the 10 pt values inside `\AtBeginDocument` at `:26-32`; `\bibsep` is set to 0.2 pt then 0 pt; `\tbd` is defined but unused. | Remove dead packages/settings; keep one float-spacing block; delete `\tbd` or use it. | Confirmed |
| **N3** | `:1047`, `:593`, `:1260` | Thousands separators are inconsistent: 58 braced `{,}` forms but three plain forms (“4,400”, “2,640”, “13,200”). | Standardise on `{,}` in text and tables. | Confirmed |
| **N4** | `:1942`; build log | `\bibfont` is forced to 8.5 pt on 9 pt leading, which is below the class default and triggers a `T1/cmtt` size-substitution warning (8.5 pt unavailable). References look cramped on pp. 25-26. | Use the class default, or 9 pt/10.5 pt; re-run and confirm no font warnings. | Confirmed |
| **N5** | PDF; build log; metadata | PDF hygiene: **31 duplicate destination warnings** (every figure and table); **no outline/bookmarks** (`\let\WriteBookmarks\relax`); metadata `subject = "Complex STM Content"` and empty keywords; 7.46 MB PDF because 9,000–11,000 px rasters are included at 6.2 in. | Add `\hypersetup{hypertexnames=false}` (verified: 31 → 0 warnings, page count unchanged); allow bookmarks or add `\pdfbookmark`; set `pdfsubject`/`pdfkeywords`; downsample rasters to 600 DPI at final size. | Confirmed (fix tested in a scratch copy) |
| **N6** | Captions; `:301`; package | Pre-submission checks that may be journal-specific: 7 keywords (many Elsevier journals cap at 6); no Highlights; no supplementary-material pointer despite 21 tables; no `elsarticle-num.bst` in the 14-file package (it resolves from TeX Live, but the dependency is undocumented). | Check the target journal's author guide; add a one-line build note if the `.bst` is not bundled. | Speculative (journal-dependent) |

---

## 4. Abstract ↔ Introduction ↔ Results ↔ Conclusion consistency

| Claim | Abstract | Body | Verdict |
|---|---|---|---|
| Sample | 800 real prefixes (400+400) | 800 analysed; 880 generated | Consistent for the analysis; the 880 run is never in the abstract (acceptable). |
| Primary slope | 0.877; 95% CI 0.770–0.998 | Same at `:1373-1375`; Table 10 | Consistent in text; **Fig. 5 shows 0.88 [0.76, 0.99]** (Wald, see M4). |
| Tier ORs | 1.27 / 4.60 / 11.21 | Same at `:1379`; Table 11; Fig. 6 | Consistent. |
| Silent propagation | 21.3% of 1,964 switches | Same at `:1629`; Table 18 gives 23.1% for s=2 only | Consistent, different denominators; state which is which. |
| Format jitter | 20–46% | 20.3–45.6% (G1, 60 prefixes) vs 19.8–38.1% (main, Table 15) | **Mixed samples** (M8). |
| Recovery | 32.4–47.6% | 32.4 / 47.6 / **28.2** at `:1686`; Table 19 | **Interval omits Llama** (S1-5). |
| Gate failures | Three | Three at `:1266`, `:1875`, `:1891`; **two** at `:384` | **Contradiction** (S1-6). |
| Linearity | “Rejected” | Pooled χ²(2)=25.03; Llama p=.274 | **Overgeneralized** (M8). |
| Parser failure | 1.55% vs <1% | Same at `:1395`; Table 16 | Consistent. |
| Severity share | 88.3% vs ≥90% | Same at `:1544`; Table 16 | Consistent. |
| Base generations | — | 13,200 (run) vs 12,000 (Table 8/Fig. 1) | **Planned vs executed unlabeled** (M9). |
| Recovery statistic | “recover” | Table 19 “Recovered” = KM 1−S(4) | **Unlabeled** (D4; R4 C1). |

The abstract is not padded and does not invent numbers. Its problem is compression: three of its
claims are stronger than the table they summarize. The Introduction's “Two preregistered criteria”
and “replace the earlier placeholders” are the only outright draft artefacts in the front matter.

---

## 5. Structure and paragraph architecture

**Counts.** Six numbered sections (correct for the profile), six numbered subsections, **40 bold
run-in headings**, two algorithms, 23 `equation` environments plus one four-row `align` (27 numbered
displays), 21 tables, 10 figures, 58 substantive paragraphs, ~9,250 body words.

| Section | Words | Paragraphs | Run-ins | Numbered subsections | Tables | Figures |
|---|---:|---:|---:|---:|---:|---:|
| 1 Introduction | 815 | 5 | 0 | 0 | 0 | 0 |
| 2 Conventional Method | 664 | 4 | 5 | 0 | 0 | 0 |
| 3 Proposed Method | 2,991 | 20 | 12 | 4 | 4 | 4 |
| 4 Experiment | 1,268 | 13 | 10 | 1 | 3 | 0 |
| 5 Results | 3,358 | 22 | 13 | 1 | 14 | 6 |
| 6 Conclusion | 158 | 1 | 0 | 0 | 0 | 0 |

**Interpretation.** The heading density is the problem, not the section count. Section 4 has one
heading per ~115 words; Section 3 has one per ~185. The numbered subsections do not track the
content: 4.1 "Evaluation Metrics" appears after the gate, environment, and model-fit
material; 5.1 “Primary severity–switch estimate” is followed by ten unnumbered headings that
look like siblings but are not numbered. In Section 3.3 (“Next-decision prompt”), the run-ins
“Parser and canonicalization,” “Context and length envelope,” and “Serving stack and the model trio”
are not about the prompt at all; they belong under a “Harness” subsection or in Section 4.

**Paragraphs.** Mean 175 words, median 168, max ~420. That is broadly within the profile's
120–250 target, but six paragraphs are below 110 words and the 420-word estimate paragraph (D1)
is the outlier. The profile bans 3–6-line stubs; the paper has few true stubs, but it has many
one-sentence “paragraphs” created by a run-in heading with no following blank line.

**Ending.** The Conclusion is one paragraph (correct) but 184 words (above the 120–160 target) and
ends on the gate failure rather than a forward-looking sentence. That is a defensible choice for
this paper; the length is the only craft issue.

---

## 6. Voice against `VOICE_PROFILE.md`

I measured the body (Introduction through Conclusion, floats/equations removed; 236 sentences,
~9,250 words) with the same rough tokenisation for both texts.

| Feature | Profile target | Manuscript | Verdict |
|---|---|---|---|
| Sections | 6 | 6 | Pass. |
| Subsections | 3–5 core per section; no sprawl | 6 numbered + 40 run-ins | **Fail.** |
| Paragraph mean | 120–250+ words | 175 mean, 168 median, 420 max | Mostly pass; one major outlier. |
| Sentence mean / SD | 20.4 / 10.8 words | 22.8 / 13.3 | Pass (slightly longer, slightly burstier). |
| Sentences >40 words | Occasional | 18/236 (7.6%) | Pass. |
| “The” sentence openings | Not specified, but variety expected | **98/236 (41.5%)** | **Fail.** Monotone. |
| First-person plural | “We” for author decisions | **1 “We”**, 0 “our”; ~30 self-references (“the paper/study/design”) | **Fail.** The paper narrates itself in third person. |
| Subordinating connectors | While 20, Although 11, Since 7, However 12, Thus 8 (per 10k) | While 2, Although 0, Since 0, However 0, Thus 0, Therefore 2 | **Fail.** The prose is paratactic; clauses are stacked with “and” rather than subordinated. |
| Banned clichés | Furthermore / Moreover / In conclusion = 0 | 0 / 0 / 0 | Pass. |
| Tense | Past for results, present for definitions/visuals | Present indicative dominates Results (“The pooled slope is…”, “The base matrix is complete”); 234 is/are vs 16 was/were | **Fail** for the Results convention. |
| `where` definitions | Every display continued with lowercase "where" | 12 displays begin with lowercase "where"; most others use "with"/"over"; 4 faults (D3) | Partial. |
| Conclusion | One paragraph, 120–160 words | One paragraph, 184 words | Partial. |
| Captions | 1–2 lines, ≤25 words | All ≤24 words | Pass. |
| Figures | 600+ DPI, large legible fonts | 600 DPI, but effective 4.6–7.7 pt | **Fail** on legibility (M3). |

**Diagnosis.** The voice is not “AI-flavoured” in the usual sense — there are no banned transitions
and no adjective inflation. It is *bureaucratic*: 41.5% “The” openings, ~30 self-references, almost
no “we,” and a tense pattern that describes the paper rather than the work. The profile's own
sample uses “We evaluated…”, “We tested…”, and subordination (“While…”, “Although…”) to vary the
rhythm. The fix is not to add clichés; it is to restore agents (“we”) and subordinate clauses, and
to put the completed study in the past tense.

**Registered-report residue (M7).** The voice problem is concentrated in the Discussion. Lines
1786–1851 were evidently written before the run and not fully revised: “If the slope is flat…,”
“The result will inform…,” “the paper will say so,” “known in advance,” “null-result asset,”
“What would change the claim.” This is the largest single block of text that reads as unreconciled
with the completed results.

---

## 7. Figures (10)

All ten files are PNG with a 600 DPI `pHYs` chunk, 4,477–10,944 px wide, 0.13–1.66 MB. Technical
resolution is not the issue; printed type size is.

| Fig. | Canvas (in) | Included width | Smallest effective type* | Cited? | Content | Redundant with | Verdict |
|---|---:|---:|---:|---|---|---|---|
| 1 | 15.0×9.2 | 0.95 | ~5.8 pt | Yes | Fixed-prefix design | §3.1 text | Keep, regenerate at print size |
| 2 | 17.0×10.0 | 0.95 | ~5.1 pt | Yes | Arm construction | Table 3 + §3.1 text | Move to supplement or drop |
| 3 | 18.0×10.0 | 0.95 | ~4.8 pt | Yes | Pipeline and gates | Table 2 + Table 5 | Regenerate or drop |
| 4 | 16.0×8.8 | 0.95 | ~5.4 pt | Yes | "Illustrative, not data" | §3 design text | **Remove/replace** (S1-1) |
| 5 | 7.6×3.3 | 0.95 | ~8.1 pt | **No** | Forest plot | Table 10 | Cite; fix CI (M4) |
| 6 | 12.6×3.6 | 0.98 | ~4.6 pt | Yes | Tier ORs | Table 11 | Supplement or regenerate |
| 7 | 8.4×4.0 | 0.95 | ~7.4 pt | **No** | Switch rates | Table 15 | Cite; keep one of table/figure |
| 8 | 8.0×3.7 | 0.95 | ~7.7 pt | **No** | Field types | Table 18 | Cite; keep one of table/figure |
| 9 | 11.2×3.8 | 0.98 | ~5.1 pt | Yes | KM curves | Table 19 | Keep, regenerate, note truncated axis |
| 10 | 12.0×3.8 | 0.98 | ~4.8 pt | Yes | Sensitivity + strata | Table 21 (left panel) | Keep right panel; regenerate |

\* Estimated from the scripts' `figsize` and font sizes, scaled to a 444.9 pt (6.18 in) text width;
checked against 100-dpi page renders. Error ≈ ±0.5 pt.

**Findings.**

1. **Legibility (M3).** Nine of ten figures print below 8 pt; seven are ~5 pt. The schematics are
   the worst because they were drawn on 15–18 in canvases with 14 pt labels. The QC script checks
   DPI and pixel count, so it passes while the page result fails. This is the clearest violation of
   the profile's “large legible fonts” requirement.
2. **Fig. 4 is a draft artefact (S1-1).** The red “ILLUSTRATIVE — NOT DATA” stamp and the sentence
   “no study outcomes have been generated” are visible at print size on p. 11. Even if the figure
   is retained as a conceptual diagram, the sentence is false for this submission.
3. **Fig. 5 uses a different interval from the text (M4).** The forest labels are Wald; the text
   and Table 10 report bootstrap. The pooled label [0.76, 0.99] cannot be reconciled with
   [0.770, 0.998] by rounding.
4. **Three figures are orphaned (M5).** Figs 5, 7, 8 are never cited. Journals routinely return
   manuscripts for this.
5. **Redundancy (M5).** Five figure–table pairs carry the same numbers: Fig. 6/Table 11,
   Fig. 7/Table 15, Fig. 8/Table 18, Fig. 10-left/Table 21, Fig. 2/Table 3. In a 26-page paper,
   that is ~2–3 pages of duplicated evidence.
6. **Colour accessibility (S3).** Figs 7 and 9 distinguish model series by colour only (blue/orange/green; all solid lines in Fig. 9). Fig. 6 and Fig. 10 use colour but also direct row labels/panels. Deuteranopes can separate orange from blue but not reliably blue from green. Add markers, line styles, or direct labels; keep the palette.
7. **Captions.** All are ≤25 words, as required, but several are too terse to be self-contained:
   Fig. 2 (“Arm construction illustrated for one prefix”) does not say what the five arms are;
   Fig. 9 does not say it has two panels (s=2 and s=3) or that the y-axis is truncated at 0.55;
   Fig. 10's “within strata” is vague. The profile wants concise captions, not cryptic ones — one
   extra clause each is compatible with the limit.
8. **Axis choices.** Fig. 9 truncates the y-axis at 0.55, which exaggerates the separation. That is
   defensible for survival curves, but the caption must say so; otherwise it reads as a misleading
   scale.

---

## 8. Tables (21)

**Are they all necessary?** No. The main text carries 21 tables for ~9,250 words, roughly one float
per 300 words. Six to eight are supplementary-grade or duplicates. A realistic main-text set is
13–15 tables plus 7 figures.

| # | Label | Content | Verdict | Note |
|---:|---|---|---|---|
| 1 | `tab:notation` | Symbols | Keep | Caption false; ~20 symbols missing (M6). |
| 2 | `tab:supply` | Harvest funnel | Keep | “87.39%” in the Count column (D4). |
| 3 | `tab:arms` | Five arms | Keep | Good; Fig. 2 duplicates it. |
| 4 | `tab:models` | Model trio | Keep | Fold Table 6 into this table. |
| 5 | `tab:gates` | G0–G4 criteria | Keep | Incomplete/outdated; omits the s2/s3 ≥90% row (S1-4). |
| 6 | `tab:fit` | Synthetic fit checks | **Merge/supplement** | Non-study table; duplicates Table 4's model rows. |
| 7 | `tab:envelope` | Planned generations | **Supplement** | Planning arithmetic; label “planned” (M9). |
| 8 | `tab:pilot` | Pilot results | Keep (or supplement) | Screening only; one table is enough. |
| 9 | `tab:g1` | Calibration | Keep | Needed for the G1 story; add the amendment note. |
| 10 | `tab:primary` | Primary slopes | Keep | **Never cited**; add CI column (M5, D4). |
| 11 | `tab:tiers` | Tier ORs | Keep | “groups/rows” slash (D4). |
| 12 | `tab:diagnostics` | LRT + McNemar | Keep | Good. |
| 13 | `tab:missing` | Coverage | Keep | Reconcile with 741–770 (M10). |
| 14 | `tab:typology` | Strata types | Keep or supplement | Text repeats all four shares. |
| 15 | `tab:armrates` | Switch rates | **Drop** | Fig. 7 shows the same numbers with CIs; cite Fig. 7 instead. |
| 16 | `tab:audit` | Audit gates | Keep | Slashes unexplained (D4). |
| 17 | `tab:panel` | Verification panel | **Supplement** | Secondary audit detail. |
| 18 | `tab:fieldtypes` | Field classes | Keep | Rows do not sum to total (M10). |
| 19 | `tab:recovery` | KM by model | Keep | “Recovered” unlabeled (M10). |
| 20 | `tab:recovery_all` | Recovery summary | **Merge into 19** | Repeats s=2/s=3 columns. |
| 21 | `tab:sensitivity` | Sensitivity slopes | Keep | Fig. 10-left duplicates it. |

**Formatting and overfull.** There are **zero overfull hboxes** in the build; the tables fit. Tables
5, 11, 12, 19 use `\footnotesize` (8 pt), which is acceptable but at the low end; Table 19's eight
columns are the most cramped. `booktabs` rules and `\arraystretch{1.08}` are consistent. The main
formatting problem is not overflow but **self-containment** (D4): four tables need notes to be
readable without the body.

**Numbering.** Table order matches first appearance and all numbers are sequential. Only Table 10
is never cited. Figure numbering is also sequential, but Figs 5, 7, 8 are never cited (M5).

---

## 9. Equations and notation (23 `equation` environments; 27 numbered displays)

**Collisions.** Table 1 says “The same symbol is used with the same meaning throughout the paper.”
The paper uses at least ten symbols with two or three meanings:

| Symbol | Meaning A | Meaning B | Meaning C | Suggested resolution |
|---|---|---|---|---|
| `S` | Success `S(τ)` (eq:e2e) | Subset `S ⊆ g` (eq:clogit) | Survival `S(h)`, `S_W(t)` (eq:km, eq:weibull) | Rename survival to `R(h)`; keep `S(τ)` for success; use `T ⊆ g` for subsets. |
| `α` | Prefix intercept `α_{p,m}` (eq:primary) | Level `.05` (eq:mde) | Krippendorff's α (eq:alpha) | Rename intercept to `a_{p,m}` or the level to `α_0`. |
| `β` | Severity slope (eq:primary) | Power in `z_{1-β}` (eq:mde) | Quadratic `β_2` (eq:categorical text) | Use `1-π` for power; rename the quadratic coefficient `δ`. |
| `κ` | Cohen's κ (eq:kappa) | Weibull shape (eq:weibull) | — | Rename the shape `ν`. |
| `h` | Recovery step (eq:recovery) | Hazard `h_W(t)` (eq:weibull) | — | Rename the hazard `λ_W(t)`. |
| `U` | `Y^U` silent propagation (eq:silent) | Score `U_g(β)` (eq:score) | — | Rename the score `s_g(β)`. |
| `V` | Verbatim arm | Variance `V_g(β)` (eq:score, eq:sandwich) | — | Rename the variance `W_g`. |
| `p` | Prefix | p-value (eq:mcnemar) | `p_o`, `p_e`, `p̂` (eq:kappa, eq:wilson) | Use `i` for prefix in the statistical section, or `P` for p-values. |
| `H` | Horizon `H=4` (eq:recovery) | Null `H_1` (eq:primary text) | — | Spell out `H_0/H_1` or use `H_{\text{hyp}}`. |
| `k` | `k_g` switches (eq:clogit) | Binomial index (eq:mcnemar) | `δ²(c,k)` categories (eq:alpha) | Minor; subscript the category index. |

**Missing definitions.** Table 1 omits `Π_s`, `T_prose`, `f_m`, `γ_k`, `Λ`, `λ`, `θ_e2e`, `G_τ`,
`z_T`, `v*`, `𝒱(d)`, `F`, `C^A/C^F/C^U/C^O`, `n_a`, `E_g`, `U_g`, `V_g`, `S_W`, `h_W`, and
`RMST`. Some are defined in passing; at least a dozen are not. A reader who starts at Eq. (1) cannot
decode the conditional-likelihood display without the text.

**Equation hygiene (D3).** Four punctuation/grammar faults (`eq:render`, `eq:decision`, `eq:recovery`,
`eq:ppv`) and **21 of 27 equation labels never referenced**. The `where` convention is otherwise mostly followed
(12 displays begin with lowercase "where"; the rest use "with"/"over" definitions), which is a
strength.

**Recommendation.** Keep Table 1 but change its caption to “Symbols used in the primary estimand”
and add a second block for the statistical displays; or rename the collisions. The first option is
less invasive and truthful.

---

## 10. Citations (56)

**Strengths.**

- 56 entries, 56 cited, zero uncited, zero duplicates, zero BibTeX warnings.
- The statistical canon is complete and correctly used: Chamberlain (1980), Cameron & Miller (2015),
  Efron (1979), Holm (1979), Wilson (1927), McNemar (1947), Kaplan & Meier (1958), Jonckheere
  (1954), Cohen (1960), Landis & Koch (1977), Hayes & Krippendorff (2007).
- The agent-benchmark canon is present: τ-bench, AgentBench, WebArena, OSWorld, WebVoyager,
  Mind2Web, GAIA, SWE-bench, AppWorld, ToolLLM, MINT, BFCL, API-Bank, ToolSandbox.
- No self-citation padding.

**Problems.**

1. **Recency.** Maximum year is **2024**; 35/56 entries are 2023–2024; nothing from 2025–2026 at a
   November 2026 submission. For a fast-moving agent-reliability paper, that is a visible gap.
2. **Preprint dependence.** 36/56 (64%) are `arXiv preprint` records, many from 2023. Several have
   since appeared at NeurIPS/ICLR/ACL/EMNLP (I did not verify each); the list still cites the preprints. The `.bib` types
   them as `@article` with `journal = {arXiv preprint arXiv:...}`, which is not a journal.
3. **Inconsistent author truncation.** [1] lists seven authors; [3] and [4] print “X. Liu, et al.”
   and “S. Zhou, et al.” because those entries use `and others`. This is visible on p. 25 and looks careless.
4. **No model citations.** Qwen3.5-9B, Ministral-3-8B-Instruct-2512, and Llama-3.1-8B have no
   model card, technical report, or revision hash. For reproducibility, the exact HF revision is
   as important as the vLLM version.
5. **No preregistration citation.** The paper's central credibility device is a pre-registration
   with no registry entry and no DOI/URL in the references (R4 C3 covers the status).
6. **BFCL is a leaderboard URL only.** It has an access date in the `.bbl` (“accessed 11 November
   2026”), which is good; it should also have a stable report or a note that it is a live
   leaderboard.
7. **Renderer/parser.** The parser is named (`toolresult-parser-v4`) but not cited or deposited;
   the renderer version is never named at all.

**Fix.** Add 2025–26 agent/tool-reliability work, replace preprints with published versions where
they exist, unify author truncation, add model cards and revision hashes, cite the preregistration,
and name the renderer version. I did not verify the publication status of each arXiv record; that
is the one speculative part of this item.

---

## 11. Reproducibility and Overleaf readiness

**Package.** Exactly **14 files**: `toolresults.tex`, `ref.bib`, `cas-sc.cls`,
`cas-common.sty`, and `figures/fig1.png`–`fig10.png`. No `\input`, no absolute paths, no missing
graphics. The `.tex` and `.bib` are pure ASCII, so there are no encoding or special-character
risks.

**Clean-room compile (verified).** I copied the 14 files to a scratch directory and ran
`pdflatex → bibtex → pdflatex → pdflatex` with TeX Live 2026:

- 26 pages, 0 errors, 0 undefined references, 0 overfull boxes.
- 31 `pdfTeX warning: destination with the same identifier ... duplicate ignored` (one per
  figure/table).
- 2 underfull hboxes, both in the supply paragraph (`:551-571`).
- 2 font warnings: `T1/cmtt/m/n` at 8.5 pt unavailable, and size substitutions.
- `elsarticle-num.bst` resolves from TeX Live; it is **not** in the package. A 14-file package is
  honest only if the target venue's TeX distribution includes `elsarticle`. Overleaf does; a
  minimal local TeX install may not.

| Check | Result | Action |
|---|---|---|
| Files | 14, all present | Add a one-line build note (pdfLaTeX, BibTeX, two passes). |
| Compile | Clean, 26 pp | None. |
| Overfull boxes | 0 | None. |
| Underfull boxes | 2 (supply paragraph) | Reword the long value-used sentence. |
| Duplicate anchors | 31 | `\hypersetup{hypertexnames=false}`; verified 31 → 0, 26 pp unchanged. |
| PDF outline | Empty | Allow bookmarks (`\let\WriteBookmarks\relax` currently suppresses them) or add `\pdfbookmark`. |
| PDF metadata | Title/author set; subject “Complex STM Content”; keywords empty | Set `pdfsubject`, `pdfkeywords`. |
| Line numbering | Continuous 1–660; references 661+ | Acceptable; check journal style. |
| Figure paths | `\graphicspath` + `figures/` | Fine. |
| Pending macros | 3 red blocks | Resolve (S1-3). |
| Fonts | STIX body, cm-super sans; cmtt 8.5 substitution | Use 9 pt bibliography or class default. |
| PDF size | 7.46 MB; the four largest rasters (9,000–11,000 px) are included at 6.2 in | Downsample to 600 DPI at final size; the file should shrink substantially. |
| Class patches | ORCID/`\stmauthors`/nologo patches rely on cas-common v2.3 internals | Fine while the class files are bundled; document the version in a build note. |

**Fragility notes.** The `\ExplSyntaxOn` patches that redefine `\author`, `\stmauthors`,
`\printorcid`, and the nologo boolean are tightly coupled to `cas-common.sty` v2.3. Because the
class files are bundled, this works; if the journal's production system replaces them, the byline
will break. Keep a plain-class fallback comment or a `\providecommand` guard. The `\figfile`
fallback is a good idea and should stay.

---

## 12. Declarations

| Item | Status | Finding |
|---|---|---|
| Funding | OK | No external funding; H200 in kind. Clear. |
| Conflicts of interest | OK | Standard wording. Elsevier's CAS template usually calls this “Declaration of competing interest”; check the journal. |
| Data availability | **Blocked** | DOI/manifest hash is `\pending{}`; the dataset is unreleased. The licence plan (CC BY 4.0, upstream notices) is clear. R4 C5 covers the evidence gap. |
| Code availability | OK with check | GitHub URL and MIT licence. I did not verify the URL live; R4 M8 says the “one-command validation target” does not exist, which contradicts `:1251-1253`. |
| Ethical approval | **Contradictory** | Says “Annotation is performed by the author team on public benchmark rows,” but the AI-use item and Methods say blind rating sessions were operated with an AI agent. Both cannot be true. The determination is also `\pending{}`. |
| Author contributions | **Blocked** | Credits S.A.S. and M.M.A., who are not authors; prints an internal “must be confirmed” note; uses hyphens where Elsevier uses en dashes. |
| AI-assisted tooling | Present, incomplete | Discloses sessions and the panel, but not the model family/version, prompts, or dates (R4 H13). Heading is non-standard; Elsevier asks for a “Declaration of generative AI in scientific writing.” |
| Acknowledgements | OK | Appropriate. |
| Missing items | — | No Highlights, no supplementary-material pointer, 7 keywords. Check the target journal. |

---

## 13. Top 10 priorities (in order)

1. **Clear the submission blockers.** Fix the author/CRediT mismatch, remove the three
   `\pending{}` blocks and the internal “confirm” note, and reconcile the ethics sentence with the
   AI-use statement. Nothing else matters if the byline is wrong.
2. **Remove or replace Fig. 4.** A figure that says “no study outcomes have been generated” cannot
   ship with a completed-results paper. Relabel Fig. 3's audit box at the same time.
3. **Fix the three misstatements a referee will check first:** the recovery interval that omits
   28.2, the Introduction's “two” vs the body's “three,” and the G1 criterion in Table 5/Fig. 3.
4. **Reconcile planned/executed and the denominator mismatches** (12,000/13,200;
   34,800/36,000; 617/28.3%; 741–770/Table 13; Table 18's 1,984/2,267; Table 19's KM column).
5. **Regenerate Figs 1–4, 6, 9, 10 at print size** with ≥8 pt effective type, and fix Fig. 5's CI
   method. This is the single biggest visual-quality gain.
6. **Restructure headings.** Convert 40 run-ins to at most 5 numbered subsections per section,
   add the six missing paragraph breaks, and either rename Section 5 “Results and Discussion” or
   add a Discussion section.
7. **Consolidate the float program.** Cite Table 10/Figs 5/7/8, merge Table 20 into 19, move 6–8
   tables to supplementary material, and eliminate the text-free plate page (p. 21).
8. **Clean the notation.** Make Table 1's caption true, add the missing symbols, resolve the ten
   collisions, and fix the four equation-grammar faults.
9. **Revise the Discussion out of registered-report tense.** Replace future/conditional sentences
   with what was found and what it means; delete “replace the earlier placeholders.”
10. **Refresh the references and the PDF package.** Add 2025–26 work and published versions, unify
    author lists, add model cards, set metadata/bookmarks, and apply the verified
    `hypertexnames=false` fix.

---

## 14. Copy-edit checklist (10 items)

- [ ] **1. Notation sweep.** Replace bare `s0`, `s2`, `s3`, `s2/s3` with `$s=0$`…`$s=3$` in text,
  table headers, and figure labels; define `s(V)`; add the missing symbols or change Table 1's
  caption; rename at least `S` (survival), `α` (level), `β` (power), `κ` (shape), `h` (hazard),
  `U` (score), and `V` (variance).
- [ ] **2. Heading sweep.** Add a blank line before every `\noindent\textbf`; convert the 40 run-ins
  to ≤5 numbered subsections per section; fix 4.1 and 5.1 so the numbering matches the content.
- [ ] **3. Figure sweep.** Cite Figs 5, 7, 8; label Fig. 9's KM and truncated axis; label
  Fig. 5's interval method; remove Fig. 4's “no outcomes” sentence or the figure; relabel Fig. 3's
  audit box.
- [ ] **4. Table sweep.** Add notes to Tables 2, 11, 13, 16, 19; add a CI column to Table 10;
  merge Table 20 into 19; drop Table 15 or Fig. 7.
- [ ] **5. Sentence sweep.** Rewrite the six flagged sentences: the odds-ratio fragment (1377), “All
  three are positive” (1394), “In at least three” (1578), “Two second raters” (1598), “airline arm”
  (604), and the PPV where-clause (1179).
- [ ] **6. Terminology sweep.** Standardise `pre-registered`, `GPU-hours`, `prefix-by-model`,
  `versus`, and `serving seed`; remove `Reliance` from the title or define it.
- [ ] **7. Duplicate sweep.** Delete the repeated freeze sentence (1046–48), merge the two
  sensitivity openings (1747–49), and collapse the four G0 count statements to one.
- [ ] **8. Declarations sweep.** Fix authors/CRediT, remove all three `\pending{}` blocks and the
  internal note, make the ethics sentence accurate, add the AI model/version, and add the DOI or a
  neutral status sentence.
- [ ] **9. PDF sweep.** Add `\hypersetup{hypertexnames=false}`; enable bookmarks; set
  `pdfsubject`/`pdfkeywords`; raise the bibliography font to 9 pt; downsample the rasters.
- [ ] **10. Source-hygiene sweep.** Update the stale comments (15/8, “four figures”, script path),
  drop unused `tabularx`/`multirow`/`color`, resolve the 4 pt vs 10 pt float lengths, and use
  `{,}` in the three plain thousands.

---

## 15. Limits

- I did not re-run the analysis, re-generate the figures from artifacts, or inspect raw τ-bench
  trajectories or PII. I read the paper, the PDF, the figure scripts, the `.bib`, the build log,
  and the package.
- I did not verify each arXiv entry's publication status, the GitHub URL's liveness, or the target
  journal's current limits on keywords/highlights. Those items are marked speculative where they
  depend on external facts.
- Effective figure font sizes are estimates from the scripts' `figsize`/font sizes scaled to the
  printed width, checked against 100-dpi page renders; the error is about ±0.5 pt, which does not
  change the conclusion (all are below 8 pt except Fig. 5).
- Where the text and a table disagree, I recommend making the text match the table or naming the
  denominator; I do not assert which number is scientifically correct. Statistical substance is
  R1's and R4's remit.
- I did not test the manuscript in the journal's own submission class or editorial system; the
  clean-room test used the bundled `cas-sc.cls`/`cas-common.sty` and TeX Live 2026.
