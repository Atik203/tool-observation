# Implementation plan — CTO-800 / tool-observation

**Version:** 0.1.0 (scaffold), 2026-11-09.
**Study:** Tool-Observation Sensitivity in Language-Model Agents: A Fixed-Prefix Causal Study (E2).
**Status:** pre-confirmatory. No gate has been run. This plan is the execution reference for
P0–P5 and is subordinate to the preregistration once frozen.

---

## 1. Objective and claim boundary

The study asks a narrow causal question: **conditional on a real tool observation inside a frozen
prefix, does changing the observation's content change the agent's next decision, and is the
change ordered by a pre-specified severity level?** It also asks how quickly the agent returns to
the verbatim-observation decision, or explicitly flags the observation, over four subsequent
steps.

The unit is a frozen message prefix ending immediately after a real τ-bench tool output. The
target model produces the next decision. Because every arm shares the same prefix, the contrast
is within-prefix and does not depend on between-task differences in difficulty, domain, or donor
style.

The claim, if all gates pass, is bounded: three open-weight 7–8B model families, τ-bench airline
and retail, one deterministic prose renderer, four severity levels, four recovery steps. The study
does **not** claim a universal constant, a model ranking, frontier-model behavior, end-to-end task
success, or live-API external validity. A null result is a legitimate outcome and will be reported
as a measurement result.

The pilot is disclosed but not used as evidence for the confirmatory claim: N=60, qwen3.5:4b,
synthetic prefixes, consult 54/60, placebo jitter 0/60, error switch 5/60 = 8.3% [1.3, 15.3] pp,
McNemar p=.0625. It is a screening signal, not a dose-response law.

---

## 2. Repository and data layout

The repository is `Atik203/tool-observation`; the dataset brand is **CTO-800**. The package is
`toolobs`, laid out under `src/toolobs/` with subpackages `taubench`, `harvest`, `render`,
`infer`, `code`, `analysis`, and `release`.

```
configs/        base, models, harvest, arms, field_registry, calibration, main, analysis
scripts/        00_pin_source … 10_release (stage entry points)
src/toolobs/    library code; stdlib-only import surface
tests/          smoke tests; fixtures will be synthetic and tiny
data/raw/       downloaded upstream, gitignored
data/upstream/  pinned τ-bench checkout and task DBs, gitignored
data/interim/   candidates, scrubbed, eligible, replay tables, gitignored
data/frozen/    frozen prefix payloads, gitignored
data/manifests/ small non-PII manifests, hashes, freeze records — tracked
data/runs/      calibration and main ledgers/traces, gitignored
artifacts/      audit, analysis, env, cost, paper outputs — gitignored except README/.gitkeep
docs/           protocol, gates, rubric, data card, runbook, decisions, this plan
prereg/         preregistration and amendments log
paper/          manuscript source
release/        CTO-800 packaging checklist
```

Only `data/manifests/` and placeholder `.gitkeep` files are tracked under `data/`. Raw
trajectories, model weights, caches, credentials, and run outputs never enter git. The release
package is built from local files after a PII re-scan, not from the working tree.

Manifests are the reproducibility spine. `data/manifests/cto800_v1.json` will record prefix IDs,
message hashes, observation hashes, arm assignments, perturbation-record hashes, renderer
version, field-registry hash, and the preregistration hash. Every analysis table must be
traceable to a manifest row and a ledger row.

---

## 3. Environment and rental contract

Local work uses Python 3.12 at `C:\ProgramData\anaconda3\python.exe`, the `tool-observation`
conda environment, and an RTX 3060 6 GB. The 3060 is for imports, smoke tests, renderer checks,
and tiny forward passes only. It cannot host a 7–8B AWQ model with an 8k context at the batch
sizes the study needs.

The main run uses one 24 GB RTX 3090/4090 community instance at $0.30–0.50/h, with vLLM, AWQ
4-bit, batch 8–16, 8–12k context, greedy decoding, and one model loaded at a time. The rental
contract is defined by these requirements:

- 24 GB VRAM minimum, 32 GB system RAM recommended, 60 GB disk for weights plus traces.
- CUDA/driver compatible with the vLLM and torch wheels recorded in
  `artifacts/env/rental_env.txt`.
- Stable SSH or job API, resumable uploads, and a spend dashboard.
- The three model revisions are pinned in `data/manifests/model_pins.json` before G1.
- No paid API, no second GPU, no autoscaling, no managed inference endpoint.
- Hard stop at **$22 spend or 45 GPU-hours**, whichever comes first. Base budget is **$23**;
  hard cap **$50**. Reaching the cap is a G2 stop, not permission to continue.

Lock files are placeholders in the scaffold. CPU and GPU locks are generated on the target
machine and committed with the driver, CUDA, and vLLM versions recorded. A lock from a different
CUDA host is not accepted.

---

## 4. G0 — harvest and freeze (CPU, 2 days, $0)

G0 is the only stage that can invalidate the study before GPU spend. The empirical supply is
already measured: 1,980 public trajectories, 13,605 post-tool candidates, 11,318 JSON-parseable,
and **6,554 eligible value-used observations** across 165 task–domain pairs (airline 1,593;
retail 4,961). Eligible per task: min 7, median 38, max 121; airline median 31. A cap of 10/task
yields 1,646, so 800 is feasible; the airline arm is the binding constraint (50 tasks × 10 = 500
maximum; 496 after the observed cap).

The protocol is:

1. **Pin.** Resolve the τ-bench commit, record the URL, license, and SHA-256 of
   `gpt-4o-airline.json`, `gpt-4o-retail.json`, `sonnet-35-new-airline.json`, and
   `sonnet-35-new-retail.json`. Retain the MIT notice.
2. **Parse.** For every assistant message immediately following a `tool` message, reconstruct
   the exact prefix (system policy, user turns, donor turns, prior tool calls/results). Record
   trajectory ID, task ID, trial, donor, domain, step index, tool name, raw observation, and the
   factual continuation.
3. **Scrub.** Exclude profile tools (`get_user_details`, 3,692 candidates). Replace names,
   emails, addresses, phones, and payment identifiers with stable synthetic tokens. Exclude a
   prefix if decision-relevant content is itself PII.
4. **Relevance.** Flatten scalar values from the observation and test which appear in the
   donor's factual continuation after normalization. Keep prefixes with at least one used field.
   This is the automatic criticality label used to build s=1 and s=2.
5. **Replay.** Load the task DB, execute the prefix's tool calls from the initial state, and
   compare the last observation to the historical one (hash plus normalized values). Keep only
   ≥98% matches. Replay is what makes the observation a real environment output and makes the
   four-step recovery continuation possible.
6. **Sample.** Cap 10/task, target 400 airline + 400 retail, stratify by domain, donor,
   step-index bucket, and tool family, seed 20261108. Select **880**: 800 primary plus 80 reserve.
7. **Perturb.** Build deterministic prose renderings and one perturbation record per prefix and
   arm. Verify s=0 preserves the full value set of V.
8. **Audit.** A human reads 40 random prefixes for eligibility, PII, relevance, and replay match.
   Pass at **≥36/40 (90%)**.
9. **Freeze.** Write `cto800_v1.json` with all hashes and the preregistration hash. No target
   output may have been generated before this point.

G0 passes only with **≥880 eligible**, **≥440 per domain pre-audit**, **≥400 per domain
post-audit**, **replay ≥98%**, and **audit ≥36/40**. Failures trigger the fallback to 500
prefixes / 2 models, or a stop.

---

## 5. G1 — calibration (GPU, ~3 hours)

Calibration uses 60 prefixes (30 per domain), five arms, three models: 900 generations. It is a
harness test, not a result. The purposes are parser stability, prompt-format acceptance, refusal
detection, jitter estimation, and a first look at whether s=3 is a ceiling.

Gates, per model:

- parse rate **≥95%**;
- placebo jitter (s=0 vs V) **≤20%**;
- s=3 switch rate **10–80%**;
- format refusal **<5%**.

A failure means fix the parser or prompt and rerun calibration. No main-run spend occurs before
G1 passes. Calibration prefixes are disjoint from the main 800 and stay out of the primary
analysis. The calibration ledger is retained and reported.

---

## 6. P2 — main run matrix

The main run is fully crossed: 800 prefixes × 5 arms × 3 models for the base matrix, plus
recovery and jitter.

| Component | Calculation | Generations |
|---|---:|---:|
| Base | 800 × 5 × 3 | 12,000 |
| Recovery, transient | 800 × 2 severities × 4 steps × 3 | 19,200 |
| Recovery, persistent | 200 × 1 severity × 4 steps × 3 | 2,400 |
| Jitter repeats | 80 × 5 × 3 | 1,200 |
| **Total** | | **34,800** |

The base matrix yields 12,000 decisions. Recovery is injected at s=2 and s=3 for every prefix
under the transient regime, with H=4 continuation steps; the persistent regime corrupts the same
field on 25% of prefixes (200) and requires the model to flag or work around it rather than
re-query for truth. Jitter repeats use 80 prefixes across all five arms to estimate decoding and
prompt-format noise, not to increase power.

Execution is sharded by model and domain. Each shard checkpoints every 40 prefixes and appends
one ledger row per generation: run ID, model, prefix, arm, step, prompt hash, output, parse
status, latency, cost, UTC timestamp. A parser-error rate above 5% in a shard fails fast rather
than burning budget. The runner is resumable after a rental interruption.

The main run stops at **$22** or **45 GPU-hours**, whichever comes first. If the stop lands
mid-envelope, the analysis uses completed shards and the paper discloses the shortfall. No second
rental is authorized.

---

## 7. Renderer and perturbation rules

All of s=0…3 use the same deterministic key–value/bullet template. V is the raw JSON observation
and is an anchor for format and jitter, excluded from the primary linear slope. No LLM-generated
text enters the manipulation. A renderer version hash is frozen at G0.

| Arm | Content | Role |
|---|---|---|
| V | exact real observation, raw JSON | format/jitter anchor |
| s=0 | faithful prose, all values preserved | placebo |
| s=1 | one non-critical field changed or omitted | negative control |
| s=2 | one critical field changed to a plausible wrong value | dose |
| s=3 | critical wrong value plus a second contradiction | dose |

Construction rules:

- **s=0 identity.** A script flattens the V value set and the s=0 value set and verifies
  equality. Any loss excludes the prefix.
- **s=1 validity.** The perturbed field must be absent from the donor's factual continuation.
  If a non-critical change moves the decision as much as s=2, the field was misclassified or the
  model is hypersensitive; both are audit findings.
- **s=2 plausibility.** The wrong value must be plausible for the entity and must change the
  correct action if trusted. Absurd values are rejected.
- **s=3 compound.** The critical error is combined with a second inconsistency (for example
  "cancelled" while seats are available, "non-refundable" inside the refund window, or a wrong
  entity/policy). It must be detectable by a careful reader; calibration checks that it is not a
  ceiling.
- **Records.** Every perturbation stores prefix ID, JSON path, true value, false value,
  criticality label, expected action change, and renderer version.
- **No PII perturbations.** Never perturb a field whose true value is an identifier.

Severity is ordinal, not interval. The linear slope is a summary; the s=2 vs s=3 contrast is
reported separately so the compound component is not hidden. A quadratic-term or categorical
linearity check is pre-registered.

---

## 8. Outcome coding

A decision signature is the tool name plus canonicalized JSON arguments, or the final answer's
decision-critical slots plus action verb. Canonicalization sorts keys, normalizes numbers, and
lower-cases entities. The verbatim V continuation is the reference.

- **Y (any sensitivity):** signature differs from V.
- **Y^U (silent propagation):** the false value of a decision-critical field appears in the
  decision-relevant content/args and there is no flag. Not scored for s=1, whose perturbed field
  is non-critical.
- **Y^F (detection):** explicit flag, doubt, "possible error", "inconsistent", "verify", or
  "cannot trust".
- **Y^A (action switch):** tool or args differ from V (re-call, re-query, abstain).
- **Decomposition:** Y = Y^A ∨ Y^F ∨ Y^U; silent propagation is Y^U with no Y^A and no Y^F.

Recovery uses the risk set of prefixes whose decision moved at the injected step (Y^U=1 or
Y^A=1) and did not flag there, separately for s=2 and s=3. Prefixes that flagged at injection are
coded h=0 for detection and are not at risk for later recovery. The episode continues for H=4
steps against the real environment. Recovery at h is the first step where the signature matches V
(R1: correct decision) or the model explicitly flags (R2: detection). Neither by H=4 is censored.

Automatic labels are primary. A 160-response, two-rater blind audit validates them: κ ≥ .80 for
the four-way label, silent-propagation PPV ≥ .90, parser failure <1%, seed-repeat stability
≥ .90. If κ < .70 after one rubric revision, the study downgrades to action-level Y^A only and
does not make the content-sensitivity claim.

---

## 9. Statistical analysis

The primary model is a conditional (fixed-effects) logistic regression stratified by prefix:

```
logit P(Y_{p,m,s}=1) = alpha_{p,m} + beta_m * s,   s = 0,1,2,3
```

β_m is the log-odds change per one-level increase in severity. The pooled model stratifies by
prefix × model and clusters by prefix. The fixed-sequence gate is: pooled β first, then per-model
β with Holm across three models, then descriptive silent propagation, then recovery, then
exploratory heterogeneity. No model ranking is a confirmatory claim.

The design assumes a 4% placebo switch rate and a random prefix intercept σ=1.0. At N=800 the
MDE is **0.203 logit/level per model (OR 1.22)** at 80% power and α=.05 two-sided; pooled MDE is
≤0.15. The pilot-implied b≈0.8 is about four times the MDE, so power is not the binding
constraint — construct validity is.

Linearity is tested with a quadratic term or categorical severity. If it rejects, tier-specific
ORs and the slope as a summary are reported, not a "law". Secondary outcomes are Y^U, Y^F, Y^A,
the s=3 vs s=1 McNemar contrast, task-specific slopes, and exploratory model × severity and task
× severity interactions.

Recovery is a discrete-time exponential survival model with interval censoring:
P(recover at h | not yet) = 1 − exp(−μ), t½ = ln2/μ, H=4. Kaplan–Meier and restricted mean
survival time (RMST) are reported regardless. A Weibull shape test (LRT, p<.01) checks the
exponential assumption. If shape ≠ 1 or fewer than 50% of the risk set recovers by H=4, t½ is
labeled exploratory and the curve/RMST is the result. With 160–240 s=3 switchers, the per-model
t½ CI is about ±16–20%, pooled ±9–11%; between-model and between-severity differences need
32–50%, so ranking is out of scope.

Bootstrapping uses 2,000 replicates clustered by prefix. Alpha is .05, two-sided. Analysis code is
frozen with the preregistration; post-freeze changes require an amendment.

---

## 10. Gates, stop rules, and deliverables

| Gate | Criteria | Fail action |
|---|---|---|
| G0 | ≥880 eligible; ≥440/domain pre-audit; ≥400/domain post-audit; replay ≥98%; audit ≥36/40 | 500/2-model fallback or stop |
| G1 | parse ≥95%; jitter ≤20%; s=3 switch 10–80%; refusal <5% | Fix and rerun; no main spend |
| G2 | Stop at $22 or 45 GPU-h | Analyze completed shards; disclose |
| G3 | Pooled β>0; positive in ≥2/3 models, same sign; α≥.75; κ≥.80 (or adjudicated ≥.70 with downgrade); recovery κ≥.75 | Null/measurement paper |
| G4 | ≥50% recovery events by H=4; Weibull shape not rejected | RMST/curve only; t½ exploratory |

Deliverables are CTO-800 (800 frozen prefixes plus perturbations and traces), frozen manifests,
raw run ledgers, a reproducibility package (environment, rental contract, scripts, analysis), the
preregistration and amendments, and a paper draft. If the slope is null, the dataset and the null
are still released.

Budget: 35–45 GPU-hours at $0.30–0.50/h = $15–22; storage/egress $2–3; contingency $3–5; **$23
base, $50 hard cap**. Local CPU work is 20–30 hours at $0. Annotation is ~200 team judgments at
$0 cash. No paid API.

Storage: ~60 GB total disk for three AWQ weights, caches, and traces. Raw traces stay local; the release contains
only scrubbed derived data. Checkpoints and model caches are deleted after the run once hashes
and ledgers are archived.

---

## 11. Risks

The dominant risks are construct validity and contamination, not prefix supply. τ-bench tasks are
public and may be memorized; the within-prefix perturbation is novel, but baseline reliance may be
inflated. Mitigations: verbatim-arm accuracy, s=0 jitter, an optional 120-prefix template-transfer
arm only if under budget, and explicit domain scope.

Donor-prefix off-policy is handled by fixing prefixes across arms and stratifying by donor.
Severity construct validity is handled by the s=1 negative control, three blind raters, α≥.75,
and the s=3 plausibility check. Model-format refusal is a G1 gate. Rental availability is handled
by early booking and the $0.89/h fallback at 30 GPU-hours with N=600 or no persistent arm. Replay
mismatch is handled by a ≥98% threshold and a mismatch taxonomy before sampling. PII is handled by
profile-tool exclusion, scrubbing, human audit, and a release re-scan. Recovery state drift is
handled by continuing with the real environment and logging state hashes and divergence. Budget
overrun is handled by the G2 stop. Analysis overreach is handled by the fixed sequence, the
preregistration, and labeling heterogeneity exploratory.

---

## 12. First sprint and definition of done

The first ten days are the G0 sprint: pin (day 1), parse (2), scrub (3), relevance (4), replay
harness (5), full replay (6), sample 880 (7), perturb/render (8), 40-item audit (9), freeze and
G0 report (10). Each day has an output and an acceptance check in `ROADMAP.md`.

A task is done only with code, a test, a docs update, and a ledger/manifest entry where
applicable. A gate is done when its report records pass or fail and the consequence. No number is
reported without a raw source. No post-freeze change is made without a prereg amendment logged
before the affected analysis.
