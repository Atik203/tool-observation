# H200 environment record

**Status:** environment check only; no study prefix has been run.

| Item | Value |
|---|---|
| GPU | H200 1g.18gb (18 GB VRAM) |
| Driver | 580.178.04 |
| CUDA | 13.5 |
| Python | 3.12.3, project-local `.venv` |
| vLLM | 0.33.0 |
| torch | 2.14.0+cu130 |
| Transformers | 5.20.2 |
| Storage | project + caches ≈16 GB; hard cap 200 GB |

## Fit check

`scripts/11_fit_check.py` loaded the pinned Qwen AWQ model with a generic non-study prompt:

| Metric | Value |
|---|---|
| Model | `Qwen/Qwen2.5-7B-Instruct-AWQ` |
| Revision | `b25037543e9394b818fdfca67ab2a00ecc7dd641` |
| Context | 8,192 tokens |
| Batch | 4 prompts |
| `gpu_memory_utilization` | 0.85 |
| Weights | 5.38 GiB |
| KV cache | 7.76 GiB (145,376 tokens; 17.75× concurrency at 8k) |
| Load time | 27.7 s |
| Batch generation | 0.08 s |
| Outputs | four `ready` responses |

The 0.90 setting requested 16.02 GiB but only 15.36 GiB was free, so 0.85 is the logged
reduction. The slice is 18 GB nominal; another process or allocator overhead can reduce free
memory at startup, so `0.85` is the operating point.

## Updated-trio fit results (2026-11-15)

All three pinned models load and generate at 8,192- and 24,576-token context, batch 4,
`gpu_memory_utilization=0.85`, and `max_num_seqs=8` on the 18 GB slice.

| Model | Weights | KV cache | Concurrency at 8k | Load | Batch gen | Outputs |
|---|---|---|---|---|---|---|
| Qwen3.5-9B-AWQ | 8.37 GiB | 4.63 GiB (89,770 tokens) | 10.96× | 59.6 s | 0.16 s | four `ready` |
| Ministral-3-8B-2512-AWQ | 7.03 GiB | 7.15 GiB (55,104 tokens) | 6.73× | 359.7 s (incl. download) | 0.08 s | four `ready` |
| Llama-3.1-8B-Instruct-AWQ-INT4 | 5.58 GiB | 8.38 GiB (68,640 tokens) | 8.38× | 210.6 s (incl. download) | 0.11 s | four `Ready.` |

The configured context is **24,576 tokens**. The prompt-length audit
(`artifacts/env/prompt_lengths.json`) found a maximum prompt of 20,682 tokens plus the
256-token decision; an 8k context would have rejected 107–237 of the 880 frozen prefixes. The
24k fit reruns all passed:

| Model | 24k load | Outputs |
|---|---|---|
| Qwen3.5-9B-AWQ | 94.7 s | four `ready` |
| Ministral-3-8B-2512-AWQ | 51.7 s | four `ready` |
| Llama-3.1-8B-Instruct-AWQ-INT4 | 41.0 s | four `Ready.` |

### Long-prompt fit

Two synthetic ~20k-token prompts per model, batch 2, 16 output tokens:

| Model | Prompt tokens | Generation | Status |
|---|---|---:|---|
| Qwen3.5-9B-AWQ | 20,002 | 4.30 s | ok |
| Ministral-3-8B-2512-AWQ | 20,001 | 5.17 s | ok |
| Llama-3.1-8B-Instruct-AWQ-INT4 | 20,025 | 5.46 s | ok |

The synthetic text is a repeated pangram, so the outputs are not study outputs. Ministral emitted
empty strings on this repetitive prompt; that is model behavior to watch in G1, not a load
failure. The test confirms that a 20k prompt fits and runs at the configured 24k context.

### Backend smoke (non-study)

A synthetic airline tool-call history (system policy, user request, one historical call, one tool
result) was sent through `VLLMBackend` on all three models with prompt v3. Each produced parsed
JSON: Qwen3.5 a `final_answer`, Ministral a `get_user_details` call, and Llama a
`list_all_airports` call. Under prompt v2, Ministral returned an empty completion when the last
turn was a bare tool result; v3 adds a final instruction turn and renders the call history as
plain text (D-020). Evidence: `artifacts/env/v3_smoke.log` and
`artifacts/env/backend_v3_smoke.log`.

Notes:

- Qwen3.5-9B is a Mamba-hybrid model. The default `max_num_seqs=256` exceeds its Mamba cache
  blocks (214), so the runner pins `max_num_seqs=8`. The first fit attempt failed at engine
  init with that error; the capped rerun passed.
- Qwen3.5-9B is also a reasoning model. With the stock template it emitted
  `Thinking Process:\n1. **`, which would spend the 256-token decision budget on reasoning.
  `configs/models.yaml` sets `chat_template_kwargs: {enable_thinking: false}`; the rerun emitted
  `ready`. The backend passes these kwargs to `apply_chat_template` for every model.
- Ministral has the tightest KV headroom (6.73× at 8k, about 2.2× at 24k), so a batch of 8
  full-length 24k prefixes would queue rather than run concurrently. Actual prompts have a
  median of 6.7k tokens; the runner keeps `max_num_seqs=8` and lets vLLM schedule with chunked
  prefill.
- `peak_torch_allocated_gb` reads 0.00 because vLLM v1 runs the engine in a subprocess; the
  in-process CUDA allocator counter is not meaningful. Per-model `gpu_after` and vLLM's own
  KV-cache report are the evidence.
- The Qwen2.5-7B check above is historical environment evidence; it is not the confirmatory
  Qwen model after D-016.

## Project-local Python headers

vLLM/Triton compiles a small CUDA helper at first use and needs Python headers. The system
interpreter does not include `Python.h`. The project extracted `python3.12-dev` and
`libpython3.12-dev` into `.deps/pyheaders/` and exposes a combined include tree through a
project-local `sitecustomize.py` (`PYTHONPATH=.deps/pyheaders`). No system package, driver, CUDA,
or shared library was changed.

## Scope

This record is environment evidence, not a study result. Calibration and the main run remain
blocked until the G0 human audit and freeze pass.
