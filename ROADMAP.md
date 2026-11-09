# Roadmap — Tool-Observation Sensitivity (E2)

**Status:** pre-confirmatory scaffold, v0.1.0 (2026-11-09).
**Scope:** open-weight 7–8B models, τ-bench airline and retail, next-decision sensitivity, and
4-step recovery. Thirty-five to forty-five GPU-hours on a single 24 GB rental.
**Cash:** $23 base, $50 hard cap. No paid API, no second GPU.
**Planning horizon:** 18 weeks, part-time team of 3–4.

---

## 1. Claim boundary

### What we intend to claim, if every gate passes

A **bounded causal result**: within a frozen real τ-bench prefix, changing the content of the
tool observation changes the probability that an open-weight 7–8B agent's next decision departs
from its verbatim-observation continuation, and the change is ordered by the pre-specified
severity level. The study also estimates a pooled recovery half-life over four steps for a
transient injection, with a Weibull shape check. The result is conditional on three model
families, two τ-bench domains, and the exact renderer and perturbation rubric frozen at G0.

### What we will not claim

- A universal constant or "law" that holds for all models, tasks, or tool formats.
- A ranking of models by sensitivity or recovery speed. The design is not powered for that.
- Transfer to frontier or API models; we test open-weight 7–8B families only.
- An effect on end-to-end task success or on the extensive margin of tool use.
- External validity to live web/API tools. τ-bench observations are deterministic benchmark
  outputs, not live services.

### What would falsify the claim

Any one of the following converts the paper from a sensitivity result to a measurement or null
result:

1. Pooled slope **β ≤ 0.1 logit/level**, or a negative slope.
2. Placebo jitter **> 20%** (the s=0 arm is not stable).
3. s=3 switch rate **> 80%** (ceiling: everything moves, so severity is not graded) or **< 10%**
   (insensitivity).
4. Model slopes with **opposite signs**, or a positive slope in fewer than **2 of 3** models.
5. **No recovery** by H=4 in at least 50% of the s=3 risk set, or a Weibull shape clearly
   different from 1 (p < .01).
6. A **task × severity interaction that reverses sign** between airline and retail.
7. Severity labels fail the construct audit: s=1 (non-critical) moves decisions as much as s=2,
   or Krippendorff α < .75 after one rubric revision.

A flat or null result is still publishable as a measurement paper with the CTO-800 dataset. It
will not be reframed post hoc as a positive law.

---

## 2. Phase plan

| Phase | Weeks | Work | Exit gate | Main output |
|---|---:|---|---|---|
| **P0 — Harvest and freeze** | 1–2 | Pin τ-bench, parse, PII scrub, relevance labeling, replay, stratified sample, freeze 800 + 80 reserve, 40-item audit, preregistration | **G0** | `cto800_v1` frozen manifest, G0 report, prereg draft |
| **P1 — Calibration** | 3 | 60-prefix × 3-model calibration on the rental; parser and prompt-format fixes; refusal check | **G1** | Calibration ledger, pass/fail report, frozen prompt + parser version |
| **P2 — Main run** | 4–7 | 34,800-generation envelope: base, transient recovery, persistent recovery, jitter repeats; ledger every generation | **G2** | Raw continuations, recovery traces, run ledger, cost report |
| **P3 — Labels and analysis** | 6–10 | Human severity audit (120 items), outcome audit (160 items), recovery audit (80 sequences), automatic coding, slope and survival models | **G3 / G4** | κ/α report, slope table, recovery curves, analysis notebook |
| **P4 — Paper** | 9–14 | Draft, internal review, figures, limitations, reproducibility appendix | Internal review pass | Paper draft, figures, tables |
| **P5 — Release** | 15–18 | CTO-800 packaging, license audit, PII re-scan, DOI, repository release, artifact check | Release checklist | Public CTO-800 v1.0, tagged repo, DOI |

Phases overlap deliberately: P3 begins as soon as the first main-run shard lands, and P4 begins
when the primary slope is estimable, not when every exploratory analysis is finished.

### Contingency

| Trigger | Response |
|---|---|
| G0 eligible < 880, or < 440/domain before audit | Fallback to **500 prefixes / 2 models**; keep 400/100 domain split and drop the persistent arm first |
| G0 post-audit < 400/domain | Re-sample from reserve and the eligible pool; if still short, fall back as above |
| Replay match < 98% | Fix the replay harness before sampling; do not relax the threshold |
| G1 parse < 95% | Fix the parser and rerun calibration; no main spend |
| G1 placebo jitter > 20% | Fix prompt/decoding; if still high, stop and report a measurement failure |
| G1 s=3 switch > 80% | Reduce severity compounding; re-audit s=3 plausibility |
| Rental unavailable at ≤ $0.50/h | Use the $0.89/h secure 4090 cap at 30 GPU-hours, reduce N to 600 or drop persistent; still ≥ 500 prefixes |
| Main run reaches $22 or 45 GPU-hours | Stop immediately, analyze completed shards, disclose the shortfall |
| Outcome κ < .70 after one revision | Downgrade to action-level Y^A only; do not make the content-sensitivity claim |
| Recovery events < 50% by H=4 | Report RMST and the recovery curve; label t½ exploratory |
| Team capacity drops | Protect G0–G2 and the primary slope; cut the optional template-transfer arm and exploratory interactions |

---

## 3. Ten-day G0 sprint

G0 is CPU-only, $0 cash, and runs before any rental spend.

| Day | Task | Output | Acceptance check |
|---:|---|---|---|
| 1 | Pin τ-bench commit; record URL, license, SHA-256 of each trajectory file; vendor the tool/environment harness | `configs/harvest.yaml` pin filled; `data/upstream/PIN.json` | Pin resolves; four trajectory files hash-match; MIT notice retained |
| 2 | Parse all trajectories into candidate post-tool decision points | `data/interim/candidates.parquet` | Every candidate has trajectory ID, task ID, trial, donor, domain, step, tool, raw observation, factual continuation |
| 3 | PII scrub; exclude profile tools; tokenize names/emails/addresses/phones/payment IDs | `data/interim/scrubbed.parquet` + scrub report | 0 raw emails/phones in scan; excluded-tool count reported |
| 4 | Decision-relevance labeling: value-used proxy between observation scalars and donor continuation | `data/interim/eligible.parquet` | ≥ 6,500 eligible; airline ≥ 1,500; no prefix with zero used field |
| 5 | Build replay harness against task DB; replay first 50 prefixes | Replay report v0 | Tool-call replay executes; mismatch taxonomy documented |
| 6 | Full replay verification over eligible pool | `data/interim/replay.parquet` | ≥ 98% normalized match on retained prefixes |
| 7 | Stratified sample: cap 10/task, 880 selected, 800 primary + 80 reserve | `data/manifests/sample_880.json` | 400/400 domain target; donor and step strata reported |
| 8 | Build perturbation records and deterministic prose renderer; verify s=0 value-set identity with V | `data/manifests/perturbations.jsonl`, renderer hash | 100% s=0 value-set equality; every s=1/2/3 record has JSON path, true value, false value, criticality, expected action change |
| 9 | Human audit of 40 random prefixes (eligibility, PII, relevance, replay) | `artifacts/audit/g0_audit.csv` | **≥ 36/40 (90%)**; every failure categorized |
| 10 | Freeze manifest, write G0 report, finalize preregistration v1.0 | `data/manifests/cto800_v1.json`, `prereg/PREREGISTRATION.md`, G0 report | Hashes recorded; no target-model outcome seen; prereg locked |

**G0 freeze rule:** after day 10, `data/manifests/cto800_v1.json`, the perturbation records, the
renderer version, the field registry, and the analysis plan are immutable. Any later change is a
logged prereg amendment and is reported in the paper.

---

## 4. Gates

| Gate | When | Criteria | Fail action |
|---|---|---|---|
| **G0 — Harvest/freeze** | End of week 2 | ≥ 880 eligible prefixes; ≥ 440/domain pre-audit; ≥ 400/domain post-audit; replay ≥ 98%; 40-item audit ≥ 36/40 | Fallback 500/2 models or stop |
| **G1 — Calibration** | Week 3 | Parse ≥ 95%; placebo jitter ≤ 20%; s=3 switch 10–80%; format refusal < 5% per model | Fix and rerun; no main spend |
| **G2 — Main run** | Weeks 4–7 | Stop at **$22** spend or **45 GPU-hours**, whichever first; ledger complete | Analyze completed shards; disclose |
| **G3 — Analysis** | Weeks 8–10 | Pooled β > 0; positive in ≥ 2/3 models with the same sign; severity α ≥ .75; outcome κ ≥ .80 (or adjudicated ≥ .70 with downgrade); recovery κ ≥ .75 | Null/measurement paper; no law claim |
| **G4 — Recovery** | Weeks 9–10 | ≥ 50% of the s=3 risk set recovers by H=4; Weibull shape not rejected (p ≥ .01) | Report RMST/curve; t½ exploratory only |

The gates are sequential. G1 cannot start before G0 freezes. G2 cannot start before G1 passes.
G3/G4 are analysis gates and cannot be re-run on a different sample without a prereg amendment.

---

## 5. Budget

| Item | Specification | Cost |
|---|---|---:|
| GPU rental | 35–45 h on a 24 GB RTX 3090/4090 community instance, $0.30–0.50/h | **$15–22** |
| Storage / egress | ~60 GB weights + logs + traces | **$2–3** |
| Annotation | ~200 judgments by team members, no cash | **$0** |
| Contingency | GPU or storage overrun | **$3–5** |
| **Total** | Base assumes $18 GPU + $2 storage + $3 contingency | **$23 base / $50 hard cap** |
| Local CPU | Harvest, replay, analysis, writing: 20–30 h on the local machine | $0 |
| Paid API | None | $0 |

The hard cap is a stop line, not a target. Reaching $22 or 45 GPU-hours triggers G2 stop even if
generations remain. There is no second rental and no paid judge/API fallback.

---

## 6. Deliverables

1. **CTO-800** — 800 frozen real τ-bench prefixes (400 airline / 400 retail) with message hashes,
   observation hashes, perturbation records, arm assignments, and renderer version.
2. **Frozen manifests** — sample, perturbations, field registry, replay hashes, and preregistration
   hash, all under `data/manifests/`.
3. **Raw traces** — one ledger row per generation (34,800 envelope) with model, arm, prefix,
   step, prompt hash, output, parser result, latency, and cost accounting. Ledgers stay local
   until scrubbed and packaged.
4. **Reproducibility package** — pinned environment, rental contract, run scripts, analysis
   notebook, figure-generation code, and a one-command validation target.
5. **Preregistration** — design, estimands, gates, multiplicity sequence, and amendments log.
6. **Paper draft** — bounded claim, pilot disclosure, confirmatory results or null, limitations,
   and a data statement.

---

## 7. Risks and mitigations

| Risk | Why it matters | Mitigation |
|---|---|---|
| **τ-bench contamination** | Public tasks may be memorized; baseline reliance could be inflated | Report verbatim-arm accuracy and s=0 jitter; within-prefix contrast remains valid; optional 120-prefix template-transfer arm only if under budget; state domain scope |
| **Donor-prefix off-policy** | Target models continue gpt-4o/sonnet histories | Prefixes are fixed and shared across arms; stratify by donor; report donor-specific slopes; do not let target models generate prefixes |
| **Severity construct validity** | If s=1 moves decisions like s=2, "dose" is not a dose | Three-rater blind audit; α ≥ .75; s=1 negative control; s=3 plausibility check; collapse levels if it fails |
| **Model-format refusal** | A model may refuse the forced next-decision format | Calibration refusal gate < 5%; prompt/grammar fix before main run; document exclusions |
| **Rental availability** | 24 GB community instances can be scarce | Book early; fallback $0.89/h secure 4090 at 30 GPU-hours; reduce N or drop persistent arm |
| **Replay mismatch** | A non-replayable observation is not a real environment output | ≥ 98% normalized match; mismatch taxonomy; fix harness before sampling; never relax silently |
| **PII leakage** | τ-bench trajectories contain user profile data | Exclude profile tools; scrub stable synthetic tokens; 40-item human PII audit; re-scan before release; never commit raw trajectories |
| **Recovery state drift** | Replaying four steps may diverge from the donor episode | Continue with the real environment, not the donor transcript; log state hashes; report divergence rate; transient primary |
| **Budget overrun** | GPU rental is the only cash risk | Hard stop at $22/45 h; per-shard cost ledger; no second rental; contingency capped at $5 |
| **Analysis overreach** | Many secondary contrasts invite post-hoc stories | Fixed-sequence gate; preregistered primaries; heterogeneity exploratory; no model ranking; null reported as null |

---

## 8. Out of scope

- A universal law of observation sensitivity.
- Ranking models, model families, or providers.
- Frontier, proprietary, or API models.
- End-to-end task success, pass@k, or user satisfaction.
- Live APIs, web browsing, or non-deterministic tools.
- Training, fine-tuning, preference optimization, or agent policy improvement.
- Multi-agent interaction, debate, or tool selection strategy.

These are follow-up questions, not hidden claims of this study.

---

## 9. Change control

- **No post-freeze changes** to the sample, perturbations, field registry, renderer, prompts,
  or analysis plan after G0. The freeze hash is recorded in `data/manifests/cto800_v1.json`.
- Any necessary deviation is written to `docs/DECISIONS.md` and to the prereg amendments log
  (`prereg/AMENDMENTS.md`) **before** the affected analysis is run.
- Amendments state the trigger, the change, the analyses affected, and whether the change was
  made blind to target-model outcomes.
- Out-of-sequence or unlogged analyses are labeled exploratory and cannot support the primary
  claim.
- The paper reports every amendment and every gate outcome, including failures.
- Code changes after freeze are allowed only for reproducibility fixes that do not alter the
  frozen artifacts; they are recorded in `CHANGELOG.md`.

---

## 10. Definition of done

A phase is done only when: the code is merged with tests, the relevant docs are updated, the
gate report is written, and every reported number traces to a ledger or manifest row. A gate
that is not met is still "done" when the failure and its consequence are documented.
