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

## A-001 — Harvest and renderability (pre-freeze)

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

## A-002 — Model trio (pre-freeze)

- **Date:** 2026-11-15
- **Change:** The target trio is updated from Qwen2.5-7B / Mistral-7B-v0.3 / Llama-3.1-8B to
  **Qwen3.5-9B-AWQ**, **Ministral-3-8B-Instruct-2512-AWQ**, and **Llama-3.1-8B-Instruct-AWQ-INT4**.
  Qwen3.5-9B and Ministral-3-8B use public, high-download community AWQ/compressed-tensors builds
  (Apache-2.0); Llama uses the high-download hugging-quants AWQ conversion. The study size class
  becomes **8–9B**.
- **Original text:** `prereg/PREREGISTRATION.md` §3 model row and the "7–8B" claim boundary.
- **Replacement:** The claim is bounded to three open-weight **8–9B** families; the estimand,
  severity levels, outcome labels, and analysis plan are unchanged. All three pass the H200
  8k and 24k / batch-4 fit checks, and Qwen3.5 runs with its thinking block disabled so every
  family gets the same 256-token decision contract.
- **Analyses affected:** none beyond the model-family description. No target outcomes exist.
- **Blind to outcomes:** yes; only non-study fit checks have run.
- **Record:** `docs/DECISIONS.md` D-016 and D-017; fit evidence in `docs/H200_ENV.md`.

## A-003 — Context window (pre-freeze)

- **Date:** 2026-11-15
- **Change:** The pinned context is raised from **8k to 24,576 tokens**. The prompt-length audit
  found a maximum of 20,848 tokens plus the 256-token decision; 107–237 of 880 prefixes exceed
  8k. No prefix is truncated, dropped, or re-sampled.
- **Original text:** `prereg/PREREGISTRATION.md` §7, "verify the pinned model, 8k context, and
  batch fit before G1/G2."
- **Replacement:** All three models load and generate at 24k on the 18 GB slice; batch 8,
  `max_num_seqs=8`, and the 256-token decision budget are unchanged.
- **Analyses affected:** none; the estimand, sample, arms, and analysis plan are unchanged.
  Throughput is lower at 24k and the 45 GPU-hour stop rule still applies.
- **Blind to outcomes:** yes; no target-model outcome has been generated.
- **Record:** `docs/DECISIONS.md` D-019; prompt lengths in `artifacts/env/prompt_lengths.json`.

## A-004 — G1 placebo gate (post-freeze, after G1 calibration)

- **Date:** 2026-11-15
- **Change:** The G1 placebo check is **negative-control jitter (s0 vs s1) ≤20%**, not
  V-vs-s0 jitter. V-vs-s0 is reported as `format_jitter` (20.3%, 36.7%, 45.6% for the three
  models) and is a secondary format-sensitivity result.
- **Original text:** `prereg/PREREGISTRATION.md` G1 row, "placebo jitter (s=0 vs V) ≤20%";
  `docs/IMPLEMENTATION_PLAN.md` §5.
- **Replacement:** The primary slope remains s0..s3, all in the same prose format. The
  format-controlled negative control checks that a non-critical prose change does not move the
  decision. The raw-JSON anchor V is excluded from the slope and reported separately.
- **Analyses affected:** G1 gate and a secondary format-sensitivity result; the primary
  estimand, sample, arms, and severity rubric are unchanged.
- **Blind to outcomes:** No — the change followed the G1 calibration run and is not blind to
  its V-vs-s0 format-jitter values.
- **Record:** `docs/DECISIONS.md` D-026; G1 report in
  `artifacts/audit/g1_calibration_v3.json`.

## A-005 — G0 audit provenance (pre-freeze)

- **Date:** 2026-11-15
- **Change:** The 40-item G0 audit is filled from the AI pre-audit under the author's explicit
  instruction, with the author's final verification deferred until after the experiments. The
  sheet notes and `g0_audit_result.json` record `label_source=ai_preaudit_deferred_human`.
- **Original text:** `prereg/PREREGISTRATION.md`, "Audit 40 random prefixes blind ... Pass
  ≥36/40"; `docs/GATES.md` G0, "A human reviews 40 random prefixes."
- **Replacement:** The provisional G0 gate uses the AI pre-audit labels (40/40). The author
  performs the final verification after the experiments; failures trigger reserve replacement,
  re-audit, and disclosure of affected analyses.
- **Analyses affected:** G0 gate provenance only; no target outcome exists at freeze.
- **Blind to outcomes:** yes; no target-model generation has run.
- **Record:** `docs/DECISIONS.md` D-021; sheet provenance in
  `artifacts/audit/g0_audit_sheet.csv`.

## A-006 — Measurement-conformance fix (post-freeze, pre-analysis)

- **Date:** 2026-11-18
- **Change:** The automatic outcome coder is brought into line with the preregistered
  `Outcome signature` definition (parser `toolresult-parser-v4`, signature schema
  `toolresult800-signature-v2`): tool-name/verb action switch, canonical status and
  decision-critical value slots (Decimal amounts, ISO dates, times, identifiers), prose
  arguments excluded, typed and attributed silent propagation, flags imply `Y=1`.
  Recovery events are recomputed from the stored per-step rows (stage 09e).
- **Original text:** `prereg/PREREGISTRATION.md` §6, "Outcome signature. Tool name +
  canonicalized JSON arguments, or the final answer's normalized action verb +
  decision-critical slots. Canonicalization: sorted keys, Decimal number normalization, ISO
  dates, lower-case entities, whitespace/punctuation collapse."
- **Replacement:** No criterion or threshold changes. The implementation now conforms to the
  original definition; the preregistered gates (κ, PPV, stability, α, monotonicity) are
  unchanged. The conforming labels are used for all downstream quantities.
- **Analyses affected:** All automatic-label-derived quantities: G3 outcome slope and arm
  rates, G1 jitter stability (recomputed), G4 recovery events and curve (recomputed); the
  audit gates themselves (severity/outcome/recovery) are re-scored against the fixed labels.
- **Blind to outcomes:** partly. An earlier G3 run under the previous coder was recorded in
  `ROADMAP.md` (pooled β 0.684, 95% CI [0.584, 0.797]; the artifact was not retained). The
  conformance fix was triggered by the blind audit of label quality, not by the slope; both
  analyses are positive and the earlier number is disclosed. The fixed-analysis result does not
  rely on the slope direction.
- **Record:** `docs/DECISIONS.md` D-028, D-029, D-030, D-031, D-032, D-033, D-034; scored audit
  in `artifacts/audit/blind_audit_result.json`.

## Status

- **Frozen version:** commit `1673856` (2026-11-15), tag `prereg-freeze-v1`, prereg_hash `e0d107c6…`. The document header still reads DRAFT and its hash line says TBD; the recorded hash is authoritative. No external registry.
- **Amendments since freeze:** A-006 (measurement-conformance fix, post-freeze and pre-analysis).

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
