# Protocol — fixed-prefix observation sensitivity (CTO-800)

**Version:** 1.0-draft (pre-G0). Frozen at G0; amendments logged in `prereg/AMENDMENTS.md`.
**Study ID:** E2. **Dataset:** CTO-800. **Repository:** `Atik203/tool-observation`.

---

## 1. Research question and estimand

**Question.** Conditional on a real tool observation in a frozen agent prefix, does changing the
observation's content change the agent's next decision, and is the change ordered by the severity
of the content error? Secondarily, how many steps does the agent take to recover?

**Unit.** A message prefix ending immediately after a real τ-bench tool observation. The prefix
contains the system policy, user turns, donor assistant turns, and all prior tool calls/results.
The target model produces the next decision; it does not generate the prefix.

**Primary estimand.** For model *m*, the conditional-logistic slope β_m of a content-switch
indicator on severity *s* ∈ {0,1,2,3}, holding the prefix fixed:

```
logit P(Y_{p,m,s} = 1) = α_{p,m} + β_m s
```

The pooled β stratifies by prefix × model and clusters by prefix. The s=0 arm is the placebo;
the intercept absorbs format jitter. The verbatim JSON arm V is a separate anchor and is excluded
from the primary slope.

**Secondary estimands.** Silent propagation Y^U and its share of Y; detection Y^F; action switch
Y^A; the paired s=3 vs s=1 contrast; the recovery half-life under a discrete-time exponential
model for the transient s=3 injection; persistent-injection recovery as a secondary contrast.

**Claim boundary.** Bounded to three open-weight 7–8B families, τ-bench airline and retail, one
frozen renderer, and the pre-specified severity rubric. No universal law, model ranking, frontier
transfer, end-to-end success, or live-API claim.

---

## 2. Sample and design

| Element | Value |
|---|---|
| Primary sample | 800 prefixes: 400 airline + 400 retail |
| Reserve | 80 prefixes, held out of the primary analysis |
| Selection | Harvest 880, freeze 800 before any target-model outcome |
| Cap | 10 prefixes per task–domain |
| Strata | domain, donor, step-index bucket, tool family |
| Seed | 20261108 |
| Arms | V, s=0, s=1, s=2, s=3 |
| Pairing | All arms generated from the same frozen prefix |
| Models | Qwen2.5-7B-Instruct-AWQ, Mistral-7B-Instruct-v0.3-AWQ, Llama-3.1-8B-Instruct-AWQ |
| Decoding | greedy, T=0, fixed seed, one model at a time |
| Recovery | H=4 steps; transient primary, persistent on 25% |

Donors are the public gpt-4o and claude-3.5-sonnet τ-bench historical trajectories. The target
models are open-weight 7–8B models and never generate the prefix, which avoids donor–target
circularity.

The airline arm is the binding supply constraint. The eligible pool is 6,554 value-used
observations across 165 task–domain pairs (airline 1,593; retail 4,961). A 10/task cap yields
1,646; airline has 50 tasks × 10 = 500 maximum (496 observed after the cap), enough for 400 plus
attrition.

---

## 3. Arms and rendering

All of s=0…3 use the same deterministic key–value/bullet template. V is raw JSON. No LLM
paraphrase enters the manipulation.

| Arm | Observation | Role |
|---|---|---|
| V | exact real tool output, raw JSON | format/jitter anchor; secondary total effect |
| s=0 | faithful prose, all values preserved | placebo; intercept/jitter |
| s=1 | one non-critical field changed or omitted | negative control |
| s=2 | one decision-critical field changed to a plausible wrong value | dose |
| s=3 | critical wrong value plus a second contradiction | dose |

**s=0 identity.** The s=0 value set must equal the V value set. A script verifies this; any
information loss excludes the prefix.

**s=1.** The field must not appear in the donor's factual continuation. If a non-critical change
moves decisions as much as s=2, the field was misclassified or the model is hypersensitive; both
are audit findings.

**s=2.** The wrong value must be plausible and must change the correct action if trusted.

**s=3.** A critical error plus a second inconsistency (for example "cancelled" while seats are
available; "non-refundable" inside the refund window; a wrong entity or policy). It must be
detectable by a careful reader; calibration checks it is not a ceiling.

**Severity is ordinal, not interval.** s=3 is intentionally compound. The linear slope is a
summary; the s=2 vs s=3 contrast is reported separately. A quadratic-term or categorical
linearity check is pre-registered.

**Perturbation records** store prefix ID, JSON path, true value, false value, criticality,
expected action change, and renderer version. Perturbing PII is prohibited.

---

## 4. Outcomes

A **decision signature** is tool name + canonicalized JSON args, or the final answer's
decision-critical slots + action verb. Canonicalization: sorted keys, numeric normalization,
lower-cased entities. The reference is the verbatim V continuation.

- **Y:** signature differs from V.
- **Y^U (silent propagation):** the false value of a decision-critical field appears in the
  decision-relevant content/args and there is no flag. Not scored for s=1.
- **Y^F (detection):** explicit flag, doubt, "possible error", "inconsistent", "verify", or
  "cannot trust".
- **Y^A (action switch):** tool/args differ from V.
- **Decomposition:** Y = Y^A ∨ Y^F ∨ Y^U; silent propagation = Y^U and not Y^A and not Y^F.

Labels are produced automatically from the perturbation record and the signature, then validated
by a blind human audit. The audit sample is 160 responses, stratified 3 models × 4 levels
(≈13/cell), with 2 raters blind to arm. Pass: Cohen's κ ≥ .80 for the 4-way label, silent-PPV
≥ .90, parser failure <1%, 10% seed-repeat stability ≥ .90. If κ < .70 after one revision,
downgrade to action-level Y^A only.

---

## 5. Recovery

The risk set for R1/R2 is prefixes whose decision moved at the injected step (Y^U=1 or Y^A=1) and
did not flag there, separately for s=2 and s=3. Prefixes that flagged at injection are coded h=0
for detection and are not at risk for later recovery.

Continue the episode for H=4 steps with the real environment. Recovery at h is the first step
where the signature matches V (R1: correct decision) or the model explicitly flags (R2:
detection). Censor at H=4 if neither occurs.

- Primary: R1 under transient injection at s=3.
- Secondary: R2, persistent, s=2.
- Persistent injection corrupts the same field on 25% of prefixes; recovery requires flagging or
  working around, not just re-querying.

Model: P(recover at h | not yet) = 1 − exp(−μ); t½ = ln2/μ. Report Kaplan–Meier and RMST
regardless. Weibull shape LRT at p<.01. t½ is identifiable only if ≥50% of the risk set recovers
by H=4; otherwise report a lower bound/curve and label t½ exploratory.

---

## 6. Models and analysis

Primary: conditional logistic, stratified by prefix, cluster-robust SE by prefix, fit separately
per model and pooled.

Fixed sequence:

1. Pooled β > 0 (primary confirmatory).
2. Per-model β_m > 0, Holm across three.
3. Silent propagation Y^U > 0 and share of Y (descriptive).
4. Recovery t½ with CI (estimation, not a significance gate).
5. Model/task heterogeneity (exploratory).

Linearity: quadratic term or categorical severity; if rejected, report tier ORs and treat the
slope as a summary. Sensitivity: exclude the placebo (s=1…3), per-domain, per-donor.

Multiplicity: fixed sequence then Holm for the three model slopes. No post-hoc model ranking.

---

## 7. Missing data and exclusions

- A prefix with an unreplayable observation is excluded before freeze.
- A generation with a parser failure is retained in the ledger and reported; it is not silently
  dropped. Parser failure >5% in a shard fails fast.
- A model that refuses the format at G1 is fixed or excluded before the main run; the exclusion
  is reported.
- Missing arms are not imputed. The primary analysis is complete-case within prefix; the
  missingness rate is reported.
- Post-freeze exclusions require a prereg amendment.

---

## 8. Blinding and annotation

Two blind co-authors handle the 160 outcome items plus 40 severity items (≈200 judgments; about
8.3 hours of team time, $0 cash). Raters are blind to arm labels. The second rater sees only the
response and the rubric, not the perturbation record. A third co-author adjudicates
disagreements. Severity audit: 120 observations, 30 per level, 3 raters, α ≥ .75; mean severity
monotone (Jonckheere–Terpstra p<.01); ≥90% of s=1 rated non-decision-changing; ≥90% of s=2/s=3
rated decision-changing; s=3 not "absurd" by >20%.

Recovery audit: 80 sequences (40 R1, 40 R2/censored), 2 raters, 3-way label, κ ≥ .75.

---

## 9. Deviations

Any deviation from this protocol is written to `docs/DECISIONS.md` and
`prereg/AMENDMENTS.md` before the affected analysis. The amendment states the trigger, the
change, the analyses affected, and whether it was made blind to target outcomes. Deviations are
reported in the paper. No frozen artifact is edited after G0.
