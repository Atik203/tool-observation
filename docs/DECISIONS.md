# Decision log

Architectural and research decisions for `tool-observation`. Add new entries at the top. Any
decision that touches the preregistration, frozen data, or analysis plan also requires an entry
in `prereg/AMENDMENTS.md` before the affected analysis runs.

---

## D-018 — Historical tool calls are rendered as canonical text; prompt v2

- **Date:** 2026-11-15
- **Status:** accepted (pre-freeze; no study generation has run)
- **Context:** The τ-bench prefixes carry OpenAI-style assistant `tool_calls` with JSON-string
  arguments and sometimes `content: null`. Rendering the real prefixes exposed three failures:
  Qwen3.5's template requires `arguments` to be a mapping, Llama's template calls `len()` on a
  null content, and Ministral's backend silently drops `tool_calls`. A family-specific template
  fix would give each model a different view of the same history.
- **Decision:** `build_prompt_messages` normalizes every message before templating: null content
  becomes `""`, and each historical tool call becomes a deterministic
  `<tool_call>{"name": ..., "arguments": ...}</tool_call>` text block with arguments parsed from
  JSON strings. The `tool_calls` field is removed so no template-specific tool grammar is used.
  The prompt version becomes **`toolresult-next-decision-v2`**; the parser is unchanged. The
  frozen prefix payload and the arm manipulation are untouched.
- **Consequences:** All three families see the same textual history, and the prompt renders on
  every pinned tokenizer. The system instruction, tool schemas, decoding, and 256-token budget
  are unchanged. Because no study generation exists, this is a pre-freeze implementation change,
  not a prereg amendment; the fixed-version requirement is satisfied by v2.

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
- **Fit status (2026-11-15):** All three pass at 8k context, batch 4,
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
