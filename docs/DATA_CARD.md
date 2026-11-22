# Data card — ToolResult-800

**Status:** v1.0.1 release packaged and validated (2026-11-23; redaction errata over v1.0.0). DOI pending (see `docs/submission/doi_record.md`);
release date is the DOI registration date. Hashes below are from the frozen manifest, not estimates.

---

## 1. Dataset identity

| Field | Value |
|---|---|
| Name | ToolResult-800 |
| Full title | Counterfactual Tool-Observation dataset, 800 frozen prefixes |
| Version | 1.0.1 (packaged 2026-11-23; released on DOI registration; supersedes v1.0.0 redaction errata) |
| Repository | https://github.com/Atik203/tool-observation |
| Dataset brand | ToolResult-800 (the repository is `tool-observation`) |
| Study | Tool-Result Errors in Language-Model Agents |
| Maintainer | Md. Atikur Rahaman (mrahaman2310298@bscse.uiu.ac.bd) |
| License | Dual: CC BY 4.0 for project data additions; MIT for the repository code; upstream τ-bench MIT |
| Release date | TBD (= DOI registration date) |
| DOI | TBD (`docs/submission/doi_record.md`) |
| Package | `release/ToolResult-800-v1.0.1/` — 127 checksummed files (129 files with `SHA256SUMS` and `release_record.json`); 17/17 L1 validated |
| Manifest hash | `d6e034d7f1132b314ad1f82bf14faa0f6762975ee7b404b54cc365acfac5487a` (`data/manifests/toolresult800_v1.json` + sidecar) |
| Preregistration hash | `e0d107c6` (freeze commit 1673856, tag prereg-freeze-v1; no external registry; record in `prereg/DEPOSIT_NOTE.md`) |

## 2. Summary

ToolResult-800 is a fixed-prefix counterfactual dataset for measuring whether the content of a real tool
observation changes a language-model agent's next decision. Each unit is a frozen τ-bench message
prefix ending immediately after a real tool output, with five observation arms: verbatim JSON
(V), faithful prose (s=0), one non-critical change (s=1), one critical wrong value (s=2), and a
critical wrong value plus a contradiction (s=3). A subset has four-step recovery traces under
transient and persistent injection.

The dataset contains **800 primary prefixes** (400 airline, 400 retail) plus an **80-prefix
reserve** that is not part of the primary analysis. The confirmatory analysis is complete and frozen;
target-model outputs are released in v1.0.1 as scrubbed derived text (no weights, no raw trajectories).
The distributed copy is redacted; the frozen source is not distributed (see §6 and §11).

Executed envelope (G2 complete, within the 45 GPU-hour / 200 GB stop line): **21,611 generations**
(13,200 base + 7,211 recovery + 1,200 jitter), 8.9 GPU-hours on the university H200 slice, \$0 cash.
Planned 34,800; recovery is conditional on switching by design (see `tab:envelope` in the paper).

## 3. Composition

| Split | Count | Description |
|---|---:|---|
| Airline primary | 400 | τ-bench airline prefixes |
| Retail primary | 400 | τ-bench retail prefixes |
| Reserve | 80 | held out; not in primary analysis |
| Arms per prefix | 5 | V, s=0, s=1, s=2, s=3 |
| Models | 3 | Qwen3.5-9B-AWQ, Ministral-3-8B-Instruct-2512-AWQ, Llama-3.1-8B-Instruct-AWQ-INT4 (greedy) |
| Base generations | 12,000 | 800 × 5 × 3 |
| Recovery generations | 21,600 | 19,200 transient + 2,400 persistent |
| Jitter generations | 1,200 | 80 × 5 × 3 |
| Total envelope | 34,800 | planned main run |

Per-record fields:

- `prefix_id`, `domain`, `task_id`, `trajectory_id`, `donor`, `trial`, `step_index`, `tool_name`
- `message_hashes[]`, `observation_hash`, `replay_match`, `eligible`, `split`
- `observation_json` (scrubbed; raw PII never released)
- `factual_continuation`
- `perturbations[]`: `json_path`, `true_value`, `false_value`, `criticality`,
  `expected_action_change`, `renderer_version`
- `arm`, `severity`, `renderer_version`
- `decision_signature`, outcome labels (`Y`, `Y^U`, `Y^F`, `Y^A`)
- recovery fields: `regime`, `horizon`, `recovered_step`, `endpoint`, `censored`, `state_hash`

## 4. Collection

Source: public τ-bench historical trajectories, pinned commit **`59a200c`**, MIT license. Four
files: gpt-4o airline, gpt-4o retail, sonnet-35-new airline, sonnet-35-new retail. The empirical
pool is 1,980 trajectories, **13,605 post-tool candidates**, **11,318 JSON-parseable**, **3,692
profile/PII-tool candidates excluded**, and **5,516 eligible value-used observations** (airline
1,434; retail 4,082). Eligible-pool replay matches 5,511/5,516 (99.91%). Sampling caps at 10 per
task-domain and stratifies by domain, donor, step-index bucket, and tool family, seed 20261108.
The earlier 6,554 planning figure is retained as a planning input, not a gate; the operational
value-used rule is stricter.

"Real tool output" means emitted by the benchmark's tool implementation against the task
database and verified by replay, not LLM-generated prose.

## 5. Processing

1. Parse assistant messages following tool messages; reconstruct the exact prefix.
2. Exclude profile tools; scrub names, emails, addresses, phones, payment identifiers with stable
   synthetic tokens; exclude if decision-relevant content is PII.
3. Label decision relevance by value-used matching between observation scalars and the donor's
   factual continuation.
4. Replay tool calls against the task DB; keep ≥98% normalized matches.
5. Render deterministic prose; verify s=0 value-set equality with V.
6. Apply s=1/s=2/s=3 perturbations from the frozen field registry.
7. Freeze hashes and the preregistration before any target-model outcome.

## 6. Personal and sensitive information

Raw τ-bench trajectories may contain names, emails, addresses, phone numbers, and payment
identifiers. The release excludes profile-tool observations and scrubs direct identifiers.
Decision-relevant content that is itself PII is excluded. A 40-item PII pre-audit was run before
freeze (AI pre-audit adopted by the author; human verification deferred, D-021/A-005); a separate
automated re-scan runs before release.

Scrubber-artifact email fragments (a bare scrubber token followed by an unsanitized given
name plus digits on the reserved `example.com` domain) survived the harvest scrub in the
frozen prefix set. Freeze integrity requires the frozen source to stay bit-identical, so they
remain there; **the frozen source is not distributed**. The release builder replaces every
match with `person_redacted_0001` in every staged file on every build (D-046, v1.0.1), and
`pii_rescan.json` reports the replacement counts. **The distributed release therefore contains no
unredacted participant identifiers** (the corresponding-author contact email in `CITATION.cff`
and this card is intentional and allowlisted). The independent human re-scan is still pending;
report suspected PII privately per `SECURITY.md`.

## 7. Licensing and attribution

- ToolResult-800 data additions: CC BY 4.0 (`DATA_LICENSE.md`).
- Repository code: MIT (`LICENSE`; also `CITATION.cff`).
- Upstream τ-bench: MIT; notices preserved (Sierra copyright line in `ATTRIBUTION.md`).
- Model outputs: subject to each model's license; released only as derived, scrubbed text.
  Qwen3.5-9B and Ministral-3-8B are Apache-2.0; Llama-3.1-8B-Instruct is under the Llama 3.1
  Community License, with no weights distributed and only derived text released.
- Users must cite ToolResult-800/tool-observation and the upstream τ-bench paper/repository.

See `DATA_LICENSE.md` and the consolidated notices in `ATTRIBUTION.md`.

## 8. Intended use

Research on tool-result errors, silent propagation, agent recovery, and
reproducible evaluation of open-weight 8–9B models. Suitable for secondary analysis of
within-prefix contrasts and for benchmarking detection/flagging behavior.

## 9. Limitations

- τ-bench tasks are public and may be in target-model training data; baseline reliance may be
  inflated.
- Only three 8–9B model families; no frontier or API models.
- Two domains, one renderer, one severity rubric.
- Mock/deterministic benchmark tools, not live APIs.
- Donor prefixes come from gpt-4o/sonnet; target models continue off-policy histories.
- Recovery is observed for four steps; longer horizons are censored.
- Severity is ordinal and s=3 is compound.
- Human labels come from a small team, not an external annotation vendor. **Correction
  (2026-11-22): the preceding sentence was false. No human annotation was used.** All ratings were
  produced by blind rater sessions operated with an AI agent and checked by a multi-role agent
  panel, author-overseen (D-043); the task-utility endpoint is single-agent coded, author-overseen
  (D-044). Agreement statistics measure consistency among sessions, not human independence.

## 10. Maintenance

- Version 1.0.1 is frozen; corrections require a new version and a changelog entry.
- Errata are published in the repository and linked from the DOI record; v1.0.1 is the PII
  redaction errata over v1.0.0 (`CHANGELOG.md` in the release package).
- The manifest and checksums are the authoritative record.
- Contact: mrahaman2310298@bscse.uiu.ac.bd.

## 11. Release contents (v1.0.1)

Packaged at `release/ToolResult-800-v1.0.1/` (127 files; not yet uploaded; DOI deposit
record at `docs/submission/doi_record.md`):

- `manifests/` — frozen manifest + SHA-256 sidecar, perturbation records, source pin.
- `frozen/prefixes.jsonl` — 880 scrubbed prefixes with five arm observations each, in the
  redacted release derivative (D-046). The unredacted frozen source is not distributed.
- `traces/` — scrubbed, redacted ledger extracts (base, recovery, jitter, G1 calibration_v3
  runs) plus `ledger_hashes.json` (SHA-256 and byte size of every distributed extract,
  computed after redaction). Prompt text was never logged (hashes only); decisions are
  model outputs on scrubbed inputs.
- `labels/` — audit packets, sheets, rater instructions, blind-audit result, verification
  record (`panel_record.json`), second-rater agreement.
- `analysis/` — every analysis JSON behind the reported tables (`g3_analysis`,
  `g4_recovery`, `g4_recovery_v2`, `rowlevel_refits`, `severity_sensitivity`,
  `inference_robustness`, `wrong_direction`, `new_evidence`, `field_taxonomy`,
  `prereg_secondary`, jitter stability). `rowlevel_refits.json` records its generation
  commit (`8e6f536`) and SHA-256 `965805ea…dbedfcb`; its `reconciliation.note` is the
  text-only correction later committed as `7f0169d` (no numeric change).
- `packets/` — T6 blinded packets, sealed maps, and codes (single-agent coded, author-overseen),
  with the flagged identity redacted.
- `prereg/` — frozen preregistration, amendments A-001–A-011, deposit note.
- `licenses/` — upstream τ-bench MIT text (verbatim) + model-output license verification.
- `ATTRIBUTION.md`, `DATA_LICENSE.md`, `CHANGELOG.md`, `TABLE_MAP.md` (all 25 paper tables:
  11 main + S1–S14), `VALIDATION.md` (one-command validation), `SHA256SUMS`,
  `release_record.json`, `pii_rescan.json` (including `n_redactions`).

Validate: `make validate-release` (L1 on the package alone; `--rerun` with repo ledgers
rebuilds the six T2–T6 analysis JSONs and diffs). The G0 harvest audit is an AI pre-audit (40/40)
adopted by the author with human verification deferred (D-021, A-005); the freeze stands
provisional on that item. The automated identifier re-scan is clean (reserved-domain
placeholders, synthetic-token echoes, and the redaction count reported in `pii_rescan.json`);
the independent human re-scan is pending (see `docs/submission/checklist.md`).
