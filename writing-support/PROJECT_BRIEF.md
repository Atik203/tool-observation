# PROJECT_BRIEF.md — ToolResult800 paper release (paper-overleaf)

Scope: this brief is the shared factual reference for Tasks 2-7 of the Overleaf release.
It introduces no new numbers, claims, citations, or experiments. Every value below
traces to a frozen artifact or a cited external source. Do not edit paper/ prose to
change any numeric value, claim, or citation on the basis of this file; this file
summarizes, it does not authorize changes.

## 1. Problem

Tool-using language models act on tool results that may be corrupted, stale, or
adversarially perturbed. A model that silently propagates a corrupted value into a
decision (booking, purchase, payment) creates a failure that no downstream check
catches. The project measures whether graded corruptions of a tool result move the
model's decision, how often the move is silent, and whether the model recovers.

## 2. Gap

Existing tool-use and agent benchmarks (Tau-bench, ToolLLM, WebArena, AgentBench,
BFCL) score task success but do not isolate the causal effect of tool-result
perturbation severity on the decision, do not separate silent from flagged
propagation, and do not audit the severity manipulation itself with blind raters.
No prior study combines a pre-registered dose-response slope, tier odds ratios,
silent-share quantification, recovery survival analysis, and a label-free blind
audit of severity, outcome, and recovery coding.

## 3. Objective

Ship the frozen 6-section manuscript (`paper/toolresults.tex`) plus figures fig1-fig10, references, and style
files as a 14-file Overleaf zip, with prose polished (Tasks 5-6) but all numbers,
claims, and citations byte-identical to the frozen artifacts.

## 4. Data

- 800 primary prefixes + 80 held-out reserve prefixes (reserve excluded from all
  confirmatory estimates; reserve-only slope reported as exploratory).
- 3 models (AWQ): qwen3_5_9b_instruct_awq, ministral_3_8b_instruct_2512_awq,
  llama_3_1_8b_instruct_awq.
- 13,200 base generations (880 prefixes x 5 arms: verbatim V + severity tiers
  s0-s3); 9,075 labels observed of 9,600 potential (525 missing, 5.47%).
- 2,297 of 2,400 prefix x model units carry at least one label.
- Manifest: `data/manifests/toolresult800_v1.json`; parser `toolresult-parser-v4`;
  renderer `toolresult-prose-v1`; seed 20261108.
- References: 56 entries in `paper/ref.bib` (frozen; no citation changes).

## 5. Design

- Within-prefix graded manipulation: each prefix yields a verbatim V continuation
  plus arms s0 (placebo re-render), s1, s2, s3 (increasing severity).
- Primary estimator: conditional (fixed-effects) logit stratified by prefix x model,
  clustered by prefix; linear dose model x = s in {0,1,2,3} plus categorical
  (s1/s2/s3 vs s0) and quadratic diagnostics.
- Uncertainty: prefix-cluster percentile bootstrap, 2,000 replicates.
- Recovery: H=4 continuation horizon on switched sequences (transient_s2,
  transient_s3, persistent_s3 regimes); Kaplan-Meier + exponential/Weibull.
- Audits: label-free blind rating (3 severity, 2 outcome, 2 recovery raters) with
  pre-registered gates; second-rater agreement on fresh subsamples; 10% jitter
  seed-repeat stability per model (1.000 / .9895 / .9894, report-only).
- Preregistration: `prereg/PREREGISTRATION.md`; gates: `docs/GATES.md`; decisions:
  `docs/DECISIONS.md` (D-039 label-free re-rate is authoritative; the earlier
  label-visible round is archived as a sensitivity only).

## 6. Estimators (frozen definitions, `prereg_secondary.json` "definitions")

- `switch_any`: decision signature differs from the verbatim V continuation, or
  the generation explicitly flags doubt/inconsistency.
- `strict` coding: tool + canonical arguments for tool calls; action verb +
  decision-critical slots for final answers (flags excluded). `lenient` coding:
  tool-name / action-verb differences only.
- Conditional logit likelihood within each stratum with k events among n rows;
  pooled models stratify by prefix x model and cluster by prefix.
- McNemar: paired s2-vs-s3 (and s3-vs-s1) exact two-sided binomial tests.
- MDE: `(z_{1-alpha/2} + z_{1-beta}) * SE_cluster`; realized pooled MDE
  (cluster) 0.166 vs design pooled ~0.15 (design assumed a 4% placebo switch
  rate; observed s0 rate is much higher, so realized MDE is conditional on the
  observed design, not a replication of the design calculation).
- Wilson intervals for rates; Cohen's kappa (outcome, recovery); Krippendorff's
  alpha nominal/interval (severity); Jonckheere-Terpstra for monotone severity.

## 7. Results index (artifact -> content)

- `artifacts/analysis/g3_analysis.json` — pooled + per-model slopes, bootstrap CI,
  arm table, silent propagation counts.
- `artifacts/analysis/prereg_secondary.json` — tier ORs, linearity/quadratic/LRT
  diagnostics, McNemar, stratified (domain/donor) slopes, strict-vs-lenient,
  realized MDE, sample/missingness ledger.
- `artifacts/analysis/g4_recovery.json` — per-group KM curves, recovered-by-H4,
  exponential/Weibull fits, gate verdicts (all primary groups fail).
- `artifacts/analysis/g3_report.md` — G3 gate matrix incl. parser-failure row
  (205/13,200) and audit summary.
- `artifacts/audit/blind_audit_result.json` — label-free severity/outcome/recovery
  gates, kappas, alphas, silent PPV, rater disagreements, packet hashes.
- `artifacts/audit/second_rater_agreement.json` — fresh-subsample agreement
  (severity alpha, outcome kappa, recovery kappas).
- `artifacts/audit/human_verification.json` — agent-panel verification record
  (accepted with documented corrections; shared model family, not human
  independence).
- `artifacts/analysis/jitter_stability_*.json` — 10% seed-repeat stability
  (parser-v4 rescores).

## 8. Claim-evidence map (frozen; verify before quoting)

- Pooled slope 0.877 [0.770, 0.998] <- artifacts/analysis/g3_analysis.json
- Per-model slopes 1.079 / 0.915 / 0.649 <- same
- Tier ORs 1.27 / 4.60 / 11.21 <- artifacts/analysis/prereg_secondary.json
- Silent share 419/1,964 = 21.3% <- artifacts/analysis/g3_analysis.json
- Recovery by H=4 32.4 / 47.6 / 28.2% <- artifacts/analysis/g4_recovery.json
- Parser failure 205/13,200 = 1.55% <- artifacts/analysis/g3_report.md
- Severity s2/s3 gate 53/60 = 88.3% (fail) <- artifacts/audit/blind_audit_result.json
- Severity alpha .911 nominal / .959 interval <- same
- Outcome kappa .987 <- same
- Recovery kappa .920 step / .917 endpoint <- same
- Silent PPV / recall 1.00 / .75 <- same
- Second-rater agreement alpha .917, kappa .942, kappa .918/.907 <- artifacts/audit/second_rater_agreement.json

Slash-order note: per-model lists run qwen3_5_9b / ministral_3_8b / llama_3_1_8b
(e.g. recovered-by-H4 transient_s3: qwen .324, ministral .476, llama .282).
Silent recall .75 = 9/9 automatic YU items confirmed (PPV 1.00, exact 95% lower
bound .66) while the coder misses three panel-confirmed silent items (D-039).

## 9. Terminology lock (use exactly; do not rename in prose)

- ToolResult800; verbatim V; severity tiers s0/s1/s2/s3; switch (any/action);
  flag; silent propagation; silent share; PPV / recall (silent).
- Conditional logit; cluster bootstrap; McNemar; MDE; Wilson interval;
  Cohen's kappa; Krippendorff's alpha; Jonckheere-Terpstra.
- Recovery regimes transient_s2 / transient_s3 / persistent_s3; horizon H=4;
  recovered-by-H4; survival_h4.
- Label-free round (authoritative) vs label-visible round (sensitivity,
  archived, never reported as primary).
- G1/G2/G3/G4 gates; FAIL is a reported verdict, never smoothed over.

## 10. Known conflicts and stop rules

- `artifacts/` in this release worktree holds placeholders; authoritative numbers
  live in the frozen manifests and the main-repo run ledgers. Any mismatch
  between prose and `blind_audit_result.json` / `g3_analysis.json` /
  `prereg_secondary.json` / `g4_recovery.json` stops the line: report, do not
  reconcile by editing numbers (prereg change control, `docs/DECISIONS.md`).
- Two G3 criteria FAIL and are reported as fails: severity s2/s3
  decision-changing 88.3% vs 90% gate, and parser failure 1.55% vs <1% gate
  (`docs/GATES.md`). Prose must keep both failures visible.
- The label-visible audit round (alpha .919 / kappa .975 / recovery .787) must
  never replace the label-free figures.
- Global release locks: 6 sections; conclusion one paragraph 120-170 words; body
  paragraphs 120-250 words, none under 80; no Furthermore / Moreover /
  In conclusion / pivotal / delve / tapestry / testament / not only...but also;
  fig1-fig10 at 600 DPI with captions <= 25 words; final `paper/` contents only
  `toolresults.tex`, `ref.bib`, `cas-common.sty`, `cas-sc.cls`,
  `figures/fig1-10`; 14-file zip; no numeric, claim, or citation changes; no new
  experiments. Task 1 does not touch `paper/` source.
