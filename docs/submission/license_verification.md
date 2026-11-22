# License verification - ToolResult-800 v1.0.2 (2026-11-23; v1.0.0 → v1.0.1 redaction errata → v1.0.2 path-leak errata)

## Upstream τ-bench (data source)

- Repository: https://github.com/sierra-research/tau-bench, pinned commit
  `59a200c6d575d595120f1cb70fea53cef0632f6b` (`data/manifests/source_pin.json`).
- License: **MIT**, "Copyright (c) 2024 Sierra" — full text fetched verbatim from the
  upstream repository on 2026-11-22 and bundled at
  `release/ToolResult-800-v1.0.2/licenses/TAU_BENCH_LICENSE_MIT`.
- Citation: the τ-bench paper/repository must be cited by any use (see `DATA_LICENSE.md`).

## Target-model outputs (released as scrubbed derived text only)

Verified 2026-11-22 against the HuggingFace API for the exact pinned revisions in
`configs/models.yaml` (API SHAs match the served revisions):

| Served model | Quant repo | License tag | Revision verified |
|---|---|---|---|
| Qwen3.5-9B-AWQ-4bit | cyankiwi/Qwen3.5-9B-AWQ-4bit | apache-2.0 | e4d2d39cede8c5d1716d824cd843e2889c648083 ✓ |
| Ministral-3-8B-Instruct-2512-AWQ-4bit | cyankiwi/Ministral-3-8B-Instruct-2512-AWQ-4bit | apache-2.0 | 563842192acb68a00b8864e3bfa5a3e740ece90c ✓ |
| Llama-3.1-8B-Instruct-AWQ-INT4 | hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4 | llama3.1 | db1f81ad4b8c7e39777509fac66c652eb0a52f91 ✓ |

Base weights: Qwen/Qwen3.5-9B, mistralai/Ministral-3-8B-Instruct-2512,
meta-llama/Llama-3.1-8B-Instruct (Llama 3 herd report cited in the paper).

What is released: only short derived decision strings (tool calls with scrubbed synthetic
arguments, or final-answer action verbs) produced on scrubbed frozen prefixes. **No model
weights, adapters, caches, or GPU artifacts are released.**

Redistribution basis: Apache-2.0 outputs carry no redistribution restriction; the Llama 3.1
Community License governs model use and its acceptable-use policy, and the released decision
strings are user-owned derived text containing no model weights. Venue confirmation is an
author step at submission if the target venue requires more.

## Bundle contents check

- [x] MIT `LICENSE` (code), `LICENSE-DOCS` (CC BY 4.0 docs/data), `DATA_LICENSE.md` staged.
- [x] Consolidated `ATTRIBUTION.md` staged (authors, upstream MIT + Sierra copyright,
      three model families and licenses, changes-made statement).
- [x] Upstream MIT notice + attribution staged (`licenses/TAU_BENCH_LICENSE_MIT`).
- [x] Model-output license record staged (`licenses/MODEL_OUTPUT_LICENSES.md`).
- [x] No weights/caches in the package (builder allowlists payload files; `*.safetensors`,
      `*.bin`, `*.pt`, model dirs are gitignored and never staged).
