#!/usr/bin/env python
"""Non-study H200 fit check for one pinned AWQ model.

This script does not read a study prefix and does not write a generation ledger.
It verifies that the model, 24k context, and a small batch fit in 18 GB and
records the environment evidence under `artifacts/env/`.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import load_config  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR  # noqa: E402
from toolobs.provenance import utc_now, write_json  # noqa: E402


def _gpu_memory() -> str:
    try:
        return subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=10,
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-id", default="qwen3_5_9b_instruct_awq")
    parser.add_argument("--max-model-len", type=int, default=24576)
    parser.add_argument("--gpu-memory-utilization", type=float, default=0.90)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-num-seqs", type=int, default=8)
    parser.add_argument("--max-tokens", type=int, default=8)
    parser.add_argument(
        "--prompt-tokens",
        type=int,
        default=0,
        help="If >0, use a synthetic prompt of about this many tokens instead of 'ready'.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", default=str(ARTIFACTS_DIR / "env" / "qwen_fit_check.json"))
    args = parser.parse_args(argv)

    models = load_config("models.yaml").get("models", [])
    config = next((model for model in models if model.get("id") == args.model_id), None)
    if config is None:
        print(f"[11_fit_check] FAIL: unknown model {args.model_id}")
        return 1
    if str(config.get("revision", "TBD")) == "TBD":
        print("[11_fit_check] FAIL: model revision is TBD")
        return 1

    try:
        import torch  # noqa: PLC0415 - GPU host only
        from vllm import LLM, SamplingParams  # noqa: PLC0415 - GPU host only
    except ImportError as exc:
        print(f"[11_fit_check] FAIL: GPU stack import failed: {exc}")
        return 1

    if args.dry_run:
        print(f"[11_fit_check] imports OK; model {config['repo_id']}@{config['revision']}")
        return 0

    record = {
        "stage": "11_fit_check",
        "recorded_utc": utc_now(),
        "model_id": args.model_id,
        "repo_id": config["repo_id"],
        "revision": config["revision"],
        "max_model_len": args.max_model_len,
        "gpu_memory_utilization": args.gpu_memory_utilization,
        "batch_size": args.batch_size,
        "max_num_seqs": args.max_num_seqs,
        "gpu_before": _gpu_memory(),
    }
    started = time.perf_counter()
    try:
        quantization = str(config.get("quantization", "auto"))
        if quantization == "awq_4bit":
            quantization = "awq"
        elif quantization in {"compressed_tensors", "compressed_tensors_4bit"}:
            quantization = "compressed-tensors"
        llm_kwargs = {
            "model": str(config["repo_id"]),
            "revision": str(config["revision"]),
            "dtype": str(config.get("dtype", "float16")),
            "max_model_len": args.max_model_len,
            "gpu_memory_utilization": args.gpu_memory_utilization,
            "enforce_eager": bool(config.get("enforce_eager", True)),
            "tensor_parallel_size": 1,
            "max_num_seqs": args.max_num_seqs,
        }
        if quantization not in {"", "auto", "none"}:
            llm_kwargs["quantization"] = quantization
        llm = LLM(**llm_kwargs)
        load_seconds = time.perf_counter() - started
        tokenizer = llm.get_tokenizer()
        template_kwargs = dict(config.get("chat_template_kwargs") or {})
        if args.prompt_tokens > 0:
            filler = "The quick brown fox jumps over the lazy dog. "
            content = filler * (args.prompt_tokens // 8 + 1)
        else:
            content = "Reply with the single word: ready."
        messages = [
            {"role": "user", "content": content}
            for _ in range(args.batch_size)
        ]
        prompts = [
            tokenizer.apply_chat_template(
                [message],
                tokenize=False,
                add_generation_prompt=True,
                **template_kwargs,
            )
            for message in messages
        ]
        prompt_token_counts = [
            len(tokenizer(prompt, add_special_tokens=False)["input_ids"])
            for prompt in prompts
        ]
        record["prompt_tokens"] = prompt_token_counts
        sampling = SamplingParams(temperature=0.0, top_p=1.0, max_tokens=args.max_tokens)
        generation_started = time.perf_counter()
        outputs = llm.generate(prompts, sampling)
        generation_seconds = time.perf_counter() - generation_started
        record.update(
            {
                "status": "ok",
                "load_seconds": load_seconds,
                "generation_seconds": generation_seconds,
                "outputs": [output.outputs[0].text for output in outputs],
                "gpu_after": _gpu_memory(),
                "peak_torch_allocated_gb": torch.cuda.max_memory_allocated() / 1e9,
                "peak_torch_reserved_gb": torch.cuda.max_memory_reserved() / 1e9,
                "torch": torch.__version__,
            }
        )
        import vllm  # noqa: PLC0415

        record["vllm"] = vllm.__version__
    except Exception as exc:  # noqa: BLE001 - OOM and load failures are the result
        record.update(
            {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "gpu_after": _gpu_memory(),
            }
        )
        write_json(Path(args.out), record)
        print(f"[11_fit_check] FAIL: {record['error']}")
        print(f"[11_fit_check] wrote {args.out}")
        return 1

    write_json(Path(args.out), record)
    print(f"[11_fit_check] status {record['status']}")
    print(f"[11_fit_check] load_seconds {record['load_seconds']:.1f}")
    print(f"[11_fit_check] peak_torch_reserved_gb {record['peak_torch_reserved_gb']:.2f}")
    print(f"[11_fit_check] wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
