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

## Updated-trio fit status (paused 2026-11-15)

- **Qwen3.5-9B-AWQ:** weights load (8.37 GiB) and the 8k KV cache fits (73,045 tokens), but the
  default `max_num_seqs=256` exceeds the Mamba cache blocks (214). The fit check is capped at
  `max_num_seqs=8` and must be rerun. No generation was produced.
- **Ministral-3-8B-Instruct-2512-AWQ:** fit check pending.
- **Llama-3.1-8B-Instruct-AWQ-INT4:** fit check pending.

The Qwen2.5-7B check above is historical environment evidence; it is not the confirmatory Qwen
model after D-016.

## Project-local Python headers

vLLM/Triton compiles a small CUDA helper at first use and needs Python headers. The system
interpreter does not include `Python.h`. The project extracted `python3.12-dev` and
`libpython3.12-dev` into `.deps/pyheaders/` and exposes a combined include tree through a
project-local `sitecustomize.py` (`PYTHONPATH=.deps/pyheaders`). No system package, driver, CUDA,
or shared library was changed.

## Scope

This record is environment evidence, not a study result. Calibration and the main run remain
blocked until the G0 human audit and freeze pass. Model revisions for Mistral and Llama remain
TBD.
