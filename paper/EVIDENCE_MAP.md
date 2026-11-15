# Evidence map — ToolResult-800 manuscript

**Snapshot:** 2026-11-15 · working tree at time of writing · HEAD moved from `0a0ebc0` to
`e25782a` during the session · pre-G2. Re-check line numbers and the decision log before citing.
**Companion:** `paper/toolresult800.tex` (manuscript skeleton). This file is the register for its
numbers; the manuscript's `\pending{...}` markers should match the placeholders in §4.
**Purpose:** one register of every quantitative claim the manuscript may make, the exact value,
and the file that records it. If a value is not in a source, it stays `[PENDING: ...]`.
**Hard rule:** a number may enter the manuscript only if it appears here with a source that
exists at the cited path, or in a G2+ ledger row added here after the run.

**How to use this file**

1. Copy values; do not recompute or silently round. Where a percentage is quoted, the source
   value is in the same row.
2. When sources disagree, the frozen manifest wins. Fix the narrative document; never edit the
   manifest to match prose.
3. `artifacts/` is gitignored. A release claim must cite a tracked manifest/ledger or a packaged
   artifact, not a local path alone.
4. `[PENDING: ...]` is a blocker, not a prompt to guess.

**What the paper may say today**

- G0 is frozen: 800 primary + 80 reserve prefixes, 4,400 rendered arms, 2,640 perturbation
  records, 60 disjoint calibration prefixes.
- The G0 audit is a **provisional AI pre-audit adopted by the author** (40/40 items,
  `label_source=ai_preaudit_deferred_human`), not a completed human audit.
- No confirmatory (G2) generation exists. G1 calibration is in progress and is **harness
  evidence, not a study result**.
- The only empirical effect estimate is the 60-prefix pilot, and it is **screening only**.

**G0 headline counts (frozen)**

| Quantity | Value | Detail |
|---|---|---|
| Post-tool candidates | 13,605 | H-02 |
| JSON-parseable | 11,318 | H-03 |
| Profile/PII candidates excluded | 3,692 | H-04 |
| Eligible value-used | 5,516 (airline 1,434; retail 4,082) | H-05 |
| Eligible-pool replay matched | 5,511/5,516 = 99.91% | H-07 |
| Primary prefixes | 800 (400 airline + 400 retail) | H-12 |
| Reserve prefixes | 80 (40 + 40) | H-12 |
| Rendered arms | 4,400 (880 × 5) | R-01 |
| Perturbation records | 2,640 (880 each s=1/s=2/s=3) | R-02 |
| Calibration prefixes | 60 (30 airline + 30 retail) | H-16 |

---

## 0. Evidence classes and source hierarchy

Every row carries one status. The status controls what the sentence may claim.

| Status | Meaning | May support |
|---|---|---|
| **frozen** | Recorded in `data/manifests/toolresult800_v1.json` and hash-verified | Data/design facts |
| **recorded** | A G0 pipeline artifact under `artifacts/audit/` | Data/design facts with the artifact cited |
| **provisional** | AI pre-audit adopted under D-021; human verification deferred | G0 gate provenance only, with the caveat |
| **narrative** | A decision log, protocol, or README statement with no artifact | Design intent; not an observed count |
| **design** | A protocol, prereg, or roadmap specification | Methods and claim boundary only |
| **gate** | A pre-registered threshold | Methods and decision rules; not an observed result |
| **decision** | A logged pre-freeze choice (D-xxx) | Methods and reproducibility |
| **frozen pin** | A model or source revision pinned before G1 | Methods and reproducibility |
| **policy** | A data, licensing, or release rule | Data/ethics section |
| **environment** | Fit check, smoke test, or install log | Methods/reproducibility only |
| **harness** | G1 calibration output | Gate status only; never a Results claim |
| **screening** | The 60-prefix pilot | Motivation only; never pooled |
| **superseded** | A planning value replaced by an operational one | Nothing; use the replacement |
| **pending** | No source exists yet | Nothing until filled |

`frozen / verified` means the frozen value plus a hash or line count recomputed at snapshot. A
compound status does not add evidentiary weight beyond its parts.

**Source hierarchy** (highest first):

1. `data/manifests/toolresult800_v1.json` + `data/manifests/toolresult800_v1.sha256.json`
2. `artifacts/audit/*.json` (G0 pipeline outputs)
3. `docs/DECISIONS.md` and `prereg/AMENDMENTS.md` (logged decisions)
4. `docs/GATES.md`, `docs/PROTOCOL.md`, `prereg/PREREGISTRATION.md` (plan and thresholds)
5. `README.md`, `ROADMAP.md`, `docs/DATA_CARD.md`, `paper/proposal.tex` (narrative; may lag)

When 1 and 5 disagree, 1 wins and 5 is a documentation bug. Known cases are in §5.

---

## 1. Claim-evidence register

### 1.1 Harvest, eligibility, and sample

| ID | Claim (manuscript wording) | Exact value | Source | Status |
|---|---|---|---|---|
| H-01 | The harvest frame is 1,980 public τ-bench trajectories. | 1,980 | `configs/harvest.yaml:14` (`expected_trajectories`); `docs/DATA_CARD.md:67` | recorded |
| H-02 | Parsing yields 13,605 post-tool candidates. | 13,605 | `artifacts/audit/scrub_report.json` → `relevance.candidates`; `configs/harvest.yaml:15`; `docs/GATES.md:44` | recorded |
| H-03 | 11,318 candidates have JSON-parseable observations; 2,287 are text. | 11,318 / 2,287 | `configs/harvest.yaml:16`; `tests/test_parse_real.py:34-35`; `docs/DECISIONS.md` D-009 | recorded (not in manifest) |
| H-04 | 3,692 profile/PII candidates are excluded: `get_user_details` 1,719, `find_user_id_by_name_zip` 1,159, `find_user_id_by_email` 695, `modify_user_address` 119. | 3,692 = 1,719 + 1,159 + 695 + 119 | `docs/DECISIONS.md` D-009; `artifacts/audit/scrub_report.json` → `relevance.reasons.profile_tool`; `configs/harvest.yaml:41` | recorded |
| H-05 | 5,516 observations are eligible (airline 1,434; retail 4,082). | 5,516 (1,434 / 4,082) | `artifacts/audit/scrub_report.json` → `by_domain`; `artifacts/audit/relevance_report.json` → `by_domain`; `docs/GATES.md:46` | recorded |
| H-06 | The other exclusions are 3,626 no-used-field, 426 text-observation, and 345 decision-critical-PII candidates. | 3,626 / 426 / 345; total 8,089 | `artifacts/audit/scrub_report.json` → `relevance.reasons` | recorded |
| H-07 | Eligible-pool replay matches 5,511/5,516 = 99.91%. | 5,511/5,516; `match_rate` 0.9990935460478607 | `artifacts/audit/replay_report.json` → `stats` | recorded |
| H-08 | The five replay mismatches are 1 JSON value mismatch and 4 replayed errors; airline 1,429/1,434, retail 4,082/4,082. | 5 = 1 + 4; 1,429/1,434; 4,082/4,082 | `artifacts/audit/replay_report.json` → `stats.diffs`, `stats.by_domain` | recorded |
| H-09 | Full-pool replay is 11,889/13,605 = 87.39%, dominated by `get_user_details` 9/1,719; the gate is evaluated on the eligible non-profile pool. | 11,889/13,605 = 87.39%; 9/1,719 | `docs/DECISIONS.md` D-011; `docs/GATES.md:57` | narrative (no artifact) |
| H-10 | The 10/task cap leaves 442 airline and 1,144 retail (1,586 total). | 442 / 1,144 / 1,586 | `artifacts/audit/replay_report.json` → `cap10_by_domain`; `artifacts/audit/sample_report.json` → `stats.input` | recorded |
| H-11 | 194 scalar-only `calculate` prefixes are dropped as unrenderable; the airline cap remains 442. | 194 | `artifacts/audit/sample_report.json` → `stats.unrenderable`; `docs/DECISIONS.md` D-013 | recorded |
| H-12 | The sample is 800 primary (400 airline + 400 retail) + 80 reserve (40 + 40) = 880. | 800 + 80 = 880; 400/400; 40/40 | `data/manifests/toolresult800_v1.json` → `counts`; `artifacts/audit/sample_report.json` → `stats`; `artifacts/audit/freeze_dry_run.json` → `counts` | **frozen** |
| H-13 | Sampling uses seed 20261108, a cap of 10 per task–domain, and 22 strata. | seed 20261108; cap 10; 22 strata | `configs/harvest.yaml:24,37`; `artifacts/audit/sample_report.json` → `stats` | recorded |
| H-14 | Primary composition: 534 `claude-3.5-sonnet` / 266 `gpt-4o`; early 222 / mid 388 / late 190; read 544 / write 256. | as listed | `artifacts/audit/sample_report.json` → `stats` | recorded |
| H-15 | Reserve composition: 52 `claude-3.5-sonnet` / 28 `gpt-4o`; early 20 / mid 41 / late 19; read 53 / write 27. | as listed | `artifacts/audit/sample_report.json` → `stats` | recorded |
| H-16 | 60 calibration prefixes (30 airline + 30 retail) are disjoint from the 880; 4,437 were available. | 60 (30/30); available 4,437 | `artifacts/audit/freeze_dry_run.json` → `calibration`; `artifacts/audit/calibration_render_report.json` | **frozen** |
| H-17 | The 6,554 figure is a planning input, not achieved supply. | 6,554 (airline 1,593; retail 4,961; 165 task–domain pairs) | `prereg/PREREGISTRATION.md` §3; `docs/IMPLEMENTATION_PLAN.md` §4; `prereg/AMENDMENTS.md` harvest note | superseded — never report as eligible |

### 1.2 Rendering, perturbations, and PII

| ID | Claim (manuscript wording) | Exact value | Source | Status |
|---|---|---|---|---|
| R-01 | The frozen sample has five arms per prefix: 4,400 rendered arms (880 × 5), 880 per arm. | 4,400; 880 each | `artifacts/audit/render_report.json` → `by_arm`; `data/manifests/toolresult800_v1.json` → `counts.rendered_arms` | **frozen** |
| R-02 | There are 2,640 perturbation records, 880 each for s=1, s=2, and s=3. | 2,640; 880 each | `artifacts/audit/render_report.json`; `data/manifests/perturbations.jsonl` (2,640 lines); manifest → `counts.perturbations` | **frozen** |
| R-03 | The s=0 arm preserves the V value set on 100% of prefixes; the render reports 0 errors. | 100%; 0 errors | `docs/GATES.md:50`; `artifacts/audit/render_report.json` → `error_count`, `errors`; `configs/arms.yaml` (`verify_s0_value_set_equals_v: true`) | recorded (the equality metric itself is not stored) |
| R-04 | The renderer is `toolresult-prose-v1`; no LLM paraphrase enters the manipulation. | `toolresult-prose-v1`; hash `9bea0e8d8995a290000b0deb51be01365749da41b0a5290e3ab2badce3c21405` | manifest → `renderer_version`, `renderer_hash`; `configs/arms.yaml` | **frozen** |
| R-05 | Calibration rendering covers 60 records, 300 arms, and 180 perturbations. | 300; 180 | `artifacts/audit/calibration_render_report.json` | recorded |
| R-06 | The scrubbed scan has 0 residual direct identifiers; 30,321 PII tokens were replaced across 5,516 records, with 1,946 trajectory maps. | 0; 30,321; 5,516; 1,946 | `artifacts/audit/scrub_report.json` → `scrub`, `direct_identifiers_remaining` | recorded |
| R-07 | PII fields are never perturbed; every perturbation record carries `pii_check` and `identifier_check`. | boolean fields | `data/manifests/perturbations.jsonl`; `docs/PROTOCOL.md` §3 | **frozen** |

### 1.3 Freeze record and hashes

| ID | Claim (manuscript wording) | Exact value | Source | Status |
|---|---|---|---|---|
| F-01 | The frozen manifest is `data/manifests/toolresult800_v1.json`, 5,285,713 bytes, SHA-256 `d6e034d7f1132b314ad1f82bf14faa0f6762975ee7b404b54cc365acfac5487a`. | 5,285,713 bytes; `d6e034d7…5487a` | `data/manifests/toolresult800_v1.sha256.json`; `artifacts/audit/g0_report.md`; recomputed at snapshot (match) | **frozen / verified** |
| F-02 | The manifest was frozen at 2026-11-15T09:45:02Z at git commit `1673856cc6cd335ae9fd8b0132343082f167077a`, with no target outputs before freeze. | `2026-11-15T09:45:02+00:00`; `1673856…`; `no_target_outputs_before_freeze: true` | manifest → `freeze`; `artifacts/audit/g0_report.md` | **frozen** |
| F-03 | The frozen prefix payload hash is `6f6374cdda311d53ee5b58f0a3f5ec3a7c0d7440692951d8d6f547998256ca97`. | `6f6374cd…ca97` | manifest → `frozen_prefixes_hash`; `data/frozen/prefixes.jsonl` (880 lines; recomputed match) | **frozen / verified** |
| F-04 | The perturbation-record hash is `4b47f9b5f60b988ca3bdf5f90696b73ab4d9cfcab746bbdb5b922a777d8e8cf5`. | `4b47f9b5…8cf5` | manifest → `perturbations_hash`; `data/manifests/perturbations.jsonl` (recomputed match) | **frozen / verified** |
| F-05 | The renderer hash is `9bea0e8d8995a290000b0deb51be01365749da41b0a5290e3ab2badce3c21405`. | `9bea0e8d…1405` | manifest → `renderer_hash`; `artifacts/audit/g0_report.md` | **frozen** |
| F-06 | The field-registry hash is `3cbcfa063352b09cef9ce1207ce3d1135c2735d5732a4702a1f6a9bfa47d4dab`. | `3cbcfa06…4dab` | manifest → `field_registry_hash`; `configs/field_registry.yaml` (recomputed match) | **frozen / verified** |
| F-07 | The preregistration hash is `e0d107c6013065374fb16df204e2eb30fbcafad039ed6fc7050c68dd26f4fc8a`. | `e0d107c6…fc8a` | manifest → `prereg_hash`; `prereg/PREREGISTRATION.md` (recomputed match) | **frozen / verified** |
| F-08 | The source-pin hash is `b74cfdc810387c209682e2b178178751d2b00c27319ad2bc12a71c43ae7a4d48`. | `b74cfdc8…4d48` | manifest → `source_pin_hash`; canonical JSON reconstruction of `data/manifests/source_pin.json` (match) | **frozen / verified** |
| F-09 | The sample hash is `d86021f9f1343223fa3250974ba7cb487bb957bbf90606b5b19c4a021ed93764`. | `d86021f9…3764` | manifest → `sample_hash`; `data/interim/sample.jsonl` (880 lines; recomputed match) | **frozen / verified** |
| F-10 | The τ-bench source is pinned at commit `59a200c6d575d595120f1cb70fea53cef0632f6b` under MIT, with 4 trajectory files and 6 task-DB hashes. | `59a200c…f6b`; MIT; 4 + 6 hashes | `data/manifests/source_pin.json`; `configs/harvest.yaml:7-13` | **frozen** |
| F-11 | The manifest schema is `toolresult800-manifest-v1`; the dataset id is `toolresult800-v1`. | `toolresult800-manifest-v1`; `toolresult800-v1` | manifest → `schema_version`, `manifest_id` | **frozen** |

Hash semantics (do not mix them up):

- `manifest_sha256`, `frozen_prefixes_hash`, `perturbations_hash`, `sample_hash`, and
  `field_registry_hash` are raw-byte SHA-256 values and were recomputed at snapshot.
- `source_pin_hash` is the SHA-256 of canonical JSON (`indent=2`, trailing LF), not the raw file
  bytes. The raw `source_pin.json` hash at snapshot is
  `5942df70325fd99e2d3dda5765a79b2481c24d690525879e8f0099e7ab3519a0`; the manifest value
  reconstructs from the same object. Cite the manifest value, not the raw-file value.
- `prereg_hash` matches the current `PREREGISTRATION.md` bytes, even though the document still
  carries a `DRAFT` banner and `TBD` sign-off. See X-21.

### 1.4 G0 audit provenance

| ID | Claim (manuscript wording) | Exact value | Source | Status |
|---|---|---|---|---|
| A-01 | The G0 audit has 40 items (20 airline + 20 retail), a pass minimum of 36, and 40 items passed. | 40 (20/20); minimum 36; passed 40 | `artifacts/audit/g0_audit_result.json`; `artifacts/audit/g0_audit_packet.json`; manifest → `audit` | **provisional** |
| A-02 | The audit record carries `label_source=ai_preaudit_deferred_human`. | `ai_preaudit_deferred_human` | `artifacts/audit/g0_audit_result.json` → `label_source`; manifest → `audit.label_source` | **provisional** |
| A-03 | The AI pre-audit passed 40/40 items on all four checks, with 0 items flagged for attention; the official audit status remained `pending_human`. | 40/40; 0 attention; `pending_human` | `artifacts/audit/g0_audit_ai_preaudit.json`; `artifacts/audit/g0_audit_ai_preaudit.md` | **provisional** |
| A-04 | The 40 official rows are filled from the AI pre-audit with the provenance note on every row. | 40 rows; note text | `artifacts/audit/g0_audit_sheet.csv` (notes column) | **provisional** |
| A-05 | The author adopted the AI pre-audit under D-021 and deferred independent verification until after the experiments. | decision text | `docs/DECISIONS.md` D-021; `prereg/AMENDMENTS.md` audit-provenance note; `docs/GATES.md:31-33` | **provisional** |
| A-06 | A failed post-experiment verification item would be replaced from the reserve, re-audited, and disclosed. | procedure | `docs/DECISIONS.md` D-021 (consequences) | **provisional** |
| A-07 | The author's independent verification result is not yet available. | `[PENDING: g0_human_verification]` | No artifact; D-021 defers it | **pending** |

**Use exactly this wording (and no stronger):**

> The 40-item G0 audit was scored from an AI pre-audit in which 40/40 items passed all four
> mechanical checks; the author adopted those labels under D-021, the audit record carries
> `label_source=ai_preaudit_deferred_human`, and independent author verification is deferred
> until after the experiments. We do not claim human sign-off.

Do **not** write "the human audit passed", "40/40 human review", or "160/160 checks". The unit is
40 items, each passing four checks; 40/40 items is not 160/160 individual checks.

### 1.5 Models, environment, and fit

| ID | Claim (manuscript wording) | Exact value | Source | Status |
|---|---|---|---|---|
| M-01 | The confirmatory trio is three open-weight 8–9B families: Qwen3.5-9B-AWQ, Ministral-3-8B-Instruct-2512-AWQ, and Llama-3.1-8B-Instruct-AWQ-INT4. | 3 families; 8–9B | `README.md:88`; `docs/DECISIONS.md` D-016; `prereg/AMENDMENTS.md` model-trio note; `docs/DATA_CARD.md:46` | narrative (design fact) |
| M-02 | Qwen3.5-9B-AWQ is `cyankiwi/Qwen3.5-9B-AWQ-4bit` at revision `e4d2d39cede8c5d1716d824cd843e2889c648083`. | repo + revision | `configs/models.yaml:12-14`; `artifacts/server_sync/env/qwen3_5_9b_fit_check_24k.json` | **frozen pin** |
| M-03 | Ministral-3-8B-Instruct-2512-AWQ is `cyankiwi/Ministral-3-8B-Instruct-2512-AWQ-4bit` at revision `563842192acb68a00b8864e3bfa5a3e740ece90c`. | repo + revision | `configs/models.yaml:29-31`; `artifacts/server_sync/env/ministral_3_8b_fit_check_24k.json` | **frozen pin** |
| M-04 | Llama-3.1-8B-Instruct-AWQ-INT4 is `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` at revision `db1f81ad4b8c7e39777509fac66c652eb0a52f91`. | repo + revision | `configs/models.yaml:51-53`; `artifacts/server_sync/env/llama_3_1_8b_fit_check_24k.json` | **frozen pin** |
| M-05 | All three models load and generate at 24,576 context, batch 4, `gpu_memory_utilization=0.85`, and `max_num_seqs=8`, with four successful outputs each. | 24,576; batch 4; 0.85; 8; 4/4 outputs | `artifacts/server_sync/env/*_fit_check_24k.json`; `docs/H200_ENV.md:39-46` | environment |
| M-06 | 24k load times are Qwen 94.7 s, Ministral 51.7 s, Llama 41.0 s; batch-generation times are 0.158 s, 0.082 s, 0.107 s. | 94.7 / 51.7 / 41.0 s; 0.158 / 0.082 / 0.107 s | `qwen3_5_9b_fit_check_24k.json`; `ministral_3_8b_fit_check_24k.json`; `llama_3_1_8b_fit_check_24k.json` | environment |
| M-07 | Recorded GPU memory after load/generation is 13,889 / 14,790 / 14,576 MiB of 18,432 MiB. | 13,889; 14,790; 14,576; 18,432 MiB | the three 24k fit JSONs → `gpu_after` | environment |
| M-08 | Weights and KV cache: Qwen 8.37 GiB / 4.63 GiB (89,770 tokens; 10.96× at 8k); Ministral 7.03 GiB / 7.15 GiB (55,104; 6.73×); Llama 5.58 GiB / 8.38 GiB (68,640; 8.38×). | as listed | `docs/DECISIONS.md` D-016; `docs/H200_ENV.md:42-46` | environment |
| M-09 | The environment is driver 580.178.04, CUDA 13.5, Python 3.12.3, vLLM 0.33.0, torch 2.14.0+cu130, Transformers 5.20.2, on the H200 1g.18gb slice. | as listed | `docs/H200_ENV.md:5-14`; `artifacts/server_sync/env/gpu_install.log`; fit JSONs → `vllm`, `torch` | environment |
| M-10 | Qwen3.5 runs with its thinking block disabled; Ministral runs with reasoning effort `none`. | `enable_thinking: false`; `reasoning_effort: none` | `configs/models.yaml:27-28,49-50`; `docs/DECISIONS.md` D-017 | environment |
| M-11 | Two synthetic ~20k-token prompts per model pass at batch 2 and 16 output tokens: Qwen 20,002 tokens / 4.30 s; Ministral 20,001 / 5.17 s; Llama 20,025 / 5.46 s. | as listed | `qwen3_5_9b_long_prompt_fit.json`; `ministral_3_8b_long_prompt_fit.json`; `llama_3_1_8b_long_prompt_fit.json`; `docs/H200_ENV.md:61` | environment |
| M-12 | Ministral returned empty strings on the repetitive long prompt; this is a watch item, not a load failure. | 2 empty outputs | `ministral_3_8b_long_prompt_fit.json` → `outputs`; `docs/H200_ENV.md:69-71` | environment |
| M-13 | Prompt v3 produced parsed JSON on all three models in the backend smoke test: Qwen `final_answer`, Ministral `get_user_details`, Llama `list_all_airports`. | 3/3 parsed | `artifacts/server_sync/env/backend_v3_smoke.log`; `artifacts/server_sync/env/v3_smoke.log` | environment |
| M-14 | The fit checks are environment evidence, not study results; the historical Qwen2.5-7B check is not the confirmatory model. | 1 historical check | `docs/DECISIONS.md` D-015, D-016; `docs/H200_ENV.md:99-100` | environment |

### 1.6 Prompt-length audit and context

| ID | Claim (manuscript wording) | Exact value | Source | Status |
|---|---|---|---|---|
| P-01 | All 880 V-arm prompts were tokenized with the three pinned tokenizers at 24,576 context; none exceeded the context or the prompt budget. | 880; 24,576; `over_context=0`; `over_prompt_budget=0` | `artifacts/server_sync/env/prompt_lengths.json` | recorded |
| P-02 | Qwen prompt tokens: min 3,777; p50 6,446; p90 9,331; p95 10,292; p99 12,969; max 20,124. | as listed | `prompt_lengths.json` → `models.qwen3_5_9b_instruct_awq.tokens` | recorded |
| P-03 | Ministral prompt tokens: min 3,919; p50 6,645; p90 9,572; p95 10,609; p99 13,436; max 20,681. | as listed | `prompt_lengths.json` → `models.ministral_3_8b_instruct_2512_awq.tokens` | recorded |
| P-04 | Llama prompt tokens: min 3,617; p50 5,812; p90 8,085; p95 8,813; p99 10,955; max 16,195. | as listed | `prompt_lengths.json` → `models.llama_3_1_8b_instruct_awq.tokens` | recorded |
| P-05 | The longest audited prompt is 20,681 tokens (Ministral); the audit reserved 256 decision tokens. | 20,681; 256 | `prompt_lengths.json` → `max`, `max_tokens` | recorded |
| P-06 | The context was raised from 8k to 24,576 tokens; no prefix is truncated, dropped, or re-sampled; 107–237 of 880 prefixes would have exceeded 8k. | 24,576; 107–237 | `docs/DECISIONS.md` D-019; `prereg/AMENDMENTS.md` context note; `configs/models.yaml:22,39,61` | decision |
| P-07 | The current decision budget is 1,024 tokens, not the 256 tokens used at audit time. | 1,024 vs 256 | `docs/DECISIONS.md` D-023; `configs/models.yaml:69`; `prompt_lengths.json` → `max_tokens` | decision (see X-11) |

**Discrepancy to resolve before the context paragraph:** three values are in circulation:
**20,848** (D-019), **20,682** (current `ROADMAP.md`, `docs/H200_ENV.md:49-50`, and
`configs/models.yaml:9` in the working tree), and **20,681** (the audit artifact
`prompt_lengths.json`). No source in this checkout explains the 167-token or 1-token gap. Use
20,681 (the artifact) until a source reconciles it; do not write 20,848 or 20,682 as if either
were the audited value.

### 1.7 Design, estimands, gates, and budget

| ID | Claim (manuscript wording) | Exact value | Source | Status |
|---|---|---|---|---|
| D-01 | The design has five arms: V, s=0, s=1, s=2, s=3; V is excluded from the primary slope and s=0 is the placebo. | 5 arms | `docs/PROTOCOL.md` §3; `configs/arms.yaml`; `prereg/PREREGISTRATION.md` §6 | design |
| D-02 | The primary estimand is `logit P(Y_{p,m,s}=1) = α_{p,m} + β_m s` for s = 0…3, with prefix-cluster SEs and a pooled prefix × model stratification. | equation | `docs/PROTOCOL.md` §1; `prereg/PREREGISTRATION.md` §4; `docs/IMPLEMENTATION_PLAN.md` §9 | design |
| D-03 | The main-run envelope is 34,800 generations: 12,000 base + 19,200 transient + 2,400 persistent + 1,200 jitter. | 34,800 = 12,000 + 19,200 + 2,400 + 1,200 | `configs/main.yaml` → `generation_budget`; `prereg/PREREGISTRATION.md` §3; `docs/DATA_CARD.md:47-50` | design |
| D-04 | Calibration is 900 generations: 60 prefixes × 5 arms × 3 models. | 900 | `configs/calibration.yaml:2-7`; `docs/GATES.md:71` | design |
| D-05 | Recovery uses H=4; transient injection is primary; persistent injection covers 25% (200 prefixes) at s=3; endpoints are R1 and R2; censoring is at H=4. | H=4; 25%; 200; R1/R2 | `docs/PROTOCOL.md` §5; `configs/main.yaml` → `recovery`; `configs/arms.yaml` → `recovery` | design |
| D-06 | At N=800 the per-model MDE is 0.203 logit/level (OR 1.22) at 80% power and α=.05, assuming a 4% placebo switch rate and intercept variance 1.0; the pooled MDE is ≤0.15. | 0.203; OR 1.22; 80%; α=.05; 4%; 1.0; ≤0.15 | `prereg/PREREGISTRATION.md` §4; `docs/IMPLEMENTATION_PLAN.md` §9 | design |
| D-07 | Inference uses 2,000 prefix-cluster bootstrap replicates, percentile 95% CIs, and Holm correction across the three model slopes in a fixed sequence. | 2,000; 95%; Holm; 3 models | `prereg/PREREGISTRATION.md` §8; `docs/PROTOCOL.md` §6 | design |
| D-08 | The budget is $0 cash, 35–45 GPU-hours on the H200 1g.18gb slice, with a hard stop at 45 GPU-hours or 200 GB storage; no paid API and no second GPU. | $0; 35–45 GPU-h; 45 GPU-h; 200 GB; 18 GB VRAM | `ROADMAP.md` §5; `README.md:93`; `configs/main.yaml` → `budget` | design |
| D-09 | Annotation is about 200 judgments at $0: 160 outcome items plus 40 severity items (2 blind co-authors); the severity audit separately uses 120 observations (30/level, 3 raters); the recovery audit uses 80 sequences (2 raters). | ~200; 160 + 40; 120; 80 | `docs/PROTOCOL.md` §8; `prereg/PREREGISTRATION.md` §6 | design (see X-22) |
| D-10 | G0 criteria: ≥880 eligible; ≥440/domain pre-audit; ≥400/domain post-audit; replay ≥98%; audit ≥36/40. | as listed | `docs/GATES.md` G0; `ROADMAP.md` §4 | gate |
| D-11 | G1 criteria: parse ≥95%; placebo jitter ≤20%; s=3 switch 10–80%; format refusal <5% per model. | as listed | `docs/GATES.md` G1; `configs/calibration.yaml` → `gates` | gate |
| D-12 | G2 stops at 45 GPU-hours or 200 GB storage, whichever comes first, with a complete ledger. | 45 GPU-h; 200 GB | `docs/GATES.md` G2; `configs/main.yaml` → `budget` | gate |
| D-13 | G3 criteria: pooled β>0; positive in ≥2/3 models with the same sign; severity α≥.75; outcome κ≥.80 (or adjudicated ≥.70 with downgrade); recovery κ≥.75; silent-PPV ≥.90; parser failure <1%. | as listed | `docs/GATES.md` G3 | gate |
| D-14 | G4 criteria: ≥50% of the s=3 risk set recovers by H=4; Weibull shape not rejected at p≥.01. | ≥50%; p≥.01 | `docs/GATES.md` G4 | gate |
| D-15 | Severity is ordinal, not interval; the linear slope is a summary and the s=2 vs s=3 contrast is reported separately. | ordinal | `docs/PROTOCOL.md` §3; `prereg/PREREGISTRATION.md` §4 | design |

### 1.8 Pilot (screening only)

| ID | Claim (manuscript wording) | Exact value | Source | Status |
|---|---|---|---|---|
| PIL-01 | The pilot used N=60 synthetic WebArena-lite / τ-style prefixes, `qwen3.5:4b`, greedy decoding, and three collapsed action codes (trust / re-call / flag). | N=60; 1 model; 3 codes | `README.md:63-64`; `prereg/PREREGISTRATION.md` §1; `paper/proposal.tex:114-117` | **screening** |
| PIL-02 | Consult rate was 54/60 = 90.0%. | 54/60 = 90.0% | `README.md:69`; `prereg/PREREGISTRATION.md` §1 | **screening** |
| PIL-03 | Placebo jitter (P vs T) was 0/60 = 0%. | 0/60 = 0% | `README.md:70`; `prereg/PREREGISTRATION.md` §1 | **screening** |
| PIL-04 | Error switch (E vs T) was 5/60 = 8.3%, 95% CI [1.3, 15.3] pp. | 5/60 = 8.3%; [1.3, 15.3] | `README.md:71-72`; `paper/proposal.tex:132-133` | **screening** |
| PIL-05 | McNemar was b=5, c=0, exact p=.0625. | b=5; c=0; p=.0625 | `README.md:73`; `prereg/PREREGISTRATION.md` §1 | **screening** |
| PIL-06 | The human spot-check agreed on 12/12 labels. | 12/12 | `README.md:74`; `paper/proposal.tex:135` | **screening** |
| PIL-07 | The pilot is not pooled with the confirmatory sample and is not used to rescue a null result. | rule | `README.md:76-80`; `docs/DECISIONS.md` D-003; `prereg/PREREGISTRATION.md` §1 | **screening** |
| PIL-08 | The 8.3 pp gap is an action-level lower bound because letter coding missed silent fact propagation; the CI is an unpaired Wald interval and the McNemar test is the design-matched comparison. | caveat | `README.md:76-80`; `paper/proposal.tex:143-147` | **screening** |

### 1.9 Claim boundary and data policy

| ID | Claim (manuscript wording) | Exact value | Source | Status |
|---|---|---|---|---|
| B-01 | The claim is bounded to three open-weight 8–9B model families, τ-bench airline and retail, one deterministic renderer, four severity levels, and four recovery steps. | 3 families; 2 domains; 1 renderer; 4 levels; H=4 | `README.md:100-106`; `ROADMAP.md` §1; `docs/PROTOCOL.md` §1 | design |
| B-02 | The paper does not claim a universal law, a model ranking, frontier transfer, end-to-end task success, or live-API validity. | rule | `README.md:102-106`; `ROADMAP.md` §1; `docs/PROTOCOL.md` §1 | design |
| B-03 | A null or flat slope is reported as a measurement result, not reframed as a positive law. | rule | `README.md:105-106`; `ROADMAP.md` §1; `docs/GATES.md` G3 | design |
| B-04 | Raw τ-bench trajectories, interim data, frozen prefixes, and run ledgers are never committed; only small manifests are tracked. | rule | `README.md:146-159`; `AGENTS.md` §3 | policy |
| B-05 | ToolResult-800 additions are CC BY 4.0; upstream τ-bench remains MIT; the release contains only scrubbed derived data. | licenses | `README.md:179-184`; `docs/DATA_CARD.md` §7; `DATA_LICENSE.md` | policy |
| B-06 | The release is blocked without a passed G0 audit and a frozen manifest, and is re-scanned for PII. | rule | `docs/RUNBOOK.md` §6; `release/README.md`; `scripts/10_release.py` | policy |

---

## 2. Terminology lock

Use the left column exactly in the manuscript. The right column lists variants to avoid. Code and
artifact field names (for example `s0`, `qwen3_5_9b_instruct_awq`) belong in the reproducibility
appendix, not in the prose.

### 2.1 Dataset and unit

| Locked term | Exact form | Definition | Do not write |
|---|---|---|---|
| Dataset | **ToolResult-800** | The dataset brand: 800 primary frozen prefixes + 80 reserve, with perturbations, arms, and traces | CTO-800, E2, ToolResult800, ToolResult 800, "the 800" |
| Dataset full title | **Counterfactual Tool-Observation dataset, 800 frozen prefixes** | Full title from the data card | "tool-observation dataset" |
| Manifest | `toolresult800_v1.json` | Frozen manifest id `toolresult800-v1` | `cto800_v1.json`, `toolresult800.json` |
| Prefix | **frozen prefix** | A message prefix ending immediately after a real τ-bench tool observation; the unit of analysis | "prompt", "episode", or "trajectory" when the prefix is meant |
| Donor | **donor** | The historical model that produced the prefix (gpt-4o or claude-3.5-sonnet) | "source model" |
| Target | **target model** | One of the three open-weight 8–9B models that produces the next decision | "test model", "student" |
| Study | **tool-result study** or **Tool-Result Errors in Language-Model Agents** | The study name | "E2" |

**Title status (fix before submission):** the working manuscript
(`paper/toolresult800.tex:255`) uses "Tool-Result Errors in Language-Model Agents: A Fixed-Prefix
Causal Study of Detection, Reliance, and Recovery". Other variants remain in
`configs/base.yaml` ("A Fixed-Prefix Causal Study"), `paper/proposal.tex` ("A Controlled Study of
Detection, Reliance, and Recovery"), and `README.md` (a lowercase sentence). Use the manuscript
title in the PDF metadata, abstract, and release; update the other files to match. Do not mix
subtitles.

### 2.2 Arms

| Locked term | Exact form | Definition | Do not write |
|---|---|---|---|
| Verbatim arm | **V** | Exact real tool output as raw JSON; format/jitter anchor; excluded from the primary slope | "baseline", "control", "T" |
| Placebo | **s=0** | Faithful deterministic prose with all values preserved | S0, "placebo arm" without s=0 |
| Negative control | **s=1** | One non-critical field changed or omitted; the field is absent from the donor continuation | "easy", "minor", "low" |
| Dose | **s=2** | One decision-critical field changed to a plausible wrong value | "error arm" alone |
| Compound dose | **s=3** | A critical wrong value plus a second detectable contradiction | "severe", "worst", "max" |
| Severity | **severity level s** | Ordinal level 0…3; the slope is a summary, not an interval scale | "dose" as a physical quantity |

### 2.3 Outcomes

| Locked term | Exact form | Definition | Do not write |
|---|---|---|---|
| Any sensitivity | **Y** | Decision signature differs from the V continuation | "switch" without defining it once |
| Action switch | **Y^A** | Tool name or canonicalized arguments differ from V | "action change" as a separate label |
| Detection | **Y^F** | Explicit flag, doubt, "inconsistent", "verify", or "cannot trust" | "flag rate" without the label |
| Silent propagation | **Y^U** | The false critical value appears in decision content/args with no flag; scored only for s=2 and s=3 | "silent error", "hallucination" |
| Decomposition | **Y = Y^A ∨ Y^F ∨ Y^U** | Strict silent propagation is `Y^U ∧ ¬Y^A ∧ ¬Y^F` | "Y is the union of the three" without the formula |

**Signature note (D-024):** a final answer now hashes to an action verb plus a sorted set of status
slots (`cancel`, `book`, `modify`, `confirm`, `deny`, `refund`, `transfer`, `upgrade`, `downgrade`,
`exchange`, `return`, `keep`, `cannot`, `unable`, `not possible`, `succeed`, `fail`, `change`,
`update`). Numbers, dates, and identifiers are not signature slots. Primary Y is therefore
decision-level for final answers, while Y^U still checks the perturbation's false value against
the full output. Do not describe Y as a full-string comparison.

### 2.4 Recovery

| Locked term | Exact form | Definition | Do not write |
|---|---|---|---|
| Horizon | **H=4** | Four continuation steps after the injected observation | "4 steps" in formulas; "four-step" is fine in prose |
| Recovery endpoint 1 | **R1** | First step where the signature matches V (correct decision) | "recovery" alone |
| Recovery endpoint 2 | **R2** | First step where the model explicitly flags (detection) | "flag recovery" |
| Risk set | **risk set** | Prefixes whose decision moved at injection (`Y^U=1` or `Y^A=1`) and did not flag there | "failures" |
| Half-life | **t½** | `ln 2 / μ`; reported only if ≥50% recover by H=4 and the Weibull shape is not rejected | "half-life law" |
| RMST | **RMST** | Restricted mean survival time; reported regardless | "average recovery time" |
| Persistent injection | **persistent** | The same field is corrupted on 25% of prefixes; recovery requires flagging or working around | "permanent" |

### 2.5 Gates

| Locked term | Exact form | One-line criterion |
|---|---|---|
| G0 | **G0** | ≥880 eligible; ≥440/domain pre-audit; ≥400/domain post-audit; replay ≥98%; 40-item audit ≥36/40 |
| G1 | **G1** | Parse ≥95%; placebo jitter ≤20%; s=3 switch 10–80%; refusal <5% per model |
| G2 | **G2** | Main run completes within 45 GPU-hours and 200 GB storage, with a complete ledger |
| G3 | **G3** | Pooled β>0; positive in ≥2/3 models with the same sign; α≥.75; κ≥.80 (or adjudicated ≥.70); recovery κ≥.75 |
| G4 | **G4** | ≥50% of the s=3 risk set recovers by H=4; Weibull shape not rejected (p≥.01) |

### 2.6 Model identifiers

| Display name (prose) | Internal id (code) | Repository | Revision |
|---|---|---|---|
| **Qwen3.5-9B-AWQ** | `qwen3_5_9b_instruct_awq` | `cyankiwi/Qwen3.5-9B-AWQ-4bit` | `e4d2d39cede8c5d1716d824cd843e2889c648083` |
| **Ministral-3-8B-Instruct-2512-AWQ** | `ministral_3_8b_instruct_2512_awq` | `cyankiwi/Ministral-3-8B-Instruct-2512-AWQ-4bit` | `563842192acb68a00b8864e3bfa5a3e740ece90c` |
| **Llama-3.1-8B-Instruct-AWQ-INT4** | `llama_3_1_8b_instruct_awq` | `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` | `db1f81ad4b8c7e39777509fac66c652eb0a52f91` |

Rules: write **8–9B**, not 7–8B. Write the quantized display name, not the base model name, when
reporting results. Use the internal id only in tables that also give the display name. The
historical `Qwen2.5-7B-Instruct-AWQ` check is environment history, not a fourth model.

### 2.7 Version strings

| Item | Locked value | Source |
|---|---|---|
| Renderer | `toolresult-prose-v1` | manifest → `renderer_version` |
| Prompt | `toolresult-next-decision-v3` | `configs/calibration.yaml:10`; D-020 |
| Parser, G0 snapshot | `toolresult-parser-v1` | D-014; G0 config snapshot |
| Parser, D-024 decision | `toolresult-parser-v2` | D-024 (status/action slots; superseded by D-025) |
| Parser, current code/config | `toolresult-parser-v3` | D-025 (decision-verb slots and ledger re-scoring); `src/toolobs/infer/runner.py:24`; `configs/calibration.yaml:11` |
| Manifest schema | `toolresult800-manifest-v1` | manifest → `schema_version` |
| Perturbation schema | `toolresult800-perturbation-v1` | `data/manifests/perturbations.jsonl` |
| G1 serving overlay | constrained JSON regex; `think` excluded; 1,024-token budget; no `\n\n` stop | D-023 |
| Ministral G1 serving | `enforce_eager: true`; `max_num_seqs: 4`; `max_num_batched_tokens: 4096` | `configs/models.yaml:44-46` |

### 2.8 Status vocabulary in prose

Use these labels consistently:

- **screening signal** — the pilot, and only the pilot.
- **environment evidence** — fit checks, load times, memory, smoke tests.
- **harness evidence** — G1 calibration; never a model-capability finding.
- **provisional gate** — the G0 audit under D-021.
- **study result** — a G2/G3/G4 estimate with a ledger row and an analysis artifact.

---

## 3. Pending results — G1 calibration (not study results)

**Status at snapshot:** G1 is in progress. No `artifacts/audit/g1_calibration.json` exists; G2 has
not started. The calibration sample is 60 prefixes (30 airline + 30 retail), disjoint from the
800, and stays out of the primary analysis (`docs/GATES.md:71-72`).

| Model | Rows generated | Parse result | G1 status | Source |
|---|---:|---|---|---|
| Qwen3.5-9B-AWQ | 300/300 first run; re-scored, not regenerated | 300/300 first run (D-023); placebo jitter **42.4%** (v1) → **23.7%** (v2) → **13.3%** (v3) | Parse gate passed; jitter is 13.3% under v3 (below the 20% threshold); s=3 and refusal gates not recorded; final G1 verdict `[PENDING: g1_qwen_verdict]` | `docs/DECISIONS.md` D-023, D-024, D-025 |
| Ministral-3-8B-Instruct-2512-AWQ | First attempt: 300 rows | 76/300 parsed = 25.3% (42 empty outputs, 134 truncated `final_answer` objects, a few prompt echoes) | **Failed the parse gate** (<95%); rerun required under D-023/D-024 | `docs/DECISIONS.md` D-023; `configs/models.yaml:41-46` |
| Llama-3.1-8B-Instruct-AWQ-INT4 | 0 recorded | Not run | `[PENDING: g1_llama_rows]` | No Llama G1 artifact in `artifacts/`; D-023 reports no Llama run |

**What changed during G1**

- D-022: one vLLM process per model. Loading Qwen then Ministral in one process left the first
  engine alive and Ministral failed with `CUBLAS_STATUS_ALLOC_FAILED`.
- D-023: exclude the `think` tool from the prompt and constrained decoding; force one JSON object
  with a listed task tool or `final_answer` using a vLLM structured regex; raise the decision
  budget from 256 to 1,024 tokens; remove the `\n\n` stop sequence.
- D-024: Qwen's first fixed-harness calibration had **42.4% placebo jitter**; the differences were
  almost entirely paraphrased `final_answer` text, and action-level differences were 10%. The
  final-answer signature was changed to an action verb plus sorted status slots (numbers, dates,
  and identifiers excluded); the parser becomes `toolresult-parser-v2`. Jitter fell to 23.7%,
  still above the 20% gate.
- D-025: the status set was restricted to decision verbs; jitter fell to **13.3%**. The parser
  becomes `toolresult-parser-v3`. Existing G1 ledgers are re-scored without regenerating outputs,
  and the stored `output_text` is never changed. The primary Y is decision-level for final
  answers; Y^U remains value-level.
- The jitter progression is a signature-definition fix, not a model-capability finding.
- Ministral serving was made conservative after a 24k + batch-8 OOM at row 96: eager mode, 4
  sequences, 4k chunked prefill (`configs/models.yaml:41-46`).
- On five previously failing Ministral rows, the constrained run parsed 5/5 as real task actions
  (`get_user_details`, `search_direct_flight`). This is **harness evidence, not a study result**
  (`docs/DECISIONS.md` D-023).
- G1 was rerun from scratch after D-023; D-025 re-scores the existing G1 ledgers without
  regenerating outputs. The frozen data, manifest, sample, arms, and estimand are unchanged
  (`docs/DECISIONS.md` D-023, D-025).

**Prohibited sentences (do not write any of these)**

- "Qwen is more robust than Ministral" or any model comparison from G1 rows.
- "Ministral fails calibration" as a model-capability finding. Write: "the first Ministral
  calibration attempt failed the parse gate; the harness was revised and G1 is being rerun."
- "Qwen passed calibration." Write: "Qwen produced 300/300 parseable rows; placebo jitter fell
  from 42.4% to 13.3% as the final-answer signature was revised (D-024/D-025); the remaining G1
  gates are not yet recorded."
- "Qwen is unstable" or "Qwen is hypersensitive." The 42.4% jitter was driven by paraphrased
  `final_answer` text under an over-strict signature; it is a parser/signature artifact, not a
  model-capability finding (D-024/D-025).
- "Llama passed/failed." Llama has not been run under G1.
- "Calibration shows s=3 is not a ceiling." That is a G1 gate check, not a result; the value is
  `[PENDING: g1_s3_switch_rate]`.
- Any severity, recovery, or dose-response estimate from calibration.

**What the paper may report about G1 (Methods/Reproducibility only):** the calibration design (60
prefixes, 5 arms, 3 models, 900 generations), the four per-model thresholds, the gate history
including the first-attempt Ministral parse failure and the Qwen jitter failure that motivated
D-024, and the final pass/fail. It may not report a calibration effect size.

---

## 4. Numbers to fill after G2

Every row below is a number the manuscript will need but cannot source today. `Cardinality` is the
number of distinct values to report; do not collapse cells silently. §4.1 is the only pre-G2
block; §4.2–4.8 are filled from the main run, the label audits, the G0 re-verification, and the
release.

### 4.1 G1 handoff (before G2)

First-attempt and interim G1 values are recorded in §3; the placeholders below are for the final
G1 report that clears the gate.

| # | Quantity | Cardinality | Placeholder | Fill from |
|---|---|---:|---|---|
| 1 | Qwen parse rate, jitter, s=3 switch, refusal | 4 | `[PENDING: g1_qwen_metrics]` | G1 report |
| 2 | Ministral rerun parse rate, jitter, s=3 switch, refusal | 4 | `[PENDING: g1_ministral_metrics]` | G1 report |
| 3 | Llama parse rate, jitter, s=3 switch, refusal | 4 | `[PENDING: g1_llama_metrics]` | G1 report |
| 4 | Per-model G1 pass/fail | 3 | `[PENDING: g1_verdicts]` | G1 report |
| 5 | Calibration ledger rows completed | 1 | `[PENDING: calibration_rows]` | calibration ledger |
| 6 | Calibration GPU-hours and wall-clock | 2 | `[PENDING: calibration_cost]` | calibration ledger/cost |
| 7 | Final prompt, parser, and serving-version strings | 3 | `[PENDING: g1_version_strings]` | G1 report/config snapshot |
| 8 | G1 report date and hash | 2 | `[PENDING: g1_report_provenance]` | `artifacts/audit/g1_calibration.json` |

Qwen interim values, for orientation only: parse 300/300; placebo jitter 42.4% → 23.7% → 13.3%
under parser v1 → v2 → v3 (D-023–D-025). These are harness values; the final G1 report is still
the source for the gate verdict.

### 4.2 G2 run accounting (Methods/Reproducibility)

| # | Quantity | Cardinality | Placeholder | Fill from |
|---|---|---:|---|---|
| 9 | Run start and end UTC | 2 | `[PENDING: run_window]` | `data/runs/main/ledger.jsonl` |
| 10 | Ledger rows, total | 1 | `[PENDING: ledger_rows_total]` | ledger |
| 11 | Base generations completed / 12,000 | 1 | `[PENDING: base_completed]` | ledger |
| 12 | Transient recovery completed / 19,200 | 1 | `[PENDING: transient_completed]` | ledger |
| 13 | Persistent recovery completed / 2,400 | 1 | `[PENDING: persistent_completed]` | ledger |
| 14 | Jitter repeats completed / 1,200 | 1 | `[PENDING: jitter_completed]` | ledger |
| 15 | Total completed / 34,800 | 1 | `[PENDING: envelope_completed]` | ledger |
| 16 | GPU-hours, total | 1 | `[PENDING: gpu_hours_total]` | `artifacts/cost/main_cost.json` |
| 17 | GPU-hours per model | 3 | `[PENDING: gpu_hours_by_model]` | cost report |
| 18 | Peak storage, GB | 1 | `[PENDING: peak_storage_gb]` | cost report |
| 19 | Stop reason (complete vs cap) | 1 | `[PENDING: stop_reason]` | cost report |
| 20 | Shards completed / planned | 1 | `[PENDING: shards_completed]` | ledger |
| 21 | Missing cells | 1 | `[PENDING: missing_cells]` | ledger |
| 22 | Parser-failure rate, overall | 1 | `[PENDING: parse_failure_overall]` | ledger |
| 23 | Parser-failure rate per model | 3 | `[PENDING: parse_failure_by_model]` | ledger |
| 24 | Refusal rate per model | 3 | `[PENDING: refusal_by_model]` | ledger |
| 25 | Latency p50/p95 per model | 6 | `[PENDING: latency_by_model]` | ledger |
| 26 | Recovery state-divergence rate | 1 | `[PENDING: state_divergence]` | recovery ledger |
| 27 | Ledger SHA-256 and analysis commit | 2 | `[PENDING: ledger_provenance]` | packaged ledger |
| 28 | Model revisions verified on host | 3 | `[PENDING: host_revision_check]` | run log |

### 4.3 Primary and base-matrix results (Results, Table 2)

| # | Quantity | Cardinality | Placeholder | Fill from |
|---|---|---:|---|---|
| 29 | Prefixes analyzed (complete case) | 1 | `[PENDING: n_analyzed]` | analysis table |
| 30 | Prefixes analyzed per domain | 2 | `[PENDING: n_by_domain]` | analysis table |
| 31 | Prefixes analyzed per model | 3 | `[PENDING: n_by_model]` | analysis table |
| 32 | Switch counts Y by arm × model | 15 | `[PENDING: switch_counts_matrix]` | outcome table |
| 33 | Switch rates Y by arm × model | 15 | `[PENDING: switch_rates_matrix]` | outcome table |
| 34 | Pooled β | 1 | `[PENDING: pooled_beta]` | G3 analysis |
| 35 | Pooled SE and 95% CI | 2 | `[PENDING: pooled_se_ci]` | G3 analysis |
| 36 | Pooled one-sided p and OR per level | 2 | `[PENDING: pooled_p_or]` | G3 analysis |
| 37 | Per-model β | 3 | `[PENDING: beta_by_model]` | G3 analysis |
| 38 | Per-model SE and 95% CI | 6 | `[PENDING: se_ci_by_model]` | G3 analysis |
| 39 | Per-model raw p and Holm p | 6 | `[PENDING: p_holm_by_model]` | G3 analysis |
| 40 | Domain-specific β (airline, retail) | 2 | `[PENDING: beta_by_domain]` | G3 analysis |
| 41 | Linearity LRT statistic, df, p | 3 | `[PENDING: linearity_lrt]` | G3 analysis |
| 42 | Quadratic coefficient and p | 2 | `[PENDING: quadratic_term]` | G3 analysis |
| 43 | Tier ORs (s=1, s=2, s=3 vs s=0) | 3 | `[PENDING: tier_ors]` | G3 analysis |
| 44 | s=3 vs s=1 McNemar b, c, p | 3 | `[PENDING: mcnemar_s3_s1]` | G3 analysis |
| 45 | V vs s=0 format effect | 1 | `[PENDING: format_effect]` | G3 analysis |
| 46 | Placebo jitter rate (s=0 vs V) | 1 | `[PENDING: placebo_jitter_main]` | G3 analysis |
| 47 | Realized MDE and power at the analyzed N | 2 | `[PENDING: realized_power]` | G3 analysis |
| 48 | Missingness rate | 1 | `[PENDING: missingness_rate]` | G3 analysis |
| 49 | G3 pass/fail | 1 | `[PENDING: g3_verdict]` | `artifacts/analysis/g3_report.md` |

### 4.4 Secondary outcomes and sensitivity

| # | Quantity | Cardinality | Placeholder | Fill from |
|---|---|---:|---|---|
| 50 | Y^A counts/rates | 2 | `[PENDING: y_action]` | outcome table |
| 51 | Y^F counts/rates | 2 | `[PENDING: y_flag]` | outcome table |
| 52 | Y^U counts/rates at s=2 | 2 | `[PENDING: y_silent_s2]` | outcome table |
| 53 | Y^U counts/rates at s=3 | 2 | `[PENDING: y_silent_s3]` | outcome table |
| 54 | Silent-propagation share of Y | 1 | `[PENDING: silent_share]` | outcome table |
| 55 | Strict silent count (`Y^U ∧ ¬Y^A ∧ ¬Y^F`) | 1 | `[PENDING: strict_silent_count]` | outcome table |
| 56 | Silent-propagation PPV | 1 | `[PENDING: silent_ppv]` | outcome audit |
| 57 | Per-donor slopes (claude, gpt-4o) | 2 | `[PENDING: beta_by_donor]` | sensitivity analysis |
| 58 | Seed-repeat stability | 1 | `[PENDING: seed_repeat_stability]` | jitter analysis |
| 59 | Sensitivity β excluding s=0 | 1 | `[PENDING: beta_no_placebo]` | sensitivity analysis |
| 60 | Strict vs lenient action-coding β | 2 | `[PENDING: beta_coding_sensitivity]` | sensitivity analysis |

### 4.5 Recovery (Results, Figures; G4)

| # | Quantity | Cardinality | Placeholder | Fill from |
|---|---|---:|---|---|
| 61 | Risk-set size, s=2 transient | 1 | `[PENDING: risk_s2_transient]` | recovery table |
| 62 | Risk-set size, s=3 transient | 1 | `[PENDING: risk_s3_transient]` | recovery table |
| 63 | Risk-set size, s=3 persistent | 1 | `[PENDING: risk_s3_persistent]` | recovery table |
| 64 | R1 recovery events by H=4 | 1 | `[PENDING: r1_events]` | recovery table |
| 65 | R2 recovery events by H=4 | 1 | `[PENDING: r2_events]` | recovery table |
| 66 | Share recovered by H=4 (s=3) | 1 | `[PENDING: recovered_share]` | recovery table |
| 67 | Kaplan–Meier estimates at h=1…4 (R1) | 4 | `[PENDING: km_r1]` | recovery curve |
| 68 | RMST, R1 | 1 | `[PENDING: rmst_r1]` | recovery curve |
| 69 | RMST, R2 | 1 | `[PENDING: rmst_r2]` | recovery curve |
| 70 | μ (recovery rate) | 1 | `[PENDING: mu]` | survival model |
| 71 | t½ | 1 | `[PENDING: half_life]` | survival model |
| 72 | t½ 95% CI | 1 | `[PENDING: half_life_ci]` | survival model |
| 73 | Weibull shape k | 1 | `[PENDING: weibull_shape]` | survival model |
| 74 | Weibull LRT p | 1 | `[PENDING: weibull_p]` | survival model |
| 75 | Censored sequences at H=4 | 1 | `[PENDING: censored_count]` | recovery table |
| 76 | Persistent vs transient contrast | 1 | `[PENDING: persistent_contrast]` | recovery model |
| 77 | G4 pass/fail | 1 | `[PENDING: g4_verdict]` | `artifacts/analysis/g4_report.md` |

### 4.6 Human label audits

| # | Quantity | Cardinality | Placeholder | Fill from |
|---|---|---:|---|---|
| 78 | Severity Krippendorff α | 1 | `[PENDING: severity_alpha]` | severity audit |
| 79 | Severity Jonckheere–Terpstra p | 1 | `[PENDING: severity_jt_p]` | severity audit |
| 80 | Share of s=1 rated non-decision-changing | 1 | `[PENDING: s1_nondc_share]` | severity audit |
| 81 | Share of s=2 rated decision-changing | 1 | `[PENDING: s2_dc_share]` | severity audit |
| 82 | Share of s=3 rated decision-changing | 1 | `[PENDING: s3_dc_share]` | severity audit |
| 83 | Share of s=3 rated absurd | 1 | `[PENDING: s3_absurd_share]` | severity audit |
| 84 | Outcome Cohen's κ (4-way) | 1 | `[PENDING: outcome_kappa]` | outcome audit |
| 85 | Outcome-audit parser-failure rate | 1 | `[PENDING: audit_parse_failure]` | outcome audit |
| 86 | Recovery κ (3-way) | 1 | `[PENDING: recovery_kappa]` | recovery audit |
| 87 | Adjudicated disagreements | 1 | `[PENDING: adjudications]` | audit log |
| 88 | G3 audit pass/fail | 1 | `[PENDING: g3_audit_verdict]` | `artifacts/analysis/g3_report.md` |

### 4.7 G0 final verification (D-021)

| # | Quantity | Cardinality | Placeholder | Fill from |
|---|---|---:|---|---|
| 89 | Author verification result, x/40 | 1 | `[PENDING: g0_human_verification]` | verification sheet |
| 90 | Verification date | 1 | `[PENDING: g0_verification_date]` | verification sheet |
| 91 | Failed items | 1 | `[PENDING: g0_failed_items]` | verification sheet |
| 92 | Reserve replacements | 1 | `[PENDING: g0_replacements]` | verification sheet |
| 93 | Re-audit result for replacements | 1 | `[PENDING: g0_reaudit]` | verification sheet |

### 4.8 Release and paper metadata

| # | Quantity | Cardinality | Placeholder | Fill from |
|---|---|---:|---|---|
| 94 | Release date and DOI | 2 | `[PENDING: release_date_doi]` | release record |
| 95 | Final manifest SHA-256 (if re-frozen) | 1 | `[PENDING: final_manifest_sha256]` | manifest sidecar |
| 96 | Release file count and size | 2 | `[PENDING: release_size]` | release package |
| 97 | Analysis code commit and prereg tag | 2 | `[PENDING: analysis_commit_prereg_tag]` | git tag |
| 98 | Amendments since freeze | 1 | `[PENDING: amendments_count]` (0 at snapshot) | `prereg/AMENDMENTS.md` |
| 99 | Author list, affiliations, funding, competing interests | — | `[PENDING: paper_front_matter]` | author input |

**Do not use known values as substitutes for missing results:** the 6,554 planning figure, the
pilot numbers, any G1 row, or any number copied from `paper/proposal.tex` without checking §5.

---

## 5. Conflicts and stale text to fix before drafting

These are not scientific disagreements; they are documents that lag the frozen record. The
manuscript must use the right-hand value, and the repo docs should be corrected separately. Do not
edit the frozen manifest.

| ID | Location | Current text | Contradicted by | Manuscript action |
|---|---|---|---|---|
| X-01 | `README.md:9-14, 49-50` | "human audit and freeze pending"; "G1 calibration starts only after both pass" | `toolresult800_v1.json` → `freeze` (frozen 2026-11-15T09:45:02Z); `g0_audit_result.json`; D-021 | Say: "G0 is frozen under a provisional AI-scored audit (D-021); human verification is deferred." Never say human audit passed. |
| X-02 | `README.md:47-48` | "the official human sheet remains blank and the gate is not claimed" | `g0_audit_sheet.csv` has 40 filled rows; `g0_audit_result.json` → `gate_pass: true` | Same as X-01. |
| X-03 | `README.md:12,46`; `ROADMAP.md:15`; `RUNBOOK.md:6-10` | "no GPU run has started" / "no study workload has run" | D-023/D-024: G1 calibration ran (Qwen 300/300 first run, 42.4% jitter on the fixed harness; Ministral 76/300); no G2 | Say: "G1 calibration is in progress; no confirmatory G2 generation has run." |
| X-04 | `ROADMAP.md:37-38` | Human audit **PENDING**; Freeze **PENDING** | manifest `freeze`; `g0_audit_result.json` | Mark G0 complete-provisional, not pending. |
| X-05 | `docs/GATES.md:52` | "Freeze … pending this step" | manifest `freeze` | Mark freeze done; keep the audit provisional. |
| X-06 | `paper/proposal.tex:61,200,218,452,482` | "7–8B" | D-016; amendments model-trio note; `proposal.tex:333-336` itself says 8–9B | Replace all with **8–9B**. |
| X-07 | `paper/proposal.tex:244` | Table row "Eligible value-used observations 6,554" | `scrub_report.json` → 5,516; `GATES.md:46`; proposal text at 255-258 already corrects it | Use 5,516 as achieved; keep 6,554 only as a labeled planning input. |
| X-08 | `paper/proposal.tex:261-262` | "The 40-item human audit and the frozen manifest are pending" | manifest `freeze`; `g0_audit_result.json` | Rewrite as provisional-audit + frozen manifest. |
| X-09 | `paper/proposal.tex:445` | "pipeline entry points are stubs" | G0 stages implemented; G1 ran; manifest exists | Rewrite implementation status. |
| X-10 | `paper/toolresult800.tex:654` (20,682); `docs/DECISIONS.md` D-019 (20,848); `docs/H200_ENV.md:49-50`, `ROADMAP.md`, `configs/models.yaml:9` (20,682) | Longest prompt 20,848 or 20,682 tokens | `prompt_lengths.json` max 20,681 | Use 20,681 until reconciled, or record the source of 20,682; do not let the manuscript and artifact disagree. |
| X-11 | `docs/DECISIONS.md` D-019, D-020; `configs/models.yaml` comment history | 256-token decision budget | D-023; `configs/models.yaml:69` (1,024) | Say 1,024 for G1/G2; note 256 was the pre-G1 value. |
| X-12 | `configs/main.yaml:70-71` | `batch_size: 12`, `max_num_seqs: 16` | `configs/models.yaml` serving: batch 8, `max_num_seqs: 8`; Ministral 4 | State the actually served configuration; fix the config or document the override. |
| X-13 | `artifacts/audit/render_report.json` → `renderer_hash` | `dcfac86b0dd4766363e30ad5280f910c54b083e78ca19541bc7af8a0aa66d576` | manifest `renderer_hash` `9bea0e8d…1405` | Cite the manifest hash as the freeze hash; the render report is an earlier pre-freeze render at commit `3d0d7b6`. |
| X-14 | manifest → `config_hashes` | G0 snapshot hashes (`models.yaml` `4a7c3e99…`, `calibration.yaml` `6623b52d…`) | current `configs/models.yaml` (`dd264639…`) and `calibration.yaml` (`7259639b…`) differ from the snapshot; models.yaml changed with D-017/D-023 | Do not claim the G0 config hash describes the G1/G2 serving config; name the snapshot. |
| X-15 | Docs citing `artifacts/env/…` | e.g. `docs/H200_ENV.md:49` | This checkout stores the files under `artifacts/server_sync/env/…`; `artifacts/` is gitignored | Cite logical artifact names in the paper; package the actual files in the release. |
| X-16 | `docs/DATA_CARD.md:22` | "Manifest hash: TBD" | `d6e034d7…5487a` | Fill at release. |
| X-17 | `docs/PROTOCOL.md` §2 | 6,554 eligible; airline 1,593 / retail 4,961; 496 after cap | `scrub_report.json` 5,516; `replay_report.json` airline 442 | Treat as planning text; use the operational counts. |
| X-18 | `prereg/PREREGISTRATION.md` §3 | Harvest frame "6,554 eligible … expected" | amendments harvest note | Cite the amendment for achieved counts. |
| X-19 | `docs/H200_ENV.md:3` | "environment check only; no study prefix has been run" | G1 calibration rows exist (D-023) | Say "no confirmatory prefix; G1 calibration in progress." |
| X-20 | `artifacts/audit/g0_report.md`; `artifacts/audit/freeze_dry_run.json` | Freeze commit `1673856…`; audit commit `79c90fa…`; dry-run commit `a79457f…` | Three different commits for three artifacts | In the reproducibility appendix, name each artifact with its own commit; do not present one commit as the whole freeze. |
| X-21 | `prereg/PREREGISTRATION.md:3-6, 196-205` | Status "DRAFT — not yet frozen"; sign-off `TBD` | `prereg_hash` is recorded in the manifest and matches the current file | Report the hash as recorded; disclose that the prereg text still carries a draft banner and unsigned sign-off. Do not claim a signed prereg. |
| X-22 | `prereg/PREREGISTRATION.md` §6 vs `docs/PROTOCOL.md` §8 | Prereg: "120 severity items (30/level, 3 blind raters)". Protocol: "160 outcome items plus 40 severity items (≈200 judgments)", then a separate "Severity audit: 120 observations, 30 per level, 3 raters" | The two documents imply different severity-audit item counts (120 vs 40 + 120) | Reconcile the severity-audit design before writing Methods; do not add 120 + 160 + 80 and call it "about 200". |
| X-23 (resolved) | `docs/DECISIONS.md` D-024 vs `configs/calibration.yaml:11` and `src/toolobs/infer/runner.py:24` | D-024 says the parser becomes `toolresult-parser-v2`; config and code say `toolresult-parser-v3` | D-025 now records v3 and the re-scoring procedure | Cite D-025 for v3; no open conflict. |
| X-24 | `paper/toolresult800.tex:5,379,397-398,873,1180` | "the 40-item human audit and the frozen manifest are pending"; "no study prefix has been run on a GPU"; "G1 has not run" | manifest `freeze`; D-023/D-024 G1 runs. The abstract at 307-311 is already correct ("manifest is frozen; audit provisionally filled; G1 in progress") | Make the header comment, intro, G1 section, and conclusion match the abstract. |
| X-25 | `paper/toolresult800.tex:639` | "parser versions are frozen at G0 and recorded in the manifest" | The manifest has no `parser_version` field (it records config hashes and the renderer version); D-024/D-025 change the parser after freeze; current code is v3 | Say the G0 parser snapshot was v1 (recoverable from the hashed config), the G1 parser changed under D-024/D-025, and name the final version (v3). |

---

## 6. Verification log (snapshot)

These checks were run on 2026-11-15 against the working tree. They verify provenance; they do not
create new claims.

| Check | Result |
|---|---|
| `toolresult800_v1.json` SHA-256 | `d6e034d7…5487a` — matches the sidecar; 5,285,713 bytes |
| `perturbations.jsonl` SHA-256 / lines | `4b47f9b5…8cf5` — matches `perturbations_hash`; 2,640 lines |
| `data/frozen/prefixes.jsonl` SHA-256 / lines | `6f6374cd…ca97` — matches `frozen_prefixes_hash`; 880 lines |
| `data/interim/sample.jsonl` SHA-256 / lines | `d86021f9…3764` — matches `sample_hash`; 880 lines |
| `configs/field_registry.yaml` SHA-256 | `3cbcfa06…4dab` — matches `field_registry_hash` |
| `prereg/PREREGISTRATION.md` SHA-256 | `e0d107c6…fc8a` — matches `prereg_hash` |
| `source_pin.json` canonical SHA-256 | `b74cfdc8…4d48` — matches `source_pin_hash`; raw bytes are `5942df70…19a0` |
| Manifest counts | 880 prefixes; 800 primary; 80 reserve; 60 calibration; 4,400 arms; 2,640 perturbations |

---

## 7. Pre-submission checklist

- [ ] Every number in the abstract, tables, figures, and appendix has a row here or a G2+ ledger
      row added after the run.
- [ ] Every `[PENDING: …]` is replaced or the sentence is removed.
- [ ] The pilot is labeled **screening only** and is not pooled.
- [ ] G1 is described as **harness evidence**; no model comparison is drawn from it.
- [ ] G0 is described as **frozen under a provisional AI-scored audit (D-021)**; no human
      sign-off is claimed.
- [ ] The model trio is **8–9B**, with the quantized display names and pinned revisions.
- [ ] The 6,554 planning figure is not reported as achieved supply; 5,516 is the operational
      eligible count.
- [ ] The G1/G2 serving configuration (1,024 tokens, constrained JSON, `think` excluded,
      Ministral eager/4-seq) is stated separately from the G0 manifest config hashes.
- [ ] The prereg hash is reported with the draft-banner caveat.
- [ ] No sentence ranks models, claims a universal law, or generalizes to frontier/live APIs.
- [ ] Release claims cite packaged manifests/ledgers, not local `artifacts/` paths alone.
