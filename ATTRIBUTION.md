# Attribution and third-party notices — ToolResult-800

ToolResult-800 is a derived dataset built on the public τ-bench benchmark. **Changes were made**
to the upstream material: prefixes were selected and frozen, observations were scrubbed, prose
renderings and perturbations were generated, labels and recovery traces were produced, and target
models were run on the frozen prefixes. ToolResult-800 is not a copy of τ-bench and is not a
re-license of it. The upstream notices and license terms are preserved below.

## ToolResult-800 (this dataset)

- **Dataset:** ToolResult-800 (repository `tool-observation`)
- **Authors:** Md. Atikur Rahaman (ORCID 0009-0008-2945-4117) and Ohidujjaman Tuhin
  (ORCID 0000-0002-8776-7145)
- **Project additions:** CC BY 4.0 (see `DATA_LICENSE.md` and `LICENSE-DOCS`)
- **Citation:** see `CITATION.cff`; cite the accompanying paper and the upstream τ-bench paper and
  repository for any use.
- **Version:** 1.0.1 (2026-11-23). The distributed release is redacted; the frozen source under
  `data/frozen/` is not distributed and remains bit-identical under the manifest hash (D-046).

## τ-bench (upstream data and code)

- **Source:** <https://github.com/sierra-research/tau-bench>
- **Pinned commit:** `59a200c6d575d595120f1cb70fea53cef0632f6b` (see
  `data/manifests/source_pin.json`)
- **License:** MIT
- **Copyright:** Copyright (c) 2024 Sierra
- **Full text:** bundled in each release package at `licenses/TAU_BENCH_LICENSE_MIT`; reproduced
  here:

```text
MIT License

Copyright (c) 2024 Sierra

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Changes made to τ-bench material:** prefix extraction at the first post-tool
message, exclusion of profile-tool observations, PII scrubbing, deterministic
prose rendering, perturbation construction, and the derived labels and analysis.
The task databases and historical trajectories themselves are not redistributed;
users obtain them from upstream under the MIT license.

## Target-model families (derived text only)

The release contains short derived decision strings produced by running the models below on
scrubbed frozen prefixes. **No model weights, adapters, caches, tokenizer files, or GPU
artifacts are distributed.** The strings are user-produced derived text, not a redistribution of
the models. License tags were verified 2026-11-22 against the HuggingFace API for the exact
pinned revisions in `configs/models.yaml`.

| Family | Served build (pinned revision) | License |
|---|---|---|
| Qwen3.5-9B | `cyankiwi/Qwen3.5-9B-AWQ-4bit` (`e4d2d39cede8c5d1716d824cd843e2889c648083`); base `Qwen/Qwen3.5-9B` | **Apache-2.0** |
| Ministral-3-8B-Instruct-2512 | `cyankiwi/Ministral-3-8B-Instruct-2512-AWQ-4bit` (`563842192acb68a00b8864e3bfa5a3e740ece90c`); base `mistralai/Ministral-3-8B-Instruct-2512` | **Apache-2.0** |
| Llama-3.1-8B-Instruct | `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4` (`db1f81ad4b8c7e39777509fac66c652eb0a52f91`); base `meta-llama/Llama-3.1-8B-Instruct` | **Llama 3.1 Community License** |

- The two Apache-2.0 families: outputs carry no redistribution restriction; the Apache-2.0
  notices apply to the model material, which is not included here.
- **Llama 3.1:** the Llama 3.1 Community License governs use of the Llama model and its
  acceptable-use policy. The released decision strings are derived text containing **no model
  weights**; the model itself is not redistributed. The Llama 3.1 Community License is not
  re-licensed by this project. See
  <https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct> for the license text.

Model-output licensing details and the venue confirmation item are recorded in
`docs/submission/license_verification.md`. If a venue requires different terms, that is resolved
at submission (P6.8); the dataset license above is unchanged.

## Redistribution

If you redistribute ToolResult-800 or a derived work, include `ATTRIBUTION.md`,
`DATA_LICENSE.md`, `LICENSE-DOCS`, the MIT `LICENSE`, and the upstream τ-bench notice; preserve
this attribution and the "changes were made" statement; do not imply endorsement by the
ToolResult-800 authors, Sierra, or the model providers; and do not add restrictions that prevent
others from exercising the CC BY 4.0 rights in the project additions.
