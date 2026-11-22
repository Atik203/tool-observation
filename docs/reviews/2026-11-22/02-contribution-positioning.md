# Reviewer 2 — Contribution, Novelty, and Q1 Positioning

**Manuscript:** `paper/toolresults.tex` (1,945 lines)
**Review date:** 2026-11-22
**Reviewer lens:** contribution, novelty, Q1 positioning. Read-only audit; no paper edits.
**Verdict:** **Major revision — not acceptable in current form for a top-quartile venue.** The study is publishable as a measurement/benchmark paper; it is not publishable as the "causal method" paper the title and section structure promise. Acceptance odds as-is: low. With the reframing and three targeted additions in §7: plausible.

---

## 0. One-paragraph diagnosis

The paper contains a real, reusable artifact and several publishable findings: a fixed-prefix five-arm stimulus design on 800 real τ-bench prefixes; a 20–46% format-sensitivity effect; a 21.3% silent-propagation share with a useful field-type gradient; and a persistence result (only 32–48% of affected, unflagged episodes return to the reference decision within four steps). Those are enough for a solid measurement paper.

The manuscript, however, is positioned as a "fixed-prefix causal study of detection, reliance, and recovery" and claims four contributions that the evidence does not support as stated. Detection is 0.1–1.9%; recovery fails its gate and is a composite of reversion and flagging; severity is a threshold, not a dose–response; and the paper simultaneously says "critical errors move the next decision" and "no content-sensitivity claim." The section headings ("Conventional Method," "Proposed Method") promise a baseline and an algorithm that do not exist. The related work stops in 2024 and omits the 2026 literature that directly studies quiet tool failures, recovery, and paired error injection. The dataset is not released, the human audit is deferred, the preregistration file is a draft, and the author list/CRediT block is inconsistent. A Q1 editor will see a paper that has not decided what it is.

The fix is not more caveats. It is to choose one contribution hierarchy, align title/abstract/intro/conclusion to it, cite the nearest neighbors, and add two or three pieces of evidence that turn "deviation from a donor continuation" into "error with consequences."

---

## 1. What the paper is — and what it should be

The manuscript tries to be three paper types at once:

| Type | What the manuscript offers | What a Q1 reviewer expects | Verdict |
|---|---|---|---|
| **Dataset paper** | ToolResult-800: 800 real τ-bench prefixes × 5 arms, perturbation records, renderer, hashes | Public release, datasheet, field documentation, splits, licensing, baseline results, intended-use statement | Not yet; release is pending (line 1913), no datasheet, name says 800 while manifest has 880 |
| **Measurement paper** | Fixed-prefix manipulation, conditional-logit slope, silent decomposition, recovery curve | A validated instrument, a clearly bounded estimand, a population-average or explicitly local claim, manipulation checks | The right identity, but the instrument is only AI-audited and the claim boundary is unstable |
| **Method paper** | "Proposed Method" is an experimental design; no algorithm, no learned component, no procedure that outperforms a baseline | A method, a baseline comparison, an ablation | No; there is no method contribution |

**Recommendation:** position it as a **measurement/benchmark paper with an artifact**, not a method paper and not yet a dataset paper. The contribution is the combination of (a) real τ-bench prefixes, (b) a deterministic graded content manipulation, (c) a pre-registered within-prefix estimator, (d) a silent/flagged/action decomposition, and (e) a four-step survival curve. Each ingredient exists elsewhere; the combination and the rigor are the contribution. That is defensible if stated as a combination, not as a vacuum.

The section structure actively works against this. "Conventional Method" (line 387) is related work, not a baseline; "Proposed Method" (line 464) is a study design, not an algorithm. A Q1 reviewer reads headings as a contract: the first promises a comparison that never happens, the second promises a method that does not exist. Rename them "Related Work" and "Study Design," move the end-to-end estimand to "Problem Formulation," and drop "proposed."

---

## 2. What is actually new — and what is not

I checked the nearest-neighbor literature on arXiv (2026-11-22). All works below were verified at the title/abstract level; publication status was not verified. The point is not that any one paper does exactly this study; the point is that the manuscript's sweeping gap claim is no longer tenable.

| Component | Manuscript claim | Nearest verified prior work | Novelty assessment | What the paper can defensibly claim |
|---|---|---|---|---|
| **ToolResult-800 stimulus set** | 800 real τ-bench prefixes × 5 arms, perturbation records, hashes (lines 364–366) | τ-bench (2406.12045); StableToolBench (2403.07714); ToolMaze (2606.05806); Fabrication After Tool Failure (2609.14758) | Moderate as an artifact; not a dataset contribution until released and documented | "A reusable fixed-prefix stimulus set," conditional on public release |
| **Fixed-prefix design** | Within-prefix content manipulation, V + s0–s3 (lines 487–520) | Measuring What Tool-Using LLM Agents Actually Do (2604.16706) uses paired wrong-argument injection; AgentAbstain (2607.10059) uses paired should-act/should-abstain tasks; Loud Failures, Quiet Failures (2610.10062) injects controlled faults | The paired-design idea is not new; the specific combination (real prefixes + graded content + silent decomposition) is | "A pre-registered, graded, within-prefix manipulation on real benchmark prefixes," not "the first controlled estimate" |
| **Silent-propagation decomposition** | Y^A/Y^F/Y^U/Y^O partition (lines 779–823) | Loud Failures distinguishes quiet vs loud failures; Fabrication finds 45.3% dishonesty when a tool returns status:ok with corrupted values; ToolScan (2411.13547) characterizes tool-use error patterns | The operationalization is new; the phenomenon is documented | "An operational decomposition and field-type map," not a discovery of silent failure |
| **Four-step recovery** | KM/RMST/Weibull over H=4 (lines 915–953) | ToolMaze measures a Perturbation Recovery Rate; Loud Failures measures recover/repeat; PALADIN (2509.25238) trains recovery | Survival framing is more rigorous than most; recovery itself is studied | "A survival-based persistence estimate," not "the first recovery study" |
| **Agent audit** | Label-free blind ratings plus an AI-agent panel (lines 666–698, 1541–1604) | LLM-as-a-judge literature (2306.05685); human annotation norms | Process novelty, but not independent validation | "A reproducible AI-agent consistency check," not "verification" |

**The honest novelty statement** is something like: "To our knowledge, no prior study combines a pre-registered graded content manipulation on real τ-bench prefixes with a silent-propagation decomposition and a survival-based recovery estimate. Prior work has studied tool failures, quiet corruption, and recovery separately, but not this combination under a fixed-prefix counterfactual." That is a claim a Q1 reviewer can evaluate. The current sentence — "There is no controlled estimate of how the content of a realistic tool observation changes the next decision..." (lines 360–362) — is false as written in November 2026 and will be treated as either uninformed or overstated.

---

## 3. Severity-ranked findings

Legend: **C** = critical, **H** = high, **M** = medium. "Confirmed" means the textual/numerical fact is verified in the manuscript or repo; "speculative" marks a judgment about reviewer reaction or an unverified consequence.

| ID | Sev | Location | Issue | Why it matters | Fix | Status |
|---|---|---|---|---|---|---|
| C1 | Critical | `toolresults.tex:360–362`, `404–440`; `ref.bib` | Claims "no controlled estimate" of graded within-prefix tool-observation effects; related work ends in 2024 and omits 2026 quiet-failure/recovery work | A Q1 reviewer will see the novelty claim as outdated; the paper's real delta is a combination, not a vacuum | Cite ToolMaze (2606.05806), Loud Failures (2610.10062), Fabrication (2609.14758), Robustness Analysis (2608.22676), Measuring What... (2604.16706), ToolScan (2411.13547), ToolSword (2402.10753), ToolBeHonest (2406.20015), Sclar et al. (2310.11324); narrow the gap; add a comparison table | Confirmed text; novelty judgment based on verified abstracts |
| C2 | Critical | Title 244; abstract 284–295; intro 364–372, 384; results 1395–1398; conclusion 1894–1896 | Simultaneously claims "Critical errors move the next decision" and "no content-sensitivity claim"; title says "Causal Study"; intro says two failed criteria, results say three; conclusion says audit caught a defect "before analysis" though it was after the main run and an initial analysis | The reader cannot tell what is claimed; the inconsistency looks like post-hoc hedging and undermines trust | One claim hierarchy; descriptive language for the gated estimate; fix the count; correct "before analysis"; align title/abstract/intro/conclusion | Confirmed |
| C3 | Critical | 779–823; 917–923; abstract 289–290; scope 1864–1866 | "Switch" is deviation from donor V, not error; "recovery" is reversion to V, not task correctness; no task-success endpoint | A reviewer cannot conclude that silent propagation harms outcomes; a switch could be correct skepticism; the practical implications assume harm that is not shown | Add a task-success/utility endpoint on a 100–200 prefix subsample; classify switch direction against the perturbation's expected action change; rename "correct decision" to "reference decision" | Confirmed omission; impact interpretive |
| C4 | Critical | 666–698; 1541–1604; 1917–1935 | Audits are AI-agent sessions sharing one model family; the "verification panel" reproduces automatic endpoint/step on 80/80; two severity sessions are identical on 116/120 | The measurement paper's central validation is not independent; "blind" is not human; a Q1 reviewer will discount the audit and the silent share | Human audit on 60–120 items; an independent model family; report human–agent agreement; rename "verification panel" to "consistency check"; report flag-detector recall | Confirmed |
| C5 | Critical | 364–366; 1837–1841; 1907–1913 | ToolResult-800 is unreleased (DOI pending), has no datasheet/field documentation, and is named 800 while the manifest has 880 | A Q1 reviewer will not credit an unreleased dataset; the dataset is the fallback contribution if the causal claim fails | Release before submission with DOI, datasheet, fields, splits, licensing, and a baseline; or demote it to "stimulus set" and drop the dataset contribution | Confirmed |
| C6 | Critical | 1370–1385; 1465–1479; Table 6 1497–1513 | The slope uses 617 strata, 423 unique prefixes, 2,458 rows; 47.8% never switch, 23.9% always switch; the estimate is a mover effect, not an 800-prefix average | The abstract's "800 prefixes" overstates the effective sample and precision; a reviewer will ask for the effective N and the population-average contrast | Foreground 423 prefixes/617 strata; put marginal contrasts (+10.2/+16.3/+6.2 points) in the abstract; define the estimand as a within-stratum mover effect; make task-clustered inference primary or justify prefix clustering | Confirmed |
| C7 | Critical | 987; 1322–1325; abstract 290; 519; 1864 | Re-serializing the same observation moves 20–46% of decisions, larger than the content effect; only one renderer; V is excluded from the slope | The "content" effect is entangled with format; a reviewer will say the manipulation is a format effect; the paper treats its largest effect as a nuisance | Make format sensitivity a headline; add a second deterministic renderer on 100–200 prefixes; report prompt length/position by arm; justify V exclusion with a sensitivity analysis | Confirmed numbers; interpretive |
| C8 | Critical | Table 3 1416; 1444; 1574–1586; 1642–1653 | s1 negative-control OR is 1.27 [1.04,1.55], not null; s2/s3 audit is 88.3% (s2 83.3%); field-class spread is 21.1 points vs criticality 10.1; "field type is at least as informative as the critical/non-critical label" | The severity ladder is confounded with field class and the negative control is not clean; the "threshold at s2" may be a field-composition effect | Field-class-by-tier table; within-field-class severity slope; refit with audit labels; errors-in-variables sensitivity; report s1 OR honestly as a failed negative control; consider defining severity by field class | Confirmed |
| C9 | Critical | 917–923; 1681–1698; Table 8 1702–1720; abstract 289–290 | Recovery risk set = switchers who did not flag; endpoint combines R1 reversion and R2 flag; V is a donor reference, not ground truth; abstract says "corrupted episodes" | The estimate is a selected principal-stratum quantity, not a population recovery rate; detection is not recovery; a reviewer will challenge the generalization | Define the risk set explicitly; split R1/R2 in the main table and abstract; report R1-first sensitivity; reword "corrupted episodes" to "affected, unflagged episodes" | Confirmed |
| H1 | High | 387; 464 | "Conventional Method" is related work; "Proposed Method" is an experimental design, not an algorithm; no baseline is run | Section headings are a contract; a reviewer expects a baseline/method and finds neither, making the paper look confused about its contribution | Rename "Related Work" and "Study Design"; move the e2e estimand to "Problem Formulation"; drop "proposed"; add a design flow figure | Confirmed |
| H2 | High | 244 | Title promises "Causal Study of Detection, Reliance, and Recovery"; detection is 0.1–1.9%, recovery fails, severity is a threshold, reliance is inferred | Title/abstract misalignment is the first thing an editor sees; it overpromises and invites rejection | Retitle around measurement + format sensitivity + silent propagation + persistence; keep "causal" only with a formal estimand/DAG | Confirmed judgment |
| H3 | High | 1820–1831 | Recommends verification, second tool call, confidence flags, human approval; none tested; "if the slope is flat, checks may be less urgent" is unsupported | A Q1 reviewer will call these speculations; the paper's own evidence shows detection is rare | Add a small intervention probe (verification instruction or consistency check) on 100–200 prefixes; otherwise frame as hypotheses and remove the flat-slope recommendation | Confirmed omission |
| H4 | High | 1395–1398; 1569; Table 10 1552–1572 | Parser failure 1.55% vs 1% gate; 3.45% including refusals; no complete-case/worst-case sensitivity analysis | The gate failure may or may not invalidate the slope; without a sensitivity analysis the reader cannot tell; the headline 1.55% understates total invalid output | Report parser failure by arm/model/failure type; complete-case and worst-case slope; if stable, argue the gate failure is a technicality; if not, drop the positive claim | Confirmed numbers; impact speculative |
| H5 | High | 1041–1066; 1311–1315; 1917–1919; `prereg/PREREGISTRATION.md:3–6,196–205` | Prereg file is DRAFT with TBD sign-off; G0 human audit deferred (D-021); G1 negative-control criterion amended (A-004) after V-vs-s0 format jitter 20.3–45.6%; ethics pending | The "pre-registered" claim is weakened; a Q1 editor will ask for the frozen, timestamped protocol and the human audit; the G1 amendment looks like moving the goalposts if timing is undocumented | Freeze/sign/timestamp the prereg; complete the human G0 audit; report A-004 timing and blindness; resolve ethics; put the amendment log in the supplement | Confirmed from files; frozen tag may exist but is not verifiable from the manuscript |
| H6 | High | 254–270; 1894–1896; 1920–1925 | Byline has two authors; CRediT lists S.A.S. and M.M.A. who are not in the byline; conclusion says the audit caught a defect "before analysis," but it was after the main run and an initial analysis (pre-fix β=0.684) | Authorship/CRediT inconsistency is an integrity flag; "before analysis" is a factual error | Reconcile authorship and CRediT; add missing authors or remove their roles; correct the timeline | Confirmed |
| H7 | High | 384 vs 291; 1380–1385 vs 1469–1470; 1465–1479 vs Table 9; 1786–1798; 1840–1841 | "Two" vs "three" failed criteria; 617/2,297 = 26.9%, not 28.3% (28.3% matches 649); 5.47% cell loss vs 97–98.6% table coverage; conditional interpretation and "null-result asset" are proposal leftovers | Arithmetic and leftover text make the paper look unrevised; reviewers lose trust | Reconcile denominators; add a missingness flow; rewrite conditional passages in past tense; delete "null-result asset" or condition it | Confirmed |
| H8 | High | 949–952; 1207–1211; 1688–1691; 1828–1831 | Persistent arm was supposed to re-inject on 25% of prefixes; in execution prompts are 97–100% identical to transient; the contrast is uninformative | A designed contribution failed in execution; repeating it in methods/results/limitations looks like incomplete work | Drop the persistent arm from the contribution list; report the implementation failure once in limitations; or fix/re-run a small persistent subset with state-aware injection | Confirmed |
| H9 | High | 1855–1880 | No frontier/API model, no on-policy control, no live APIs, one renderer, no human baseline; the paper acknowledges these but still makes practical claims | External validity is limited to three 8–9B families on τ-bench; a Q1 reviewer will ask for at least one contrast | Add one exploratory frontier model (if budget allows) or a 100-prefix on-policy control; otherwise tighten every claim to "three open-weight 8–9B families under one renderer" | Confirmed scope; reviewer demand speculative |
| M1 | Medium | 15–16; 1007–1257 | 15 tables/8 figures; results start at line 1,257 of 1,945 (~65%); much of the paper is protocol/reproducibility | A Q1 reviewer may lose the contribution in the protocol; the paper reads as a lab notebook | Move design tables to appendix; keep 6–8 result tables; start results by Section 4; shorten "Experiment" to the essentials | Confirmed |
| M2 | Medium | 512–520; 1786–1811 | "Causal" is informal; no DAG/potential-outcomes formalization; treatment is a bundle (value change + length + salience + contradiction); no length/position control | A causal-inference reviewer will ask what the treatment is and whether the exclusion restriction holds | Add a DAG and define the treatment as the rendered observation; report prompt length by arm; add a length-matched control; drop "causal" if not formalized | Confirmed |
| M3 | Medium | 981–996; 1441–1442 | "Realized power at the observed effect is 1.0" is post-hoc observed power, not design power; the design assumed 4% placebo but observed 30.1% | Observed power is uninformative and can mislead; the design power calculation is invalidated by the placebo miss | Report CI/precision and the realized MDE only; remove observed power; explain the placebo miss | Confirmed |
| M4 | Medium | 604–606; 1749–1755 | Cap-10 sampling; airline 400 of 442 (near census), retail 400 of 1,144; primary clusters by prefix, task-clustered only as sensitivity | Up to 10 prefixes per task induce dependence; prefix clustering may be anti-conservative; airline generalizability is limited | Make task-clustered inference primary or two-way; report design effect; discuss airline near-census | Confirmed |
| M5 | Medium | 1623–1653 | Silent share 21.3% has a 34.4% "other" residual; silent share is a lower bound; field taxonomy is exploratory but the abstract presents it as a finding | The decomposition is not exhaustive; the headline may understate silent propagation; the abstract overclaims the field gradient | Subdivide Y^O or label silent share as a lower bound; mark field taxonomy exploratory in the abstract; report CIs | Confirmed |
| M6 | Medium | 917–923; 1632; 1693–1695 | Recovery combines R1 reversion and R2 flag; detection at injection is 0.1–1.9%, but 85/141 Ministral recoveries are flags; this needs reconciliation | Detection is not recovery; the composite endpoint inflates recovery and confuses the narrative | Split R1/R2 in Table 8 and the abstract; explain when flags occur; report R1-only recovery | Confirmed |
| M7 | Medium | 277–296; 364–366 | Abstract says "agent verification panel" (ambiguous); "ToolResult-800" vs 880 prefixes; "five arms" vs "four prose arms" | Small ambiguities compound; a reviewer may misread the audit as human or the dataset as 800 only | Say "AI-agent consistency panel"; clarify 800 primary + 80 reserve; use "five arms (V + four prose)" consistently | Confirmed |

---

## 4. Expanded critical findings

### C1. The novelty claim is outdated and the related work is two years stale

The manuscript's gap sentence is the single most dangerous sentence in the paper:

> "There is no controlled estimate of how the content of a realistic tool observation changes the next decision, whether that change is ordered by the severity of the content error, and how quickly the agent returns to the verbatim-observation decision." (lines 360–362)

As of November 2026, this is not true in the broad sense. Verified nearest neighbors include:

- **ToolMaze / "When Tools Fail" (arXiv:2606.05806)** benchmarks dynamic replanning and anomaly recovery with a 2×2 taxonomy of tool perturbations (explicit/implicit, transient/permanent) and a Perturbation Recovery Rate. It finds the sharpest drops under implicit semantic failures and "systemic over-trust in corrupted outputs." That is the paper's phenomenon, measured.
- **"Loud Failures, Quiet Failures" (arXiv:2610.10062)** injects four typed faults at a controlled point in multi-turn agents, records whether the agent notices, changes plan, recovers, or repeats, and finds 58.8% notice a plausible wrong value vs 91.3% for an explicit error, against a 26.8% baseline of reporting problems when nothing is wrong. It also finds a prompt line asking the agent to check each result did not move detection. This is the closest work to the paper's core claim; it must be cited and differentiated.
- **"Fabrication After Tool Failure" (arXiv:2609.14758)** finds 45.3% dishonesty when a tool returns `status:ok` with corrupted, stale, or truncated values, vs 0.0% when it returns `status:error`; a one-sentence `retrieval_status` requirement reduces dishonesty to 0.87%. This directly supports the paper's silent-propagation finding and offers an intervention the paper could test.
- **"Robustness Analysis of Agentic AI to Inconsistent and Incomplete Tool Responses" (arXiv:2608.22676)** injects incomplete and inconsistent returns into a retail customer-service benchmark and measures how strongly a failure changes the next decision via action distributions. That is the paper's next-decision estimand in a different stimulus set.
- **"Measuring What Tool-Using LLM Agents Actually Do" (arXiv:2604.16706)** uses a paired design with one schema-valid wrong argument injected into the first tool call, across 7 models, and reports a +22.0 percentage-point error-rate increase. It is a paired causal error-propagation study, even though the treatment is a tool argument rather than observation content.
- **ToolScan (arXiv:2411.13547)**, **ToolSword (arXiv:2402.10753)**, and **ToolBeHonest (arXiv:2406.20015)** cover tool-use error patterns, noisy misdirection/error conflicts, and tool hallucination respectively.
- **Sclar et al. (arXiv:2310.11324)** is the canonical prompt-formatting-sensitivity result (up to 76 accuracy points), which is exactly the phenomenon behind the paper's 20–46% V-vs-s0 effect. Not citing it is a glaring gap.

None of these is the same study. The paper's defensible delta is the combination of real τ-bench prefixes, a graded content-only manipulation, a pre-registered within-prefix estimator, a silent/flagged/action decomposition, and a four-step survival curve. But a Q1 reviewer will not accept a vacuum claim that ignores the closest work. The fix is cheap: cite, differentiate, and add a comparison table. This alone can move the paper from "reject" to "major revision."

### C2. The claim boundary is internally contradictory

The abstract says both:

> "Critical errors move the next decision: tier odds ratios against the placebo are 1.27 ..., 4.60 ..., and 11.21 ..." (line 284)

and

> "The paper therefore reports a measurement estimate, not a confirmed content-sensitivity claim." (line 293)

The title says "A Fixed-Prefix Causal Study of Detection, Reliance, and Recovery." The introduction says "Two preregistered criteria failed" (line 384) while the abstract and results say three (parser, severity, recovery). The conclusion says the audit procedure "caught a labeling defect before analysis" (lines 1894–1895), but the audit was after the main run and after an initial pre-fix analysis that gave β=0.684 (lines 1390–1392). The paper's own statistical section says β is "not a clean per-level causal parameter" (lines 1804–1806), yet the title says "Causal Study."

A reviewer will ask: which is it? If the estimate is not a confirmed content-sensitivity claim, the abstract should not use causal verbs ("move") or report tier ORs as findings without a descriptive label. If it is a claim, the paper must defend the parser failure as a technicality with a sensitivity analysis. The current half-in/half-out is the worst of both worlds: it invites the causal criticism while disclaiming the causal conclusion.

There are two viable paths:

- **Path A (conservative, safer):** a descriptive measurement paper. Replace "move" with "differ under"; label ORs as descriptive; retitle without "causal"; define the estimand precisely as "the within-prefix conditional log-odds of a decision-signature change per assigned severity level, among prefixes with within-prefix variation." Report the three gate failures as measurement limitations, not as a failed hypothesis.
- **Path B (stronger, riskier):** a bounded content-sensitivity claim. Add a complete-case/worst-case parser and refusal sensitivity analysis; show the slope is stable; argue that 1.55% (or 3.45% including refusals) is a data-quality limitation, not a threat to the sign; make a bounded claim for three 8–9B models on τ-bench under one renderer. If the sensitivity analysis supports it, this is the stronger paper. If not, Path A.

Either way, the title, abstract, intro, results, and conclusion must use the same claim. The current contribution list also changes between sections: the intro lists dataset, design, decomposition, recovery (lines 364–372); the conclusion lists dataset, design, audit procedure, bounded estimate (lines 1894–1896). That instability is a positioning failure, not just a wording issue.

### C3. There is no task-success or correctness endpoint

The outcome is a decision-signature difference from the donor's verbatim continuation V. V is a donor decision, not ground truth. The paper calls R1 "correct decision" (line 921), but a model that notices a wrong refund amount and refuses to quote it is "switching" from V and may be behaving correctly. Conversely, a model that silently repeats a wrong value may still reach a goal-consistent final state, which is exactly the failure the paper wants to expose. Without a task-success or utility endpoint, the paper measures **deviation**, not **error**.

This is the most important missing baseline. A Q1 reviewer will accept a next-decision study only if the paper shows that the deviations are consequential. The perturbation records already store an "expected action change" (lines 650–651), but the analysis does not use it to classify whether a switch is in the expected direction. That is a cheap partial fix: report the share of switches that are "wrong-direction" relative to the expected action change, and the share that are "correct skepticism."

The stronger fix is a 100–200 prefix subsample that continues the episode to termination against the τ-bench environment and scores task success under s0 vs s2/s3. If task success is too expensive, a smaller "utility probe" (e.g., does the final state contain the injected false value? does the action violate policy?) would still convert deviation into harm. This is the single most valuable addition for a Q1 reviewer, and it is feasible with the existing harness.

### C4. The audit is a consistency check, not independent validation

The paper is commendably honest about this:

> "Its ratings are agent-produced and share one model family, so they establish reproducibility rather than human independence." (lines 688–690)

> "Agreement statistics measure consistency among sessions, not correctness: the recovery panel found 14/80 rater over-credits while reproducing the automatic coding on 80/80 sequences, and two severity sessions were identical on 116/120 items." (lines 1871–1873)

But the abstract says "Audits were blind-rated label-free and checked by an agent verification panel" (lines 294–295), which a reader may mistake for human verification. The panel's 80/80 reproduction of the automatic endpoint is not independent evidence; it is evidence that the panel and the coder agree, possibly because they share a model family or because the coding is mechanical. The severity panel's independent passes are *lower* than the primary (81.7% and 73.3% vs 88.3%), which actually strengthens the failure, not the validation.

For a measurement paper, the instrument is the contribution. An AI-only audit is a consistency check; it cannot establish that the labels are correct. A Q1 reviewer will discount the silent-propagation share, the severity ladder, and the recovery endpoint accordingly. The fix is a human audit on 60–120 stratified items (severity, outcome, recovery) with a written rubric and two independent raters; report human–human and human–agent agreement. If human annotation is impossible, use a different model family and call it a "consistency check," not "verification," and report flag-detector recall and parser error rates. Do not use the word "verification" for a same-family panel.

### C5. The dataset is not yet a contribution

ToolResult-800 is described as a contribution (lines 364–366) and as a reusable test bed (lines 1837–1841), but the release is pending (line 1913), there is no datasheet, and the name says 800 while the manifest has 880 (800 primary + 80 reserve). A Q1 reviewer will not credit an unavailable artifact. The release is also gated on a passed audit, which is provisional (D-021).

The dataset is the paper's fallback if the causal claim fails. It is worth doing properly: a public release with DOI, a datasheet (fields, splits, licensing, PII handling, intended use), a short "Dataset" section, and a baseline table (the three models' switch rates by arm). A dataset paper also needs a benchmark protocol and baselines; this paper has neither. If the release cannot happen before submission, demote the dataset to "stimulus set" and remove it from the contribution list; do not claim a dataset contribution you cannot deliver.

### C6. The effective sample is much smaller than the headline

The abstract says "800 real τ-bench prefixes." The estimate uses 617 strata, 423 unique prefixes, and 2,458 rows (lines 1380–1385). Of the 2,297 prefix×model strata, 47.8% never switch, 23.9% switch in every arm, 19.0% are dose-responsive, and 9.3% are placebo switchers (Table 6). The conditional logit drops 1,680 concordant strata; the slope is identified from the movers. This is disclosed in the results, but not in the abstract or intro. A Q1 reviewer will say the effective sample is ~423 prefixes, not 800, and the estimate is a within-stratum mover effect, not a population-average effect. Both are legitimate, but the paper must say so up front.

There is also an arithmetic inconsistency: the text says "617 strata that vary across arms (28.3% of the 2,297 strata)" (lines 1469–1470). 617/2,297 = 26.9%, not 28.3%. The 28.3% matches 649, which is the sum of dose-responsive (436) and placebo switchers (213) in Table 6. The 617 and the 28.3% cannot both describe the same set; either 32 strata are dropped (e.g., missing V references) or one number is wrong. Reconcile the denominator and add a missingness flow.

The marginal paired contrasts (+10.2, +16.3, +6.2 points) are the population-average answer and should appear in the abstract alongside the ORs. The paper already reports them (lines 1471–1472), but the abstract only reports ORs, which overstates the average effect.

### C7. Format is a first-order effect, but the paper treats it as a nuisance

The V-vs-s0 format effect is 20.3% (Qwen), 36.7% (Ministral), 45.6% (Llama) (Table 5, lines 1336–1338). The s2-vs-s0 marginal contrast is +10.2 points and s3-vs-s0 is +16.3 points. In two of three models, re-serializing the same observation moves more decisions than injecting a critical error. That is a major finding, and the abstract does mention it ("Re-serializing the same observation already moves 20–46% of decisions," line 290). But the paper then excludes V from the slope and interprets only s0–s3, which is defensible for a format-controlled contrast but means the "content sensitivity" is conditional on one prose template.

A Q1 reviewer will ask: is the treatment content or format? The paper's answer is "both, but the slope is within format." That is not enough without a second renderer. A second deterministic renderer (e.g., table vs bullet vs key–value) on 100–200 prefixes would test whether the slope is template-specific. If the slope is stable, the content claim is stronger. If it is not, the paper becomes a format-sensitivity paper, which is still publishable and arguably more novel. Either way, report prompt length and field position by arm; a longer/shorter rendered value could change attention independently of content.

### C8. The severity ladder is confounded and the negative control is not null

Three facts, taken together, are a serious construct-validity problem:

1. The s1 negative-control OR is 1.27 [1.04, 1.55] (Table 3, line 1416). The paper calls it "near one" (line 1444), but a 27% odds increase with a CI excluding 1 is not a clean negative control.
2. The severity audit fails at 88.3% (53/60), with s2 at 83.3% (25/30) and s3 at 93.3% (28/30) (lines 1564, 1574–1575). The panel's independent passes are lower: 81.7% and 73.3% (lines 1594–1595).
3. The field-type breakdown shows identifiers and money have 45.0% and 45.6% silent shares, while entity and status have 6.9% and 6.6% (Table 7). The field-class spread in switch rates is 21.1 points, while the criticality contrast adds 10.1 points over a 30.1% render floor; the paper itself concludes "field type is therefore at least as informative as the critical/non-critical label" (lines 1650–1653).

If the severity tiers are confounded with field class — e.g., s2 perturbations are disproportionately identifiers/money and s3 disproportionately status/entity — then the "threshold at s2" may be a field-composition effect, not a severity effect. The paper does not report the field-class composition by tier, so the reader cannot check. This is a fixable but essential analysis: a field-class-by-tier table, a within-field-class severity slope, and a refit using the audit labels (reassign the 7 misses) with an errors-in-variables sensitivity. The paper's directional argument that correcting the misclassification would steepen the s1–s2 contrast (lines 1583–1586) is plausible but not a substitute for the calculation.

The paper's own power section says "Construct validity is [the binding constraint]" (line 991). The severity audit and the field-class confound are exactly that constraint. A Q1 reviewer will use the paper's own sentence against it.

### C9. Recovery is a selected, composite estimand

The recovery risk set is prefixes whose decision moved at the injection step (`Y^U=1` or `Y^A=1`) and did not flag there (lines 917–919). That is a post-treatment selected group. The estimate is a principal-stratum/affected-subgroup quantity, not a population recovery rate. The endpoint combines R1 (signature reversion to V) and R2 (explicit flag) (lines 920–923); for Ministral, 85 of 141 recoveries are flags, not reversion (lines 1693–1695). Detection is therefore counted as recovery, which inflates the recovery rate and confuses the narrative. V is the donor continuation, not ground truth; calling R1 "correct decision" (line 921) overclaims.

The abstract says "Fewer than half of corrupted episodes recover within four steps" (lines 289–290). The denominator is affected, unflagged episodes, not all corrupted episodes. That is a generalization the design does not support. The 50% G4 gate is also arbitrary; the scientific finding is persistence ("one verification step is not enough"), not "the study failed." The paper should reframe recovery as the finding, not the failure: among episodes whose decision moved without a flag, only 32–48% return to the reference decision within four steps; the half-lives exceed the horizon; the Weibull shape rejects the exponential in 2 of 3 groups. That is a strong negative result about self-correction.

---

## 5. Top-10 priority list

1. **Choose the paper type.** Measurement/benchmark paper with an artifact; not a method paper, not yet a dataset paper. Rewrite the title and section structure accordingly.
2. **Fix the claim hierarchy.** One claim, one estimand, one set of verbs. Align title (244), abstract (284–295), intro (364–384), results (1395–1398), and conclusion (1894–1896). Fix "two vs three" and "before analysis."
3. **Cite and differentiate the 2026 literature.** Add a nearest-neighbor table; narrow the gap to the combination; stop claiming a vacuum. This is the cheapest high-impact fix.
4. **Add a task-success/utility endpoint** on a 100–200 prefix subsample, or at minimum a wrong-direction analysis using the perturbation records. Turn deviation into error.
5. **Add an independent human audit** on 60–120 items, or stop calling the AI-agent panel "verification." Report human–agent agreement and flag-detector recall.
6. **Make format sensitivity a headline** and add a second renderer on a subsample. The 20–46% format effect is larger than the content effect; it is the paper's most robust finding.
7. **Resolve the severity confound.** Field-class-by-tier table, within-field-class severity slope, audit-label refit, errors-in-variables sensitivity. Report the s1 OR 1.27 honestly as a failed negative control.
8. **Reframe recovery.** Selected risk set, R1/R2 split, V as reference, persistence as the finding. Reword "corrupted episodes."
9. **Fix preregistration and integrity.** Freeze/sign/timestamp the prereg; complete the G0 human audit; document A-004 timing/blindness; resolve ethics; reconcile authorship/CRediT; correct arithmetic and proposal leftovers.
10. **Release the dataset or demote it.** DOI, datasheet, fields, splits, licensing, baseline; otherwise remove it from the contribution list.

---

## 6. Strongest contribution claims (what to lead with)

1. **The fixed-prefix, five-arm stimulus design on real τ-bench prefixes is a genuine methodological contribution.** Holding a real prefix fixed and varying only the rendered observation, with a deterministic renderer and perturbation records, is reusable and auditable. This is stronger than the dataset claim because it does not depend on a release. Caveat: it is a design, not an algorithm; call it that.

2. **Format sensitivity is the most robust and surprising result.** Re-serializing the same observation moves 20–46% of decisions, more than the critical-error effect in two of three models. This is a first-order measurement result that any tool-use benchmark must confront. It is currently a nuisance variable; it should be a headline. It also explains why end-to-end scores cannot attribute effects to content.

3. **The silent-propagation map is useful and actionable.** 21.3% of critical-arm switches repeat the injected value without a flag; identifiers and money carry ~45% silent shares, status/entity ~7%. Even as a descriptive result, this tells builders where to put checks. Caveats: the 34.4% "other" category means the silent share is a lower bound; the field taxonomy is exploratory; the flag detector is not fully validated.

4. **Persistence is a strong negative result about self-correction.** Only 32–48% of affected, unflagged episodes return to the reference decision within four steps; half-lives exceed the horizon; the Weibull shape rejects the exponential in 2 of 3 groups. Framed as "one verification step is not enough," this is more interesting than the failed G4 gate. Caveat: the risk set is selected and the endpoint is composite; split R1/R2.

5. **The pre-registration and gate discipline is a credibility asset.** Reporting three failed criteria, a coder defect, and a label-free audit is rare and valuable. It is a process contribution, not a scientific one, and it needs human-independent validation to carry weight. Do not oversell it as "verification."

6. **The dataset is a promising artifact, but not yet a contribution.** It needs a release, a datasheet, and a baseline. If delivered, it is the paper's most durable asset; if not, do not claim it.

**What is not a contribution as stated:** a "dose–response law" (linearity is rejected; it is a threshold), "detection" as a major finding (0.1–1.9%), "recovery" as a success (the gate fails; the endpoint is composite), "agent audit" as independent validation (same family), and "causal" as a broad claim (the treatment is a bundle; the paper itself says β is not a clean causal parameter).

---

## 7. Five concrete revision moves that would most improve acceptance odds

### Move 1 — Rewrite the paper around its strongest evidence, not its failed hypothesis

Retitle to something like: *"Tool-Result Errors in Language-Model Agents: A Pre-Registered Fixed-Prefix Study of Format Sensitivity, Silent Propagation, and Persistence."* Drop "causal study of detection, reliance, and recovery." Rewrite the abstract in this order: (1) the fixed-prefix design and sample; (2) format sensitivity (20–46%); (3) the critical-error effect (tier ORs and marginal contrasts, with the effective N and the threshold caveat); (4) silent propagation (21.3%; identifiers/money 45%); (5) persistence (32–48% return within four steps); (6) the three gate failures and what they do and do not license. This hierarchy matches the evidence and gives the reviewer a clear takeaway. It also resolves the "critical errors move" vs "no content-sensitivity claim" contradiction: the format and silent/persistence results are descriptive and robust; the severity estimate is a bounded, gated measurement.

### Move 2 — Add a task-success/utility endpoint on a 100–200 prefix subsample

Continue the episode to termination against the τ-bench environment for a stratified subsample of prefixes under s0 and s2/s3. Score task success with the benchmark's own goal-state check. Classify each switch as harmful (task fails, wrong action, policy violation), benign (task succeeds despite deviation), or corrective (the switch avoids the injected error). Report the harm rate by arm and model. This is the single addition that would most change a Q1 reviewer's assessment, because it converts "deviation from a donor continuation" into "error with consequences." If a full rollout is too expensive, use the perturbation records' expected action change to classify wrong-direction switches, and report the share; that is a cheaper partial substitute, not a full one.

### Move 3 — Add two robustness experiments: a second renderer and a small intervention probe

A second deterministic renderer (e.g., a table or a different key–value order) on 100–200 prefixes tests whether the slope is template-specific. Report the slope under both renderers and the format effect for each. If the slope is stable, the content claim is much stronger; if not, the paper becomes a format-sensitivity paper, which is still publishable. In parallel, run a small intervention probe on 100–200 prefixes: add a prompt instruction to verify values before acting, or a consistency check between the observation and the policy. The literature suggests a generic "check each result" prompt may not help (Loud Failures), while naming a failure state can (Fabrication). Either result is informative and turns the engineering implications from speculation into evidence.

### Move 4 — Replace the AI-only audit with a human audit, and freeze the preregistration

Recruit two human raters for a stratified 60–120 item sample covering severity, outcome, and recovery; use a written rubric; report human–human and human–agent agreement. If human annotation is impossible within the project's constraints, use a different model family and call the result a "consistency check," not "verification"; report flag-detector recall and parser error rates. At the same time, freeze, sign, and timestamp the preregistration; complete the deferred G0 human audit; document the A-004 amendment's timing and whether it was blind to target outcomes; resolve the ethics determination; reconcile the byline and CRediT block. These are not scientific additions, but they are acceptance blockers at a Q1 venue.

### Move 5 — Restructure the paper and release the artifact

Rename "Conventional Method" to "Related Work" and "Proposed Method" to "Study Design"; move the end-to-end estimand to "Problem Formulation"; drop "proposed." Move protocol tables (notation, arms, models, fit, envelope, gates) to an appendix; keep 6–8 result tables; start the results by Section 4. Add a nearest-neighbor comparison table that positions the paper against ToolMaze, Loud Failures, Fabrication, Robustness Analysis, Measuring What..., ToolScan, ToolSword, ToolBeHonest, and Sclar et al. Release the dataset with a DOI, datasheet, fields, splits, licensing, and a baseline table, or demote it. A Q1 reviewer should be able to read the first three pages and know the contribution, the estimand, the strongest result, and the claim boundary.

---

## 8. What a Q1 reviewer would demand vs what is out of scope

### Must-fix with existing data (no new GPU runs required)

| Demand | Why | Feasible? |
|---|---|---|
| One claim hierarchy; title/abstract/intro/conclusion aligned | The current text contradicts itself | Yes, writing only |
| Cite and differentiate 2025–26 nearest neighbors; add comparison table | The novelty claim is outdated | Yes, writing only |
| Report effective N (423 prefixes/617 strata), marginal contrasts, task-clustered CI | The headline overstates precision | Yes, reanalysis |
| Split R1/R2 recovery; define the selected risk set; reword "corrupted episodes" | The recovery claim overgeneralizes | Yes, reanalysis/writing |
| Field-class-by-tier table; within-field-class severity slope; audit-label refit | The severity ladder is confounded | Yes, reanalysis |
| Parser/refusal complete-case and worst-case sensitivity | The gate failure's impact is unknown | Yes, reanalysis |
| Release dataset/DOI or demote the dataset claim | Unreleased artifacts are not contributions | Depends on release process |
| Freeze/sign/timestamp prereg; complete G0 human audit; resolve ethics/authorship | Integrity/acceptance blockers | Yes, process |
| Remove proposal leftovers ("if the slope is positive," "null-result asset") | The paper looks unrevised | Yes, writing only |

### New evidence that would materially raise acceptance odds (modest compute)

| Addition | What it buys | Suggested scope |
|---|---|---|
| Task-success/utility endpoint | Converts deviation into harm; answers the biggest reviewer objection | 100–200 prefixes, s0 vs s2/s3 |
| Second deterministic renderer | Tests whether the slope is template-specific; strengthens or reframes the content claim | 100–200 prefixes |
| Human audit | Independent validation of the instrument | 60–120 stratified items |
| Intervention probe (verification/consistency check) | Tests the practical implication; engages the 2026 literature | 100–200 prefixes |
| One exploratory frontier/API model | Tests generality beyond 8–9B open-weight models | 100–200 prefixes, if budget allows |
| On-policy prefix control | Tests whether off-policy donor histories drive the effect | 100 prefixes, target model generates history |

### Out of scope — argue explicitly, do not hide

- **Full 800-prefix task-success rollout.** A 100–200 prefix subsample is enough to establish consequence; a full rollout is expensive and not necessary for the measurement claim.
- **Frontier/API model sweep.** The project's budget is $0 cash and no paid API; one exploratory model is a compromise, not a requirement.
- **Live APIs / web browsing / non-deterministic tools.** The deterministic benchmark is the point: it makes the counterfactual clean. Say so.
- **Model ranking.** The design is not powered for ranking; the paper already says this (lines 1756–1757).
- **Universal law / transfer to all agents.** The claim is local to three 8–9B families, two domains, one renderer.
- **Multi-agent interaction, training, fine-tuning, policy improvement.** Out of scope per the preregistration and roadmap.
- **Human annotation of all 13,200 outputs.** A stratified subsample is sufficient for validation; full annotation is not.

### What would still be a reject even after revision

- Insisting on both "causal dose–response" and "no content-sensitivity claim."
- Keeping the dataset unreleased while claiming it as a contribution.
- Calling an AI-only, same-family panel "verification" without human agreement.
- Keeping the engineering recommendations without any intervention evidence.
- Keeping the 2024-only related work and the "no controlled estimate" sentence.

---

## 9. Literature verification note

I checked the following on arXiv on 2026-11-22 and verified title/abstract, not peer-review status. arXiv IDs are given so the authors can re-verify; if any ID is wrong, treat that citation as unverified rather than relying on this report.

| Work | arXiv ID | Relevance |
|---|---|---|
| ToolMaze / "When Tools Fail: Benchmarking Dynamic Replanning and Anomaly Recovery in LLM Agents" | 2606.05806 | Tool perturbation taxonomy; implicit semantic failures; Perturbation Recovery Rate |
| "Loud Failures, Quiet Failures: Fault Detection and Recovery in Tool-Using Language Model Agents" | 2610.10062 | Controlled fault injection; quiet vs loud failures; detection and recovery; prompt intervention |
| "Fabrication After Tool Failure: Tool-Augmented Agents Assert Values Their Tools Did Not Return" | 2609.14758 | status:ok corruption → 45.3% dishonesty; retrieval_status intervention |
| "Robustness Analysis of Agentic AI to Inconsistent and Incomplete Tool Responses" | 2608.22676 | Inconsistent/incomplete returns in retail; next-decision action signals |
| "Measuring What Tool-Using LLM Agents Actually Do: Structured Validation, Causal Error Propagation, and Fabricated Tool Use" | 2604.16706 | Paired wrong-argument injection; causal error propagation; 7 models |
| ToolScan: "A Benchmark for Characterizing Errors in Tool-Use LLMs" | 2411.13547 | Seven tool-use error patterns |
| ToolSword: "Unveiling Safety Issues of Large Language Models in Tool Learning Across Three Stages" | 2402.10753 | Noisy misdirection and error conflicts in tool learning |
| ToolBeHonest: "A Multi-level Hallucination Diagnostic Benchmark for Tool-Augmented Large Language Models" | 2406.20015 | Tool hallucination diagnostic |
| Sclar et al., "Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design..." | 2310.11324 | Prompt-format sensitivity; the V-vs-s0 effect |
| "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" | 2306.05685 | Judge biases and human agreement; relevant to the audit |
| PALADIN: "Self-Correcting Language Model Agents to Cure Tool-Failure Cases" | 2509.25238 | Tool-failure recovery training; recovery-rate baselines |
| AgentAbstain: "Do LLM Agents Know When Not to Act?" | 2607.10059 | Paired should-act/should-abstain tasks; controlled perturbation; frontier models |
| StableToolBench | 2403.07714 | Stable simulated APIs; benchmark stability |

The manuscript's reference list has 56 entries and no 2025–26 work. That is the single clearest signal to a Q1 reviewer that the related work was not updated after the 2026 literature appeared. Adding 12–20 citations and a comparison table is a low-cost, high-return revision.

---

## 10. Bottom line

The paper has a publishable measurement study inside it. Its strongest assets are the fixed-prefix design, the 20–46% format-sensitivity result, the silent-propagation/field-type map, and the persistence finding. Its weakest assets are the failed severity ladder, the AI-only audit, the unreleased dataset, and the unstable claim boundary.

A top-Q1 editor will not accept the current manuscript because it cannot answer three questions in the first two pages: *What is the contribution type? What exactly is claimed after three failed criteria? Why should I believe the measurement instrument?* The revision must answer those questions directly, cite the 2026 neighbors, and add at least one consequence endpoint (task success or wrong-direction harm). If the authors do that, the paper can be a strong Q1 measurement/benchmark paper. If they do not, it will read as a well-intentioned but unfinished study that mistook a failed dose–response for a causal result.

**Recommendation:** Major revision, with the five moves in §7. Do not resubmit as a "causal study" without a formal estimand, a task-success endpoint, and an independent audit. Do resubmit as a measurement paper that leads with format sensitivity, silent propagation, and persistence; that paper is already most of the way there.
