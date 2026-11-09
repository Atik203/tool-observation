# Gates and stop rules

Gates are sequential and pre-registered. A gate cannot be skipped, relaxed after seeing data, or
re-run on a different sample without an amendment. Every gate report states the criterion, the
observed value, the pass/fail decision, and the consequence.

---

## Gate summary

| Gate | Phase | Criteria | Evidence artifact | Fail action |
|---|---|---|---|---|
| **G0** | Harvest / freeze | ≥880 eligible; ≥440/domain pre-audit; ≥400/domain post-audit; replay ≥98%; 40-item audit ≥36/40 | `artifacts/audit/g0_report.md`, `data/manifests/cto800_v1.json` | 500 prefixes / 2 models fallback, or stop |
| **G1** | Calibration | parse ≥95%; placebo jitter ≤20%; s=3 switch 10–80%; format refusal <5% per model | `artifacts/audit/g1_calibration.json` | Fix prompt/parser and rerun; no main spend |
| **G2** | Main run | Stop at $22 spend or 45 GPU-hours, whichever first; complete ledger | `artifacts/cost/main_cost.json`, `data/runs/main/ledger.jsonl` | Analyze completed shards; disclose shortfall |
| **G3** | Analysis | Pooled β>0; positive in ≥2/3 models with the same sign; severity α≥.75; outcome κ≥.80 (or adjudicated ≥.70 with downgrade); recovery κ≥.75 | `artifacts/analysis/g3_report.md` | Null/measurement paper; no content-sensitivity claim |
| **G4** | Recovery | ≥50% of the s=3 risk set recovers by H=4; Weibull shape not rejected (p≥.01) | `artifacts/analysis/g4_report.md` | Report RMST/curve; t½ exploratory only |

---

## G0 — Harvest and freeze

**Owner:** harvest lead. **Cost:** CPU only, $0. **Timing:** days 1–10 of the sprint.

Checks:

1. **Supply.** ≥880 eligible prefixes after PII exclusion and value-used filtering.
2. **Domain balance.** ≥440 airline and ≥440 retail before audit; ≥400 each after audit.
3. **Replay.** ≥98% normalized match between replayed and historical observations.
4. **Audit.** A human reviews 40 random prefixes on eligibility, PII, relevance, and replay;
   pass at ≥36/40 (90%).
5. **Freeze integrity.** Message hashes, observation hashes, perturbation records, renderer
   version, field-registry hash, and prereg hash recorded.

**Observed pilot supply (planning input, not a gate result):** 13,605 candidates, 11,318
JSON-parseable, 6,554 eligible value-used, 1,646 at a 10/task cap.

**Fail:** if supply is short or replay fails, fix the harness and re-run before sampling. If the
audit fails, revise the scrub/relevance rules and re-sample from the reserve. If the shortfall
persists, fall back to 500 prefixes and 2 models (drop persistent first), or stop.

---

## G1 — Calibration

**Owner:** inference lead. **Cost:** ~3 GPU-hours, ~$2. **Timing:** week 3.

Sample: 60 prefixes (30/domain), 5 arms, 3 models = 900 generations. Calibration prefixes are
disjoint from the main 800.

Per-model gates:

| Metric | Threshold |
|---|---|
| Parse rate | ≥95% |
| Placebo jitter (s=0 vs V) | ≤20% |
| s=3 switch rate | 10–80% |
| Format refusal | <5% |

Also inspected: parser failure taxonomy, prompt truncation, context length, latency, and whether
s=3 is a ceiling. A model that refuses the forced next-decision format is fixed with a
prompt/grammar change; if it still refuses, it is excluded and the substitution policy applies
(prereg amendment before calibration results are used).

**Fail:** no main-run spend. Fix and rerun calibration. If jitter stays >20% or s=3 remains >80%,
stop and report a measurement failure.

---

## G2 — Main run stop

**Owner:** inference lead. **Budget:** $23 base, $50 hard cap, stop at **$22** or **45
GPU-hours**.

The runner checks cumulative cost and GPU-hours after every shard and every 40 prefixes. On
reaching either limit it stops cleanly, flushes the ledger, and writes a stop record. Completed
shards are analyzed; missing cells are reported, not imputed. No second rental and no paid API.

**Fail:** budget reached before completion is not a scientific failure, but the paper must
disclose the reduced sample and any resulting power loss.

---

## G3 — Analysis

**Owner:** analysis lead. **Timing:** weeks 8–10.

| Check | Threshold |
|---|---|
| Pooled slope β | > 0 |
| Per-model slopes | positive in ≥2/3, same sign |
| Severity agreement | Krippendorff α ≥ .75 |
| Outcome agreement | Cohen's κ ≥ .80; adjudicated ≥ .70 with downgrade |
| Recovery agreement | κ ≥ .75 |
| Silent-propagation PPV | ≥ .90 |
| Parser failure | <1% overall |

If β ≤ 0 or fewer than 2/3 models are positive, the paper reports a null/measurement result. If
κ < .70 after one rubric revision, the study downgrades to action-level Y^A only and drops the
content-sensitivity claim. If .70 ≤ κ < .80, the adjudicated labels are primary on the audit
subsample and both analyses are reported.

---

## G4 — Recovery

**Owner:** analysis lead. **Timing:** weeks 9–10.

| Check | Threshold |
|---|---|
| Recovery events by H=4, s=3 risk set | ≥50% |
| Exponential assumption | Weibull shape not rejected, p ≥ .01 |
| Censoring | correctly coded at H=4 |
| State drift | reported, with divergence rate |

If <50% recover, report a lower bound, the recovery curve, and RMST; t½ is exploratory. If the
Weibull shape rejects, report Weibull/RMST and do not call t½ a law.

---

## Global stop conditions

Stop the study and write a public note if any of the following occurs:

- G0 cannot reach 880 eligible after a documented re-run and the fallback is not viable.
- G1 cannot reach a parseable, non-ceiling format after two calibration attempts.
- A PII leak is found in a release candidate (stop the release, not the science).
- The budget hard cap is reached before any confirmatory shard completes.
- A frozen manifest is found to be corrupted and cannot be reconstructed from upstream hashes.

## Reporting

Each gate report is a short Markdown file with: date, commit, config hash, criteria table,
observed table, decision, and next action. Gate failures are reported in the paper, not hidden.
Every number in a report cites a ledger, manifest, or audit CSV row.
