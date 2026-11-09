# Tool-Observation Sensitivity in Language-Model Agents

## A Fixed-Prefix Causal Study — Supervisor Proposal

**Prepared for:** Project supervisor  
**Date:** 2026-11-09  
**Version:** 0.1  
**Repository:** <https://github.com/Atik203/tool-observation>  
**Status:** Scaffold complete (v0.1.0). No confirmatory data collected; G0 not started. The only empirical evidence is a 60-prefix pilot, reported in Appendix A as a screening signal, not a dose-response result.

---

## 1. Executive summary

An LLM agent calls a tool, reads the observation, and decides what to do next. If the observation is wrong, the agent may copy the error into its answer. End-to-end benchmarks score the whole episode, so a fluent transcript can hide that failure.

This study isolates the moment after the observation. We freeze a real τ-bench conversation immediately after a real tool output, keep the prefix identical, and vary only the observation's content across five arms. Each prefix is its own control. We then follow the episode for four steps to estimate recovery.

The sample is **800 real τ-bench prefixes** (400 airline, 400 retail), plus 80 reserve, tested on three open-weight 7–8B model families with greedy decoding. The main run is 34,800 generations on one 24 GB GPU. The primary analysis is a conditional logistic regression (a within-prefix comparison) of a decision switch on severity, with prefix fixed effects and standard errors clustered by prefix. Recovery uses a discrete-time survival model, an exponential half-life, a Weibull shape check, and an RMST fallback (average recovery time).

The study is pre-registered and gated (G0–G4); a null is a measurement result.

**Why approve it.** The question is narrow, the design is paired, the supply is measured, the cost is small, and a negative result is publishable.

**Deliverables and cost.** CTO-800, manifests, ledgers, a reproducibility package, a pre-registration, and a paper draft. The run is 35–45 GPU-hours ($15–22), plus $2–3 storage and $3–5 contingency: **$23 base / $50 hard cap**; 20–30 CPU hours; 18 weeks part-time.

**Decision requested.** Approve G0 now (CPU only, $0, ten working days) and the staged budget. GPU spend is released only after G0 and G1 pass.

---

## 2. The problem in plain language

An **LLM agent** is a language model in a loop: it reads context, acts, receives a result, and repeats. A **tool call** is a structured request to an external function. An **observation** is what the tool returns. A **prefix** is the frozen conversation up to and including that observation; the **next decision** is the next call or final answer.

If a support agent receives `refund_amount: 84.50` but the tool wrongly returns `48.50`, an agent that trusts it tells the customer $48.50. The episode may still be marked "completed." A wrong flight date or dose has the same shape; this study uses airline and retail.

End-to-end benchmarks mix tool selection, planning, observation interpretation, and environment noise into one score. Each episode usually contains one realisation, so there is no counterfactual, and no label for "repeated the wrong value without flagging it."

---

## 3. Why this matters

**Reliability.** Agents handle refunds, bookings, and support; builders need to know whether models notice conflicts or copy them.

**Safety.** Wrong amounts, dates, and identifiers can cause loss or unsafe actions.

**Evaluation blind spot.** Aggregate success cannot show whether an agent is sensitive to observation content; two agents with the same score can differ sharply.

**Deployment.** The result informs validation steps, second tool calls for critical fields, confidence flags, or human approval. A null result bounds how much content matters at a known precision.

**Research gap.** Prior tool benchmarks evaluate task completion or single-turn call accuracy; they do not freeze a real prefix, vary content by severity, and estimate the effect with recovery.

---

## 4. Research question and hypotheses

**Primary question.** Inside a frozen prefix, does changing a real observation's content change the agent's next decision, and is the change ordered by severity?

**Secondary questions.** When the decision changes, how often is the false value propagated silently rather than flagged or detected? Over four steps, how quickly does the agent recover under transient versus persistent injection?

Let `Y_{p,m,s} = 1` if the decision signature for prefix `p`, model `m`, and severity `s` differs from the verbatim-observation (V) continuation. The primary model is:

```text
logit P(Y_{p,m,s} = 1) = α_{p,m} + β_m · s,    s = 0, 1, 2, 3
```

`α_{p,m}` is a prefix-by-model intercept; `β_m` is the log-odds change per severity level. The pooled model stratifies by prefix × model and clusters by prefix. V is excluded from the slope.

| ID | Hypothesis | Type |
|---|---|---|
| **H1** | Pooled slope of a decision switch on severity is positive: `β > 0`. | Primary confirmatory |
| **H2** | Per-model slope is positive in at least two of three models, same sign. | Confirmatory replication |
| **H3** | Silent propagation (`Y^U`) is a non-zero share of changes at `s=2` and `s=3`. | Secondary |
| **H4** | ≥50% of the `s=3` risk set recovers by `H=4`; Weibull shape not rejected at `p < .01`. | Confirmatory estimation |
| **H5** | The `s=3` switch rate exceeds the `s=1` rate. | Secondary |
| **H6–H7** | Donor/task consistency and model/task interactions. | Exploratory, underpowered |

H1 is primary; H2 is replication, not ranking; H4 is estimation, so failure means reporting the curve and RMST.

---

## 5. What is new

The novelty is a **design combination**, not the bare idea of injecting errors into tool outputs.

1. **Fixed-prefix content manipulation.** Every arm starts from the same frozen prefix; only content changes. Task difficulty, donor style, domain, and history cancel out.
2. **Five arms.** V is the exact observation in raw JSON; s=0 is faithful prose; s=1 changes one non-critical field; s=2 changes one critical field to a plausible wrong value; s=3 adds a second contradiction. All s=0…3 use the same prose template.
3. **Paired design.** The same 800 prefixes are crossed with three model families and two domains.
4. **CTO-800.** A frozen dataset with hashes, perturbation records, arm assignments, renderer version, decision signatures, and recovery traces.

| Work | What it does | What it does not do |
|---|---|---|
| **τ-bench** (2024) | Simulated-user tool benchmark for airline and retail. | One realisation per step; no counterfactual branches; scores episodes. |
| **ToolBench / ToolLLM** (2023–24) | Tool-use trajectories and training. | No replay arms or content manipulation. |
| **BFCL v1–v3** (2024–25) | Single-turn function-call accuracy. | No multi-step replay or perturbation. |
| **MINT** (2023–24) | Multi-turn tasks with tool feedback. | Feedback is never counterfactually varied. |
| **WebArena** (2023) | Live web-task benchmark. | No observation control or paired branches. |
| **ToolEmu** (2023–24) | Emulated tool-use safety analysis. | Single realisation; no paired branches. |
| **Stanford CS224R, Targeted Counterfactual Branching** (2026) | Branches at tool-invocation points for RLOO training. | Different estimand: policy-gradient variance, not a dose-response or half-life. |

A kill-test recheck found no shipped fixed-prefix observation-branch dataset; if one appears, novelty is revisited. We do not claim priority on perturbing tool outputs.

---

## 6. How the study works, step by step

| # | Stage | What happens |
|---:|---|---|
| 1 | **Harvest** | Pin τ-bench; parse post-tool prefixes; reconstruct continuation; hashes match. |
| 2 | **PII scrub** | Exclude profile tools; tokenise identifiers (personally identifiable information); zero raw emails/phones. |
| 3 | **Relevance** | Keep observations with a value used in the donor continuation; ≥6,500 pool. |
| 4 | **Replay** | Execute calls against the task DB; ≥98% match. |
| 5 | **Sample/freeze** | 10/task cap; 880 = 800 + 80 reserve; seed 20261108; 400/400 split. |
| 6 | **Render** | Deterministic prose; verify s=0 value set equals V; 100% equality. |
| 7 | **Query** | Greedy; 3 models × 5 arms; ledger every generation; 12,000 base. |
| 8 | **Code** | Signature vs V; assign Y, Y^U, Y^F, Y^A; 160-item audit. |
| 9 | **Recover** | H=4; transient primary, persistent 25%; code R1/R2; censor at 4. |
| 10 | **Analyse** | Conditional logistic; survival; sensitivity; G3/G4. |

```text
pin → parse → scrub → relevance → replay → sample/freeze
    → render → query → code → recover → analyse
```

Replay must reach ≥98% before sampling; nothing is generated before the freeze.

### Worked example: one retail prefix across five arms

This is an **illustrative construction, not a harvested record**. The user asks to return headphones from order W1842. The donor calls `get_order_details({"order_id": "W1842"})` and receives:

```json
{"order_id": "W1842", "status": "delivered", "delivered_days_ago": 3,
 "return_window_days": 30, "return_window_open": true,
 "refund_amount": 84.50, "product_rating": 4.4}
```

The reference continuation is `initiate_return({"order_id": "W1842", "reason": "changed_mind"})` plus an answer whose refund slot is $84.50. Every arm uses the same bullet template for the order, status, days since delivery, return window, refund amount, and rating.

| Arm | Level | What changes | Expected response |
|---|---:|---|---|
| **V** | anchor | Nothing; raw JSON. | Same decision as the donor continuation. |
| **s=0** | 0 | Nothing; all values preserved. | Same decision; any difference is format jitter. |
| **s=1** | 1 | `product_rating` 4.4 → 4.1. Not used in the continuation. | Same decision; a change suggests a misclassified field or hypersensitivity. |
| **s=2** | 2 | `refund_amount` $84.50 → $48.50. Plausible but wrong. | Flag or verify; if the answer says $48.50, that is silent propagation. |
| **s=3** | 3 | Refund $48.50 plus `return_window_open: false`, although delivered 3 days ago and the policy allows 30 days. | Detect the contradiction and flag/verify. |

Under s=2, if the model calls `initiate_return` with the same arguments but answers "$48.50", the refund slot differs from V: `Y=1`, `Y^A=0`, `Y^F=0`, `Y^U=1`. Under s=3, "the return window says closed but the item arrived three days ago; let me verify" is `Y^F=1`, possibly with `Y^A=1`.

---

## 7. Dataset: CTO-800

The source is the public **τ-bench** historical trajectories (MIT): gpt-4o airline, gpt-4o retail, sonnet-35-new airline, sonnet-35-new retail. The supply analysis measured 1,980 trajectories and 13,605 post-tool candidates. After excluding profile tools, keeping JSON-parseable observations, and requiring a value used in the donor continuation, **6,554 eligible observations** remain across 165 task–domain pairs.

| Stage | Count |
|---|---:|
| Source trajectories | 1,980 |
| Post-tool candidates | 13,605 |
| JSON-parseable | 11,318 |
| Profile-tool candidates excluded | 3,692 |
| Eligible value-used observations | 6,554 |
| — airline / retail | 1,593 / 4,961 |
| Task–domain pairs | 165 |
| Capped at 10 per task–domain | 1,646 |
| Selected (primary + reserve) | 880 |
| Primary | 800 (400 airline, 400 retail) |
| Reserve | 80 (40 airline, 40 retail) |

**Inclusion.** A real tool message, a reconstructable prefix, a scalar used in the donor continuation, PII-scrubbed content, replay ≥98%, and lossless s=0 rendering. **Excluded:** profile-tool observations, no used field, irreproducible observations, decision-critical PII, s=0 information loss.

**PII.** Raw trajectories may contain names, emails, addresses, phones, and payment identifiers, and are treated as PII-bearing. Direct identifiers become stable synthetic tokens; profile tools are excluded; a prefix is excluded if decision-relevant content is PII. A 40-item audit runs before freeze.

**Replay.** The harness executes the prefix's tool calls against the task database from the initial state and compares the final observation. The 98% threshold is not relaxed; replay makes the observation a real environment output.

**Storage and licence.** The project lives on `G:\PROJECT\tool-observation`. Raw data, upstream checkouts, interim files, frozen payloads, weights, caches, and run logs are local-only and gitignored; only small, non-PII manifests under `data/manifests/` are tracked. Code is MIT; documentation and CTO-800 additions are CC BY 4.0; upstream τ-bench remains MIT. The public release contains scrubbed derived data only; raw trajectories, weights, and run logs are never released.

---

## 8. Models and serving

| Model | Parameters | Licence | Role |
|---|---:|---|---|
| Qwen2.5-7B-Instruct-AWQ | 7B | Apache 2.0 | Primary family |
| Mistral-7B-Instruct-v0.3-AWQ | 7B | Apache 2.0 | Second family |
| Llama-3.1-8B-Instruct-AWQ | 8B | Llama 3.1 Community | Third family |

If Llama-3.1 access fails, the pre-registered substitutes are InternLM2.5-7B-Chat or Yi-1.5-9B-Chat, logged before calibration and never chosen after seeing outcomes.

Serving uses **vLLM** (an inference server), **AWQ 4-bit** weights (compression that fits a 7–8B model on 24 GB), and **greedy decoding** (always pick the most likely next token). Batch 8–16, 8–12k context, fixed seed, pinned revisions. The local RTX 3060 (6 GB) is only for smoke tests, renderer checks, and tiny forward passes. The models are open-weight, reproducible, fit one 24 GB rental, and come from distinct families; the design tests whether a result is family-specific.

---

## 9. Outcomes and measurement

A **decision signature** is the tool name plus canonicalised JSON arguments, or the final answer's action verb plus decision-critical slots.

| Term | Definition |
|---|---|
| **Y** | Any sensitivity: signature differs from V. |
| **Y^U** | Silent propagation: the false critical value appears in decision content, with no flag; not scored for s=1. |
| **Y^F** | Detection: explicit flag, doubt, "inconsistent", "verify", or "cannot trust". |
| **Y^A** | Action switch: tool or arguments differ from V. |
| **Y = Y^A ∨ Y^F ∨ Y^U** | Every change is an action switch, detection, or silent propagation; strict silent = `Y^U ∧ ¬Y^A ∧ ¬Y^F`. |
| **R1** | Correct decision: signature first matches V at `h ≤ 4`. |
| **R2** | Detection: explicit flag at `h ≤ 4` without a signature match. |
| **Censored** | Neither R1 nor R2 by H=4. |

A **critical field** determines which next action is correct: reservation status, flight number, origin/destination, departure time, cabin, refundability, price, order status, product ID, stock, return-window state, or refund amount. A **non-critical field** is not used in the donor continuation: aircraft type, gate, notes, carrier, description, rating, review count, or return-reason code. PII fields are never perturbed.

| Arm | Level | Construction | Role |
|---|---:|---|---|
| V | anchor | Exact real observation, raw JSON. | Format/jitter anchor; excluded from the primary slope. |
| s=0 | 0 | Faithful prose; all values preserved. | Placebo. |
| s=1 | 1 | One non-critical field changed or omitted. | Negative control. |
| s=2 | 2 | One critical field changed to a plausible wrong value. | Dose. |
| s=3 | 3 | Critical wrong value plus a second detectable contradiction. | Dose, compound. |

Severity is ordinal; the s=2 versus s=3 contrast is always reported separately.

---

## 10. Analysis plan

The primary analysis is a **conditional (fixed-effects) logistic regression**, stratified by prefix. Each prefix gets its own intercept, so the slope is identified from within-prefix severity changes; between-prefix differences cancel out. Standard errors cluster by prefix. The pooled model stratifies by prefix × model.

Fixed sequence: pooled β; per-model β with Holm across three models; descriptive silent propagation; recovery; exploratory heterogeneity. A quadratic term and categorical-severity LRT check linearity; if rejected, report tier odds ratios and treat the slope as a summary.

**Secondary outcomes.** `Y^U` and its share of `Y`; `Y^F`; `Y^A`; the paired s=3 versus s=1 McNemar contrast; per-domain and per-donor slopes; transient versus persistent recovery.

**Recovery.** R1 under transient s=3 is primary. Discrete-time survival with interval censoring: `P(recover at h | not yet) = 1 − exp(−μ)`, so `t½ = ln2/μ` over H=4. Report Kaplan–Meier and RMST regardless; a Weibull shape LRT at p < .01 checks the exponential assumption. If shape rejects or fewer than 50% recover, `t½` is exploratory.

**Inference and sensitivity.** 2,000 prefix-clustered bootstrap replicates; α = .05, two-sided. Sensitivity: exclude the placebo and fit s=1…3; per domain; per donor; strict versus lenient coding; seed-repeat stability.

**Falsification / null result.** Pooled β ≤ 0.1 logit/level, negative β, positive in fewer than two of three models, opposite signs, placebo jitter >20%, s=3 switch >80% or <10%, or <50% recovery by H=4 is reported as a null/measurement result.

---

## 11. Power and sample size

The design assumes a 4% placebo switch rate, a random prefix intercept with standard deviation 1.0, a balanced design, α = .05 two-sided, and 80% power. The **minimum detectable effect (MDE)** is the smallest true slope detected with 80% probability.

At 400/500/600 prefixes the per-model MDE is 0.280/0.259/0.234; at **N=800** it is **0.203 logit/level (OR 1.22)**, and the pooled MDE is ≤0.15. At a true slope of 0.5, the per-model standard error is about 0.074, giving a 95% CI of roughly ±0.15. The pilot implies `b ≈ 0.8`, four times the MDE, but is not the effect-size estimate.

**Why 800.** It is feasible (12% of the eligible pool), gives 400 prefixes per domain, and leaves 80 for reserve and replacement.

**Recovery precision.** With a 20% s=3 switch rate, 160 switchers per model give a 95% CI on `t½` of about ±20% per model and ±11% pooled; at 30%, 240 switchers give about ±16% and ±9%.

| s=3 switch rate | Switchers/model | Per-model 95% CI | Pooled 95% CI |
|---:|---:|---:|---:|
| 15% | 120 | ±22.5% | — |
| 20% | 160 | ±19.8% | ±11.4% |
| 30% | 240 | ±15.7% | ±9.2% |

**Underpowered.** Between-model `t½` differences need 32–50% separation; model ranking is out of scope. Model × severity, task × severity, and adjacent-severity recovery differences are exploratory.

---

## 12. Human audits and quality control

Human labels validate, not replace, automatic coding. Raters are blind to arm labels. The second outcome rater sees only the response and the rubric, not the perturbation record. A third co-author adjudicates disagreements.

| Audit | Sample | Raters | Pass threshold | Failure handling |
|---|---|---:|---|---|
| **G0 eligibility/PII/replay** | 40 prefixes | 1 | ≥36/40 (90%) | Revise rules, replace from reserve, re-audit. |
| **Severity construct** | 120 observations (30/level) | 3 | Krippendorff α ≥ .75; Jonckheere–Terpstra p < .01; ≥90% s=1 non-decision-changing; ≥90% s=2/s=3 decision-changing; s=3 "absurd" ≤20% | Revise rubric or collapse levels; re-audit. |
| **Outcome labels** | 160 responses (3 models × 4 levels) | 2 | Cohen κ ≥ .80; silent PPV ≥ .90; parser failure <1%; seed-repeat stability ≥ .90 | Revise once; if κ < .70, downgrade to action-level `Y^A` only. |
| **Recovery labels** | 80 sequences (40 R1, 40 R2/censored) | 2 | Cohen κ ≥ .75 | Revise rubric; re-audit. |

If outcome κ falls between .70 and .80 after one revision, adjudicated labels are primary on the audit subsample and both analyses are reported. Below .70, the study drops the content-sensitivity claim.

Calibration (G1) is a harness check: parse ≥95%, placebo jitter ≤20%, s=3 switch 10–80%, format refusal <5% per model. Failure: fix and rerun; no main spend.

---

## 13. Expected results, contributions, and limitations

The study is designed to estimate, not to confirm the pilot. If the direction survives real prefixes, the paper reports a positive graded slope, a meaningful silent-propagation share, and a recovery curve with a pooled half-life where identifiable. If the slope is flat or negative, it reports a null/measurement result at a known precision.

| Contribution | What it is |
|---|---|
| **Dataset** | CTO-800: 800 frozen real prefixes, five arms, perturbation records, renderer hash, decision signatures, recovery traces, data card. |
| **Empirical result** | A within-prefix causal estimate of content sensitivity, graded by severity, plus a four-step recovery estimate across three families and two domains. |
| **Methods** | A reusable fixed-prefix protocol, deterministic renderer, perturbation schema, and recovery-coding scheme. |
| **Null-result value** | A well-powered flat slope bounds how much observation content matters; the dataset still enables replication. |
| **Paper target** | An empirical NLP or agent-evaluation venue, selected after G3/G4 because the claim's strength depends on the gates. |

The claim is bounded: three open-weight 7–8B families, τ-bench airline and retail, one renderer, four severity levels, four recovery steps. It is not a universal law, model ranking, frontier result, or end-to-end success claim.

---

## 14. Feasibility: team, timeline, compute, budget

| Role | Main responsibilities |
|---|---|
| **PI / research lead** | Design, pre-registration, gates, paper, supervisor communication. |
| **Harvest and data lead** | Pin, parse, PII scrub, relevance, replay, sampling, freeze, data card. |
| **Inference lead** | Rental, vLLM/AWQ, calibration, main run, ledger, cost stop. |
| **Analysis and release lead** | Coding, audits, slope/survival models, figures, CTO-800 packaging. |

With three people, the PI absorbs paper/release work and the analysis lead keeps the statistics; harvest and inference stay separate because they are schedule-critical.

| Phase | Weeks | Gate |
|---|---:|---|
| **P0 — Harvest and freeze** | 1–2 | G0 |
| **P1 — Calibration** | 3 | G1 |
| **P2 — Main run** | 4–7 | G2 |
| **P3 — Labels and analysis** | 6–10 | G3/G4 |
| **P4 — Paper** | 9–14 | Internal review |
| **P5 — Release** | 15–18 | Release checklist |

P0 harvests, replays, samples, and freezes. P1 runs 60 prefixes × 5 arms × 3 models. P2 runs the 34,800-generation envelope (12,000 base + 19,200 transient recovery + 2,400 persistent + 1,200 jitter). P3 runs the 120/160/80 audits and models; P4 drafts the paper; P5 packages and releases CTO-800.

| Item | Specification | Cost |
|---|---|---:|
| GPU rental | 35–45 h on a 24 GB RTX 3090/4090, $0.30–0.50/h | **$15–22** |
| Storage / egress | ~60 GB weights, logs, traces | **$2–3** |
| Annotation | ~200 judgments by team members | **$0** |
| Contingency | GPU or storage overrun | **$3–5** |
| **Total** | $18 GPU + $2 storage + $3 contingency | **$23 base / $50 hard cap** |
| Local CPU | Harvest, replay, analysis, writing: 20–30 h | **$0** |
| Paid API | None | **$0** |

The rental needs 24 GB VRAM, 32 GB RAM, 60 GB disk, a compatible CUDA stack, SSH or job API, resumable uploads, and a spend dashboard. The run stops at **$22** or **45 GPU-hours**, whichever first; no second rental, no paid API. If a 24 GB instance is unavailable at ≤$0.50/h, the fallback is a $0.89/h secure 4090 at 30 GPU-hours with N=600 or no persistent arm.

---

## 15. Risks and mitigations

| Risk | Why it matters | Mitigation |
|---|---|---|
| **τ-bench contamination** | Public tasks may be memorised. | Report verbatim accuracy and s=0 jitter; within-prefix contrast remains valid; optional template-transfer arm. |
| **Donor-prefix off-policy** | Targets continue gpt-4o/sonnet histories. | Fix prefixes across arms; stratify by donor; report donor slopes; targets never generate prefixes. |
| **Severity construct validity** | If s=1 moves decisions like s=2, "dose" is not a dose. | Three-rater blind audit; α ≥ .75; s=1 negative control; s=3 plausibility check. |
| **Model-format refusal** | A model may refuse the format. | G1 refusal gate <5%; fix prompt/grammar; document exclusions. |
| **Rental availability** | 24 GB instances can be scarce. | Book early; $0.89/h fallback at 30 GPU-hours; reduce N or drop persistent. |
| **Replay mismatch** | A non-replayable observation is not real. | ≥98% match; mismatch taxonomy; fix harness before sampling. |
| **PII leakage** | Trajectories contain profile data. | Exclude profile tools; synthetic tokens; 40-item audit; re-scan; no raw data in git. |
| **Recovery state drift** | Four steps may diverge from the donor episode. | Continue with the real environment; log state hashes; report divergence. |
| **Budget overrun** | GPU rental is the only cash risk. | Hard stop at $22/45 h; per-shard ledger; no second rental. |
| **Analysis overreach** | Many contrasts invite post-hoc stories. | Fixed sequence; pre-registered primaries; heterogeneity exploratory. |

---

## 16. Ethics, privacy, licensing, and open science

**Privacy.** Raw τ-bench trajectories may contain names, emails, addresses, phones, and payment identifiers; they are treated as PII-bearing even before scrubbing. Profile tools are excluded, direct identifiers become stable synthetic tokens, and a prefix is excluded if decision-relevant content is PII. A 40-item audit runs before freeze and a re-scan before release. No raw trajectories, weights, credentials, or secrets enter the repository.

**Licensing.** Upstream τ-bench is MIT and its notice is preserved. Code is MIT. Documentation and CTO-800 additions are CC BY 4.0. Model outputs are released only as derived, scrubbed text and remain subject to each model's licence; no weights are redistributed.

**Open science.** The design, estimands, gates, rubric, and analysis plan are frozen at G0 and tagged `prereg-freeze-v1`. Any deviation is logged in `prereg/AMENDMENTS.md` and `docs/DECISIONS.md` before the affected analysis, with trigger, change, affected analyses, and blinding status. Every gate outcome, including failure, is reported. The release includes a data card, checksums, the pre-registration, and the amendments log. The frozen git tag is the record.

---

## 17. Deliverables and decision requested

**Deliverables.** (1) CTO-800, 800 frozen prefixes plus 80 reserve, with perturbations and recovery traces. (2) Frozen manifests and hashes. (3) One ledger row per generation. (4) A reproducibility package. (5) Pre-registration and amendments. (6) A paper draft with a bounded claim, pilot disclosure, result or null, limitations, and a data statement.

**Decision requested today.** Approve the **G0 start**: ten working days, CPU only, $0 cash. G0 pins τ-bench, builds the harvest and replay pipeline, scrubs PII, labels relevance, samples 880, freezes 800 + 80 reserve, runs the 40-item audit, and freezes the pre-registration. No target-model output is generated before the freeze.

**Budget release.** Approve **$23 base / $50 hard cap**. G0 costs $0. G1 costs about 3 GPU-hours (~$2) and runs only after G0 passes. The main run is released only after G1 passes and stops at $22 or 45 GPU-hours. The hard cap is a stop line, not a target.

**Resources requested.** One 24 GB GPU rental for 35–45 hours; ~60 GB storage; 3–4 team members for 18 weeks part-time; 20–30 local CPU hours; ~200 human judgments at $0 cash. No paid API, second GPU, or external annotator.

**Gate consequences.** G0 fail → 500-prefix/2-model fallback or stop; G1 fail → no main spend; G2 early stop → analyse completed shards; G3 fail → null/measurement paper or action-level downgrade; G4 fail → RMST/curve only.

---

## 18. Glossary

| Term | Definition |
|---|---|
| **Agent** | A language model in a loop that reads context, acts, and repeats. |
| **Tool call** | A structured request to an external function. |
| **Observation** | The content a tool returns. |
| **Prefix** | The frozen conversation up to and including the observation. |
| **Fixed-prefix design** | Every arm starts from the same prefix; only the manipulation differs. |
| **Arm** | One condition: V, s=0, s=1, s=2, or s=3. |
| **Severity** | Level of content error: none, non-critical, critical, critical plus contradiction. |
| **Dose-response** | A stronger error produces a larger change in a graded way. |
| **Silent propagation** | The agent uses a false value without flagging it or changing action. |
| **Recovery half-life (`t½`)** | Steps by which half the at-risk prefixes recover. |
| **Conditional logistic regression** | Regression comparing arms within a prefix, with a separate intercept per prefix. |
| **Clustering** | Treating observations from one prefix as correlated for standard errors. |
| **MDE** | Minimum detectable effect at the stated power. |
| **Krippendorff's α** | Agreement statistic for multiple raters. |
| **Cohen's κ** | Agreement statistic for two raters, corrected for chance. |
| **Placebo arm** | s=0; faithful prose that measures format jitter. |
| **Negative control** | s=1; a non-critical change that should not move the decision. |
| **RMST** | Restricted mean survival time within the four-step horizon. |
| **PII** | Personally identifiable information: names, emails, addresses, phones, payment IDs. |

---

## 19. References

Only works named in the source audit are listed. Author lists and venues will come from the pinned upstream bibliography, not guessed.

| Work | Year | Role in this proposal |
|---|---|---|
| **τ-bench** | 2024 | Source of the real airline and retail trajectories. Repository: <https://github.com/sierra-research/tau-bench>. |
| **ToolBench / ToolLLM** | 2023–24 | Closest tool-trajectory collection and training work; no paired observation branches. |
| **BFCL v1–v3** | 2024–25 | Single-turn function-call benchmark; no multi-step observation manipulation. |
| **MINT** | 2023–24 | Multi-turn tool feedback; feedback is not counterfactually varied. |
| **WebArena** | 2023 | Live web-task benchmark; no observation control. |
| **ToolEmu** | 2023–24 | Tool-use safety emulation; single realisation, no paired branches. |
| **Stanford CS224R, Targeted Counterfactual Branching** | 2026 | Adjacent branching method for RLOO training; different estimand. |

Internal resources: `README.md`, `ROADMAP.md`, `docs/PROTOCOL.md`, `docs/GATES.md`, `docs/LABEL_RUBRIC.md`, `docs/IMPLEMENTATION_PLAN.md`, `prereg/PREREGISTRATION.md`.

---

## Appendix A. Pilot evidence: what it does and does not establish

The pilot used **N=60 synthetic WebArena-lite / τ-style prefixes**, `qwen3.5:4b`, greedy decoding, and three collapsed action codes (trust / re-call / flag). It is a kill-gate, not an estimate of the confirmatory slope.

| Quantity | Pilot result | Reading |
|---|---:|---|
| Consult rate | 54/60 = 90.0% | Model engaged the decision point. |
| Placebo jitter (P vs T) | 0/60 = 0% | Optimistic floor; design assumes 4%, gates at 20%. |
| Error switch (E vs T) | 5/60 = 8.3% | Screening signal, not a dose estimate. |
| Gap, 95% CI | 8.3 pp [1.3, 15.3] | Compatible with a 1.3 pp effect. |
| McNemar | b=5, c=0; exact p=.0625 | b = error-only, c = placebo-only; marginal. |
| Human spot-check | 12/12 labels agree | 20% sample. |

**Establishes.** The manipulation is runnable, the model consults observations, placebo jitter was low, and error content can move the next action. The letter coding missed some silent propagation, so 8.3 pp is an action-level lower bound.

**Does not establish.** A dose-response slope, recovery, other models, real prefixes, or content-level sensitivity. It is marginal at p=.0625, is not pooled with the confirmatory data, and is not used to rescue a null confirmatory result.

---

## Appendix B. Ten-day G0 sprint and gates G0–G4

G0 is CPU-only, $0 cash, and runs before any rental spend.

| Day | Task | Check |
|---:|---|---|
| 1 | Pin τ-bench; record URL, licence, hashes; vendor harness. | Pin resolves; hashes match; MIT notice. |
| 2 | Parse post-tool decision points. | Required fields present. |
| 3 | PII scrub; exclude profile tools; tokenise identifiers. | Zero raw emails/phones. |
| 4 | Decision-relevance labelling. | ≥6,500 pool; airline ≥1,500. |
| 5 | Build replay harness; replay first 50. | Tool calls execute; taxonomy documented. |
| 6 | Full replay verification. | ≥98% match. |
| 7 | Stratified sample: 880 = 800 + 80 reserve. | 400/400 target. |
| 8 | Perturbations and renderer; verify s=0 identity. | 100% s=0 equality. |
| 9 | Human audit of 40 prefixes: eligibility, PII, relevance, replay. | ≥36/40. |
| 10 | Freeze manifest, G0 report, preregistration v1.0. | Hashes recorded; prereg locked. |

| Gate | Criteria | Fail action |
|---|---|---|
| **G0 — Harvest/freeze** | ≥880 eligible; ≥440/domain pre-audit; ≥400/domain post-audit; replay ≥98%; 40-item audit ≥36/40. | 500 prefixes / 2 models, or stop. |
| **G1 — Calibration** | Parse ≥95%; placebo jitter ≤20%; s=3 switch 10–80%; refusal <5% per model. | Fix and rerun; no main spend. |
| **G2 — Main run** | Stop at $22 or 45 GPU-hours; ledger complete. | Analyse completed shards; disclose. |
| **G3 — Analysis** | Pooled β > 0; positive in ≥2/3 models, same sign; severity α ≥ .75; outcome κ ≥ .80 (or adjudicated ≥ .70 with downgrade); recovery κ ≥ .75. | Null/measurement paper; no content claim. |
| **G4 — Recovery** | ≥50% of s=3 risk set recovers by H=4; Weibull shape not rejected (p ≥ .01). | RMST/curve; `t½` exploratory. |

---

## Appendix C. Repository map and scaffold checks

```text
configs/       8 YAML configs
src/toolobs/   package: harvest, render, infer, code, analysis, release
scripts/       00_pin_source … 10_release (stubs in v0.1.0)
tests/         2 stdlib-only smoke tests
docs/          protocol, gates, rubric, data card, runbook, decisions, plan, proposal
prereg/        pre-registration and amendments
data/          local-only raw/upstream/interim/frozen/runs; manifests tracked
artifacts/     local-only audit, analysis, cost, env, paper
```

From `G:\PROJECT\tool-observation`:

```powershell
C:\ProgramData\anaconda3\python.exe -m pytest -q          # 2 passed
$env:PYTHONPATH = "src"
C:\ProgramData\anaconda3\python.exe -m toolobs.cli validate  # 8/8 configs; OK
C:\ProgramData\anaconda3\python.exe -m toolobs.cli --version # toolobs 0.1.0
```

The package is not installed in the base environment; use `pip install -e . --no-deps` or `PYTHONPATH=src`. Pipeline scripts `00`–`10` are stubs that exit with code 2 and print their plan; they produce no data. CI installs with `--no-deps`, byte-compiles `src`, and runs `python -m pytest -q`.
