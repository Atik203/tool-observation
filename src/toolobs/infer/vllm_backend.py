"""Lazy vLLM backend for the H200 run.

Importing this module is safe without vLLM installed. The engine is created only
when a GPU run is explicitly authorized.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from .runner import Generation


class VLLMBackend:
    """Batch chat-generation backend using vLLM."""

    def __init__(
        self,
        model_config: dict[str, Any],
        *,
        max_tokens: int = 256,
        seed: int = 20261108,
    ) -> None:
        try:
            from vllm import LLM, SamplingParams  # noqa: PLC0415 - lazy GPU import
        except ImportError as exc:  # pragma: no cover - GPU host only
            raise RuntimeError("vLLM is not installed; install the GPU stack first") from exc

        revision = str(model_config.get("revision", "TBD"))
        if revision == "TBD":
            raise RuntimeError("model revision is TBD; pin it in configs/models.yaml")
        quantization = str(model_config.get("quantization", "auto"))
        if quantization == "awq_4bit":
            quantization = "awq"
        elif quantization in {"compressed_tensors", "compressed_tensors_4bit"}:
            quantization = "compressed-tensors"
        self.model_id = str(model_config["id"])
        kwargs: dict[str, Any] = {
            "model": str(model_config["repo_id"]),
            "revision": revision,
            "dtype": str(model_config.get("dtype", "float16")),
            "max_model_len": int(model_config.get("max_model_len", 8192)),
            "gpu_memory_utilization": float(model_config.get("gpu_memory_utilization", 0.85)),
            "enforce_eager": bool(model_config.get("enforce_eager", False)),
            "tensor_parallel_size": int(model_config.get("tensor_parallel", 1)),
        }
        if quantization not in {"", "auto", "none"}:
            kwargs["quantization"] = quantization
        self.llm = LLM(**kwargs)
        self.tokenizer = self.llm.get_tokenizer()
        self.sampling = SamplingParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=max_tokens,
            stop=["\n\n"],
            seed=seed,
        )

    def generate(self, prompts: list[list[dict[str, Any]]], **kwargs: Any) -> list[Generation]:
        texts = [
            self.tokenizer.apply_chat_template(
                prompt,
                tokenize=False,
                add_generation_prompt=True,
            )
            for prompt in prompts
        ]
        started = perf_counter()
        outputs = self.llm.generate(texts, self.sampling)
        elapsed_ms = (perf_counter() - started) * 1000.0
        per_prompt = elapsed_ms / max(1, len(outputs))
        generations: list[Generation] = []
        for output in outputs:
            completion = output.outputs[0]
            generations.append(
                Generation(
                    text=completion.text,
                    latency_ms=per_prompt,
                    prompt_tokens=len(getattr(output, "prompt_token_ids", []) or []),
                    completion_tokens=len(getattr(completion, "token_ids", []) or []),
                )
            )
        return generations
