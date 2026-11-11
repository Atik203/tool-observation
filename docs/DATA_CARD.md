# Data card — CTO-800

**Status:** template for the v1.0 release. No CTO-800 artifact has been released yet; all values
marked TBD are resolved at G0 freeze and must be filled from the manifest, not estimated.

---

## 1. Dataset identity

| Field | Value |
|---|---|
| Name | CTO-800 |
| Full title | Counterfactual Tool-Observation dataset, 800 frozen prefixes |
| Version | 1.0 (planned; scaffold is pre-release) |
| Repository | https://github.com/Atik203/tool-observation |
| Dataset brand | CTO-800 (the repository is not named cto-800) |
| Study | E2 — Tool-Observation Sensitivity in Language-Model Agents |
| Maintainer | Atikur Rahaman (atikurrahaman0305@gmail.com) |
| License | CC BY 4.0 for project additions; upstream τ-bench MIT |
| Release date | TBD |
| DOI | TBD |
| Manifest hash | TBD (`data/manifests/cto800_v1.json`) |
| Preregistration hash | TBD |

## 2. Summary

CTO-800 is a fixed-prefix counterfactual dataset for measuring whether the content of a real tool
observation changes a language-model agent's next decision. Each unit is a frozen τ-bench message
prefix ending immediately after a real tool output, with five observation arms: verbatim JSON
(V), faithful prose (s=0), one non-critical change (s=1), one critical wrong value (s=2), and a
critical wrong value plus a contradiction (s=3). A subset has four-step recovery traces under
transient and persistent injection.

The dataset contains **800 primary prefixes** (400 airline, 400 retail) plus an **80-prefix
reserve** that is not part of the primary analysis. Target-model outputs are released only after
the confirmatory analysis is frozen.

## 3. Composition

| Split | Count | Description |
|---|---:|---|
| Airline primary | 400 | τ-bench airline prefixes |
| Retail primary | 400 | τ-bench retail prefixes |
| Reserve | 80 | held out; not in primary analysis |
| Arms per prefix | 5 | V, s=0, s=1, s=2, s=3 |
| Models | 3 | Qwen2.5-7B-Instruct-AWQ, Mistral-7B-Instruct-v0.3-AWQ, Llama-3.1-8B-Instruct-AWQ (greedy) |
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

Source: public τ-bench historical trajectories, pinned commit (TBD), MIT license. Four files:
gpt-4o airline, gpt-4o retail, sonnet-35-new airline, sonnet-35-new retail. The empirical pool is
1,980 trajectories, 13,605 post-tool candidates, 11,318 JSON-parseable, and 6,554 value-used
eligible observations after excluding profile tools. Sampling caps at 10 per task–domain,
stratified by domain, donor, step-index bucket, and tool family, seed 20261108.

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
Decision-relevant content that is itself PII is excluded. A 40-item human audit checks PII before
freeze; a separate re-scan runs before release. **No raw PII is released.** Report suspected PII
privately per `SECURITY.md`.

## 7. Licensing and attribution

- CTO-800 additions: CC BY 4.0.
- Upstream τ-bench: MIT; notices preserved.
- Model outputs: subject to each model's license; released only as derived, scrubbed text.
- Users must cite CTO-800/tool-observation and the upstream τ-bench paper/repository.

See `DATA_LICENSE.md`.

## 8. Intended use

Research on tool-observation sensitivity, silent error propagation, agent recovery, and
reproducible evaluation of open-weight 7–8B models. Suitable for secondary analysis of
within-prefix contrasts and for benchmarking detection/flagging behavior.

## 9. Limitations

- τ-bench tasks are public and may be in target-model training data; baseline reliance may be
  inflated.
- Only three 7–8B model families; no frontier or API models.
- Two domains, one renderer, one severity rubric.
- Mock/deterministic benchmark tools, not live APIs.
- Donor prefixes come from gpt-4o/sonnet; target models continue off-policy histories.
- Recovery is observed for four steps; longer horizons are censored.
- Severity is ordinal and s=3 is compound.
- Human labels come from a small team, not an external annotation vendor.

## 10. Maintenance

- Version 1.0 is frozen; corrections require a new version and a changelog entry.
- Errata are published in the repository and linked from the DOI record.
- The manifest and checksums are the authoritative record.
- Contact: atikurrahaman0305@gmail.com.
