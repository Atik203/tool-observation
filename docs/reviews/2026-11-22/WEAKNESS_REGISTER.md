# ToolResult-800 — Weakness Register

**Date:** 2026-11-22
**Scope:** whole project, method, contribution, manuscript, audit, and release.
**Inputs:** four independent reviews in `docs/reviews/2026-11-22/` (method/statistics, contribution/positioning, paper craft, integrity/adversarial). This file deduplicates and ranks their findings; the individual reports hold the full evidence.

## 1. Consensus verdict

All four reviewers independently reached **major revision / reject in current form**. The study has a real artifact and a defensible measurement contribution, but the manuscript currently claims more than the gates allow, reports recovery on the wrong statistic, and cannot yet be externally reproduced.

| Lens | Verdict | One-line reason |
|---|---|---|
| Method & statistics | Major revision | Bounded, renderer-local mover effect; not the causal/content claim in the title/abstract |
| Contribution & positioning | Major revision | Publishable as measurement/benchmark paper; novelty claim outdated; no task-success endpoint |
| Paper craft | Major revision | Draft artifacts, ghost CRediT, figure/caption/table defects before science is read |
| Integrity & reproducibility | Reject | Recovery estimand, G1 amendment history, AI-only audit, unreleased evidence |

The common diagnosis: **the paper is trying to be a causal study, a dataset paper, and a measurement paper at once.** The evidence supports the third. The revision should choose that identity and make every claim, table, and disclosure match it.

## 2. Critical findings (fix before resubmission)

| ID | Area | Finding | Evidence | Why it blocks | Fix | Effort |
|---|---|---|---|---|---|---|
| C1 | Claim boundary | Title says “A Fixed-Prefix Causal Study”; abstract says “Critical errors move the next decision”; Results say “no content-sensitivity claim” because G3 failed | `toolresults.tex:244, 284–295, 1396–1398, 1894–1896`; `docs/GATES.md:16,121` | The paper asserts the exact claim its own gate forbids; reviewers read this as hedging or overclaiming | Retitle to a measurement study; lead the abstract with the measurement and the three failures; use “measured shift among movers,” not “move” | 1–2 days, writing |
| C2 | Recovery estimand | “Recovered” is Kaplan–Meier \(1-S(4)\), not `Events/n`. Crude s=3 shares are 27.3/34.7/27.2%, not 32.4/47.6/28.2% | `toolresults.tex:1686–1698, 1712–1717`; `g4_recovery.json:298–342`; `docs/GATES.md:134` | The G4 gate is “≥50% recovery events”; KM censors terminal non-recovery as non-informative, biasing upward; “Ministral is close” is an artifact | Report crude cumulative incidence as the gate; keep KM as secondary with a competing-risk caveat; add both columns; recompute RMST/\(t_{1/2}\) | 2–3 days, reanalysis |
| C3 | Recovery risk set | Risk set uses exact `signature_hash` inequality; the paper’s switch definition uses semantic `signatures_differ`. Llama s3: 412 at-risk vs 377 reported switches; Ministral 406 vs 390; Qwen 264 vs 286 | `recovery_run.py:127–136`; `outcomes.py:117`; `g4_recovery.json`; `g3_analysis.json` | The recovery estimate is conditional on a set that is not the reported switch set; the gate is not reproducible from the paper | Rebuild the risk set from the v4 semantic definition; report membership overlap; re-estimate curves; add inclusion/exclusion table | 2–3 days, reanalysis |
| C4 | Recovery censoring | Final answers and parse failures are censored, not treated as non-recovery. Ministral s3: 120/406 parse-failure, 84/406 final-answer, only 61/406 run to H=4 | `recovery_run.py:192`; `recovery.py:42–47,75–99`; `recovery_deep.json` | Censoring is informative; the 47.6% value depends on it; the recovery parse-failure rate is unreported | Add censoring-reason table; treat final answers as failures in a co-primary analysis; parse failures as failures in sensitivity; report recovery parse-failure rate | 2–3 days, reanalysis |
| C5 | Severity construct | Assigned dose ≠ realized dose: 7/60 (majority), 11/60 (sheet-visible verifier), 16/60 (blind verifier) critical items are donor-unused; s2/s3 gate 88.3%; s1 has 3/30 decision-changing | `toolresults.tex:1544–1586`; `blind_audit_result.json`; `severity_verification_report.md` | Tier ORs and the “threshold at s2” are in assigned labels, not verified criticality; 12–27% mismeasurement attenuates the effect | Report the 7/11/16 range in results/abstract; reclassify audit-flagged items and re-estimate tier ORs; describe the estimand as “assigned severity” | 3–5 days, reanalysis |
| C6 | Audit independence | Raters are AI-agent sessions sharing one model family; r1 = r2 on 116/120 severity items; no human verified the final round; packet rebuilt four times | `toolresults.tex:685–690, 1588–1604, 1868–1870`; `panel_record.json`; D-043 | \(\alpha=.911\) and \(\kappa=.987\) are consistency among near-duplicates, not independent reliability; abstract overclaims | Put “AI-operated, one model family, no human verification” in the abstract; replace “independent” with “separate”; add a human 40-item subset or call it a consistency check | 2 days + human audit if available |
| C7 | Prereg / G1 history | Original G1 V-vs-s0 criterion failed at 20.3/36.7/45.6% vs ≤20%; A-004 changed it post-freeze, not blind; paper says “G1 passed” and “no threshold was changed” | `AMENDMENTS.md:77–93`; `DECISIONS.md:67–73`; `toolresults.tex:1064–1066, 1878–1880`; `g1_calibration_v3.json` | A gate relaxed after seeing data is not a pre-registered pass; the “no threshold changed” sentence is false | Report original criterion as failed; label A-004 post-hoc/not blind; delete “no threshold was changed”; add G1 to the failure count or explain the count | 1 day, writing + gate table |
| C8 | Reproducibility | All analysis/audit artifacts and ledgers are gitignored; no DOI/release; “one-command validation” only checks YAML configs | `.gitignore:123–139`; `Makefile:25–26`; `toolresults.tex:1245–1253, 1913` | External readers cannot reproduce any table; the paper’s traceability claim is false for them | Publish scrubbed artifacts/ledger extracts with DOI; implement or remove validation claim; add table-to-artifact map | 1–2 weeks, release work |
| C9 | Novelty | “No controlled estimate” is outdated; 2026 work studies quiet tool failures, recovery, and paired error injection. 36/56 refs arXiv-only, max year 2024 | `toolresults.tex:360–362, 404–440`; `ref.bib`; verified arXiv IDs in the contribution report | A Q1 reviewer will see an uninformed or overstated gap; the real delta is a combination, not a vacuum | Cite/differentiate ToolMaze, Loud Failures, Fabrication After Tool Failure, Robustness Analysis, Measuring What…, ToolScan, ToolSword, ToolBeHonest, Sclar et al.; add comparison table; narrow gap | 2–3 days, writing + refs |
| C10 | No task-success endpoint | Outcome is deviation from donor V, not task error; recovery is reversion to V, not correctness; practical implications assume harm not shown | `toolresults.tex:779–823, 917–923, 1820–1831` | “Silent propagation harms outcomes” is unsupported; a switch can be correct skepticism | Add 100–200 prefix task-success/utility endpoint, or a wrong-direction analysis from perturbation records; rename R1 “reference decision” | 1–2 weeks if full rollout; 2 days for wrong-direction |
| C11 | Format vs content | V-vs-s0 format effect 20–46% exceeds the content effect in 2/3 models; one renderer; V excluded from slope | `toolresults.tex:987, 1322–1325, 290, 519` | Treatment is a bundle of content + format + length/salience; content claim is template-local | Make format sensitivity a headline; add a second renderer on 100–200 prefixes; report prompt length/position by arm | 1 week, new run |
| C12 | Negative control | s1 OR = 1.27 [1.04, 1.55], p=.019, not null; marginal s1–s0 +1.1 pp | `toolresults.tex:1416, 1443, 1476`; `prereg_secondary.json` | The “non-critical” arm is not inert; the threshold may be a gradient from s0 to s1 to s2 | Report s1 OR and marginal RD honestly; discuss s1 contamination; consider s1 as a low dose | 1 day, writing + table |
| C13 | Silent share / PPV | 21.3% silent share is uncorrected for recall .75; PPV 9/9 has exact 95% lower bound .66 | `toolresults.tex:1542, 1627–1634`; `blind_audit_result.json:77–82` | The headline silent share is a lower bound; the PPV gate passes on a point estimate, not at 95% confidence | Report 21.3% as a lower bound; add recall-adjusted estimate (~28.5%, uncertain); add PPV lower bound to gate table | 1–2 days, reanalysis |
| C14 | Craft blockers | Fig. 4 says “no study outcomes have been generated”; three red `[PENDING]` blocks; CRediT credits S.A.S./M.M.A. not on byline; G1 table reports a criterion the study failed; recovery range omits Llama 28.2%; Intro says two failures vs three | `toolresults.tex:998–1005, 1315, 1913, 1919, 1920–1925, 1027–1031, 289–290, 383–384` | These are visible on the first/last pages and signal an unrevised draft; editors treat ghost authors as an integrity issue | Remove/replace Fig. 4; clear pending blocks; reconcile byline/CRediT; fix G1 table; use 28.2–47.6%; say three | 2–3 days, editing |

## 3. Major findings (Q1 revision)

| ID | Area | Finding | Fix |
|---|---|---|---|
| M1 | Inference | Pooled McNemar \(b=190,c=50,p=2.1e-20\) treats 2,251 model-prefix pairs as independent; categorical LRT also assumes independent rows | Report per-model tests as primary; add cluster-robust/stratified McNemar and bootstrap LRT |
| M2 | Recovery reporting | “Half-lives 4.3–8.0 exceed horizon in every group” is false: 3.94 and 4.29 exist; Ministral s2 is below H=4 | Say 3.9–8.0; “most groups”; keep exploratory label |
| M3 | Field taxonomy | Table rows sum 1,984 vs “All s=2” 2,267; omitted other/temporal/count classes; “identifiers/money are the engines” is weaker | Add omitted rows; recompute spread over all classes or label “four largest” |
| M4 | Missingness | 5.47% cell loss; Qwen 4.9% V-unparsed/highest slope, Llama 2.3%/lowest; no missingness-by-outcome test | Add model×arm×parse table; bounding/multiple-imputation sensitivity; reconcile 205 hard errors / 250 refusals / 525 missing cells |
| M5 | Recovery comparisons | Log-rank treats paired/overlapping risk sets as independent; paired McNemar p-values exist but are omitted | Report paired McNemar/stratified log-rank; label marginal log-rank descriptive |
| M6 | Gate count | “Three” failures vs GATES.md’s G4 includes recovery rate + Weibull shape (2/3 rejected); “two” in Intro | Define the count explicitly; use one number everywhere; add gate-status table |
| M7 | Prereg drift | \(Y\) includes flags and adds \(Y^O\), while prereg defines signature-only \(Y\); H5 omitted; H3 downgraded without amendment | Add H1–H7 status table; report H5; amend outcome definition or report signature-only sensitivity |
| M8 | Parser gate provenance | Parser <1% is called preregistered but is absent from the frozen prereg G3 row; GATES summary omits it | Distinguish preregistered vs protocol criteria; add amendment or reword |
| M9 | Audit circularity | Coder fixed on the same 160 outcome items used to certify \(\kappa=.987\) and PPV=1.00; no fresh held-out audit | Hold out a fresh audit or report post-fix as in-sample; add pre/post-fix split |
| M10 | Sample reporting | Abstract “800 prefixes” hides effective 617 groups/423 prefixes; 47.8% never switch, 23.9% always switch | Foreground effective N; report marginal contrasts; define mover estimand |
| M11 | Planned vs executed | Planned 34,800 generations; executed 21,611 (13,200 base + 7,211 recovery + 1,200 jitter); recovery conditional on switching | Add executed-vs-planned table; explain at-risk design; report 8.9 GPU-h |
| M12 | Figure legibility | Effective type 4.6–7.7 pt in 9/10 figures; 600 DPI but canvases 15–18 in printed at 6.2 in | Regenerate at final physical width with ≥8 pt fonts; add effective-font check |
| M13 | Figure/text interval | Fig. 5 plots Wald intervals [0.76,0.99], text/table report bootstrap [0.770,0.998] | Plot the reported bootstrap interval or label Wald and report both |
| M14 | Float citations | Table 10 and Figs 5, 7, 8 are never cited; plate pages with no text | Add callouts; merge/drop redundant floats; move 6–8 tables to supplement |
| M15 | Heading structure | 40 bold run-in headings, 6 merge mid-sentence; Discussion buried in Results; 4.1 appears after unnumbered material | Keep ≤5 numbered subsections per section; demote run-ins; rename Section 5 “Results and Discussion” or add Discussion |
| M16 | Notation | Table 1 claims one meaning per symbol; 10 collisions (\(S,\alpha,\beta,\kappa,h,U,V,p,H,k\)); ~20 symbols undefined; 21/27 equation labels unreferenced | Rename collisions; add missing symbols; reference or inline unused displays |
| M17 | References | 36/56 arXiv-only, max 2024; missing 2025–26 work, model cards, prereg citation; inconsistent author truncation | Add verified 2025–26 work; update published versions; cite model revisions and prereg |
| M18 | Authorship / ethics | Byline 2 authors; CRediT credits S.A.S./M.M.A.; Ethics says annotation by “author team” though AI-agent | Reconcile byline/CRediT; correct ethics wording; get sign-off |
| M19 | AI-use disclosure | Does not name model/version/prompts/dates/interface or whether raters saw hypotheses | Name models, versions, dates, prompts; deposit packets/instructions |
| M20 | PII / legal | PII audit is AI mechanical pre-audit; release re-scan not done; model output licenses not verified; data card says “human labels” falsely | Complete human PII audit; verify licenses; correct data card; ethics determination |
| M21 | G0 provisional | 40-item human audit deferred; manifest records `audit_gate_pass: true` | Add provenance fields; state G0 provisional in abstract/limitations; complete human audit |
| M22 | Pre-fix number | \(\beta=0.684\) reported but artifact not retained; “caught defect before analysis” false | Retain/reconstruct artifact or remove number; say “before the reported estimate, after an earlier analysis” |

## 4. Minor / copy-edit (batch before submission)

- 617/2,297 = 26.9%, not 28.3%; 649/2,297 = 28.3% (varying strata).
- Second-rater subset is 100 items (40/40/20), not 120.
- “Seven items” list enumerates nine leaves.
- Table 19 “Recovered” is KM \(1-S(4)\), not `Events/n`.
- Table 19 mixes estimate and p-value in one column; define “Recovered.”
- Table 2 puts 87.39% in a “Count” column.
- Table 13 “V-unparsed” header lacks `%`.
- Table 16 lacks nominal/interval and step/endpoint legends.
- Table 10 lacks a CI column.
- 741–770 labeled rows vs 776–789 table coverage; state the V-unparsed filter.
- “25 vs 30” or “4,400 vs 4,000” inconsistencies in G0/Results.
- 6,000 vs 6,400? (verify each denominator before editing).
- `pre-registered` vs `preregistered`; `s0` vs `$s=0$`; `prefix-by-model` vs `prefix×model`.
- 40 run-in headings; 6 mid-sentence.
- Fig. 4 “ILLUSTRATIVE — NOT DATA” stamp.
- Fig. 9 truncated y-axis not disclosed.
- 31 duplicate hyperref destinations; no bookmarks; `hypertexnames=false` fixes.
- `\bibfont` 8.5 pt; stale preamble comments; unused packages.
- 7 keywords (some journals cap at 6); no Highlights.
- PDF metadata `subject="Complex STM Content"`.

## 5. What is strong (preserve)

1. **Fixed-prefix design and V exclusion** — clean within-prefix contrast; 100% s=0 value-set equality.
2. **Primary estimator** — exact conditional logit, cluster sandwich, 2,000-replicate bootstrap, Holm; reproduces `g3_analysis.json`.
3. **Failure reporting** — three (or four) failed criteria are stated, not hidden; pre/post-fix slopes both reported.
4. **Audit candor** — AI-only panel, same-family raters, 116/120 duplicate sessions, 14/80 recovery over-credits all disclosed in the body.
5. **Sensitivity breadth** — strict/lenient, placebo-excluded, domain/donor, task-clustered, reserve, seed-repeat all preserve the sign.
6. **Artifact** — 800 real τ-bench prefixes, five arms, 2,640 perturbations, manifest/hashes; a reusable stimulus set.

## 6. Priority plan

### P0 — before any submission (must fix)

1. **C1** claim boundary/title/abstract.
2. **C2–C4** recovery estimand, risk set, censoring; re-estimate and rewrite.
3. **C5** severity mismeasurement; add sensitivity/reclassification.
4. **C6** audit independence disclosure; human subset or rename “verification.”
5. **C7** G1/A-004 history; remove “no threshold changed.”
6. **C8** artifact/DOI/reproduction package; implement validation claim or remove it.
7. **C9** 2025–26 citations and narrowed novelty.
8. **C14** craft blockers (Fig. 4, pending blocks, CRediT, G1 table, recovery range, two vs three).
9. **M18–M21** authorship, ethics, AI-use, PII.

### P1 — high value, existing data

10. **C10** wrong-direction/task-success endpoint.
11. **C12** s1 negative control.
12. **C13** silent share lower bound / PPV CI.
13. **M1–M7** inference, gate count, prereg drift, audit circularity.
14. **M10–M17** effective N, planned/executed, figures, floats, headings, notation, refs.

### P2 — new evidence that would materially raise odds

15. 100–200 prefix task-success/utility endpoint.
16. Second deterministic renderer on 100–200 prefixes.
17. Human audit on 60–120 items.
18. Intervention probe (verification/consistency check) on 100–200 prefixes.
19. One exploratory frontier/API model or on-policy control.

## 7. Acceptance estimate

This is judgment, not a measured quantity. As-is, the paper is a **reject or major-revision** at a good Q1 venue. Fixing P0 and P1 can make it a **credible major-revision candidate**; P2 can make it **competitive**, but the scope limits (three 8–9B models, one renderer, two domains, no task-success endpoint, AI-only audit) mean it is unlikely to become a “likely accept” without at least one new evidence stream.

The biggest gains, in order:
1. Fixing the recovery estimand/risk set (removes a rejection-level statistical error).
2. Choosing the measurement identity and rewriting title/abstract (removes the claim contradiction).
3. Adding a task-success or wrong-direction endpoint (turns deviation into consequence).
4. Human audit or independent model family (validates the instrument).
5. 2025–26 citations and a comparison table (fixes the novelty gap).
6. Release/DOI/artifact package (makes the contribution checkable).

## 8. Evidence gaps / unverified

- Whether a human G0 audit would pass; the airline pool has only a two-prefix margin.
- Whether the final label-free audit is correct; a human subset is the only independent check.
- Whether the release candidate contains residual PII; the human PII audit is not done.
- Whether all three model licenses permit output redistribution.
- Whether the KM bias fully explains the 47.6% vs 34.7% gap; a censoring-pattern table would settle it.
- Whether the marginal contrast CIs are cluster-adjusted.
- Whether the 2025–26 nearest-neighbor papers are peer-reviewed; titles/abstracts verified on arXiv, publication status not.
