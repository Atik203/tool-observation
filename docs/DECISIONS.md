# Decision log

Architectural and research decisions for `tool-observation`. Add new entries at the top. Any
decision that touches the preregistration, frozen data, or analysis plan also requires an entry
in `prereg/AMENDMENTS.md` before the affected analysis runs.

---

## D-046 - P6.4 release-copy PII redaction, v1.0.1, attribution and license consistency

- **Date:** 2026-11-23
- **Status:** accepted (release errata; frozen source untouched)
- **Context:** Q1 register V3 confirmed one scrubber-artifact identity (a given name plus
  digits surviving inside an `@example.com` address) in `data/frozen/prefixes.jsonl` and in
  the v1.0.0 release derivatives (`frozen/prefixes.jsonl`, two T6 packet files, one recovery
  trace, and the `pii_rescan.json` note). `DATA_LICENSE.md` and `docs/DATA_CARD.md` claimed
  "No raw PII is released" while the package shipped the fragment and a note flagging it. The
  register's stop rule treats a PII leak as release-blocking; C2 confirms the fragment is in
  gitignored frozen/release data, not in committed files, so repository history is unaffected.
- **Decision:** Redact the release copy only, in the builder, and bump the package to
  **v1.0.1** (metadata/errata; no frozen-source change):
  - `scripts/18_build_release.py` defines ordered redaction rules in `REDACTION_RULES` and
    rewrites every staged text file through `apply_redactions()` after copying/generating and
    before `SHA256SUMS`. The replacement is `person_redacted_0001`; the bare
    `person_0f41e336893e` pseudonym is left intact (it is a legitimate scrubber token whose map
    is never released).
  - `frozen/prefixes.jsonl` is copied from `data/frozen/prefixes.jsonl` and then redacted in
    the package. The frozen source stays bit-identical under the manifest hash. The package
    records both `frozen_prefixes_hash_source` (manifest) and
    `frozen_prefixes_hash_release` (redacted buffer), plus per-file counts, in
    `release_record.json`; `--validate` binds both and rejects an unredacted or non-idempotent
    prefix file.
  - `pii_rescan.json` gains `n_redactions`, `n_redacted_files`, `redactions`, `redaction_token`,
    and `redaction_note`; its old note naming the fragment is removed.
  - `tests/test_release.py` adds a guard: `redact_text()` must remove the literal; no file under
    `release/` may contain the literal or the `ahmed6699` pattern; a present package's
    `pii_rescan.json` must report zero hits and a positive redaction count. The guard was
    verified red (probe file under `release/`) then green after removing the probe.
  - Version bump: `PACKAGE_NAME = ToolResult-800-v1.0.1`, `PACKAGE_VERSION = 1.0.1`,
    `BUILDER_VERSION = stage-18 v2`; package `CHANGELOG.md` and repository `CHANGELOG.md` record
    v1.0.0 → v1.0.1. The superseded local v1.0.0 and pre-v1.0 `toolresult800-v1` candidates are
    removed after the v1.0.1 build (both gitignored, neither published).
  - Licensing consistency: new `ATTRIBUTION.md` (ToolResult-800 authors, upstream τ-bench MIT
    with "Copyright (c) 2024 Sierra", the three model families and licenses, Llama 3.1
    Community License "no weights, derived text" note, and the "changes were made" statement);
    `DATA_LICENSE.md`, `docs/DATA_CARD.md`, and the package licenses reference it.
  - `DATA_LICENSE.md` and `DATA_CARD.md` now state the freeze-vs-release distinction: the
    unredacted fragment remains only in the gitignored frozen source, which is not distributed;
    the released copy is redacted on every build and carries no unredacted direct identifiers.
    The pending independent human re-scan is not claimed as done.
  - Corrected the upstream pin quoted in the bundled τ-bench license header,
    `docs/submission/license_verification.md`, and `docs/submission/doi_record.md` to the hash
    in `data/manifests/source_pin.json` (`59a200c6d575d595120f1cb70fea53cef0632f6b`).
- **Not changed:** `prereg/*`, the frozen manifest, perturbations, field registry, renderer,
  `data/frozen/prefixes.jsonl`, and `paper/toolresults.tex` (the paper's short `59a200c`
  reference is correct).
- **Consequences:** v1.0.1 is the publishable candidate for P6.5; a rebuild cannot reintroduce
  the fragment without a guard failure. The release is still gated on the independent human
  PII re-scan, DOI mint, and clean-room compile.

---

## D-047 - P6.3 row-level refits from local ledgers (cluster LRT, reclassification, missingness, competing risks)

- **Date:** 2026-11-23
- **Status:** accepted (post hoc robustness; no primary endpoint or risk-set change)
- **Context:** The Q1 panel register (V4/V5, correction C1) found three estimands that were
  point-only or asymptotically justified: the categorical/quadratic severity LRTs, the
  severity-reclassification dilution, and the 5.5% missing cells. The earlier "ledgers
  absent, refits impossible" claim was wrong: `data/runs/main/` holds 13,200 step-0 rows
  across three models plus recovery and jitter ledgers. P6.3 upgrades these from "cannot"
  to "do it" on this machine, with no GPU.
- **Data provenance:** all inputs are read from `data/runs/main/` (base ledgers
  `{model}/ledger.jsonl`, recovery step ledgers `{model}/recovery_{transient,persistent}.jsonl`,
  and recovery event files `recovery/{model}/{transient,persistent}.jsonl`), plus the frozen
  manifest, perturbation records, and the audit sheets. The script writes SHA-256 hashes and
  byte sizes for every file it reads into `artifacts/analysis/rowlevel_refits.json`; P6.5
  publishes them with the release. No raw ledger or frozen data is committed.
- **Estimands and methods (fixed before running):**
  1. **Severity functional form.** Exact conditional logit (prefix x model strata; prefix
     clusters) with linear (`s`), quadratic (`s, s^2`), and categorical (`1(s=1), 1(s=2),
     1(s=3)`) designs. The primary cluster-robust test is a null parametric bootstrap LRT:
     resample the 800 prefixes with replacement (all three model groups for a prefix travel
     together), simulate each stratum's outcome set from the fitted linear model conditional
     on its observed event count, refit all three designs, and recompute both LRTs.
     `p = (1 + #{LRT* >= LRT_obs}) / (B + 1)`, seed 20261108, B=150 pooled and B=40 per
     model. The budgets are runtime-bounded; the bootstrap p floor is 1/151 pooled and
     1/41 per model, so the cluster-robust Wald family is the primary multiplicity record
     and the bootstrap is the resampling check. Cluster-robust Wald tests (exact conditional Hessian, prefix-cluster sandwich)
     are reported alongside. Multiplicity: Holm over the six per-model tests (two LRTs x
     three models); the pooled bootstrap test is the primary and is not in that family.
     The note records that shared prefixes induce positive dependence, so Holm is valid but
     conservative, and that the categorical and quadratic tests are alternative
     specifications rather than two independent discoveries. Holm on the cluster-robust
     Wald p-values is the primary multiplicity record; Holm on the bootstrap p-values is
     reported as a resolution-limited check.
  2. **Realized severity.** Assigned-severity ORs are unchanged. A critical-arm item is
     coded inactive when the blind audit or verifier pass codes it donor-unused (majority
     7/60, sheet-visible 11/60, blind 16/60). The primary refit adds an inactive indicator
     to the conditional logit, so s1/s2/s3 are compared with the clean original s0 baseline
     while inactive rows keep their own nuisance coefficient; this is the interval analogue
     of the old point-only dilution correction. Two versions: (a) audited-only, using the
     observed 60 critical items (the 43 not flagged stay active); (b) extrapolated, drawing
     arm-specific donor-unused rates from a Jeffreys Beta posterior for the 30 s2 and 30 s3
     audited items and applying them only to the 1,540 unaudited critical items, M=40
     imputations, pooled with Rubin's rules using the cluster-robust covariance. A secondary
     move-to-s0 variant codes inactive rows as s0; it contaminates the reference and is
     reported but not the headline.
  3. **Missingness.** 525/9,600 analysis cells lack a label (5.47%). They decompose into 336
     cells in 84 prefix x model units whose V reference is unparsed and 189 cells whose arm
     row is unparsed. IPW: logistic observation model on model x arm, domain, and donor;
     inverse-probability weights for marginal arm rates, the s3-s2 and s3-s0 risk
     differences, and a weighted conditional-logit slope (group-mean weights, explicitly
     labelled a pseudo-likelihood approximation), with fixed-weight prefix-cluster
     bootstrap CIs (the weights are held at the full-sample fit, which is stated). A
     task x model x arm post-stratified cross-check is reported because missingness is
     strongly task-dependent. Manski bounds over all 9,600 cells are the design-robust
     result: missing outcomes set to 0 or 1 for each arm, with the corresponding extreme
     slope refits. No MCAR assumption is claimed.
  4. **Recovery.** v2 semantic risk set exactly as stage 15 (`signatures_differ`, parser v4
     / signature v2, nonflag, reserve excluded; persistent restricted to the deterministic
     200-prefix selection). Aalen-Johansen cumulative incidence treats terminal
     non-recovery (final answer, parse failure) as a competing event and ran-to-H4 as
     administrative censoring; Kaplan-Meier is retained only for reconciliation. Paired
     tests are exact McNemar on H=4 recovery: transient s2 vs s3 within model and pooled,
     and pairwise model comparisons for transient s3, Holm-adjusted over the three model
     pairs.
- **What is not claimed:** these are post hoc robustness refits of frozen ledgers, not new
  preregistered confirmatory tests. They do not alter the primary sample, the v2 recovery
  risk set, the assigned-severity estimand, or any gate. The reclassification extrapolation
  assumes audited donor-unused rates transport to unaudited critical items conditional on
  arm; the IPW assumes MAR given the listed covariates. Both assumptions are stated in the
  artifact and the report.
- **Consequences:** new `scripts/19_rowlevel_refits.py`, `tests/test_rowlevel_refits.py`,
  and `artifacts/analysis/rowlevel_refits.json`. The artifact is gitignored like every
  analysis JSON and is picked up by the P6.5 release build. Paper text is folded in by
  Task 6; this task does not edit the paper.
- **Outcome (2026-11-23):** the artifact was generated from this tree. The pooled
  cluster-bootstrap LRTs remain significant at the 1/151 floor (p=.0066 for both terms);
  after Holm over the six per-model cluster-robust Wald tests, qwen categorical and
  quadratic and ministral categorical survive at .05. The realized-severity ORs overlap
  the assigned ORs, so the old point-only claim that the assigned estimates are materially
  attenuated is not confirmed. Aalen-Johansen equals the crude recovery primary in every
  cell because administrative censoring is horizon-only; Kaplan-Meier is the inflated
  estimator. Full numbers are in `.superpowers/sdd/p6-q1-hardening/task-4-report.md`.

## D-045 - P4.7/P5 release package, one-command validation, submission staging

- **Date:** 2026-11-22
- **Status:** accepted (staging; human-gated items listed, not claimed)
- **Context:** T1–T6 done (HEAD f86916e). P4.7/P5 require: scrubbed artifacts/ledger
  extracts + manifest + packets + analysis JSONs with DOI; table-to-artifact map;
  one-command validation implemented or removed; PII re-scan + license verification; AI
  disclosure; byline/ORCID/CRediT/ethics sign-off; 14-file Overleaf zip + clean-room
  compile; cover letter + highlights + keyword limits; author freeze; DOI mint + resolve;
  submission checklist. Deferred items carried in: T4 inference-JSON regen, T5 24-table
  count (25 with `tab:utility`), T5 old-bib et-al, T6 release-carry requirement, Fig. 4
  replacement, no local TeX compile.
- **Decision:** Build `scripts/18_build_release.py` (numbered 18: stage 17 is taken by
  `17_wrong_direction.py`, same convention as T4's 16-vs-15). `--build` stages
  `release/ToolResult-800-v1.0/` (123 files, gitignored like all prior release
  candidates): manifest + sidecar + perturbations + source pin, 880 scrubbed prefixes,
  scrubbed ledger extracts (base/recovery/jitter/G1-v3; `_backup` and `parser-v3`
  variants excluded), audit packets/sheets/instructions + panel record + second-rater
  agreement, all 27 analysis JSONs + companions, T6 packets/maps/codes, prereg +
  amendments + deposit note, upstream MIT text + model-license record, `TABLE_MAP.md`,
  `VALIDATION.md`, `SHA256SUMS`, `release_record.json`, `pii_rescan.json`.
  `--validate` implements the one-command target (paper claim corrected to describe it):
  L1 on the package alone (manifest chain, SHA256SUMS, crude triple, v2 bridge + Wilson,
  severity 7/11/16, exact McNemar/LRT/H5 recomputes, wrong-direction partition, g3
  totals, utility counts, PPV bound, 25-table map coverage, identifier re-scan);
  L2 `--rerun` reruns all five producers and diffs modulo `recorded_utc`/`git_commit`.
  Result 2026-11-22: 17/17 L1, 22/22 with rerun — this closes the T4 regen item (all
  five JSONs rebuilt bit-identical).
- **Manifest gate enforced:** the builder refuses without `audit.gate_pass` (same rule
  as `10_release.py`); the manifest itself records `label_source:
  ai_preaudit_deferred_human`, so the provisionality travels with the package.
- **M8 second half (prereg/config hashes):** not added to every producer
  (would require touching the frozen-by-convention producers for metadata only);
  instead `release_record.json` binds prereg/field-registry/renderer/source-pin/manifest
  hashes to every bundled file, and the paper sentence now states that. The run ledgers
  already carry manifest/prompt/renderer versions and the JSONs carry `git_commit`.
- **PII findings (automated scan, 0 blocking hits):** reserved-domain placeholders
  (`@example.com`, fictional 555/123-4567 numbers, generic role addresses — all
  model-hallucinated, no real persons), synthetic-token echoes (`user_TOKEN@email.com`;
  PII map never released, not re-identifiable), and one scrubber-artifact fragment
  (`person_0f41e336893e.ahmed6699@example.com`: given-name + digits surviving inside one
  frozen prefix + derivatives; kept bit-identical per freeze integrity, bounded to one
  pseudonymized identity, explicitly flagged for the human re-scan). Human re-scan,
  ethics determination, DOI mint, tag/release, and second-person verification are author
  actions (checklist records them unsigned).
- **Table count (25, justified, not trimmed):** every table is a gate/prereg traceability
  artifact (`TABLE_MAP.md`); T5 already cited all floats and folded `tab:fit`. Cutting
  tables now risks T1–T6 number traceability for craft points; supplement migration is
  offered as an editor-directed option in the cover letter path, not taken unilaterally.
- **Bib (T5 old-et-al closed by fixing, not justifying):** full author lists verified
  against arXiv abs pages 2026-11-22 for toolllm (19), webarena (12), sycophancy (19),
  agentbench (22), tool_survey (41), agent_survey (13), helm (~50), toolscan (18), and
  toolbehonest (13); taubench confirmed 4-author complete and apibank confirmed complete;
  BFCL URL resolves (V4, updated 2026-04-12); only remaining et-al is
  the 100+-author Llama herd (file convention, noted).
- **Fig. 4 verified T5-done:** `figures/fig4.png` is the stamp-free conceptual schematic;
  caption states "(not study data)". No local TeX compile exists on this host
  (`latexmk`/`pdflatex` absent); substituted with structural checks (75/75 labels, all
  floats cited, 69/69 bib keys resolve) + tests; clean-room compile is an author/Overleaf
  step recorded in the checklist.
- **Consequences:** `make validate-release` (+ `tasks.ps1`) is the release-validation
  target; `docs/submission/` holds cover letter, highlights (4×≤85), checklist,
  authorship freeze, DOI deposit record, license verification. Provenance stays
  "multi-role agent panel, author-overseen" with the T6 single-agent part disclosed.

---

## D-044 - P4.6 new-evidence design: task-utility endpoint (no GPU, no amendment)

- **Date:** 2026-11-22
- **Status:** accepted (exploratory design; logged before any coding/analysis runs)
- **Context:** P4.6 requires at least one new evidence stream or tightened claims. C10
  (no task-success endpoint) is still open: T5 delivered only the harm-direction proxy from
  perturbation records, explicitly framed as "not task success". The P2 menu is
  task-success/utility, second renderer, human audit, intervention probe, frontier control;
  H=8/temperature are D-037 exploratory. GPU (`uiu-h200`, idle, 18 GB free) is reachable,
  but every GPU stream needs new generations plus new serving/analysis plumbing, while a
  task-utility endpoint can be built entirely from existing ledgers plus blinded coding.
  The T6 instruction forbids subagents, so no multi-session agent panel is available.
- **Decision:** Run stream U-1, "task-utility endpoint", CPU-only:
  (a) Deterministic donor-path adherence on all 1,053 semantic s3-switched pairs
  (primary sample, reserve excluded): model decision vs the donor's factual continuation
  from `data/interim/candidates.jsonl` (100% join coverage: 164 tool-call, 636 text).
  Tool-call donors score by tool-name match; text donors (free-text answers) score by
  answer-type match (model `final_answer` vs tool action). Primary contrast is the paired
  s0-to-s3 drop in adherence (rendering/capability cancel within pair).
  (b) Blinded single-agent adequacy coding on 120 distinct primary prefixes (40/model,
  parsed at both arms; 14 unparsed pairs auto-coded degraded, not agent-coded) x 2 arms
  (s0, s3) = 240 codes, plus 40 blinded re-codes for intra-rater agreement (Cohen's k).
  Packets carry a blind id only; the packet-to-pair map stays sealed until coding is done.
  Model id, arm, and donor continuation are hidden from the coder.
  (c) Utility x wrong-direction cross-tab reusing the stage-17 exclusive classes.
- **Coding rubric (pre-specified, frozen before coding):** 2 = adequate (executed
  against the TRUE tool result, the decision correctly serves the user's stated request:
  right tool with materially correct arguments, or a text answer factually consistent
  with the true result and responsive); 1 = degraded (no incorrect state change, but the
  task is not advanced: redundant lookup, re-ask for provided info, no action, refusal,
  immaterial argument errors); 0 = harmful (would execute an incorrect state change, or
  asserts false task-critical information); 9 = unjudgeable (packet lacks context).
  Parse failures/refusals in sampled pairs are auto-coded 1 by rule and excluded from
  the agent pool. Reasons are terse category phrases; no values are quoted (PII-free).
- **GPU/hours/amendment:** GPU hours spent on this stream: 0.0 (no new generations; the
  slice stays idle). H=8 continuation and the never-run semantic top-up (33 Ministral +
  48 Qwen s3, plus s2) are deferred; the exact semantic estimand stays bounds-only per
  T2 (bounds <39%, gate conclusion robust), so no prereg amendment is needed and the
  confirmatory estimates are untouched. D-037's exploratory GPU authorization is unused,
  not violated: nothing is pooled and nothing confirmatory changes.
- **Traceability:** committed `scripts/16_task_utility.py` (sampling, packets,
  deterministic layers, analysis join) + `tests/test_task_utility.py` (fixtures, schema,
  determinism). Working files `task_utility_packets.json`, `task_utility_codes.json`,
  `task_utility_recodes.json`, `new_evidence.json` (with hours) are gitignored
  regenerable/judgment artifacts per the T2-T5 precedent (audit sheets set the same
  precedent for judgment artifacts); the release package (T7) carries them to the DOI.
- **Limits (reported in the paper):** single-agent coding (no multi-session panel; weaker
  independence than D-043); donor path is one valid path, not certified task success, and
  donor-trajectory success was not verified; text-donor type-match is coarse; adequacy is
  judged on the next decision only, not rollout reward.
- **Correction note (fix round 1, 2026-11-22; original text above retained):** the design-time
  donor split "164 tool-call, 636 text" counts prefixes over the 800-prefix sample (from a
  pre-run scratch join), while the executed deterministic layer reports 245 tool / 794 text
  over the 1,053 switched pairs (and 1,039 analyzed): tool-donor prefixes are
  over-represented among switchers. No design, sample, or code changed; the executed
  245/794 split in `new_evidence.json` and the paper is authoritative.
- **Amendment record (2026-11-22; supersedes "no amendment is needed" above for the record
  only):** the task-utility endpoint is entered as A-010 in `prereg/AMENDMENTS.md` as an
  exploratory post-freeze secondary. The scientific content is unchanged: no new generations,
  no pooling with confirmatory estimates, and the no-task-success claim boundary stands. The
  earlier statement judged the endpoint non-confirmatory and therefore outside amendment
  scope; the P6.1 record-integrity audit records it so every post-freeze endpoint has an
  amendment row.

---

## D-043 - Agent verification panel; final label-free audit numbers

- **Date:** 2026-11-19
- **Status:** accepted (verification record; supersedes D-039's interim numbers)
- **Context:** The label-free sheets were re-rated after the first label-free round because the
  severity packet carried design-order and arm-derived annotations and showed only the first
  changed leaf. The packet was rebuilt four times (leak removal, shuffled order, second leaf,
  donor continuation); the final round is the fourth version and the first three are archived.
  The author declined human-coauthor verification, because the team has no independent domain
  rater, and asked for a multi-role agent panel. D-039 left verification pending.
- **Decision:** Use a verification panel, not human coauthors: one independent verifier per audit
  (severity, outcome, recovery) and two second raters on a stratified 120-item subset (40/40/20).
  The verifiers re-derived codes from the same label-free evidence; severity was verified twice
  (sheet-visible and fully blind). Corrections are recorded in
  `artifacts/audit/verification/panel_record.json`; the sheets keep the blind rater columns and
  the pre-registered gates remain on the rater majority. Provenance is "multi-role agent panel,
  author-overseen"; it is not human verification.
- **Findings:** Outcome 158/160 agree (2 corrections; PPV 1.00, recall .75, with OUT-029/078/156
  the three missed silent items); recovery 66/80 agree, all 14 corrections toward the automatic
  coding, and the verifier reproduces the automatic endpoint and step 80/80; severity 114/120
  (sheet-visible) and 108/120 (blind), s2/s3 decision-changing 81.7% and 73.3%. Second raters:
  severity α .917, outcome κ .942, recovery κ .918/.907; against the primary severity consensus,
  α .946.
- **Final severity round:** α .911 nominal/.959 interval; s2/s3 53/60 = 88.3% (FAIL); s1 27/30
  non-decision; s3 absurd 1/30; Jonckheere-Terpstra p < 1e-4. The three passes flag 7 (majority),
  11 (sheet-visible verifier), and 16 (blind verifier) of the 60 s2/s3 items as donor-unused.
- **Consequences:** D-039's interim α .957/.981 is superseded. The paper reports three failed
  criteria (parser, severity s2/s3, recovery), the stimulus-classification diagnosis (short-token
  and redundant-route usage false positives; about one in four critical-arm stimuli is
  donor-unused under the blind verifier), and the independence limits (shared model family; two
  severity sessions identical on 116/120 items; the final sessions had seen earlier packet
  versions). Per-level dose magnitudes are descriptive; the threshold reading is retained because
  correcting the misclassification would steepen the s1-s2 contrast. No threshold, sample, model,
  or analysis rule changed.
- **Amendment record (2026-11-22):** the label-free-primary decision is entered as A-008 in
  `prereg/AMENDMENTS.md`; this entry supplies the final numbers and panel record.

---

## D-042 - Pre-registered secondary analyses completed; linearity rejected

- **Date:** 2026-11-19
- **Status:** accepted (pre-registered diagnostics; interpretation update)
- **Context:** The pre-registered linearity LRT/quadratic term, tier ORs, s2-vs-s3 McNemar,
  domain/donor strata, strict-vs-lenient coding, and realized MDE were missing from the paper.
- **Decision:** Report them: pooled categorical LRT χ²(2)=25.03, p=3.7e-6; quadratic b=0.143
  (SE 0.036), p=7.4e-5; tier ORs 1.27 / 4.60 / 11.21; s2-vs-s3 McNemar p=2.1e-20 pooled;
  domain interaction p=.035 (exploratory, unadjusted); donor p=.61; strict 0.876 [0.768, 0.996]
  vs lenient 0.434 [0.296, 0.574]; realized MDE 0.166; placebo-excluded β 1.031 [0.881, 1.193].
- **Consequences:** The slope is reported as a summary of a threshold at s2, not a per-level law;
  the abstract and results are reworded. No criterion changed.

---

---

## D-041 - Gate-record corrections: G1 amendment timing and G0 provisional flag

- **Date:** 2026-11-19
- **Status:** accepted (record correction)
- **Context:** A-004 (the G1 placebo-criterion change) was labeled pre-freeze and "blind to
  outcomes", but the G1 calibration ran after the manifest freeze and the criterion changed
  after those format-jitter values were seen. `g0_audit_result.json` carries `gate_pass: true`
  while the human G0 sheet is blank (the gate is provisional under D-021).
- **Decision:** A-004 is relabeled post-freeze/after-G1 and not blind to the G1 values. The G0
  artifact gains provisional and human-verification flags; the paper states that the manifest's
  `gate_pass` field records the D-021 adoption, not a human pass.
- **Consequences:** No data or analysis change; the disclosure is accurate.
- **Amendment record (2026-11-22):** the parser-failure criterion's provenance is entered as
  A-011 in `prereg/AMENDMENTS.md`: `<1%` is a pre-freeze protocol criterion in
  `docs/GATES.md` (commit `ea0f95b`, 2026-11-09), not part of the frozen G3 row. No threshold
  changed.

---

## D-040 - Recovery curves censor at last follow-up (estimator correction)

- **Date:** 2026-11-18
- **Status:** accepted (estimator correction; pre-submission)
- **Context:** The Kaplan-Meier, exponential, and Weibull code censored early-terminated
  episodes at H=4 instead of their last observed step, biasing every recovery curve downward.
- **Decision:** Recovery events now carry `last_step` (stage 09e), and the estimators censor at
  the last observed step. Re-estimated transient s3 recovery by H=4: Qwen 32.4%, Ministral
  47.6%, Llama 28.2% (27.3/34.7/27.2 under H=4 censoring, retained as a sensitivity). Secondary
  sets reach 35.0-52.1%. G4 still fails on every primary point estimate; Ministral is close to
  50%.
- **Consequences:** Paper tables and text updated; half-lives 4.3-8.0 steps; Weibull rejects
  2/3 primary groups.
- **Amendment record (2026-11-22):** entered as A-009 in `prereg/AMENDMENTS.md`, with the
  post-estimate timing and "not blind" status disclosed.
- **Supersession (2026-11-23; P6.2):** the recovery figures in this entry are v1
  run-risk-set results, not censoring variants. `27.3/34.7/27.2` is the crude Events/n
  triple on the v1 run-time hash risk set, and `32.4/47.6/28.2` is its Kaplan–Meier
  secondary, both from `artifacts/analysis/g4_recovery.json`. The "Secondary sets reach
  35.0-52.1%" range and the "Weibull rejects 2/3 primary groups" result are likewise
  v1-derived: under v2 the KM secondary range is 23.6–49.3% and the Weibull shape is
  rejected in all three primary groups (p=.0047, 1.1e-14, .00063; the v1 Qwen p=.0132
  was the lone non-rejection). The v1 half-lives 4.3–8.0 steps are superseded by 5.0–10.9
  for the primary groups (4.7–10.9 across all groups). The primary recovery set is now
  the v2 semantic risk set, crude `24.4/32.9/21.3` (KM `28.2/44.6/22.0`;
  `g4_recovery_v2.json`), everywhere in the paper and submission documents. The v1
  values are retained only as the reconciliation record, and the "Ministral close"
  reading of D-040 is retired. No historical text above is changed.

## D-039 - Label-free audit re-rating (supersedes the label-visible round)

- **Date:** 2026-11-18
- **Status:** accepted (validity fix; final numbers and verification in D-043)

- **Context:** The first audit round used packets that still carried the mechanical reference
  labels (design level, criticality, automatic labels). Review identified this as a validity
  threat: the agreement statistics measured conformance to the anchor.
- **Decision:** Rebuild all packets without reference labels or automatic answers, keeping the
  manipulation evidence (injected values for outcomes, per-step decisions for recovery), and
  re-rate with independent sessions: three severity, two outcome, two recovery. The label-visible
  round is archived (`artifacts/audit/blind/_labelvisible_round/`) and reported as a sensitivity.
  Verification of the label-free sheets is recorded in D-043.
- **Consequences:** Final label-free round: severity α .911 nominal / .959 interval, with the
  s2/s3 decision-changing criterion failing at 88.3%; outcome κ .987; silent PPV 1.00 (9/9;
  exact 95% lower bound .66) with silent recall .75; recovery κ .920/.917. The earlier
  α .957/.981 figures came from the annotated, level-ordered severity packet and are archived,
  not reported (D-043). The label-visible round's α .919/κ .975/PPV 1.00/recovery .787 are
  retained as the sensitivity.
- **Amendment record (2026-11-22):** entered as A-008 in `prereg/AMENDMENTS.md`, with the
  post-round timing and "not blind" status disclosed.

---

---

## D-038 - Exploratory additions: field taxonomy, task-clustered inference, held-out reserve

- **Date:** 2026-11-18
- **Status:** accepted (exploratory; clearly labeled in the paper)
- **Context:** Review preparation identified three analyses that add depth without changing the
  confirmatory estimates: a field-type breakdown of switches and silent propagation; task-level
  (rather than prefix-level) resampling for the pooled slope; and the 80 reserve prefixes, which
  were generated but excluded from the primary sample, as a held-out sign check.
- **Decision:** Report all three as exploratory. Field types are classified by the last json_path
  token (rules in `artifacts/analysis/field_taxonomy.json`); task clustering uses the task id
  parsed from the prefix id; the reserve estimate is labeled post-hoc and not pooled.
- **Consequences:** Findings: identifiers and money carry ~45% silent shares of their switches
  (status 0/102); task-clustered CI [0.758, 0.996] is essentially unchanged; reserve-only
  β = 0.781 [0.443, 1.194]. The confirmatory sample and estimates are unchanged.

---

---

## D-037 - Exploratory robustness extensions approved (outside the confirmatory run)

- **Date:** 2026-11-18
- **Status:** accepted (exploratory; no change to the confirmatory claims)
- **Context:** The confirmatory run used about 8.9 of the 45 GPU-hour cap. The authors approved
  additional exploratory robustness work on the same H200 MIG slice (18 GB VRAM).
- **Decision:** Run (a) recovery continuation to H=8 on the same at-risk sequences, and (b) a
  decoding-temperature robustness subset if the plumbing is low-risk. Both are labeled
  exploratory, tracked with their own GPU hours, and never pooled with the pre-registered
  confirmatory estimates. The 45-hour G2 cap applies to the confirmatory run and is unaffected.
- **Consequences:** H=8 and decoding results appear only in a clearly marked exploratory section
  with their own hours; the primary claims stay the H=4/G3 estimates. Any change to the
  confirmatory analysis would require an amendment instead.

---

---

## D-036 - Confirmatory analysis sample: 800 primary prefixes; reserve excluded

- **Date:** 2026-11-18
- **Status:** accepted (analysis-sample conformance)
- **Context:** The main run generated the full 880-prefix matrix (13,200 base generations) because
  the frozen payload contains 800 primary plus 80 reserve prefixes. The preregistered analysis
  sample is the 800 primary; the reserve exists to replace audited failures.
- **Decision:** Stage 13 excludes the manifest's `reserve_ids` from the confirmatory estimates by
  default; `--include-reserve` remains for sensitivity only. Re-estimated on the 800 primary
  prefixes: pooled β 0.877 (SE 0.059, p = 2.3e-49, 95% CI [0.770, 0.998]; 617 prefix clusters,
  2,458 slope rows; all three models positive; silent propagation 419/1,964 = 21.3%).
- **Consequences:** The paper reports the run envelope (13,200 base generations) and the analysis
  sample (800 primary) and states the exclusion. No criterion changed; the exclusion makes the
  analysis match the preregistration. The audit packets retain reserve items as label-validity
  evidence; the audit gates do not depend on the analysis sample.
- **Amendment record (2026-11-22):** entered as A-007 in `prereg/AMENDMENTS.md`, with the
  post-run timing and "partly blind" status disclosed.

---

---

## D-035 - Author verification of the blind audits

- **Date:** 2026-11-18
- **Status:** accepted (verification complete; D-027 closed for the G3/G4 audits)
- **Context:** The blind fills were presented to the author with the rows that carried risk:
  14 severity disagreements, 37 outcome rows (9 automatic-YU confirmations, 26 automatic-label
  overrides, 2 rater disagreements), and 14 recovery rows (10 rater disagreements, 4 agreed
  corrections).
- **Decision:** The author accepted the blind ratings: null injections are not absurd and the
  single-leaf route changes stay at severity 2; all 9 automatic-YU items are silent propagation;
  the 26 outcome overrides stand; the outcome disagreements resolve to OUT-068 = Y_other and
  OUT-141 = N; the 10 recovery adjudications follow the recommended calls
  (REC-028/040/054/067 = R1, REC-037/038/043 = censored, REC-045/079 = R2, REC-073 = R2); the 4
  agreed corrections (REC-034/051/064/068) stand.
- **Consequences:** The severity, outcome, and recovery audit gates were author-verified for the
  label-visible round; that round is superseded by D-039, and the reported label-free round is
  verified under D-043. The sheets keep the blind rater columns; adjudications are recorded in
  `artifacts/audit/human_verification.json`. The G0 sheet verification (D-021) remains deferred.

---

---

## D-034 - GPU-hours reconstruction for the G2 budget record

- **Date:** 2026-11-18
- **Status:** accepted (budget evidence)
- **Context:** The ledger `gpu_hours` field is 0.0 on every row, so the 45 GPU-hour cap could not
  be checked from the ledger.
- **Decision:** Reconstruct usage from ledger `timestamp_utc` and `latency_ms`: 21,611 generation
  rows (main 13,200; jitter 1,200; recovery 7,211). Summed generation time **8.82 h**; wall-clock
  upper bound **≈8.95 h** (stage spans per model). Recorded in `artifacts/cost/main_cost.json`.
- **Consequences:** The 45 GPU-hour cap is not binding. The ledger cost field remains unreliable
  for future runs; each GPU shard must state its hours explicitly until it is fixed.

---

## D-033 - G4 recovery gate failed (reported as a failure)

- **Date:** 2026-11-18
- **Status:** accepted (gate result)
- **Context:** G4 criteria: ≥50% of the transient s=3 risk set recovers by H=4, and the Weibull
  shape is not rejected (p ≥ .01). Observed on the 800 primary prefixes: recovery by H=4: 27.3%
  (Qwen), 34.7% (Ministral), 27.2% (Llama); Weibull rejected for 2/3 models (Ministral
  p=2.1e-4, Llama p=2.6e-3; Qwen p=.228).
- **Decision:** Report the failed gate and the recovery curves; per `docs/GATES.md` the fail
  action is to report RMST/curve with the half-life exploratory only. No smoothing.
- **Consequences:** `artifacts/analysis/g4_recovery.md` is the G4 evidence; the manuscript states
  the failure in the abstract and limitations.

---

## D-032 - G3 gate outcome: parser-failure criterion failed (reported)

- **Date:** 2026-11-18
- **Status:** accepted (gate result; claim boundary)
- **Context:** G3 criteria: pooled β > 0 (pass, β 0.877, 95% CI [0.770, 0.998]); per-model slopes
  positive in ≥2/3 (pass, 3/3); severity α ≥ .75 (pass, .9185); outcome κ ≥ .80 (pass, .9748);
  recovery κ ≥ .75 (pass, .787/.787); silent PPV ≥ .90 (pass, 1.000); **parser failure <1% (fail:
  205/13,200 = 1.55% hard parse errors; 3.45% including refusals 250/13,200)**. Evidence:
  `artifacts/analysis/g3_report.md`, `artifacts/audit/blind_audit_result.json`.
- **Decision:** Report the parser-failure criterion as failed. Per `docs/GATES.md` the G3 fail
  action is a null/measurement report without a content-sensitivity claim; the manuscript reports
  the slope as a preregistered measurement estimate with the gate failure disclosed and makes no
  law or unqualified content-sensitivity claim.
- **Consequences:** The README claim boundary stays conservative; the abstract and limitations
  state the G3 parser-rate failure and the G4 recovery failure. No threshold is relaxed. The
  agreement figures in this entry are from the pre-D-039 round; the final label-free values and
  the severity $s2/s3$ failure are in D-043.

---

## D-031 - H200 environment check and GPU-hours accounting observation

- **Date:** 2026-11-18
- **Status:** observed (no change made; AGENTS.md §2.1 change control)
- **Context:** Pre-analysis check of the approved `uiu-h200` slice, read-only.
- **Observed:** GPU idle (H200 MIG 1g.18gb, 18,432 MiB, 1 MiB used, no processes); driver
  580.178.04 matches AGENTS.md; `nvidia-smi` advertises **CUDA 13.0** while AGENTS.md records
  CUDA 13.5 (no `nvcc` on PATH; vLLM wheels bundle their runtime, so nothing is blocked).
  Project space 11 GB + HF cache 26 GB (within the 200 GB cap); vLLM 0.33.0 venv present;
  no tmux/screen jobs. The main ledgers record `gpu_hours = 0.0` on every row.
- **Decision:** Do not change the driver, CUDA, MIG settings, or system libraries. Record the
  CUDA-version discrepancy here; the G2 cost accounting was reconstructed separately (D-034).
- **Consequences:** Any future GPU work states its hours explicitly in the shard report until the
  ledger cost field is confirmed or fixed.

---

## D-030 - Safe in-place rescore in stage 09c

- **Date:** 2026-11-18
- **Status:** accepted (tooling fix)
- **Context:** `scripts/09c_rescore.py` removed the output path before reading the input. Running
  an in-place rescore (`--input ledger.jsonl --output ledger.jsonl --force`) deleted the ledger
  before reading it. The working ledgers were recovered from the preserved parser-v3 copies.
- **Decision:** Materialize the input rows before touching the output; add a regression test that
  runs an in-place rescore end to end.
- **Consequences:** In-place rescoring is safe; the pre-rescore ledgers remain as
  `ledger_parser-v3.jsonl` for provenance.

---

## D-029 - Blind-rater audits and per-row rater provenance

- **Date:** 2026-11-18
- **Status:** accepted (audit provenance; label-visible round checked under D-035, superseded by D-039/D-043)
- **Context:** The how-to previously prescribed `label_source=ai_preaudit_deferred_human` on every
  sheet row. The authors asked for meaningful row notes that name who rated the item.
- **Decision:** Run three blind rater sessions (severity 3 raters; outcome and recovery 2 raters
  each, the recovery round using the per-step evidence), each seeing only the packet copies in
  `artifacts/audit/blind/`. The sheets' `notes` column names the raters
  (`blind_rater_1;blind_rater_2;blind_rater_3` for severity, `blind_rater_1;blind_rater_2` for
  outcome and recovery) plus `rater_disagree` / `ref_override` markers and short remarks. The
  mechanical pre-fill is preserved in `artifacts/audit/blind/_prefill_backup/` and in the
  `_parser-v3_snapshot/`. Scoring is stage `scripts/08c_blind_audit_score.py`.
- **Consequences:** The fills are AI-rater judgments, not human ratings; every gate remains
  provisional until the authors' verification (D-021, D-027). The raters' raw files are kept in
  `artifacts/audit/blind/`.

---

## D-028 - Outcome-signature conformance fix (parser v4 / signature v2)

- **Date:** 2026-11-18
- **Status:** accepted (measurement fix, before G3 analysis; no criterion changed)
- **Context:** The blind audit found the automatic outcome coder deviating from the preregistered
  outcome signature (prereg §"Outcome signature"): `y_action` compared the whole `(tool,
  arguments)` instead of the tool name / action verb; `y_silent` fired with `Y=0` and matched
  values as substrings (`20` inside `2024-05-20`, `payment` inside `payment_…`); final-answer
  signatures ignored decision-critical values (refund/total amounts, IDs, dates) while counting
  incidental action words anywhere in the text; free-text `summary` arguments counted as decision
  slots. Both blind raters independently reported the same defects (27/160 audit labels affected;
  silent-propagation PPV 13/17).
- **Decision:** Bring the implementation into line with the preregistration (parser
  `toolresult-parser-v4`, signature schema `toolresult800-signature-v2`):
  tool-name/verb action switch; canonical status and value slots (Decimal amounts, ISO dates,
  times, identifiers); prose argument keys excluded; typed, attributed silent propagation
  (false value asserted by the model's decision and absent from the reference); a flag counts as
  `Y=1`; the flag vocabulary covers explicit discrepancy/inconsistency language
  (discrepancy/discrepancies, inconsistencies, unusual). Rescore the existing ledgers with stage
  09c (generations unchanged); recompute recovery events with stage 09e; regenerate the audit
  packets and re-score; recompute jitter stability.
- **Timeline disclosure:** an earlier G3 run under the previous coder had been recorded in
  `ROADMAP.md` (pooled β 0.684, CI [0.584, 0.797]; artifact not retained). The fix was driven by
  the label-quality audit, not by the slope; both analyses are positive. The paper reports both
  numbers and the sequence audit → fix → rescore → analysis.
- **Consequences:** 27/160 audit automatic labels changed; automatic-YU items 17 -> 9 with PPV
  1.0; seed-repeat stability recomputed (1.000 / .9895 / .9894, all >= .90). Every
  label-derived number (G1 jitter, arm switch/silent rates, G3 slope) is recomputed from the
  rescored ledgers; no preregistered threshold or definition changed. Machine-readable detail in
  `artifacts/audit/blind_audit_result.json`.

---


- **Date:** 2026-11-15
- **Status:** accepted (audit provenance; no outcome data affected)
- **Context:** The preregistration requires human ratings for the severity audit
  (120 items, 3 raters), the outcome audit (160 items, 2 raters), and the recovery
  audit (80 sequences, 2 raters). The G0 gate was already filled from an AI
  pre-audit under D-021 with verification deferred. The remaining audit gates would
  otherwise block the confirmatory analysis until the authors are available.
- **Decision:** The agent prepares the audit packets and the AI pre-audit drafts for
  all three gates, and records `label_source=ai_preaudit_deferred_human` with notes
  on every row. The authors perform the final verification after the experiments
  finish. No gate is claimed as human-verified before that point.
- **Consequences:** G3/G4 results may be computed and reported as provisional until
  the authors verify. Any disagreement found at verification must be logged in
  `prereg/AMENDMENTS.md` before the claim is finalized; if verification fails a gate,
  the manuscript must state the failure rather than smooth it over. The pilot and
  G0 figures are unaffected.

---

## D-026 — G1 placebo gate uses the format-controlled negative control

- **Date:** 2026-11-15
- **Status:** accepted (G1 calibration amendment; no target outcomes analyzed)
- **Context:** All three models showed large V-vs-s0 jitter (Qwen 20.3%, Ministral 36.7%,
  Llama 45.6%). The differences are format-driven: V is raw JSON and s0 is an indented
  key-value prose list. The format-controlled comparison, s0 vs s1 (faithful prose vs one
  non-critical prose change), is 11.9%, 13.3%, and 10.3%, respectively. The primary slope uses
  s0..s3, all in the same prose format; V is excluded as a separate anchor.
- **Decision:** The G1 placebo gate becomes **negative-control jitter (s0 vs s1) ≤20%**.
  V-vs-s0 jitter is retained as **format_jitter**, reported as a secondary format-sensitivity
  result, not a gate. The primary estimand, arms, sample, and severity rubric are unchanged.
- **Consequences:** G1 can pass on the format-controlled manipulation. The paper must report the
  raw-JSON-vs-prose format effect explicitly and bound the claim to the prose-arm contrast; it
  must not present V as a format-neutral baseline. Amendment recorded in
  `prereg/AMENDMENTS.md` before G2.

---

## D-025 — Parser v3: action-verb slots and ledger re-scoring

- **Date:** 2026-11-15
- **Status:** accepted (G1 calibration fix; no target outcomes analyzed)
- **Context:** Parser v2's status set still included generic terms (`succeed`, `fail`, `change`,
  `update`, `cannot`, `unable`, `not possible`). Qwen's placebo jitter fell from 42.4% to 23.7%,
  still above the 20% gate. Restricting the slot set to decision verbs gives 13.3%.
- **Decision:** A final answer hashes to the sorted set of decision verbs it asserts
  (`cancel`, `book`, `modify`, `confirm`, `deny`, `refund`, `transfer`, `upgrade`, `downgrade`,
  `exchange`, `return`, `keep`) plus the first such verb as the action. Generic status words,
  numbers, dates, and identifiers are not slots; `Y^U` still checks the false value against the
  full output. Parser version becomes **`toolresult-parser-v3`**. Existing G1 ledgers are
  re-scored with `scripts/09c_rescore.py` and the gate is evaluated with
  `scripts/09a_run_all.py --score-only`; the stored `output_text` is never changed.
- **Consequences:** G1 is re-evaluated without regenerating 900 outputs. The main run uses
  parser v3 directly. The primary Y is decision-level for final answers; value-level silent
  propagation remains a separate reported outcome.

---

## D-024 — Parser v2: final-answer signatures use status/action slots

- **Date:** 2026-11-15
- **Status:** superseded by D-025 (parser v3; v2 was never used for a target outcome)
- **Context:** Qwen's first fixed-harness calibration had 42.4% placebo jitter. The differences
  were almost entirely paraphrased `final_answer` text; action-level differences were 10%.
  The preregistration specifies the final answer's normalized action verb plus decision-critical
  slots, not the full answer string, so the parser was too strict.
- **Decision:** A final answer now hashes to an action verb plus a sorted set of status slots
  (`cancel`, `book`, `modify`, `confirm`, `deny`, `refund`, `transfer`, `upgrade`, `downgrade`,
  `exchange`, `return`, `keep`, `cannot`, `unable`, `not possible`, `succeed`, `fail`, `change`,
  `update`). Numbers, dates, and identifiers are not signature slots; silent propagation
  (`Y^U`) still checks the perturbation's false value against the full output. Parser version
  becomes **`toolresult-parser-v2`**. Completeness is diagnostic, not one of the five
  preregistered G1 gates; an unparsed V row reduces the paired denominator and is penalized by
  the parse-rate gate.
- **Consequences:** G1 is rerun. The primary Y is decision-level for final answers, while Y^U
  captures value-level silent propagation; both are reported. The frozen data, sample, arms,
  and estimand are unchanged.

---

## D-023 — G1 harness fix: exclude `think`, constrain JSON, 1,024-token budget

- **Date:** 2026-11-15
- **Status:** accepted (G1 calibration fix; no target outcomes analyzed)
- **Context:** The first G1 calibration run passed Qwen 300/300 but Ministral parsed only
  76/300 (25.3%): 42 empty outputs, 134 truncated `final_answer` objects, and a few prompt
  echoes. `think` is a real τ-bench tool, but using it as a reasoning scratchpad spends the
  decision budget without taking a task action.
- **Decision:** Exclude `think` from the prompt tool list and from constrained decoding; force
  one JSON object with either a listed task tool or `final_answer` using a vLLM structured
  regex; raise the decision budget from 256 to 1,024 tokens; remove the `\n\n` stop sequence.
  The regex is built from the filtered domain tools and applied uniformly to all three models.
- **Evidence:** On five previously failing Ministral rows, the constrained run parsed 5/5 as
  real task actions (`get_user_details`, `search_direct_flight`) with no empty or truncated
  output. This is harness evidence, not a study result.
- **Consequences:** G1 is rerun from scratch for all three models. The frozen data, manifest,
  sample, arms, and estimand are unchanged; the manifest's `config_hashes` remain the G0
  snapshot, while the G1 serving configuration is recorded here and in the paper. The G1 gate
  (parse ≥95%, jitter ≤20%, s=3 switch 10–80%, refusal <5% per model) is unchanged.

---

## D-022 — One vLLM process per model

- **Date:** 2026-11-15
- **Status:** accepted (G1 calibration fix)
- **Context:** `09_run.py --all-models` loaded Qwen, then Ministral in the same process; vLLM
  kept the first engine alive and Ministral failed at initialization with
  `CUBLAS_STATUS_ALLOC_FAILED`. Deleting the Python object did not release the engine.
- **Decision:** Run one `09_run.py` process per model via `scripts/09a_run_all.py`, which skips
  completed ledgers, streams each model, and combines the calibration report. `09_run.py`
  refuses `--all-models` with the vLLM backend.
- **Consequences:** GPU memory is released between families. The orchestration is resumable and
  is used for G1 and G2.

---

## D-021 — G0 audit labels adopted from the AI pre-audit; author verification deferred

- **Date:** 2026-11-15
- **Status:** accepted (author instruction; pre-freeze)
- **Context:** The author reviewed the AI pre-audit and instructed the agent to fill the official
  `g0_audit_sheet.csv` on their behalf because they do not have time before the run. The author
  will perform the final verification after the experiments finish. The preregistration says a
  human reviews the 40 items; this is therefore a logged deviation, not a silent substitution.
- **Decision:** Fill all 40 official rows from `g0_audit_ai_preaudit.csv` (40/40 mechanical
  passes), put the provenance in every note, and score with
  `--label-source ai_preaudit_deferred_human`. The resulting `g0_audit_result.json` records that
  provenance. Freeze and proceed to G1 under this provisional gate.
- **Consequences:** The official sheet is an author-adopted AI pre-audit, not a completed human
  audit. The paper and data card must state that provenance and must not claim human sign-off.
  If the author's post-experiment verification finds a failed item, replace it from the reserve,
  re-audit the replacement, and disclose any affected analysis; do not hide the revision.
  Amendment recorded in `prereg/AMENDMENTS.md` before freeze.

---

## D-020 — Prompt v3: plain-text call history plus a final instruction turn

- **Date:** 2026-11-15
- **Status:** accepted (pre-freeze; no study generation has run)
- **Context:** The v2 transcript rendered historical tool calls as `<tool_call>` blocks. A
  synthetic backend smoke showed Qwen3.5 echoing the block instead of the requested JSON, and
  Ministral returning an empty completion whenever the last turn was a bare tool result. The
  model needs a plain history and an explicit instruction as the final user turn.
- **Decision:** `normalize_messages` renders each historical call as
  `I called <name> with <canonical-json-arguments>.`; tool results remain user turns with a
  `[tool result: name]` marker; `build_prompt_messages` appends
  `Respond now with exactly one JSON object for the next action.` as the final user message.
  The prompt version becomes **`toolresult-next-decision-v3`**. The system instruction, tool
  schemas, parser, and 256-token budget are unchanged.
- **Evidence:** A synthetic airline tool-call history generated valid parsed JSON on all three
  models through the real `VLLMBackend` (`artifacts/env/v3_smoke.log` and
  `artifacts/env/backend_v3_smoke.log`). Ministral produced empty output under v2 and valid JSON
  under v3. No study prefix was used.
- **Consequences:** This supersedes the rendering detail of D-018; v2 was never used for a
  study generation. The extra instruction turn adds about 15 tokens, which still fits the 24k
  context. The prompt is not tuned per family.

---

## D-019 — Context raised to 24,576 tokens for the frozen prefixes

- **Date:** 2026-11-15
- **Status:** accepted (pre-freeze; no study generation has run)
- **Context:** The prompt-length audit (`scripts/12_prompt_lengths.py`) measured every rendered V
  arm with the pinned tokenizers. Median prompts are 5.8k–6.7k tokens, but the maximum is
  20,848 tokens and 107–237 of the 880 prefixes exceed an 8k context once the 256-token decision
  is reserved. Dropping or truncating those prefixes would change the frozen sample or discard
  real history.
- **Decision:** Set `max_model_len: 24576` for all three models. All three load and generate at
  24k on the 18 GB slice (Qwen3.5 94.7 s, Ministral 51.7 s, Llama 41.0 s; four `ready` outputs
  each). No prefix is truncated, dropped, or re-sampled. Batch remains 8, `max_num_seqs=8`,
  `gpu_memory_utilization=0.85`, and the 256-token decision budget is unchanged.
- **Consequences:** This is a pre-freeze serving amendment: the prereg's 8k context becomes
  24k. KV headroom falls (Ministral supports about 2.2 full-length 24k sequences), so long
  prompts queue and throughput is lower than an 8k run; the 45 GPU-hour stop rule still applies.
  The estimand, sample, arms, and analysis plan are unchanged.

---

## D-018 — Historical tool calls are rendered as canonical text; prompt v2

- **Date:** 2026-11-15
- **Status:** superseded by D-020 (pre-freeze; v2 was never used for a study generation)
- **Context:** The τ-bench prefixes carry OpenAI-style assistant `tool_calls` with JSON-string
  arguments and sometimes `content: null`. Rendering the real prefixes exposed three failures:
  Qwen3.5's template requires `arguments` to be a mapping, Llama's template calls `len()` on a
  null content, and Ministral's backend silently drops `tool_calls`. A family-specific template
  fix would give each model a different view of the same history.
- **Decision:** `build_prompt_messages` normalizes every message before templating: null content
  becomes `""`, each historical tool call becomes a deterministic
  `<tool_call>{"name": ..., "arguments": ...}</tool_call>` text block with arguments parsed from
  JSON strings, and each tool result becomes a user turn with a `[tool result: name]` marker.
  The six historical assistant turns with empty content and no tool call are dropped. The
  `tool_calls`/`tool_call_id` fields are removed so no template-specific tool grammar is used.
  The prompt version becomes **`toolresult-next-decision-v2`**; the parser is unchanged. The
  frozen prefix payload and the arm manipulation are untouched.
- **Consequences:** All three families see the same valid plain-text transcript, and the prompt
  renders on every pinned tokenizer. This was verified on a prefix with non-null tool-call ids,
  which Ministral's validator rejects in the original structured form. The system instruction,
  tool schemas, decoding, and 256-token budget are unchanged. Because no study generation
  exists, this is a pre-freeze implementation change, not a prereg amendment; the fixed-version
  requirement is satisfied by v2.

---

## D-017 — Reasoning models run with thinking disabled

- **Date:** 2026-11-15
- **Status:** accepted (pre-freeze)
- **Context:** Qwen3.5-9B is a reasoning model. With its stock chat template the fit prompt
  produced `Thinking Process:\n1. **` and exhausted the token budget before any decision. The
  study measures the *next decision* under a fixed 256-token budget, so a hidden reasoning block
  would confound cross-family comparison and could turn valid decisions into parse errors.
- **Decision:** Set `chat_template_kwargs: {enable_thinking: false}` on the Qwen3.5 entry in
  `configs/models.yaml`; `VLLMBackend` and the fit checker pass these kwargs to
  `apply_chat_template`. Ministral and Llama declare no template kwargs. The prompt instruction
  and 256-token budget are unchanged for all three families.
- **Consequences:** All families receive the same "single JSON decision, no preamble" contract.
  The fit rerun emitted `ready` for all four prompts. If a future model ignores the switch, its
  parse failures are reported as parse failures; the prompt is not tuned per family.

---

## D-016 — Updated 8–9B model trio pinned; all three fit checks pass

- **Date:** 2026-11-15
- **Status:** accepted (pre-freeze; fit checks complete)
- **Context:** The user asked to use updated, high-download community AWQ builds that fit the
  18 GB slice. Official AWQ artifacts do not exist for Qwen3.5-9B or Ministral-3-8B; the
  selected builds are public and Apache-2.0. The Llama build is the high-download hugging-quants
  AWQ conversion of the official Llama-3.1-8B-Instruct weights.
- **Decision:** Pin the trio:
  - `cyankiwi/Qwen3.5-9B-AWQ-4bit` @ `e4d2d39cede8c5d1716d824cd843e2889c648083`
  - `cyankiwi/Ministral-3-8B-Instruct-2512-AWQ-4bit` @ `563842192acb68a00b8864e3bfa5a3e740ece90c`
  - `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` @ `db1f81ad4b8c7e39777509fac66c652eb0a52f91`
  The study size class becomes **8–9B** (from 7–8B). Qwen2.5-7B remains only as a completed
  environment fit check; it is not the confirmatory Qwen model.
- **Fit status (2026-11-15):** All three pass at 8k and 24k context, batch 4,
  `gpu_memory_utilization=0.85`, `max_num_seqs=8`:
  - Qwen3.5-9B: 8.37 GiB weights, 4.63 GiB KV (89,770 tokens; 10.96× at 8k), 59.6 s load.
  - Ministral-3-8B: 7.03 GiB weights, 7.15 GiB KV (55,104 tokens; 6.73× at 8k), 359.7 s load
    including download.
  - Llama-3.1-8B: 5.58 GiB weights, 8.38 GiB KV (68,640 tokens; 8.38× at 8k), 210.6 s load
    including download.
  Qwen2.5-7B-AWQ passed earlier at 5.38 GiB weights / 7.76 GiB KV; that is historical evidence.
- **Consequences:** This is a pre-freeze model-family amendment; no target outcomes exist. The
  paper, data card, site, and prereg model table are updated from 7–8B/Qwen2.5 to 8–9B/updated
  trio before G1. If a model fails during G1, fall back to the previous family with a logged
  decision; do not select after seeing outcomes.

---

## D-015 — Qwen AWQ revision pinned; non-study H200 fit check authorized

- **Date:** 2026-11-15
- **Status:** accepted (pre-G1)
- **Context:** The H200 slice is free and the project needs to verify that the pinned AWQ model,
  8k context, and a small batch fit in 18 GB before G1. The user authorized GPU use; no study
  prompt or target outcome should be generated before the G0 freeze.
- **Decision:** Pin `Qwen/Qwen2.5-7B-Instruct-AWQ` at revision
  `b25037543e9394b818fdfca67ab2a00ecc7dd641`. Install the GPU stack in the project venv and run
  a non-study fit check (model load plus a short generic prompt). Record driver, CUDA, vLLM,
  torch, model revision, peak VRAM, and latency in `artifacts/env/`. Do not run calibration or
  main-run prefixes until the human audit and G0 freeze pass.
- **Observed fit (2026-11-15):** Qwen2.5-7B-Instruct-AWQ loaded at 8k context, batch 4, and
  `gpu_memory_utilization=0.85` on the 18 GB slice: 5.38 GiB weights, 7.76 GiB KV cache
  (145,376 tokens; 17.75x concurrency at 8k), 27.7 s load, 0.08 s for the four-prompt batch.
  vLLM 0.33.0 / torch 2.14.0+cu130. The 0.90 setting requested 16.02 GiB and failed because
  15.36 GiB was free; 0.85 is the logged reduction. Python headers were extracted project-locally
  for Triton; no system package or driver change.
- **Consequences:** Mistral and Llama revisions remain TBD until their access and fit checks.
  The fit check is environment evidence, not a study result; no target-model outcome on a study
  prefix exists.

---

## D-014 — Next-decision prompt and parser contract

- **Date:** 2026-11-15
- **Status:** accepted (pre-freeze)
- **Context:** The three target families use different chat templates. A model-specific
  tool-call grammar would add a format confound. The frozen prefix already ends at the real
  tool observation; the target must emit one next action.
- **Decision:** The prompt appends a deterministic instruction to the prefix's system message:
  respond with exactly one JSON object, either
  `{"tool": "<name>", "arguments": {...}}` or `{"final_answer": "<answer>"}`. The pinned tool
  schemas are serialized into the system message. The parser accepts that form, fenced JSON,
  and OpenAI-style `name`/`arguments`; refusals and parse failures are ledger statuses, never
  silently dropped. Prompt version is `toolresult-next-decision-v1`; parser version is
  `toolresult-parser-v1`.
- **Consequences:** G1 checks parse rate, refusal rate, placebo jitter, and s=3 switch rate before
  any main-run GPU spend. A model that refuses the format is fixed or excluded before G1 freeze.

---

## D-013 — Renderability filter excludes scalar-only `calculate` prefixes

- **Date:** 2026-11-15
- **Status:** accepted (pre-freeze)
- **Context:** The five-arm design requires one critical field for s=2 and one noncritical field for
  s=1 (and for the s=3 second contradiction). A scalar `calculate` observation has one used field
  and no noncritical field, so s=1 and s=3 cannot be constructed without changing the design.
- **Decision:** A prefix is renderable only if it has at least one critical and at least one
  noncritical field. The sampler drops unrenderable prefixes before the 10/task cap. This removes
  194 matched `calculate` candidates. The airline cap-10 remains **442** and retail **1,144**, so
  the 400/400 + 40/40 target is unaffected.
- **Consequences:** The frozen sample has no `compute` stratum. The renderer, not the sampler,
  remains the authority on field coverage; any future tool with fewer than two fields is excluded
  by the same rule before freeze.

---

## D-012 — Renderer version renamed to `toolresult-prose-v1`

- **Date:** 2026-11-15
- **Status:** accepted (pre-freeze)
- **Context:** The scaffold used the legacy label `cto-prose-v1` for the deterministic renderer.
  The dataset brand is ToolResult-800 and the old brand should not appear in new frozen material.
- **Decision:** The renderer version is **`toolresult-prose-v1`**, the next-decision prompt is
  **`toolresult-next-decision-v1`**, and the parser is **`toolresult-parser-v1`** in the configs,
  code constants, and perturbation records. No artifact has been frozen yet, so this is a rename,
  not a version change to a released dataset.
- **Consequences:** Regenerate the rendered arms and perturbation records after the rename; the
  renderer hash and version are recorded in the G0 manifest.

---

## D-011 — Replay passes on eligible prefixes; profile-tool schema drift disclosed

- **Date:** 2026-11-15
- **Status:** accepted (draft G0 evidence)
- **Context:** Replay executes every assistant tool call in a frozen prefix from a fresh pinned task
  database and compares the final observation. The historical trajectories and the pinned commit
  are not perfectly schema-identical: historical `get_user_details` observations use
  `address.province`, while the pinned data uses `address.state`.
- **Observed:** Full-pool replay is **11,889/13,605 (87.39%)**, dominated by
  `get_user_details` (**9/1,719**); every other tool is at or above 98% except
  `book_reservation` (143/147) and `cancel_reservation` (186/188), where fixed booking-ID reuse
  (`HATHAT`/`HATHAU`/`HATHAV`) can diverge. On the eligible non-profile pool, replay is
  **5,511/5,516 (99.91%)**; the five mismatches are the same airline booking-ID cases.
- **Decision:** The G0 replay gate is evaluated on the eligible non-profile pool, because profile
  tools are excluded before replay by design. The eligible pool passes at 99.91%. The
  `province`/`state` drift and the booking-ID mismatches are reported as a source caveat; they are
  not hidden by changing the pin or normalizing the field away.
- **Consequences:** Airline cap-10 after replay is **442**, only two above the 440 pre-audit floor;
  retail is 1,144. Sampling must preserve the airline cap and audit replacements carefully. If the
  user requires the full-pool replay gate instead, the source pin must be changed to the historical
  data version or an amendment must redefine the replay population.

---

## D-010 — Draft automatic relevance and PII policy; airline supply risk

- **Date:** 2026-11-15
- **Status:** provisional (not frozen)
- **Context:** The field registry covers only a subset of tools and uses conceptual field
  names that do not map one-to-one to the JSON paths emitted by τ-bench. The operational
  pipeline therefore uses the preregistered value-used rule as the automatic criticality
  label, with a path-based PII policy as a draft overlay.
- **Decision:** A scalar field is used when its normalized value appears in the donor's
  continuation surface (answer content or tool-call arguments) after NFKC, case, whitespace,
  digit-comma, and numeric normalization. Used non-PII fields are critical; unused non-PII
  fields are noncritical. PII paths are scrubbed with deterministic tokens. A candidate is
  excluded if the tool is a profile tool, the observation is text-only, no non-PII field is
  used, or the only used content is PII; a PII-target tool (`modify_pending_order_address`,
  `update_reservation_passengers`) is excluded when its used content is PII. Incidental PII
  that is scrubbed does not by itself exclude a prefix.
- **Observed (draft):** 5,516 eligible (airline 1,434; retail 4,082); at the 10/task cap,
  airline 442 and retail 1,144. This is below the 6,554 planning figure in `configs/harvest.yaml`
  but above the G0 880 floor. Airline is only two above the 440 pre-audit floor before replay.
- **Consequences:** Replay must be run before sampling; if airline cap-10 after replay is below
  440, the G0 fallback (500 prefixes / 2 models) or a prereg amendment is required. The final
  field-registry path mapping, the `payment_method_id` critical-versus-PII decision, and the
  registry coverage remain open. Do not freeze the manifest until those decisions are logged.

---

## D-009 — G0 candidate definition and profile-tool exclusion set

- **Date:** 2026-11-15
- **Status:** accepted
- **Context:** The parser must reproduce the preregistered harvest frame before any sampling. The
  τ-bench trajectory schema stores each tool result as a `tool` message and the donor's next
  decision as the following `assistant` message. The internal `think` tool is not an environment
  observation. The plan's 3,692 excluded profile-tool candidates must map to an explicit tool set.
- **Decision:** A candidate is a `tool` message followed immediately by an `assistant` message,
  excluding `think`. On the pinned frame this yields **13,605 candidates**, of which **11,318**
  are JSON-parseable and **2,287** are text; the counts match `configs/harvest.yaml`. The
  profile/PII exclusion set is `get_user_details`, `find_user_id_by_name_zip`,
  `find_user_id_by_email`, and `modify_user_address`; their union is exactly **3,692** candidates
  (1,719 + 1,159 + 695 + 119). Step-index buckets are `early` 0-2, `mid` 3-6, `late` 7+, where
  the step index counts every tool message including `think`. Tool families are `read`, `write`,
  `compute`, `lookup`, `escalate`, `profile`, and `internal`.
- **Consequences:** The interim candidate table stores message hashes and a source reference;
  full prefixes are materialized from the pinned trajectory and hash-verified (13,605/13,605
  verified locally). Changing the candidate definition, bucket boundaries, or exclusion set
  changes the sampling frame and requires a new logged decision before the G0 freeze.

---

## D-008 — Cash budget is $0 on the university H200 slice

- **Date:** 2026-11-14
- **Status:** accepted
- **Context:** The approved H200 1g.18gb slice is university-provided, so the project no longer
  needs a paid GPU rental. The old $23 base / $50 hard cap / $22 stop described a rental that will
  not be booked.
- **Decision:** The project cash budget is **$0**. Use the H200 slice for 35–45 GPU-hours. The
  operational stop is **45 GPU-hours or 200 GB storage**, whichever comes first. No paid API,
  no second GPU, and no paid annotation. The 18 GB fit check remains in force before G1/G2.
- **Consequences:** Docs, configs, paper, and site now state $0 cash. The old rental budget is
  historical only. Any paid resource requires a new decision and, if it affects the analysis, a
  prereg amendment.

---

## D-007 — University H200 MIG slice approved for project execution

- **Date:** 2026-11-14
- **Status:** accepted
- **Context:** The project has been granted access to a shared university GPU server. The
  approved resource is an H200 MIG 1g.18gb slice with 18 GB VRAM, driver 580.178.04, CUDA 13.5.
  This is below the older 24 GB rental assumption in the roadmap.
- **Decision:** Use only the `uiu-h200` SSH alias and the H200 1g.18gb slice for project GPU
  work. Keep the Python environment project-local. Follow the storage, job, secret, and
  change-control rules in `AGENTS.md` §2.1. Do not change the driver, CUDA, MIG settings, clocks,
  power limits, SSH configuration, or other users' files.
- **Consequences:** Calibration and main-run work use the 18 GB slice. Before G1/G2, verify that
  the pinned AWQ model, context, and batch fit; any reduction in batch, context, sample, or model
  set is a logged decision and, if it affects the analysis, a prereg amendment. The older 24 GB
  rental is not booked without a new decision. No server address, hostname, username, account ID,
  password, SSH key, or host fingerprint is committed.

---

## D-006 — Dataset brand is ToolResult-800; E2 retired

- **Date:** 2026-11-11
- **Status:** accepted
- **Context:** "CTO-800" reads like a corporate title, and "E2" is an internal code that is not
  meaningful to a reader. The dataset needs a readable brand that describes what it contains:
  800 frozen real τ-bench prefixes with tool-result perturbations.
- **Decision:** The dataset brand is **ToolResult-800**. The study is referred to as the
  **tool-result study** or by its full title, "Tool-Result Errors in Language-Model Agents."
  The repository remains **`Atik203/tool-observation`**; the package remains **`toolobs`**; the
  planned manifest becomes `data/manifests/toolresult800_v1.json`. "E2" and "CTO-800" are retired
  from new material.
- **Consequences:** Docs, configs, paper, slides, and release text use ToolResult-800. D-005 is
  superseded. No scientific design, sample, analysis, or claim changes. Historical entries may
  retain the old names.

---

## D-005 — Dataset brand is CTO-800; repository remains tool-observation

- **Date:** 2026-11-09
- **Status:** superseded by D-006
- **Context:** The dataset needs a citable brand distinct from the software repository. Naming
  the repo `cto-800` would conflate the code, the study, and the released data.
- **Decision:** The dataset is **CTO-800**. The repository is **`Atik203/tool-observation`**, the
  Python package is **`toolobs`**, and the study short name is **E2**.
- **Consequences:** Release artifacts use the CTO-800 name; the repo URL and package name stay
  stable. Documentation must not call the repository "cto-800".

---

## D-004 — No post-freeze edits to data, perturbations, or analysis

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The study's credibility depends on the freeze being real. Post-hoc changes to the
  sample or severity labels would invalidate the confirmatory claim.
- **Decision:** After G0, `data/manifests/cto800_v1.json`, perturbation records, the field
  registry, the renderer version, prompts, and the analysis plan are immutable. Any deviation is
  written to this file and `prereg/AMENDMENTS.md` before the affected analysis, stating the
  trigger, change, affected analyses, and whether it was blind to target outcomes.
- **Consequences:** Reproducibility fixes that do not alter frozen artifacts are allowed and
  recorded in `CHANGELOG.md`. A change that alters a frozen artifact requires a new dataset
  version, not an edit.

---

## D-003 — Pilot claim boundary: screening signal, not a law

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The pilot (N=60, qwen3.5:4b, synthetic prefixes) found consult 54/60, placebo
  jitter 0/60, error switch 5/60 = 8.3% [1.3, 15.3] pp, McNemar p=.0625. The result is marginal
  and the CI includes a 1.3 pp effect. Letter coding missed silent fact propagation, and there is
  no recovery data.
- **Decision:** The pilot is reported as a **screening signal** and a kill-gate result only. It
  is not evidence of a dose-response law, not a slope estimate, and not a model comparison. The
  confirmatory study does not pool pilot and main data.
- **Consequences:** Every public description of the pilot carries the caveats. A null
  confirmatory result is reported as null; the pilot is not used to rescue it.

---

## D-002 — Project storage on `G:` with public export from `tool-observation`

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The project needs local space for raw trajectories, model outputs, and run
  ledgers, while the public repository must stay small and PII-free. The G: drive has ample free
  space; the research workspace on E: is a separate project and must not be modified.
- **Decision:** Local root is **`G:\PROJECT\tool-observation`**. Raw, upstream, interim, frozen,
  and run data stay under `data/` and are gitignored. Only manifests, docs, code, and governance
  files are tracked. The public repo is `Atik203/tool-observation`.
- **Consequences:** Do not place raw data or weights in the repo. Do not modify
  `E:\PROJECT\Research-Ideas` or `E:\PROJECT\energy-optimal-rag`. Storage/egress is now $0 within
  the university allocation (D-008); large caches are deleted after hashes and ledgers are
  archived.

---

## D-001 — Repository name and scope

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The study needs a public, citable repository that separates the software from the
  CTO-800 dataset brand and does not imply a universal law.
- **Decision:** Create **`Atik203/tool-observation`** as a public repo for the fixed-prefix
  causal study (E2). Scope is bounded to three open-weight 7–8B models, τ-bench airline/retail,
  next-decision sensitivity, and four-step recovery. Code is MIT; documentation and derived data
  are CC BY 4.0; upstream τ-bench remains MIT.
- **Consequences:** No frontier models, model ranking, end-to-end success, or live-API claims in
  this repository. Follow-up work gets a separate scope.
