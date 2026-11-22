# Reviewer 4 — Adversarial Q1 review: integrity, data, reproducibility

**Date:** 2026-11-22
**Reviewer role:** adversarial Q1 reviewer; research-integrity, data, and reproducibility audit
**Manuscript:** `paper/toolresults.tex` (1,945 lines)
**Scope:** read-only audit. I did not edit the manuscript. I read the full paper, `README.md`,
`ROADMAP.md`, `docs/GATES.md`, `docs/DECISIONS.md` (D-021–D-043), `prereg/PREREGISTRATION.md`,
`prereg/AMENDMENTS.md`, `docs/DATA_CARD.md`, `release/README.md`, the manifest SHA-256 sidecar,
`artifacts/audit/blind_audit_result.json`, `artifacts/audit/verification/panel_record.json`, and
`artifacts/audit/second_rater_agreement.json`. I also inspected the local analysis artifacts and
the git index where needed to test reproducibility claims. I recomputed only simple arithmetic
from the paper's own tables and artifacts; I did not re-run the models or the full analysis.

---

## 1. Verdict

**Reject in current form.** The underlying design is interesting, the dataset is potentially
useful, and the paper is more candid about failure than most submissions. But as written it is not
a Q1 paper, and the problems are not copy-edits. Four are load-bearing:

1. **The G4 recovery gate is evaluated on a statistic that is not the pre-registered one.** The
   paper's headline recovery range (32.4–47.6%) is a Kaplan–Meier `1 − S(4)` estimate in which
   terminal non-recovery (a final answer) is treated as non-informative censoring. The raw event
   shares in the same table are 27.3%, 34.7%, and 27.2%. The pre-registered gate is "recovery
   events by H=4", i.e. the raw share. The reported table's "Recovered" column cannot be
   reconciled with its own `Events` and `n` columns. This is the single most serious statistical
   problem, and it makes Ministral look "close to the threshold" (47.6%) when the crude value is
   34.7%.
2. **A pre-registered G1 criterion failed and was replaced after the calibration values were
   seen.** The amendment log says so explicitly (`prereg/AMENDMENTS.md:77-93`: "post-freeze,
   after G1 calibration"; "Blind to outcomes: No"). The paper says "G1 passed" and later says "no
   threshold was changed". Both cannot stand with the amendment record. The manuscript also
   counts "two" failed criteria in the Introduction and "three" everywhere else.
3. **The audit is not independent, and the abstract overclaims it.** The raters are AI-agent
   sessions sharing one model family; two severity sessions are identical on 116/120 items; no
   human verified the final label-free round; the severity packet was rebuilt four times and the
   final sessions had seen earlier versions. The body discloses most of this; the abstract's
   "blind-rated label-free" and "agent verification panel" do not.
4. **The paper simultaneously claims and disclaims the same result.** The title says "Causal
   Study"; the abstract says "Critical errors move the next decision" and reports ORs of 4.60 and
   11.21; the Results say "no content-sensitivity claim" because G3 failed. A Q1 reviewer will
   read the title and abstract as the claim, and the caveat as an attempt to have it both ways.

A fifth, more practical problem: **the evidence is not available.** Every analysis artifact and
ledger the paper cites is gitignored, the release has no DOI, the frozen payload is not public,
and the claimed "one-command validation target" does not exist. An external reader cannot
reproduce the reported estimates from the paper and the repository.

I would recommend **reject**, with an invitation to resubmit as a measurement paper after (a) the
recovery estimand is fixed, (b) the preregistration and gate history are made honest, (c) a human
or otherwise independent audit is added for at least a subset, and (d) the artifact/DOI package is
published. The dataset and the negative results are worth a paper; this manuscript is not yet it.

---

## 2. Severity-ranked findings

**Severity:** C = would reject / claim-invalidating; H = major revision required; M = significant
but fixable in revision; L = copy-edit or presentation.

**Status:** Confirmed = directly read in the cited file or recomputed from the cited numbers;
Speculative = inference or risk that needs the authors' confirmation.

| ID | Sev. | Location | Finding | Why it matters | Fix | Status |
|---|---|---|---|---|---|---|
| C1 | C | `paper/toolresults.tex:1686-1698`; Table `tab:recovery` `:1712-1717`; `docs/GATES.md:134`; `docs/DECISIONS.md:82-89`; `artifacts/analysis/g4_recovery.json:298-342` | The "Recovered" column is Kaplan–Meier `1 − S(4)`, not `Events/n`. Qwen s3: 72/264 = 27.3% but table says 32.4%; Ministral s3: 141/406 = 34.7% but table says 47.6%; Llama s3: 112/412 = 27.2% but table says 28.2%. Terminal final answers are censored (`Algorithm 1`, `:971-972`), so non-recovery is treated as non-informative censoring. | The G4 gate is "≥50% of the s=3 risk set recovers by H=4" (`docs/GATES.md:134`), i.e. the crude event share. The KM statistic is biased upward when terminal non-recovery is censored as if the episode could continue. The paper's "Ministral is close" is an artifact of that choice. | Make the crude cumulative incidence the gate statistic; report KM as a secondary curve with an explicit competing-risk assumption (Aalen–Johansen or state the bias direction); add both columns to the table; recompute RMST and `t½`. | Confirmed (numbers); bias direction inferred |
| C2 | C | `paper/toolresults.tex:1064-1066`, `:1878-1880`; `prereg/AMENDMENTS.md:77-93`; `docs/DECISIONS.md:67-73`, `:348-363`; `artifacts/audit/g1_calibration_v3.json:30-32` | The original G1 V-vs-s0 criterion failed at 20.3/36.7/45.6% against ≤20%. The criterion was changed to s0-vs-s1 after the calibration values were seen. The paper says "G1 passed", and later "no threshold was changed". The G1 artifact still records `placebo_jitter: false` for all three models. | A gate relaxed after seeing data is not a pre-registered pass. The paper's "three failed criteria" count excludes this failure. The sentence "no threshold was changed" is false. | Report the original G1 criterion as failed, the amendment as post-hoc/not blind, and the main run as proceeding under A-004. Add G1 to the failure count or explain why not. Delete "no threshold was changed". | Confirmed |
| C3 | C | `prereg/PREREGISTRATION.md:3-8`, `:196-205`; `prereg/AMENDMENTS.md:138-141` | The frozen preregistration document says "Status: DRAFT — not yet frozen", "Prereg hash: TBD", "Registry: none", and all sign-off rows are `TBD`. The manifest records hash `e0d107c6…` and the file hash matches, but the document itself never becomes a signed v1.0. | "Pre-registered" is a claim about a fixed, verifiable plan. A draft header, TBD hash, no registry, and no PI sign-off undermine it. A reviewer who opens the file sees a contradiction. | Freeze a clean v1.0 with status, date, hash, and sign-off; deposit on OSF/Zenodo (or explain why not); update the header and manifest; cite the deposit in the paper. | Confirmed |
| C4 | C | `paper/toolresults.tex:685-690`, `:1588-1604`, `:1868-1870`, `:1926-1935`; `docs/DECISIONS.md:9-42`; `artifacts/audit/verification/panel_record.json:5`, `:1130-1141` | The audit is AI-agent raters sharing one model family; rater 1 = rater 2 on 116/120 severity items; no human verified the final label-free round; the severity packet was rebuilt four times and the final sessions had seen earlier versions. The abstract says "blind-rated label-free and checked by an agent verification panel" without these limits. | `α = .911` and `κ = .987` measure consistency among near-duplicate AI readings, not independent reliability. The paper says this in the body but not in the abstract, and "independent verification panel" (`:687`) is contradicted by "share one model family" two lines later. | Put "AI-agent raters, one model family, no human verification" in the abstract and contributions. Report packet iterations, rater reuse, and rater model/version. Replace "independent" with "separate". Add a human-rated 40-item subset if possible. | Confirmed |
| C5 | C | `paper/toolresults.tex:1399-1400`, `:1700`, `:1913-1916`; `.gitignore:123-139`; `release/README.md:18-34`; `docs/DATA_CARD.md:3-4`, `:21-23` | All analysis/audit artifacts and ledgers are gitignored; `git ls-files artifacts` returns only READMEs and `.gitkeep`; the paper cites `artifacts/analysis/g3_analysis.json`, `g4_recovery.json`, `switch_typology.json`, `prereg_secondary.json`, `artifacts/audit/blind_audit_result.json`, and `panel_record.json`, none of which are tracked in the repository. The release checklist is entirely unchecked; DOI and manifest hash are TBD. | The paper's core claim "every quantity traces to a ledger, a manifest, or an analysis artifact" (`:384-385`) is not verifiable by an external reader. This is a reproducibility failure, not a documentation gap. | Publish the scrubbed artifacts and ledger extracts with a DOI (or Zenodo). Add a reproduction appendix with commands, commit SHA, and SHA-256s. Mint the DOI before submission. Remove "will release" language or state a hard date. | Confirmed |
| C6 | C | `paper/toolresults.tex:244`, `:284-295`, `:1396-1398`, `:1894-1896`; `docs/GATES.md:16`, `:121` | Title says "A Fixed-Prefix Causal Study"; abstract says "Critical errors move the next decision" and leads with tier ORs 4.60 and 11.21; Results say "makes no content-sensitivity claim" because G3 failed; Conclusion says "bounded switch-on-severity estimate". | The claim boundary is the paper's own gate rule. A Q1 reviewer will see the title/abstract as a causal content-sensitivity claim and the caveat as hedging. The paper cannot both claim "move" and disclaim content sensitivity. | Retitle to a measurement framing (e.g. "A Fixed-Prefix Measurement Study of ..."). Rewrite the abstract to lead with the measurement and the three failures; use "measured shift among movers" or "associated with" rather than "move". Make the gate failure the second sentence, not the last. | Confirmed |
| H1 | H | `paper/toolresults.tex:383-384` vs `:291`, `:1266`, `:1875`, `:1891` | Introduction says "Two preregistered criteria failed"; abstract, Results, limitations, and Conclusion say three. | Internal inconsistency at the exact point where the paper declares its honesty about failure. Suggests stale text and weakens trust in the count. | Say "three" consistently, or use a gate-status table that enumerates every criterion and its verdict. | Confirmed |
| H2 | H | `paper/toolresults.tex:1395-1396`, `:1027-1031`; `prereg/PREREGISTRATION.md:175`; `docs/GATES.md:16` vs `:111-119` | The parser-failure <1% criterion is called "pre-registered" and listed under G3, but the frozen preregistration's G3 row (`:175`) does not contain it; it appears only in `docs/GATES.md:119` (and the GATES summary table `:16` omits it too). | If the parser gate is a protocol gate, not a preregistration gate, the abstract's "three pre-registered criteria failed" is inaccurate. The gate set is ambiguous across documents. | Distinguish "preregistered" from "protocol" criteria; add the parser criterion to the prereg by amendment or reword the abstract to "three gate criteria (two preregistered)". Make `GATES.md` summary and detail agree. | Confirmed |
| H3 | H | `paper/toolresults.tex:1894-1895`, `:1390-1394`; `prereg/AMENDMENTS.md:130-134`; `docs/DECISIONS.md:316-319` | The Conclusion says the audit "caught a labeling defect before analysis". The amendment log says an earlier G3 run existed under the pre-fix coder (`β = 0.684`), and the artifact was not retained. | The timeline is misrepresented. The paper reports a number (`β = 0.684`) that has no artifact, contradicting "every quantity traces to ... an analysis artifact". | Say "before the final analysis, after an earlier analysis under the pre-fix coder". Retain or reconstruct the earlier artifact, or remove the number. Report the audit → fix → rescore → analysis sequence explicitly. | Confirmed |
| H4 | H | `paper/toolresults.tex:1541-1549`, `:1636-1640`; `docs/DECISIONS.md:299-324`; `artifacts/audit/blind_audit_result.json:199-203` | The automatic coder was fixed using the same 160 outcome audit items that are then used to certify `κ = .987` and `PPV = 1.00`. There is no fresh, held-out audit after the fix. | This is in-sample validation. The audit found the defect, the fix was tuned on those items, and the same items now show near-perfect agreement. The PPV `1.00 (9/9)` is especially fragile. | Draw a fresh 160-item audit after the fix, or hold out a portion; report pre-fix and post-fix separately; state the circularity explicitly. | Confirmed |
| H5 | H | `prereg/PREREGISTRATION.md:34-38`, `:71`, `:98-99`; `paper/toolresults.tex:891-894`, `:1625-1636` | Pre-registered H5 ("s3 switch rate exceeds s1") is never reported, although `artifacts/analysis/prereg_secondary.json:23-25` contains `b=431, c=93, p=5.3e-53`. H3 ("silent propagation is a non-zero share") is downgraded to "descriptive" without an amendment. H1's `Y` is defined in the prereg as signature difference vs V, but the paper's `Y` is signature difference **or flag** (`:782-789`), and the paper adds `Y^O`, which the prereg's decomposition (`Y = Y^A ∨ Y^F ∨ Y^U`) does not contain. | Selective reporting of a pre-registered hypothesis; unlogged definition drift in the primary outcome and decomposition. A reviewer checking the prereg will find three discrepancies. | Add an H1–H7 hypothesis-status table with estimates. Report H5. Either restore H3 as secondary confirmatory with a CI or log the downgrade. Add an amendment for flag-inclusive `Y` and `Y^O`; report signature-only `Y` as the primary or as a sensitivity. | Confirmed |
| H6 | H | `paper/toolresults.tex:254-263`, `:1917-1925`; `:246-251` | Byline has two authors (Rahaman, Tuhin). Declarations credit "S.A.S. and M.M.A." for data curation, validation, and writing; those people are not in the byline. The source comment says the CRediT allocation is "carried over from the companion manuscript" and "must be confirmed". The Ethics item says "Annotation is performed by the author team", but the annotation was performed by AI-agent sessions. | Authorship/credit integrity; a false provenance statement in the Declarations. Editors require a signed, accurate CRediT statement. | Reconcile the author list and CRediT (add S.A.S./M.M.A. or remove them). Replace "author team" with "AI-agent rater sessions, author-overseen". Get every author's sign-off. | Confirmed |
| H7 | H | `paper/toolresults.tex:1434-1436`, `:1454-1460`, `:1430-1433`; `artifacts/analysis/prereg_secondary.json:28-30` | Pooled McNemar `b=190, c=50, p=2.1e-20` treats 240 discordant pairs as independent, but each prefix contributes up to three model pairs and the s2/s3 pairs are within-prefix. The categorical linearity LRT (`χ²(2)=25.03, p=3.7e-6`) also assumes independent rows, while the slope uses prefix-cluster SEs. | The pooled McNemar p and the LRT p are anti-conservative under the design's own clustering. The "linearity rejected" headline and the "threshold at s2" claim rest on them. | Use a cluster-robust/stratified test for McNemar (e.g. conditional logit on the s2/s3 pair with prefix×model strata, or a prefix bootstrap), and a cluster-robust Wald or bootstrap LRT. Report both. | Confirmed statistically |
| H8 | H | `paper/toolresults.tex:1380-1385`, `:1469-1470`; `artifacts/analysis/missingness_marginal.json:129-130`; `artifacts/analysis/switch_typology.json:36` | The paper says "617 strata that vary across arms (28.3% of the 2,297 strata)". 617/2,297 = 26.9%. The artifact says 649 strata vary (`variation_strata: 649`, `variation_share: .2825`); 649/2,297 = 28.3%. The 617 is the number of informative groups that enter the conditional logit; 32 varying strata are lost (likely to missing rows). | Conflates "varying strata" with "informative groups"; the arithmetic is wrong as written. A reviewer who checks will find the paper's own artifact contradicts it. | Say "617 informative groups (26.9% of 2,297); 649 strata vary across arms (28.3%), of which 32 do not enter the slope because of missing rows." Explain the 32. | Confirmed |
| H9 | H | `paper/toolresults.tex:1691-1693`, Table `tab:recovery` `:1712-1717` | "The fitted half-lives (4.3–8.0 steps) exceed the horizon in every group." The table contains 3.94 for Ministral s2, which is below H=4 and outside the stated range. | A factual error in the recovery paragraph; the claim "exceed the horizon in every group" is false for at least one group. | Say "3.9–8.0 steps; most exceed the horizon"; correct the range; explain the Ministral s2 case. | Confirmed |
| H10 | H | `paper/toolresults.tex:1203-1212`, `:1259-1263`; `docs/DECISIONS.md:202-206` | The planned envelope is 34,800 generations (12,000 base + 19,200 transient recovery + 2,400 persistent + 1,200 jitter). The executed run is 21,611 rows (13,200 base + 1,200 jitter + 7,211 recovery), 8.9 GPU-h. The paper says recovery is injected "for every prefix" (`:1207-1208`), but recovery is run only on at-risk switchers (risk sets 239–412 per model). | A 38% shortfall against the planned envelope is not reconciled. The paper's "sample is complete" and "recovery sequences ... are collected" hide that the recovery design is conditional on switching and that the persistent arm is near-inert. | Add an executed-vs-planned table with row counts and reasons. Say "recovery continuation is conditional on switching at the injected step; the planned 19,200 was an upper bound". Report the 21,611 total and the 8.9 GPU-h in the paper, not only in D-034. | Confirmed |
| H11 | H | `paper/toolresults.tex:1049-1052`, `:1311-1315`; `data/manifests/toolresult800_v1.json:107`; `docs/DECISIONS.md:446-462`; `docs/GATES.md:30-33` | G0 requires a 40-item human audit at ≥36/40. The sheet was filled from an AI pre-audit and the author's verification is deferred. The manifest still records `"audit_gate_pass": true`. | The gate that authorises the freeze (and the sample the main run depends on) was not passed by the pre-registered method. The manifest field is misleading unless its provenance is read from D-041. | Add `audit_gate_pass_provenance: ai_preaudit_deferred_human` and `human_audit_status: deferred` to the manifest. State G0 as "provisional, not passed" in the abstract and limitations, not only in the G0 subsection. Complete the human audit before submission. | Confirmed |
| H12 | H | `paper/toolresults.tex:670-674`, `:1917-1919`; `docs/DATA_CARD.md:90-96`, `:123`; `release/README.md:18-34` | PII audit is an AI mechanical pre-audit; the release PII re-scan is not done; the ethics determination is a `\pending{}` placeholder. The data card says "Human labels come from a small team, not an external annotation vendor", which is false (labels are AI-agent). | Release risk and an ethics/consent statement that is not complete. A Q1 journal will require a PII statement and an ethics determination (or exemption) before publication. | Complete a human PII audit of the release candidate; state the residual risk; obtain and cite the ethics determination; correct the data card. | Confirmed (status); release PII risk speculative |
| H13 | H | `paper/toolresults.tex:1926-1935`; `docs/DECISIONS.md:9-42` | AI-use disclosure does not name the model(s)/version(s), the prompts, the access dates, or whether the raters saw the paper's hypotheses/gates. It says only "one underlying model family". | For reproducibility and integrity, readers need to know what produced the labels. "AI agent" is not a provenance record. | Name model(s), version(s), dates, interface, prompts, and blinding procedure; deposit the packets and rater instructions. | Confirmed |
| M1 | M | `paper/toolresults.tex:987-990`, `:1441-1442`; `artifacts/analysis/prereg_secondary.json` `realized_mde` | Post-hoc power is reported as "realized power at the observed effect is 1.0". The design assumed a 4% placebo rate; the observed s0 rate is 30.1%. | Post-hoc power is a monotone transform of the p-value and adds no information; the 4% assumption was badly miscalibrated. Presenting "power = 1.0" reassures where the design assumption failed. | Report the realized MDE and its caveat only; drop "power = 1.0"; explain the 4% vs 30.1% gap as a design limitation. | Confirmed |
| M2 | M | `paper/toolresults.tex:283-284`, `:290`, `:1322-1325` | "Three open-weight 8–9B models answer every arm" overstates: 5.47% of prose cells are missing and 2.3–4.9% of prefixes lack a parsed V. "Re-serializing the same observation already moves 20–46% of decisions" is from the 60-prefix calibration, not the 800-prefix main study. | Abstract scope slips; a reader will attribute the 20–46% to the main sample. | Say "were run on every arm; 5.5% of prose cells unparsed" and "in the 60-prefix calibration (20.3–45.6%)". | Confirmed |
| M3 | M | `paper/toolresults.tex:716-719`; `data/manifests/toolresult800_v1.json` keys | The paper says the manifest records config hashes and the renderer, "not a parser field". The parser changed after freeze (D-028), and the manifest does not pin it. | The exact analysis is not reproducible from the manifest alone. The parser version is only in ledger rows and prose. | Add parser name/version/hash to the manifest or a sidecar; state it in the paper. | Confirmed |
| M4 | M | `paper/toolresults.tex:741-742`, `:1108`, `:1873`, `:1118-1121`; `docs/DECISIONS.md:251-252` | Paper says CUDA 13.5; D-031 observed `nvidia-smi` advertising CUDA 13.0. Paper says "runs at batch 4" but the run submits 8 prefixes/step with seq caps 8/4/4. | Environment and serving facts are inconsistent with the repo record. | Report the observed CUDA value and explain the 13.5 record; separate fit-check batch size from serving `max_num_seqs`. | Confirmed |
| M5 | M | `paper/toolresults.tex:1816-1818` | "A censored curve is a lower bound on persistence" is true only under non-informative censoring. Terminal final answers are censored, so the curve is not a bound. | Overstates the guarantee of the recovery curve. | Qualify: "under non-informative censoring"; or treat terminal non-recovery as a competing event. | Confirmed |
| M6 | M | `paper/toolresults.tex:1575-1577`, `:1650-1653` | "The seven items are ... a flight status, four route leaves, a cabin, two payment-type leaves, and insurance" enumerates nine items, not seven. "Field type is therefore at least as informative as the critical/non-critical label" is an exploratory comparison without a test or CI. | Numeric inconsistency and an overreach from a descriptive breakdown. | List the seven IDs and the exact field classes; soften "therefore" to "descriptively" or add a test. | Confirmed (count); overreach speculative |
| M7 | M | `artifacts/audit/g1_calibration_v3.json:21-23` | The G1 artifact records ledger paths under a server home directory, exposing a server username. AGENTS.md §2.1 forbids committing server usernames. | If the artifact is released as part of the reproducibility package, it leaks an identifier the project policy says never to publish. | Scrub paths before release; add a path-redaction step to the packager. | Confirmed locally; release risk speculative |
| M8 | M | `paper/toolresults.tex:1245-1253`; `src/toolobs/cli.py:29-35`; `Makefile:25-26`; `artifacts/analysis/g3_analysis.json` keys | The paper claims "a one-command validation target checks that rebuilt and reported values match the frozen artifacts" and "records the preregistration hash and the configuration hash with every run". `make validate` only checks that required YAML configs exist/parse; the analysis artifacts record `git_commit` but no prereg/config hash. | Two concrete reproducibility claims are false as implemented. | Implement the validation target (recompute tables from artifacts and diff) or remove the claim. Add prereg/config hashes to every analysis artifact. | Confirmed |
| M9 | M | `paper/toolresults.tex:1251-1253` | "Every table in the paper is expected to cite a manifest row and a ledger row." No table does; most cite an artifact path or nothing. | The provenance claim is aspirational, not actual. | Add a provenance appendix mapping each table/figure to artifact, ledger shard, and manifest hash; or soften to "should". | Confirmed |
| M10 | M | `paper/toolresults.tex:1598`, `:1928`; `artifacts/audit/second_rater_agreement.json:3-19`; `docs/DECISIONS.md:20` | The second-rater subset is called "120-item" in the paper and D-043, but the artifact has 40 severity + 40 outcome + 20 recovery = 100 items. | Numeric inconsistency in the audit description. | Say "100-item subset (40 severity, 40 outcome, 20 recovery)". | Confirmed |
| L1 | L | `paper/toolresults.tex:15-16` | Preamble says "15 tables and 8 figures"; the file has 21 `table` environments and 10 figures. | Copy-edit; makes the source look unmaintained. | Update the comment. | Confirmed |
| L2 | L | `paper/toolresults.tex:1816`, `:1822` | Future tense: "the paper will say so", "The result will inform choices". | Reads like a draft. | Convert to present tense. | Confirmed |
| L3 | L | `paper/toolresults.tex:1559-1569` | Table `tab:audit` omits the seed-repeat stability gate (reported in the sensitivity text at `:1749-1752`). | The audit table is not a complete gate record. | Add the stability row. | Confirmed |

---

## 3. Detailed notes on the six critical findings

### 3.1 The recovery gate is not the pre-registered recovery gate (C1)

The gate in `docs/GATES.md:134` is: "Recovery events by H=4, s=3 risk set ≥50%". That is a
cumulative event share: among the risk set, what fraction has an R1/R2 event by step 4. The
paper's headline numbers are not that. The table's own columns show it:

| Model | s=3 n | Events | Censored | `Recovered` in table | `Events/n` |
|---|---:|---:|---:|---:|---:|
| Qwen3.5-9B | 264 | 72 | 192 | 32.4% | **27.3%** |
| Ministral-3-8B | 406 | 141 | 265 | 47.6% | **34.7%** |
| Llama-3.1-8B | 412 | 112 | 300 | 28.2% | **27.2%** |

`artifacts/analysis/g4_recovery.json:298-342` confirms the 47.6% is `1 - survival_h4` from the
Kaplan–Meier curve. Algorithm 1 (`paper/toolresults.tex:971-972`) censors a sequence when the
model returns a final answer. A final answer that is not an R1 signature match is a terminal
non-recovery: the episode is over, and the agent cannot recover at step 5. Treating it as
non-informative censoring assumes it could have recovered later. That is a competing-risk
problem, and Kaplan–Meier is not valid for the cumulative incidence of recovery in the presence
of a competing terminal event.

The practical consequence is large: the KM estimate inflates Ministral s3 from 34.7% to 47.6%,
which is what lets the paper say "Ministral is close to the threshold" (`:1697-1698`). The paper
does report the crude values as "the alternative convention that censors at H=4" (`:1697`), but
that is backwards: the crude value is the pre-registered statistic; the KM value is the
alternative. This must be reversed, or the gate must be formally amended (which would be
post-outcome and cannot support the confirmatory claim).

A second, smaller issue: the table calls the KM value "Recovered" next to raw `Events` and `n`.
Even a careful reader cannot tell that the percentages are not `Events/n`. Add an explicit column
header and a footnote.

### 3.2 The G1 gate was changed after looking at the data (C2)

`prereg/AMENDMENTS.md:77-93` is explicit: A-004 is "post-freeze, after G1 calibration"; "Blind to
outcomes: No — the change followed the G1 calibration run and is not blind to its V-vs-s0
format-jitter values." `docs/DECISIONS.md:67-73` (D-041) says the earlier label "pre-freeze / blind"
was wrong and corrects it.

The paper's G1 paragraph (`:1064-1066`) says "G1 passed on all three models under the amended
negative-control criterion (A-004; s0 vs s1 jitter 10.5–13.3%); the original V-vs-s0 format-jitter
criterion failed at 20.3–45.6% and is reported separately". That is factually accurate but
rhetorically misleading: it presents the amended criterion as the gate and the original failure
as a secondary "format jitter". The G1 calibration artifact still has `"placebo_jitter": false`
for all three models (`artifacts/audit/g1_calibration_v3.json:30-32`). The gate that the
pre-registration actually specified did not pass.

Then, at `:1878-1880`, the paper says "no threshold was changed". That is false: A-004 changed the
G1 criterion from V-vs-s0 to s0-vs-s1. The sentence should say "no analysis threshold was changed;
the G1 placebo criterion was amended post hoc under A-004". This single sentence is the clearest
integrity problem in the manuscript because it is a direct contradiction of the amendment log.

### 3.3 The preregistration is a draft (C3)

`prereg/PREREGISTRATION.md:3-8`:

> **Status:** DRAFT — not yet frozen. Freeze at the end of G0; tag `prereg-freeze-v1`.
> **Registry:** none (no external registry). The frozen git tag and its SHA-256 are the record.
> **Prereg hash:** `TBD` (recorded at freeze)

`prereg/AMENDMENTS.md:138-141` says the document was frozen at commit `1673856`, tag
`prereg-freeze-v1`, hash `e0d107c6…`, and admits "The document header still reads DRAFT and its
hash line says TBD; the recorded hash is authoritative."

I verified that SHA-256 of `prereg/PREREGISTRATION.md` is
`e0d107c6013065374fb16df204e2eb30fbcafad039ed6fc7050c68dd26f4fc8a`, matching the manifest's
`prereg_hash`. So the hash is real. The problem is that the frozen document is a draft with no
sign-off (`:198-202`, all `TBD`) and no external registry. A git tag plus a manifest hash is a
weak form of preregistration; a Q1 methods reviewer will ask for OSF/Zenodo, and the paper never
discloses that there is no registry.

The paper's "pre-registered" claims are therefore technically true only in the sense of "a draft
text was hashed". The authors should either deposit the frozen text and cite the DOI, or state
plainly "not externally registered; git tag + manifest hash" in the limitations.

### 3.4 Audit independence (C4)

The paper is candid in the body:

- `:687-689`: "Its ratings are agent-produced and share one model family, so they establish
  reproducibility rather than human independence."
- `:1600-1602`: "The sessions share one underlying model family, and two of the three severity
  sessions are identical on 116/120 items, so α = .911 is consistency among near-duplicate
  readings, not independent human reliability."
- `:1868-1870`: "not by human coauthors or an external vendor."

But the abstract (`:294-295`) says only: "Audits were blind-rated label-free and checked by an
agent verification panel." That omits (a) the raters are AI, (b) one model family, (c) no human
verification, (d) two sessions are near-duplicates, (e) the packet was rebuilt four times, and
(f) the final sessions had seen earlier packet versions (`docs/DECISIONS.md:13-16`, `:39-40`).
"Agent verification panel" is ambiguous enough that a reader may assume human research assistants.

The consequence is not that the labels are necessarily wrong. It is that the agreement statistics
cannot be interpreted as reliability. `α = .911` with two near-duplicate raters is a consistency
statistic, not an inter-rater reliability coefficient. The paper says this once, in the
limitations, but the abstract and the audit table present the numbers without the caveat.

### 3.5 The evidence is not reproducible (C5)

The paper's strongest reproducibility claim is at `:1251-1253`: "Manifests are the
reproducibility spine: every table in the paper is expected to cite a manifest row and a ledger
row." In practice:

- `.gitignore:123-139` ignores `artifacts/audit/*` and `artifacts/analysis/*`; only `.gitkeep`
  and `README.md` are tracked. `git ls-files artifacts` confirms this.
- The paper cites `artifacts/analysis/g3_analysis.json` (`:1399-1400`),
  `artifacts/analysis/g4_recovery.json` (`:1700`), `artifacts/analysis/switch_typology.json`
  (`:1386`), `artifacts/analysis/prereg_secondary.json` (`:1443`),
  `artifacts/audit/blind_audit_result.json` (`:1546`), and
  `artifacts/audit/verification/panel_record.json` (`:1604`). None are in the repo.
- The frozen payload `data/frozen/prefixes.jsonl` is gitignored (`data/frozen/*`).
- The release checklist (`release/README.md:20-34`) is unchecked; DOI and manifest hash are
  `TBD` (`docs/DATA_CARD.md:21-23`); the manuscript has a visible `\pending{}` for the DOI
  (`:1913`).
- The "one-command validation target" does not exist: `make validate` runs
  `python -m toolobs.cli validate` (`Makefile:25-26`), which only checks that required YAML
  configs exist and parse (`src/toolobs/cli.py:29-35`).
- The analysis artifacts record `git_commit` but not the preregistration hash or the
  configuration hash the paper claims (`:1245-1248`).

An external reader can read the code and run the tests (if the repository is public), but cannot
reproduce any reported table. That is a rejection-level reproducibility failure for a paper whose
central contribution is a measurement estimate.

### 3.6 Claim boundary (C6)

The paper's own gate rule says: if G3 fails, report a null/measurement paper and make no
content-sensitivity claim (`docs/GATES.md:16`, `:121`). The paper says it follows this (`:1396-1398`).
But the title is "A Fixed-Prefix Causal Study of Detection, Reliance, and Recovery", and the
abstract's first substantive sentence is "Critical errors move the next decision: tier odds ratios
against the placebo are 1.27 ..., 4.60 ..., and 11.21 ...". "Move" is a causal content-sensitivity
claim. The caveat arrives nine lines later.

A reviewer will not treat the caveat as sufficient. The paper needs a measurement framing in the
title and abstract, with the positive estimate presented as a bounded association among movers,
and the three failures in the first two sentences. The current structure asks the reader to
believe the headline and forgive the caveat.

---

## 4. Top-10 priority list

1. **Fix the G4 estimand.** Report the crude cumulative incidence (27.2–34.7%) as the gate
   statistic; report KM as a secondary curve with a competing-risk caveat; add both columns to
   Table `tab:recovery`; recompute RMST and `t½`. (C1)
2. **Make the G1 history honest.** Report the original V-vs-s0 criterion as failed, A-004 as
   post-hoc/not blind, and the main run as proceeding under the amendment. Delete "no threshold
   was changed". Add G1 to the failure count or explain the count. (C2)
3. **Freeze and deposit the preregistration.** Replace the DRAFT header/TBD hash/TBD sign-off with
   a signed v1.0; deposit on OSF/Zenodo or state "not externally registered" in the paper. (C3)
4. **Add an independent (human) audit for at least a 40-item subset.** If that is impossible,
   downgrade the abstract and title to "AI-agent ratings, one model family, no human
   verification". Report packet iterations and rater reuse. (C4)
5. **Publish the artifact and ledger package with a DOI.** Include the frozen prefixes, arm
   observations, perturbation records, audit packets, analysis JSONs, and scrubbed ledger
   extracts. Tag the code commit. Implement or remove the "one-command validation" claim. (C5)
6. **Rewrite the title and abstract as a measurement paper.** Move the three failures forward;
   replace "move" with "measured shift among movers"; drop "Causal" from the title unless the
   paper is willing to defend it against its own gate. (C6)
7. **Break the audit/coder circularity.** Hold out a fresh 160-item outcome audit after the fix,
   or report the post-fix κ/PPV as in-sample and add a held-out estimate. Do the same for the
   severity packet. (H4)
8. **Report H5, H3, and the outcome-definition amendments.** Add an H1–H7 status table; report
   `s3 > s1` (`b=431, c=93, p=5.3e-53`); either restore H3 as secondary confirmatory or log the
   downgrade; amend the flag-inclusive `Y` and the new `Y^O`. (H5)
9. **Fix the clustered inference.** Replace the pooled McNemar and the categorical LRT with
   cluster-robust/stratified versions, or report them as descriptive with the clustering caveat.
   (H7)
10. **Reconcile the executed design and the numbers.** Add an executed-vs-planned generation
    table (34,800 vs 21,611; recovery 21,600 vs 7,211); explain the at-risk design; fix
    617/649, 100 vs 120, 7 vs 9, and the 3.9 vs 4.3 half-life range. (H8–H10)

---

## 5. The five strongest rejection reasons

1. **The recovery gate is evaluated on the wrong statistic.** The paper reports KM `1 − S(4)`
   with terminal non-recovery censored as if it were non-informative. The raw event shares are
   27.3/34.7/27.2%, not 32.4/47.6/28.2%. The table's "Recovered" column is irreconcilable with
   its own `Events/n`. This is not a rounding issue; it changes the gate margin and the claim that
   Ministral is "close". A reviewer who checks the table will not trust the recovery analysis.

2. **A pre-registered gate was changed after seeing the data, and the paper denies it.** A-004 is
   explicitly post-freeze and not blind. The original G1 criterion failed. The paper says "G1
   passed" and "no threshold was changed". The failure count is "two" in the Introduction and
   "three" elsewhere. This is the kind of inconsistency that makes an editor question every other
   gate claim.

3. **The audit is AI-on-AI, and the abstract hides it.** The raters share one model family, two
   severity sessions are identical on 116/120 items, no human verified the final labels, and the
   packet was rebuilt four times with rater carryover. The body discloses this; the abstract's
   "blind-rated label-free" does not. The agreement statistics are consistency, not reliability,
   and the paper's own limitations say so.

4. **The paper claims and disclaims the same result.** The title says "Causal Study", the abstract
   says "Critical errors move the next decision", and the Results say "no content-sensitivity
   claim". The gate rule says a failed G3 yields a measurement paper. The manuscript wants the
   positive headline and the failed-gate protection. A Q1 reviewer will reject the inconsistency
   even if the underlying estimate is real.

5. **The evidence chain is not available.** All analysis artifacts and ledgers are gitignored, the
   release has no DOI, the frozen payload is not public, and the claimed validation target does
   not exist. The paper's "every quantity traces to a ledger, a manifest, or an analysis artifact"
   is false for the external reader. The earlier `β = 0.684` artifact was not retained. This is a
   reproducibility failure at the level of the paper's central contribution.

**Also serious, but easier to fix:** the author list and CRediT statement are inconsistent
(S.A.S./M.M.A. are credited but not in the byline), and the Ethics item says annotation was done
by "the author team" when it was done by AI-agent sessions. Editors treat authorship/CRediT
inconsistency as a separate integrity issue.

---

## 6. The five easiest high-impact fixes

These are text/table changes that do not require new data collection. They will not rescue the
paper on their own, but they remove the most obvious reject triggers.

1. **Fix the failure count and add a gate-status table.** Replace "Two preregistered criteria
   failed" (`:383-384`) with a table listing every gate, its pre-registered criterion, the
   observed value, the verdict, and the amendment (G0 provisional; G1 original fail/A-004; G3
   parser; G3 severity; G4 recovery). Use the same count everywhere.

2. **Delete "no threshold was changed" and state the A-004 timing.** Replace `:1878-1880` with:
   "No analysis threshold was changed. The G1 placebo criterion was amended after the calibration
   run under A-004; the original V-vs-s0 criterion failed at 20.3–45.6% and is reported in
   Table G1." This is a two-sentence fix.

3. **Correct the Declarations.** Replace "Annotation is performed by the author team" with
   "Annotation was performed by AI-agent rater sessions, author-overseen; no human verified the
   final labels." Reconcile the author list/CRediT (add S.A.S./M.M.A. or remove them). This is an
   editorial must-fix.

4. **Relabel the recovery table and add the crude share.** Add columns "Crude events/n" and
   "KM 1−S(4)"; report the gate on the crude column; add a footnote that terminal final answers
   are treated as competing events in the KM column. Correct "4.3–8.0" to "3.9–8.0" and "exceed
   the horizon in every group" to "most groups".

5. **Fix the numeric inconsistencies.** 617 informative groups = 26.9%, 649 varying strata =
   28.3%; second-rater subset = 100 items (40/40/20), not 120; the "seven items" list enumerates
   nine; "seven items listed in `blind_audit_result.json`" should point to a list that actually
   exists. These are one-pass edits.

**Honorable mention (easy):** add "AI-agent raters, one model family, no human verification" to
the abstract; replace "independent verification panel" with "separate agent verification panel";
change "Re-serializing ... 20–46%" to "in the 60-prefix calibration, 20.3–45.6%"; change "answer
every arm" to "were run on every arm; 5.5% of prose cells unparsed".

---

## 7. Disclosure gaps

The paper discloses many limitations, but the following are missing or under-specified. Each is a
place where a Q1 reviewer would ask "why didn't you say this up front?"

### 7.1 Gate and preregistration history
- G0 human audit deferred, no date, no replacement rows; the manifest's `audit_gate_pass: true`
  is not explained in the paper (`data/manifests/toolresult800_v1.json:107`; D-041 `:69-73`).
- G1 amendment A-004 is post-freeze and not blind; the paper does not say so (`:1064-1066`).
- The original G1 V-vs-s0 failure is present in the paper but framed as "format jitter", not a
  failed gate.
- The parser <1% criterion is called "pre-registered" but is absent from the frozen prereg G3 row
  (`prereg/PREREGISTRATION.md:175`).
- The preregistration is a draft with TBD hash and TBD sign-off; no external registry.
- The paper says "no threshold was changed" (false under A-004).

### 7.2 Audit provenance and independence
- Four severity packet versions; final sessions had seen earlier versions (D-043 `:13-16`,
  `:39-40`).
- Two severity sessions identical on 116/120; all three agree on 107/120 (panel_record `:1130-1141`).
- No human verification of the final label-free round; the only author verification (D-035)
  applies to the superseded label-visible round (`docs/DECISIONS.md:187-190`).
- The recovery verifier agreed with the automatic coding on 80/80 and all 14 corrections were
  toward the automatic coding (panel_record `:749-1092`). This is circular validation, not
  independent checking.
- The earlier annotated-packet severity α `.957/.981` is archived but not reported (D-043
  `:35-40`).
- The AI model(s), version(s), prompts, dates, and interface are not named (`:1926-1935`).
- The data card says "Human labels come from a small team" (`docs/DATA_CARD.md:123`), which is
  false.

### 7.3 Statistical reporting
- KM vs crude recovery: the pre-registered statistic is the crude share; the paper reports KM as
  primary.
- Pooled McNemar and categorical LRT ignore prefix/model clustering.
- `p = .035` domain interaction is unadjusted and exploratory; the paper says so, but the
  abstract and contributions do not mention the exploratory status of the field taxonomy.
- The reserve `β = 0.781` is called "held-out" but is post-hoc and not labeled as such in the
  paper (D-038 `:120-129` says it should be labeled post-hoc).
- H5 is omitted; H3 is downgraded; H1's `Y` and the `Y^O` decomposition are not amended.
- Post-hoc power `1.0` is reported without the artifact's caveat that it is "not a prospective
  power guarantee" (`artifacts/analysis/prereg_secondary.json` `realized_mde`).
- The marginal contrasts (+10.2/+16.3/+6.2) are reported without saying whether their CIs are
  cluster-adjusted; if they are row-level, they are too narrow.

### 7.4 Data and code
- No DOI, no release, no frozen payload, no ledgers; all analysis artifacts gitignored.
- No tagged analysis commit in the paper; `g3_analysis.json` records `git_commit: b4555ef…`, but
  the manuscript does not cite it.
- The "one-command validation" target does not exist.
- The analysis artifacts do not record the prereg/config hashes the paper claims.
- No table-to-manifest/ledger provenance map.
- The G1 artifact contains server-home paths; release scrub needed.
- The earlier `β = 0.684` artifact was not retained (A-006 `:130-134`).

### 7.5 Ethics, PII, and legal
- The 40-item PII audit is an AI mechanical pre-audit; no human PII check.
- The release PII re-scan is not done; the release is not built.
- The ethics determination is a `\pending{}` placeholder (`:1919`).
- The data card says "No raw PII is released" (future tense) and "Human labels ... small team"
  (false).
- Model output licenses for redistribution are not verified; the paper says outputs are
  "subject to each model's license" but does not confirm that all three permit the planned
  release (`docs/DATA_CARD.md:102`).
- τ-bench is MIT (`data/manifests/source_pin.json` `license: MIT`), and the paper's statement is
  correct; no issue there.
- Funding and conflicts are disclosed and appear consistent (`:1902-1906`).
- The author list/CRediT mismatch is an editorial integrity issue.

### 7.6 Presentation of negative results
- The three failures are in the abstract, Results, limitations, and Conclusion, which is better
  than most papers. But the abstract leads with the positive estimate and puts the failures in
  the last third; the title has no hint of failure; the Introduction undercounts ("two"); the
  G0 deferral and G1 amendment are absent from the abstract and limitations.
- The severity failure is argued away with "correcting ... would if anything steepen the
  s1–s2 contrast" (`:1582-1586`) without a sensitivity refit excluding the flagged items. That is
  a hypothesis, not a demonstrated robustness result.
- The recovery failure is softened as "convention-dependent" and "Ministral close" (`:1697-1698`);
  under the pre-registered crude statistic, the range is 27.2–34.7%, not close to 50%.
- The paper says "Three gate criteria failed" but does not count G0 (provisional) or the original
  G1 (failed before amendment). A reader of the abstract would not know that.

---

## 8. What I could not verify (and what would change my verdict)

I could not verify the following without the authors' evidence. They are marked speculative in
the table where relevant.

1. **Whether the human G0 audit would pass.** The AI pre-audit says 40/40; the human sheet is
   blank. If the human audit fails more than two airline items, the 400-airline sample cannot be
   replaced from the 442-prefix cap-10 pool (paper `:604-606`). This could invalidate the domain
   balance.
2. **Whether the final label-free audit is correct.** The AI raters may be right, but their
   agreement is not independent evidence. A human-rated 40-item subset would resolve this.
3. **Whether the release candidate contains PII.** The automated scan says 0 residual direct
   identifiers, but the human PII audit is not done. The release should not ship until it is.
4. **Whether the model licenses permit redistribution of outputs.** I did not verify the Qwen,
   Ministral, and Llama license terms against the planned release. The paper should.
5. **Whether the KM bias is the only reason for the 47.6% vs 34.7% gap.** The gap is consistent
   with censoring of terminal final answers, but I did not inspect every sequence. The authors
   should show the censoring pattern by step.
6. **Whether the marginal contrast CIs are cluster-adjusted.** The artifact
   `missingness_marginal.json` reports `pairs` and CIs but no clustering metadata. If they are
   row-level, they are anti-conservative.
7. **Whether the `α = .911` / `κ = .987` values would survive a fresh audit.** The coder was fixed
   on the same items; a held-out audit is the only way to know.

If the authors fix C1–C6 and H1–H5, the paper could become a strong measurement paper. The
dataset and the negative results are the most valuable parts; the current manuscript undersells
them by trying to sell a causal claim the gates do not support.

---

## 9. Appendix: arithmetic checks

These are simple recomputations from the paper's own tables and artifacts. They are not new
analyses.

**Recovery (Table `tab:recovery`, `:1712-1717`):**

| Group | Events/n | Crude | Table "Recovered" | Difference |
|---|---:|---:|---:|---:|
| Qwen s2 | 71/239 | 29.7% | 35.0% | +5.3 pp |
| Qwen s3 | 72/264 | 27.3% | 32.4% | +5.1 pp |
| Ministral s2 | 131/366 | 35.8% | 51.4% | +15.6 pp |
| Ministral s3 | 141/406 | 34.7% | 47.6% | +12.9 pp |
| Llama s2 | 105/376 | 27.9% | 28.9% | +1.0 pp |
| Llama s3 | 112/412 | 27.2% | 28.2% | +1.0 pp |

The KM inflation is concentrated in Ministral, which is exactly the model the paper calls "close
to the threshold". This is not a coincidence; it is the censoring pattern.

**Strata (`:1380-1385`, `:1469-1470`; `missingness_marginal.json:129-130`;
`switch_typology.json:36`):**

- 617 / 2,297 = 26.86% (paper says 28.3%).
- 649 / 2,297 = 28.25% (artifact's `variation_share`).
- 2,297 − 617 = 1,680 (paper's "concordant strata" is consistent with 617).
- 649 − 617 = 32 varying strata do not enter the slope.

**Audit subset (`:1598`, `:1928`; `second_rater_agreement.json:3-19`):**

- 40 severity + 40 outcome + 20 recovery = 100, not 120.

**"Seven items" (`:1575-1577`):**

- 1 flight status + 4 route leaves + 1 cabin + 2 payment-type leaves + 1 insurance = 9, not 7.

**Generation envelope (`:1215-1232`; D-034 `:202-206`):**

- Planned: 12,000 + 19,200 + 2,400 + 1,200 = 34,800.
- Executed: 13,200 + 1,200 + 7,211 = 21,611.
- 21,611 / 34,800 = 62.1%.
- Recovery executed: 7,211 / 21,600 = 33.4% of the planned recovery envelope.

**Half-life (`:1691-1693`; Table `tab:recovery`):**

- Table values: 3.94, 4.29, 5.58, 6.39, 7.78, 8.02.
- Stated range "4.3–8.0" excludes 3.94; "exceed the horizon in every group" is false for 3.94.

**G1 (`artifacts/audit/g1_calibration_v3.json:30-32`, `:41-66`; paper `:1336-1338`):**

- Negative-control jitter: 11.86%, 13.33%, 10.53% (paper: 11.9, 13.3, 10.5).
- Format jitter: 20.34%, 36.67%, 45.61% (paper: 20.3, 36.7, 45.6).
- The artifact's `placebo_jitter` gate is `false` for all three; the top-level `passed` is `true`
  only because the amended criterion is used.

---

## 10. Bottom line for the editor

This is a real study with a real dataset and an unusually honest failure section. It is also a
manuscript that, at the exact points where a Q1 reviewer checks integrity, does not hold up: the
recovery gate is the wrong statistic, the G1 gate was changed after the data and the paper denies
it, the audit is AI-on-AI with no human check, the title/abstract claim what the Results
disclaim, and the evidence package is not available. I would reject in current form and invite a
resubmission that (a) re-derives G4 on the pre-registered crude share, (b) publishes the full
preregistration/gate history including the original G1 failure, (c) adds a human-rated audit
subset, (d) rewrites the title/abstract as a measurement paper, and (e) releases the artifact and
ledger package with a DOI. The dataset and the three negative results are worth that work.
