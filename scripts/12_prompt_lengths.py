#!/usr/bin/env python
"""Stage 12 — non-study prompt-length audit for the rendered V arms.

Checks that the frozen prefix, the next-decision instruction, and the domain tool
schemas fit the pinned 8k context with room for the 256-token decision. This is
environment evidence, not a study run: it loads tokenizers only and generates
nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl_dicts  # noqa: E402
from toolobs.infer.prompt import build_prompt_messages  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, INTERIM_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import utc_now, write_json  # noqa: E402
from toolobs.taubench.replay import load_domain_tools  # noqa: E402


def _quantiles(values: list[int]) -> dict[str, int]:
    ordered = sorted(values)
    if not ordered:
        return {}
    result: dict[str, int] = {}
    for label, fraction in (
        ("min", 0.0),
        ("p50", 0.50),
        ("p90", 0.90),
        ("p95", 0.95),
        ("p99", 0.99),
        ("max", 1.0),
    ):
        index = min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1))))
        result[label] = ordered[index]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rendered", default=str(INTERIM_DIR / "rendered.jsonl"))
    parser.add_argument("--upstream", default="data/upstream/tau-bench")
    parser.add_argument("--context", type=int, default=8192)
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--out", default=str(ARTIFACTS_DIR / "env" / "prompt_lengths.json"))
    args = parser.parse_args(argv)

    try:
        from transformers import AutoTokenizer  # noqa: PLC0415 - tokenizer host only
    except ImportError as exc:
        print(f"[12_prompt_lengths] FAIL: transformers import failed: {exc}")
        return 1

    rows = [row for row in read_jsonl_dicts(resolve_repo_path(args.rendered)) if row["arm"] == "V"]
    upstream = resolve_repo_path(args.upstream)
    tools_cache: dict[str, list[dict]] = {}
    prompt_cache: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        domain = str(row["domain"])
        if domain not in tools_cache:
            tools_cache[domain] = load_domain_tools(upstream, domain)
        messages = json.loads(row["messages_json"])
        prompt_cache[(str(row["prefix_id"]), domain)] = build_prompt_messages(
            messages, tools_cache[domain]
        )

    budget = args.context - args.max_tokens
    models = load_config("models.yaml").get("models", [])
    records: dict[str, dict] = {}
    for model in models:
        model_id = str(model["id"])
        tokenizer = AutoTokenizer.from_pretrained(
            str(model["repo_id"]), revision=str(model["revision"])
        )
        template_kwargs = dict(model.get("chat_template_kwargs") or {})
        lengths: list[int] = []
        over_context = 0
        over_budget = 0
        for (_prefix_id, _domain), prompt in prompt_cache.items():
            text = tokenizer.apply_chat_template(
                prompt,
                tokenize=False,
                add_generation_prompt=True,
                **template_kwargs,
            )
            length = len(tokenizer(text, add_special_tokens=False)["input_ids"])
            lengths.append(length)
            over_context += int(length + args.max_tokens > args.context)
            over_budget += int(length > budget)
        records[model_id] = {
            "repo_id": model["repo_id"],
            "revision": model["revision"],
            "prefixes": len(lengths),
            "tokens": _quantiles(lengths),
            "over_context_including_decision": over_context,
            "over_prompt_budget": over_budget,
        }
        print(
            f"[12_prompt_lengths] {model_id} p50={records[model_id]['tokens'].get('p50')} "
            f"p99={records[model_id]['tokens'].get('p99')} "
            f"max={records[model_id]['tokens'].get('max')} "
            f"over={over_context}"
        )

    write_json(
        Path(args.out),
        {
            "stage": "12_prompt_lengths",
            "recorded_utc": utc_now(),
            "rendered": str(resolve_repo_path(args.rendered)),
            "arms": "V",
            "context": args.context,
            "max_tokens": args.max_tokens,
            "models": records,
        },
    )
    print(f"[12_prompt_lengths] wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
