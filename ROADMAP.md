# Roadmap — Tool-Result Errors in Language-Model Agents

**Status:** confirmatory study complete; manuscript in revision (2026-11-22).
**Scope:** three open-weight 8–9B models, τ-bench airline and retail, next-decision sensitivity, and four-step recovery.
**Compute:** 8.9 GPU-hours used of the 45-hour H200 MIG 1g.18gb allocation; $0 cash; no paid API.
**Review basis:** `docs/reviews/2026-11-22/WEAKNESS_REGISTER.md`.

**Legend:** ✅ done · 🔄 in progress · ⏳ todo

---

## 0. At a glance

| Phase | Status | Exit gate | Current output |
|---|---|---|---|
| **P0 — Harvest and freeze** | ✅ | G0 (audit provisional) | 880 prefixes, 5 arms, 2,640 perturbations, manifest hash |
| **P1 — Calibration** | ✅ | G1 (amended under A-004) | 60 prefixes × 3 models; prompt/parser frozen |
| **P2 — Main run** | ✅ | G2 | 21,611 generations; 8.9 GPU-hours |
| **P3 — Labels and analysis** | ✅ | G3 / G4 | β 0.877; three gate criteria failed |
| **P4 — Paper revision** | 🔄 | Review register P0/P1 cleared | 26-page draft; not submission-ready |
| **P5 — Release and submission** | ⏳ | Release + submission checklist | DOI, artifact package, cover letter |

---

## 1. Completed phases (collapsed)

| Phase | What was completed | Evidence |
|---|---|---|
| **P0** | 13,605 candidates → 5,516 eligible → 5,511 replay-matched → 880 sampled (800 primary + 80 reserve); 4,400 arms; 2,640 perturbation records; 100% s=0 value-set equality; frozen manifest `toolresult800_v1.json` (SHA-256 `d6e034d7…`); G0 audit is an AI pre-audit 40/40 with human verification deferred (D-021). | `data/manifests/toolresult800_v1.json`; `artifacts/audit/g0_report.md`; `artifacts/audit/freeze_dry_run.json` |
| **P1** | 60 disjoint prefixes × 3 models; parse 98.3 / 100 / 96.7%; gated negative-control jitter 11.9 / 13.3 / 10.5%; original V-vs-s0 format jitter 20.3 / 36.7 / 45.6% failed and was replaced by A-004 after calibration (post-freeze, not blind). | `artifacts/audit/g1_calibration_v3.json`; D-026, D-041, A-004 |
| **P2** | 13,200 base generations + 7,211 recovery rows + 1,200 jitter rows = 21,611; 8.9 GPU-hours; no paid API; ledger per generation. | `data/runs/main/*/ledger.jsonl`; `artifacts/cost/` |
| **P3** | Pooled β 0.877 (SE 0.059, 95% CI [0.770, 0.998]); 3/3 positive, Holm-significant; silent share 21.3% (419/1,964); label-free audits α .911, κ .987, recovery κ .920/.917. Gate failures: parser 1.55%, severity s2/s3 88.3%, recovery 27.3/34.7/27.2% crude (KM 32.4/47.6/28.2). | `artifacts/analysis/g3_analysis.json`; `g4_recovery.json`; `artifacts/audit/blind_audit_result.json`; D-039/D-043 |

The detailed 25-row G0 table and ten-day sprint from the original plan are retired; the evidence above is the record.

---

## 2. Gate record (actual)

| Gate | Status | Observed | Consequence |
|---|---|---|---|
| **G0** | ✅ completed, provisional | AI pre-audit 40/40; human 40-item audit deferred (D-021); manifest hash verified | Freeze stands; human audit remains a disclosed deviation |
| **G1** | ✅ completed, amended | Original V-vs-s0 format jitter failed at 20.3–45.6%; A-004 replaced it with s0-vs-s1 negative control 10.5–13.3% after calibration, not blind | Main run proceeded under A-004; original criterion must be reported as failed |
| **G2** | ✅ | 21,611 rows; 8.9 GPU-hours; within 45-hour / 200 GB stop line | Sample complete; recovery conditional on switching |
| **G3** | ❌ | Slope passes; parser failure 1.55% (fail); severity s2/s3 88.3% (fail); outcome κ .987 (pass); silent PPV 1.00 point, exact lower bound .66 | Measurement paper; no content-sensitivity claim |
| **G4** | ❌ | Crude recovery 27.3/34.7/27.2% by H=4 (KM 32.4/47.6/28.2); Weibull shape rejected 2/3 | Report curve/RMST; half-life exploratory; remove “Ministral close” unless failure-treated estimate is close |

---

## 3. P4 — Paper revision (🔄)

**Goal:** make the manuscript a credible measurement paper with a consistent claim boundary, corrected recovery estimand, honest audit provenance, and a reproducible artifact.

| Workstream | Status | Work | Exit criterion |
|---|---|---|---|
| **P4.1 Claim and positioning** | ⏳ | Retitle away from “Causal Study”; rewrite abstract to lead with the measurement and the failures; cite and differentiate 2025–26 nearest neighbors; add comparison table; drop “no controlled estimate” | Title, abstract, intro, results, conclusion use one claim; novelty is a stated combination, not a vacuum |
| **P4.2 Recovery re-estimation** | ⏳ | Use crude event share for the gate; rebuild risk set from semantic switches; report hash-vs-semantic overlap; add censoring-reason table; treat final answers/parse failures as failures in sensitivity; recompute RMST/\(t_{1/2}\) | Recovery table reconciles `Events/n`; gate verdict under both conventions; no “Ministral close” claim unless supported |
| **P4.3 Severity and audit robustness** | ⏳ | Report 7/11/16 of 60 donor-unused; reclassify and re-estimate tier ORs; report s1 OR 1.27 and marginal +1.1 pp; silent share as lower bound and recall-adjusted; PPV lower bound .66; human 40-item subset or rename “consistency check” | Abstract/results/audit table carry the same caveats; tier ORs have a bounded sensitivity |
| **P4.4 Inference and integrity** | ⏳ | G1/A-004 history; remove “no threshold changed”; reconcile failure count (three vs four); add H1–H7 status table; report H5; cluster-robust McNemar/LRT; paired recovery test; freeze/deposit prereg; held-out audit after coder fix | Gate-status table is internally consistent; prereg deposited; audit circularity disclosed or resolved |
| **P4.5 Craft, figures, references** | 🔄 | Remove Fig. 4 “no study outcomes” stamp or replace it; clear all `\pending{}` blocks; reconcile byline/CRediT; fix G1 table, recovery range 28.2–47.6, Intro “two vs three”; regenerate figures at print size with ≥8 pt effective fonts; cite orphan floats; trim tables; fix notation collisions; add 2025–26 refs | No draft artifacts; every float cited; 0 undefined; effective fonts ≥8 pt; references current |
| **P4.6 New evidence** | ⏳ | 100–200 prefix task-success/utility endpoint; second deterministic renderer; human audit 60–120 items; intervention probe; one frontier/on-policy control | At least one new evidence stream, or every claim tightened to the current scope |
| **P4.7 Reproducibility and release prep** | ⏳ | Publish scrubbed artifacts/ledger extracts with DOI; implement or remove “one-command validation”; add table-to-artifact map; correct data card; complete PII audit; verify model licenses; name AI models/versions/dates in disclosure | External reader can reproduce the reported tables; DOI resolves; PII/licensing cleared |

**P4 exit:** all P0 findings in the weakness register closed; P1 findings either closed or explicitly scoped; clean 26-page build; no claim exceeds the gate record.

---

## 4. P5 — Release and submission (⏳)

1. Freeze author list, ORCIDs, CRediT, and corresponding author.
2. Resolve ethics determination and AI-use statement; correct “author team” wording.
3. Mint DOI; publish data card, manifest, scrubbed prefixes/observations/perturbations, audit packets, analysis JSONs, and ledger extracts.
4. Verify τ-bench MIT notice and all three model output licenses.
5. Build the 14-file Overleaf package (`toolresults.tex`, `ref.bib`, class files, `fig1–fig10.png`) and clean-room compile.
6. Write cover letter and journal-specific highlights; check keyword limit.
7. Submit; archive the submission checklist and gate record.

**P5 exit:** DOI resolves; clean-room compile from the package; submission checklist signed.

---

## 5. Claim boundary (current)

**What the study supports.** A bounded, renderer-local, mover-weighted measurement: within a frozen real τ-bench prefix, changing the prose observation changes the probability that the next decision departs from the faithful-prose continuation; the assigned-severity gradient is positive but threshold-like; format sensitivity is 20–46% in calibration and 19.8–38.1% in the main run; silent propagation is at least 21.3% of critical-arm switches; persistence is 27.2–34.7% crude recovery by H=4.

**What it does not support.** A causal content-sensitivity claim (G3 parser and severity gates failed); a task-success effect; a model ranking; transfer to frontier/API models, live tools, or other renderers; a universal dose–response law.

**What would change the claim.** A crude recovery ≥50%; a parser rate <1%; a severity audit ≥90% with independent raters; a stable slope under a second renderer and a task-success endpoint. None is currently met.

---

## 6. Budget (actual)

| Item | Actual |
|---|---|
| H200 MIG 1g.18gb | 8.9 GPU-hours of 45 (≈20%) |
| Cash | $0 |
| Paid API | $0 |
| Storage | within 200 GB project allocation |
| Annotation | AI-agent sessions, author-overseen; no cash |

---

## 7. Live risks

| Risk | Why it matters | Mitigation |
|---|---|---|
| **Recovery estimand** | KM vs crude changes the gate margin and the “close” claim | P4.2 re-estimation; report both |
| **Claim/audit integrity** | Title/abstract overclaim; AI-only audit | P4.1/P4.3; measurement framing; human subset or “consistency check” |
| **Reproducibility** | Artifacts gitignored; no DOI | P4.7; publish scrubbed package |
| **PII/licensing** | Release risk; model output terms | Human PII audit; license verification |
| **Reference recency** | 2024 maximum at a 2026 submission | P4.1/P4.5; add verified 2025–26 work |
| **Scope / no task success** | Deviation ≠ harm | P4.6 endpoint or tighten every claim |
| **Human audit capacity** | G0 and label audits deferred | Complete a 40-item human subset before submission |

---

## 8. Out of scope

- A universal law of observation sensitivity.
- Ranking models, families, or providers.
- Frontier, proprietary, or API models (except one exploratory control if P4.6).
- End-to-end task success at full 800-prefix scale.
- Live APIs, web browsing, or non-deterministic tools.
- Training, fine-tuning, preference optimization, or policy improvement.
- Multi-agent interaction, debate, or tool-selection strategy.

---

## 9. Change control

- No post-freeze changes to sample, perturbations, field registry, renderer, prompts, or analysis plan without a logged decision and, where required, a prereg amendment.
- Every deviation goes in `docs/DECISIONS.md` and `prereg/AMENDMENTS.md` before the affected analysis.
- Every reported number traces to a ledger, manifest, or analysis artifact; the weakness register is the current audit trail.
- The paper reports every gate outcome, including failures and amendments.

---

## 10. Definition of done

A phase is done only when code is merged with tests, docs are updated, the gate report is written, and every reported number traces to a ledger, manifest, or artifact. A failed gate is still “done” when the failure and its consequence are documented. For P4, “done” additionally means the weakness register’s P0 items are closed and no claim exceeds the gate record.
