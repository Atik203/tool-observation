# Amendments log - ToolResult-800

The preregistration is frozen at the end of G0. Any change after the freeze is recorded here
**before** the affected analysis runs. An amendment is not a silent edit: it states the trigger,
the original text, the replacement, the analyses affected, and whether the change was made blind
to target-model outcomes. A row entered after its analysis states both the decision date and the
entry date; A-007–A-011 are such late entries, disclosed as such.

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

- **Frozen version:** commit `1673856cc6cd335ae9fd8b0132343082f167077a` (short `1673856`, 2026-11-15), tag `prereg-freeze-v1`, prereg_hash `e0d107c6…`. The tag object, `data/manifests/toolresult800_v1.json` (`freeze.git_commit`), and this log agree. The earlier `1675376` in `prereg/DEPOSIT_NOTE.md` was a typo: `git rev-parse 1675376` fails and no such object exists. The document header still reads DRAFT and its hash line says TBD; the recorded hash is authoritative. No external registry.
- **Amendments since freeze:** A-004 (G1 placebo criterion; post-freeze, after G1 calibration, not blind; D-041); A-006 (measurement-conformance fix; post-freeze, pre-analysis, partly blind; D-028–D-034); A-007 (confirmatory analysis sample is the 800 primary prefixes, reserve excluded by default; D-036); A-008 (label-free audit round is primary, label-visible round archived as sensitivity; D-039 and D-043); A-009 (recovery censoring at the last observed step, crude Events/n as the G4 gate statistic; D-040); A-010 (task-utility endpoint added as an exploratory secondary; D-044); A-011 (parser <1% is a protocol criterion from `docs/GATES.md`, absent from the frozen G3 row).
- **Record-entry date:** A-007–A-011 were entered on 2026-11-22 during the P6.1 record-integrity audit, after the analyses they describe. They record decisions already taken (D-036, D-039, D-040, D-043, D-044) or, for A-011, a provenance finding in the gate record; they change no analysis rule and are not presented as prospective amendments.

## Amendment table

A-001–A-006 are recorded in the prose entries above. A-007–A-011 are recorded below in the table format used for the post-freeze analysis record. The table date is the entry date; the decision date is stated in the trigger.

| ID | Date | Trigger | Original text | Replacement | Analyses affected | Blind to outcomes? | Approved by |
|---|---|---|---|---|---|---|---|
| A-007 | 2026-11-22 (decision 2026-11-18) | Main run generated the full 880-prefix matrix; the confirmatory estimates must use the frozen 800-primary sample and exclude the 80 reserve prefixes (D-036). | `prereg/PREREGISTRATION.md` §7.6: "draw 880 stratified by domain, donor, step bin, and tool family; freeze 800 primary (400/400) + 80 reserve (40/40)". The run envelope retained all 880. | Stage 13 excludes the manifest `reserve_ids` from all confirmatory estimates by default; `--include-reserve` is sensitivity only. Confirmatory estimates use the 800 primary prefixes; the 880-prefix run envelope, the all-880 slope, and the reserve-only slope are reported as checks. No criterion, threshold, or event definition changed. | All confirmatory estimates: pooled and per-model slopes, silent propagation, recovery, and audit joins. Reserve-only results are exploratory. | Partly: the 800-primary sample was frozen before generation, but the exclusion was implemented after the run; no outcome value selected the rule. | M.A.R. (author); D-036 accepted. |
| A-008 | 2026-11-22 (decision 2026-11-18) | The first audit round's packets retained mechanical reference labels (design level, criticality, automatic labels), so agreement measured conformance to the anchor; the label-free re-rating supersedes it (D-039, D-043). | `prereg/PREREGISTRATION.md` §6 audits: "120 severity items (30/level, 3 blind raters) ... 160 outcome items (2 blind raters) ... 80 recovery sequences: κ ≥ .75". The frozen text does not require packets to exclude reference labels and automatic answers; the first round carried them. | All packets were rebuilt without reference labels or automatic answers, and the label-free round is primary for the severity, outcome, and recovery audit gates. The label-visible round is archived and reported as a sensitivity (α .919, κ .975, PPV 1.00, recovery .787). No gate threshold changed. | G3 severity, outcome, and recovery audit gates and every reported agreement statistic; the claim downgrade rests on the label-free values. | No: the change followed the first label-visible round and its agreement values; the re-rating was not blind to the earlier results. | M.A.R. (author); D-039 and D-043 accepted. |
| A-009 | 2026-11-22 (decision 2026-11-18) | Kaplan–Meier, exponential, and Weibull code censored early-terminated episodes at H=4 instead of their last observed step, biasing every recovery curve downward (D-040; P4.2). | `prereg/PREREGISTRATION.md` §5.6: "Discrete-time survival over H=4; exponential t½ = ln2/μ; Kaplan–Meier and RMST; Weibull shape test." The frozen text does not state the censoring time for episodes that end before H=4. | Censor at the last observed step; recovery events carry `last_step` (stage 09e). The crude Events/n estimate is the G4 gate statistic (paper Table `tab:gate-status`); the H=4-censoring triple 27.3/34.7/27.2 is retained as a sensitivity. No event definition, threshold, or sample changed. | G4 recovery curve, Kaplan–Meier, Weibull, RMST, half-lives, and the G4 verdict. | No: the error was found after the first recovery estimates; the correction is estimator-only and changes no threshold or event definition. | M.A.R. (author); D-040 accepted. |
| A-010 | 2026-11-22 | P4.6 added a new-evidence stream for task utility (open item C10): deterministic donor-path adherence plus blinded adequacy coding from existing ledgers (D-044). | `prereg/PREREGISTRATION.md` §1: the study "does not claim ... an end-to-end task-success estimate"; no task-utility endpoint is preregistered. | Add the task-utility endpoint as exploratory secondary only: donor adherence on the 1,039 analyzable switched pairs and single-agent blinded adequacy on 115 judgeable pairs, with Wilson intervals and paired exact McNemar. No new generations (0.0 GPU-hours); nothing is pooled with the confirmatory estimates; the no-task-success claim boundary is unchanged. | Exploratory section and Table `tab:utility` only; no confirmatory estimate, gate, sample, or threshold. | No: designed and coded after the confirmatory run from existing ledgers; labeled exploratory and not pooled. | M.A.R. (author); D-044 accepted. |
| A-011 | 2026-11-22 | Gate-record audit: the paper reports a G3 parser-failure criterion (<1%) that is absent from the frozen `prereg/PREREGISTRATION.md` G3 row but present in the protocol gate table `docs/GATES.md`. | Frozen G3 row: "Pooled β > 0; positive in ≥2/3 models with the same sign; severity α ≥ .75; outcome κ ≥ .80 (or adjudicated .70–.80 with downgrade); recovery κ ≥ .75". `docs/GATES.md` G3 audit table: "Parser failure <1% overall" (present since commit `ea0f95b`, 2026-11-09, before the 2026-11-15 freeze). | No threshold change and no edit to the frozen row. Record the parser-failure criterion as a pre-freeze protocol criterion from `docs/GATES.md`, reported as a failed G3 criterion (205/13,200 = 1.55%) and carried into the claim downgrade. | G3 gate status and the claim downgrade only; no estimate, sample, event definition, or threshold changed. | Yes: the criterion was written 2026-11-09, before the freeze and before any target generation; this row records provenance, not a new decision. | M.A.R. (author); P6.1 gate-record audit. |

Provenance for these records: multi-role agent panel, author-overseen.

## Rules

- Amendments are numbered sequentially and never deleted.
- A change made after seeing the primary outcome is labeled **post-outcome** and cannot support
  the confirmatory claim.
- Every amendment is summarized in `docs/DECISIONS.md` and reported in the paper.
- If an amendment changes the sample, renderer, field registry, or primary analysis, the paper
  reports both the preregistered and amended analyses where feasible.
