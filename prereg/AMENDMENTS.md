# Amendments log - ToolResult-800

The preregistration is frozen at the end of G0. Any change after the freeze is recorded here
**before** the affected analysis runs. An amendment is not a silent edit: it states the trigger,
the original text, the replacement, the analyses affected, and whether the change was made blind
to target-model outcomes.

## Pre-freeze branding note

- **Date:** 2026-11-11
- **Change:** Dataset brand renamed from CTO-800 to **ToolResult-800**; "E2" retired.
- **Analyses affected:** none. No scientific design, sample, analysis, or claim change.
- **Blind to outcomes:** yes; no target-model outcomes have been generated.
- **Record:** `docs/DECISIONS.md` D-006.

## Pre-freeze compute and budget note

- **Date:** 2026-11-14
- **Change:** Approved execution GPU is the university **H200 1g.18gb** slice. Cash budget is
  **$0**; operational stop is **45 GPU-hours or 200 GB storage**. No paid API, no second GPU.
- **Analyses affected:** none. No scientific design, sample, analysis, or claim change.
- **Blind to outcomes:** yes; no target-model outcomes have been generated.
- **Record:** `docs/DECISIONS.md` D-007 and D-008.

## Pre-freeze harvest and renderability note

- **Date:** 2026-11-15
- **Change:** The operational value-used rule yields **5,516 eligible** observations (airline
  1,434; retail 4,082), not the 6,554 planning figure. Profile/PII-tool exclusion is 3,692
  candidates. At the 10/task cap the eligible pool is airline 442 / retail 1,144. Eligible-pool
  replay matches 5,511/5,516 (99.91%). The sampler excludes 194 scalar-only `calculate` prefixes
  because they cannot support s=1 and s=3; this does not change the airline cap-10 (442).
- **Original text:** `prereg/PREREGISTRATION.md` §3 "Harvest frame: 1,980 public τ-bench
  trajectories; 13,605 candidate post-tool decision points; 6,554 eligible value-used
  observations expected"; `docs/GATES.md` G0 supply check ≥880.
- **Replacement:** The confirmatory sample is still 800 primary + 80 reserve (400/400), and the
  G0 supply gate is still ≥880 eligible and ≥440/domain. The 6,554 figure is a planning input,
  not a gate. The airline cap-10 is 442, two above the 440 floor; replay and audit must preserve
  it.
- **Analyses affected:** sample composition and strata only. The estimand, severity levels,
  outcome labels, analysis plan, and claim boundary are unchanged.
- **Blind to outcomes:** yes; no target-model outcomes have been generated.
- **Record:** `docs/DECISIONS.md` D-009, D-010, D-011, D-013.

## Pre-freeze model-trio note

- **Date:** 2026-11-15
- **Change:** The target trio is updated from Qwen2.5-7B / Mistral-7B-v0.3 / Llama-3.1-8B to
  **Qwen3.5-9B-AWQ**, **Ministral-3-8B-Instruct-2512-AWQ**, and **Llama-3.1-8B-Instruct-AWQ-INT4**.
  Qwen3.5-9B and Ministral-3-8B use public, high-download community AWQ/compressed-tensors builds
  (Apache-2.0); Llama uses the high-download hugging-quants AWQ conversion. The study size class
  becomes **8–9B**.
- **Original text:** `prereg/PREREGISTRATION.md` §3 model row and the "7–8B" claim boundary.
- **Replacement:** The claim is bounded to three open-weight **8–9B** families; the estimand,
  severity levels, outcome labels, and analysis plan are unchanged. All three pass the H200
  8k/batch-4 fit check, and Qwen3.5 runs with its thinking block disabled so every family gets
  the same 256-token decision contract.
- **Analyses affected:** none beyond the model-family description. No target outcomes exist.
- **Blind to outcomes:** yes; only non-study fit checks have run.
- **Record:** `docs/DECISIONS.md` D-016 and D-017; fit evidence in `docs/H200_ENV.md`.

## Status

- **Frozen version:** TBD (tag `prereg-freeze-v1`, commit SHA + SHA-256 recorded at G0).
- **Amendments since freeze:** none.

## Format

| ID | Date | Trigger | Original text | Replacement | Analyses affected | Blind to outcomes? | Approved by |
|---|---|---|---|---|---|---|---|
| A-001 | YYYY-MM-DD | What happened | Quote or section | New text | Primary/secondary/exploratory | Yes/No | Name |

## Rules

- Amendments are numbered sequentially and never deleted.
- A change made after seeing the primary outcome is labeled **post-outcome** and cannot support
  the confirmatory claim.
- Every amendment is summarized in `docs/DECISIONS.md` and reported in the paper.
- If an amendment changes the sample, renderer, field registry, or primary analysis, the paper
  reports both the preregistered and amended analyses where feasible.
