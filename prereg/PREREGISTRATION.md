# Pre-Registration — Tool-Observation Sensitivity in Language-Model Agents (E2)

**Status:** DRAFT — not yet frozen. Freeze at the end of G0; tag `prereg-freeze-v1`.
**Version:** 0.1-draft · 2026-11-09
**Registry:** none (no external registry). The frozen git tag and its SHA-256 are the record.
**Prereg hash:** `TBD` (recorded at freeze)
**Design authority:** [`docs/PROTOCOL.md`](../docs/PROTOCOL.md), [`ROADMAP.md`](../ROADMAP.md)
**Amendments:** [`AMENDMENTS.md`](AMENDMENTS.md)

This document is written before the confirmatory data are collected. It records what will be
tested, on which population, with which decision rule, and what will count as failure. The
60-prefix pilot is prior evidence and is **not** part of the confirmatory sample.

## 1. Background and claim boundary

The pilot used 60 synthetic WebArena-lite / τ-style prefixes, `qwen3.5:4b`, greedy decoding,
and three collapsed action codes. It found a consult rate of 54/60, placebo jitter of 0/60, and
an error-switch rate of 5/60 = 8.3% (95% CI [1.3, 15.3] pp; McNemar b=5, c=0, exact p=.0625).
The pilot is a screening signal, not a dose-response estimate. It used one model, synthetic
prefixes, coarse action coding, and no recovery data.

The confirmatory object is the **within-prefix causal effect of tool-observation content on the
next decision, graded by severity**, across real τ-bench prefixes, three open-weight 7–8B model
families, and two task domains; plus a four-step recovery estimate. The study does **not** claim
a universal law, a model ranking, transfer to frontier models, or an end-to-end task-success
effect.

## 2. Hypotheses

| ID | Hypothesis | Type |
|---|---|---|
| **H1** | The pooled conditional-logistic slope of content switch on severity is positive: `β > 0` over `s = 0,1,2,3`. | Primary confirmatory |
| **H2** | The per-model slope is positive in at least two of three models, with the same sign. | Confirmatory |
| **H3** | Silent propagation (`Y^U`) is a non-zero share of the decision changes at `s = 2` and `s = 3`. | Secondary confirmatory |
| **H4** | Recovery is estimable: at least 50% of the `s = 3` risk set recovers by `H = 4`, and the Weibull shape is not rejected at `p < .01`. | Confirmatory estimation |
| **H5** | The `s = 3` switch rate exceeds the `s = 1` rate. | Secondary confirmatory |
| **H6** | Donor-specific and task-specific slopes are directionally consistent with the pooled slope. | Exploratory |
| **H7** | Model × severity and task × severity interactions are not claimed; they are exploratory and underpowered. | Exploratory |

The primary test is H1. H2 is a replication gate, not a model-ranking test. H4 is an estimation
target: if it fails, the paper reports the recovery curve and restricted mean survival time
(RMST), not a half-life law.

## 3. Design

| Element | Specification |
|---|---|
| Unit | A frozen message prefix ending immediately after a real τ-bench tool observation |
| Sample | **800 prefixes**: 400 airline + 400 retail; 80 held in reserve; seed `20261108` |
| Harvest frame | 1,980 public τ-bench trajectories; 13,605 candidate post-tool decision points; 6,554 eligible value-used observations expected |
| Models | Qwen2.5-7B-Instruct-AWQ; Mistral-7B-Instruct-v0.3-AWQ; Llama-3.1-8B-Instruct-AWQ |
| Model substitution | If Llama-3.1 access fails, InternLM2.5-7B-Chat or Yi-1.5-9B-Chat, pre-registered before G1 |
| Arms | **V** verbatim JSON; **s=0** faithful prose; **s=1** one non-critical change; **s=2** one critical wrong value; **s=3** critical change + contradiction |
| Recovery | H=4 steps; transient injection primary; persistent injection on 25% of prefixes at `s=3` |
| Generation envelope | 34,800: 12,000 base + 19,200 transient recovery + 2,400 persistent + 1,200 jitter repeats |
| Decoding | Greedy (T=0), fixed seed, fixed prompt and parser version |
| Prefix source | Real τ-bench historical trajectories; target models never generate or repair prefixes |
| Donor separation | Prefix donors are gpt-4o and claude-3.5-sonnet; target models are open-weight 7–8B models |

The full sampling, replay, renderer, and audit procedures are frozen at G0 and specified in
`docs/PROTOCOL.md`.

## 4. Primary estimand and test

For prefix `p`, model `m`, and severity `s ∈ {0,1,2,3}`:

\[
\operatorname{logit} P(Y_{p,m,s}=1) = \alpha_{p,m} + \beta_m s
\]

where `Y = 1` iff the decision signature differs from the verbatim-observation (V) continuation.
The model is a conditional (fixed-effects) logistic regression stratified by prefix, with
cluster-robust standard errors by prefix. The pooled model stratifies by `prefix × model` and
clusters by prefix.

**Primary test.** One-sided test of `H1: β > 0` at `α = .05`, reported two-sided for
completeness. The design MDE at N=800 is **0.203 logit/level** (OR 1.22), 80% power, assuming a
4% placebo switch rate, random prefix intercept variance 1.0, and balanced design. The pilot
implies `b ≈ 0.8`, which is about four times the MDE; the pilot is not used as the effect-size
estimate in the power claim.

**Decision rule.** H1 is supported iff the pooled slope is positive and the per-model slope is
positive in at least two of three models with the same sign. If the pooled slope is null or
negative, the paper reports a null/measurement result and does not reframe it as a law.

**Linearity.** The primary slope assumes equal spacing of `s = 0…3`. A categorical-`s` likelihood
ratio test and a quadratic term are pre-registered diagnostics. If linearity is rejected, the
paper reports tier-specific odds ratios and treats the slope as a summary, not a law. The
`s=2` vs `s=3` contrast is always reported separately because `s=3` is intentionally compound.

## 5. Secondary estimands

1. **Silent propagation (`Y^U`).** The false value of a decision-critical field appears in the
   decision-relevant content or arguments with no explicit flag. Scored only for `s=2` and `s=3`.
2. **Detection (`Y^F`).** An explicit flag, doubt, verification request, or statement that the
   observation is inconsistent or untrustworthy.
3. **Action switch (`Y^A`).** Tool name or canonicalized arguments differ from the V continuation.
4. **Decomposition.** `Y = Y^A ∨ Y^F ∨ Y^U`; silent propagation requires
   `Y^U ∧ ¬Y^A ∧ ¬Y^F`.
5. **Placebo and format.** `s=0` repeat jitter and V-vs-`s=0` format effect are descriptive.
6. **Recovery.** Discrete-time survival over H=4; exponential `t½ = ln2/μ`; Kaplan–Meier and
   RMST; Weibull shape test. If shape ≠ 1 at `p < .01` or fewer than 50% recover, `t½` is
   exploratory and the curve/RMST is primary.
7. **Heterogeneity.** Donor-specific and task-specific slopes are exploratory; no model ranking.

## 6. Severity construction and outcome coding

| Arm | Observation | Construction rule | Role |
|---|---|---|---|
| V | Exact real tool output, raw JSON | No change | Format/jitter anchor; not in the primary slope |
| s=0 | Faithful deterministic prose paraphrase | Same value multiset as V; every leaf rendered | Placebo; intercept/jitter |
| s=1 | One non-critical field changed or omitted | Field is not used in the donor continuation and is labeled `noncritical` | Negative control |
| s=2 | One decision-critical field changed | Field is used in the donor continuation; plausible wrong value | Dose |
| s=3 | Critical change plus a second inconsistency | Two leaves differ; contradiction is detectable by a careful reader | Dose (compound) |

The renderer is deterministic; no LLM paraphrase enters the manipulation. The perturbation record
stores JSON path, true value, false value, criticality, expected action change, and renderer
version. `s=0` must preserve the V value multiset exactly; a failure excludes the prefix.

**Outcome signature.** Tool name + canonicalized JSON arguments, or the final answer's normalized
action verb + decision-critical slots. Canonicalization: sorted keys, Decimal number
normalization, ISO dates, lower-case entities, whitespace/punctuation collapse.

**Audits.** 120 severity items (30/level, 3 blind raters): monotone severity means
(Jonckheere–Terpstra `p < .01`), Krippendorff `α ≥ .75`, ≥90% of `s=1` rated
non-decision-changing, ≥90% of `s=2/s=3` rated decision-changing, `s=3` not "absurd" by >20%.
160 outcome items (2 blind raters): 4-way Cohen's `κ ≥ .80`; silent-propagation PPV ≥ .90;
10% seed-repeat stability ≥ .90. 80 recovery sequences: `κ ≥ .75`. If outcome `κ` falls to
`.70–.80`, adjudicated labels are primary on the audit subsample; below `.70`, the content claim
is downgraded to action-level `Y^A` only.

## 7. Sampling, freeze, and exclusions

1. Pin the τ-bench repository at a 40-character commit SHA; record hashes of the four trajectory
   files and the task databases.
2. Parse every assistant message immediately following a `tool` message; reconstruct the exact
   prefix and the donor continuation.
3. Exclude profile/PII tools and observations with no value used in the continuation.
4. Scrub names, emails, addresses, phones, payment identifiers, and dates of birth with stable
   synthetic tokens; exclude a prefix if a decision-critical value is itself PII.
5. Replay the prefix's tool calls against the pinned task database; retain ≥98% normalized
   matches.
6. Cap at 10 prefixes per task–domain; draw 880 stratified by domain, donor, step bin, and tool
   family; freeze 800 primary (400/400) + 80 reserve (40/40).
7. Audit 40 random prefixes blind: eligibility, PII, decision relevance, replay, renderability.
   Pass ≥36/40. Replace failures from reserve; re-audit replacements.
8. Freeze `data/manifests/cto800_v1.json` with every prompt, observation, perturbation, renderer
   version, seed, and SHA-256. No changes after target-model outcomes are seen.

**Exclusions.** Parse failures are excluded from the primary slope and reported as a rate.
Prefixes whose V continuation mutates environment state are flagged and analyzed separately in
recovery. No prefix is dropped after seeing target-model outcomes without a logged amendment.

## 8. Analysis plan and multiplicity

- **Primary:** pooled conditional-logistic slope `β`; then per-model slopes with Holm across
  three models. Fixed sequence: pooled first, then per-model.
- **Diagnostics:** linearity LRT/quadratic term; placebo jitter; V-vs-`s=0` format effect.
- **Secondary:** `Y^U`, `Y^F`, `Y^A`; `s=2` vs `s=3` exact McNemar; recovery curve, `t½` or RMST.
- **Inference:** prefix-cluster bootstrap, 2,000 replicates, percentile 95% CIs. No model
  ranking; no post-hoc subgroup claim.
- **Missing data:** report the parse-failure rate; do not impute outcomes.
- **Sensitivity:** exclude `s=0`; fit `s=1…3`; donor-specific slopes; task-specific slopes;
  strict vs lenient action coding; seed-repeat stability.
- **Software:** analysis code is versioned; the analysis script records the prereg hash and
  config hash.

## 9. Gates

| Gate | Criterion | Fail action |
|---|---|---|
| **G0** | ≥880 eligible; ≥440/domain pre-audit; ≥400/domain post-audit; replay ≥98%; 40-item audit ≥36/40; freeze hash stable | Fallback 500 prefixes/2 models or stop |
| **G1** | Parse ≥95%; placebo jitter ≤20%; `s=3` switch 10–80%; refusal <5% per model | Stop and fix; no main spend |
| **G2** | Main run completes within $22 or 45 GPU-hours | Analyze completed shards; disclose |
| **G3** | Pooled `β > 0`; positive in ≥2/3 models with the same sign; severity `α ≥ .75`; outcome `κ ≥ .80` (or adjudicated `.70–.80` with downgrade); recovery `κ ≥ .75` | Null/measurement paper |
| **G4** | ≥50% recovery events by H=4; Weibull shape not rejected (`p ≥ .01`) | Report RMST/curve; `t½` exploratory |

## 10. Budget and compute

35–45 GPU-hours on a single 24 GB rental at $0.30–0.50/h ($15–22), storage/egress $2–3,
contingency $3–5; **$23 base / $50 hard cap**. No paid API, no second GPU, no paid annotation.
Local CPU 20–30 hours for harvest, replay, analysis, and writing.

## 11. Deviations, reporting, and availability

- Any post-freeze change is recorded in `AMENDMENTS.md` before the affected analysis, with the
  trigger, the change, the analyses affected, and whether it was made blind to target outcomes.
- Every gate outcome, including failures, is reported. A null result is reported as a null
  result, not reframed as a positive law.
- The CTO-800 release contains scrubbed derived data, manifests, and traces; raw τ-bench data and
  PII are not released.
- Code and analysis scripts are released under MIT; documentation and derived data under
  CC BY 4.0; upstream τ-bench remains MIT.

## Sign-off

| Role | Name | Date | Signature |
|---|---|---|---|
| Principal investigator | TBD | TBD | TBD |
| Analysis owner | TBD | TBD | TBD |
| Data owner | TBD | TBD | TBD |

_Freeze record: commit SHA and SHA-256 of this file are written to
`data/manifests/cto800_v1.json` at G0._
