#!/usr/bin/env python
"""Stage 09b — H=4 recovery continuation for one model.

Input:  data/frozen/prefixes.jsonl, data/interim/rendered.jsonl,
        data/manifests/perturbations.jsonl, data/runs/main/<model>/ledger.jsonl
Output: data/runs/main/<model>/recovery_<regime>.jsonl
        data/runs/main/recovery/<model>/<regime>.jsonl

The runner continues only prefixes whose injected arm moved the decision and did not
flag at injection. It executes the model's tool calls against the real τ-bench task
database and records one ledger row per recovery step.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl_dicts  # noqa: E402
from toolobs.hashing import sha256_text_file  # noqa: E402
from toolobs.infer.ledger import read_ledger  # noqa: E402
from toolobs.infer.recovery_run import run_recovery  # noqa: E402
from toolobs.paths import MANIFEST_DIR, RUNS_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402
from toolobs.schemas import PerturbationRecord  # noqa: E402

PERSISTENT_SEED = 20261108


def select_persistent(prefixes: dict[str, dict], per_domain: int = 100) -> set[str]:
    """Deterministically select 100 primary prefixes per domain for persistent injection."""
    selected: set[str] = set()
    for domain in ("airline", "retail"):
        pool = sorted(
            prefix_id
            for prefix_id, prefix in prefixes.items()
            if prefix.get("domain") == domain and prefix.get("split") == "primary"
        )
        random.Random(f"{PERSISTENT_SEED}|persistent|{domain}").shuffle(pool)
        selected.update(pool[:per_domain])
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--regime", choices=("transient", "persistent", "both"), default="both")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--manifest", default=str(MANIFEST_DIR / "toolresult800_v1.json"))
    parser.add_argument("--prefixes", default="data/frozen/prefixes.jsonl")
    parser.add_argument("--rendered", default="data/interim/rendered.jsonl")
    parser.add_argument(
        "--perturbations", default=str(MANIFEST_DIR / "perturbations.jsonl")
    )
    parser.add_argument("--upstream", default="data/upstream/tau-bench")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    models = load_config("models.yaml")["models"]
    model = next((item for item in models if item.get("id") == args.model_id), None)
    if model is None:
        raise SystemExit(f"unknown model id: {args.model_id}")

    prefixes = {
        str(row["prefix_id"]): row
        for row in read_jsonl_dicts(resolve_repo_path(args.prefixes))
    }
    rendered = {
        (str(row["prefix_id"]), str(row["arm"])): row
        for row in read_jsonl_dicts(resolve_repo_path(args.rendered))
    }
    perturbations = {
        (str(row["prefix_id"]), str(row["arm"])): PerturbationRecord.from_dict(row)
        for row in read_jsonl_dicts(resolve_repo_path(args.perturbations))
    }
    base_ledger = RUNS_DIR / "main" / args.model_id / "ledger.jsonl"
    base_rows = {
        (row.prefix_id, row.arm): row
        for row in read_ledger(base_ledger)
        if row.step == 0
    }
    manifest_hash = sha256_text_file(resolve_repo_path(args.manifest))
    persistent_ids = select_persistent(prefixes)

    from toolobs.infer.vllm_backend import VLLMBackend  # noqa: PLC0415 - GPU host only

    backend = VLLMBackend(
        model,
        max_tokens=int(load_config("models.yaml")["decoding"]["max_tokens"]),
        seed=int(load_config("calibration.yaml")["calibration"]["seed"]),
        max_num_seqs=int(load_config("models.yaml")["serving"]["max_num_seqs"]),
    )

    regimes = ("transient", "persistent") if args.regime == "both" else (args.regime,)
    reports = {}
    for regime in regimes:
        selected_prefixes = (
            prefixes
            if regime == "transient"
            else {key: prefixes[key] for key in persistent_ids}
        )
        out_dir = RUNS_DIR / "main" / args.model_id
        ledger_path = resolve_repo_path(
            args.out or (out_dir / f"recovery_{regime}.jsonl")
        )
        event_path = RUNS_DIR / "main" / "recovery" / args.model_id / f"{regime}.jsonl"
        if ledger_path.exists() or event_path.exists():
            raise SystemExit(f"recovery outputs already exist for {regime}: {ledger_path}")
        stats = run_recovery(
            prefixes=selected_prefixes,
            rendered=rendered,
            base_rows=base_rows,
            perturbations=perturbations,
            backend=backend,
            model_id=args.model_id,
            regime=regime,
            upstream_dir=resolve_repo_path(args.upstream),
            ledger_path=ledger_path,
            event_path=event_path,
            manifest_hash=manifest_hash,
            max_sequences=args.limit or None,
        )
        reports[regime] = stats.as_dict()
        print(f"[09b_recovery] {regime} {stats.as_dict()}")

    report_path = RUNS_DIR / "main" / args.model_id / "recovery_report.json"
    write_json(
        report_path,
        {
            "stage": "09b_recovery",
            "recorded_utc": utc_now(),
            "git_commit": git_commit(),
            "model_id": args.model_id,
            "manifest_hash": manifest_hash,
            "persistent_prefixes": len(persistent_ids),
            "reports": reports,
        },
    )
    print(f"[09b_recovery] wrote {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
