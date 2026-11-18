#!/usr/bin/env python
"""Stage 09d — seed-repeat jitter shard (80 prefixes x 5 arms x 3 models).

The base matrix is greedy and deterministic in principle. This shard repeats one
generation per cell on a fixed 10% sample of the primary prefixes with a different
sampling seed and compares the decision signature with the base row. It measures
how much of the reported switch rate could be run-to-run noise rather than content
sensitivity.

The preregistered threshold is signature stability >= 0.90 on the repeated cells.
Rows are written to data/runs/main/jitter/<model>/ledger.jsonl and the stability
report to artifacts/analysis/jitter_stability.json.
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
from toolobs.infer.runner import FakeBackend, run_rendered_rows  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, MANIFEST_DIR, RUNS_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402

SELECTION_SEED = 20261108
JITTER_SEED_OFFSET = 1


def select_jitter_prefixes(
    prefixes: dict[str, dict], per_domain: int = 40, seed: int = SELECTION_SEED
) -> set[str]:
    """Deterministically select primary prefixes for the seed-repeat shard."""
    selected: set[str] = set()
    for domain in ("airline", "retail"):
        pool = sorted(
            prefix_id
            for prefix_id, prefix in prefixes.items()
            if prefix.get("domain") == domain and prefix.get("split") == "primary"
        )
        random.Random(f"{seed}|jitter|{domain}").shuffle(pool)
        selected.update(pool[:per_domain])
    return selected


def stability_report(
    base_rows: dict[tuple[str, str], object], jitter_rows: list[object]
) -> dict[str, object]:
    """Compare repeated signatures with the base matrix, per model and arm."""
    by_arm: dict[str, dict[str, int]] = {}
    total = stable = unparsed = missing = 0
    for row in jitter_rows:
        if not row.parsed or not row.signature_hash:
            unparsed += 1
            continue
        base = base_rows.get((row.prefix_id, row.arm))
        if base is None or not getattr(base, "parsed", False) or not getattr(
            base, "signature_hash", ""
        ):
            missing += 1
            continue
        bucket = by_arm.setdefault(row.arm, {"n": 0, "stable": 0})
        bucket["n"] += 1
        total += 1
        if row.signature_hash == base.signature_hash:
            stable += 1
            bucket["stable"] += 1
    for bucket in by_arm.values():
        bucket["rate"] = round(bucket["stable"] / bucket["n"], 4) if bucket["n"] else None
    return {
        "n": total,
        "stable": stable,
        "rate": round(stable / total, 4) if total else None,
        "unparsed": unparsed,
        "missing_base": missing,
        "by_arm": by_arm,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--backend", choices=("fake", "vllm"), default="vllm")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--manifest", default=str(MANIFEST_DIR / "toolresult800_v1.json"))
    parser.add_argument("--prefixes", default="data/frozen/prefixes.jsonl")
    parser.add_argument("--rendered", default="data/interim/rendered.jsonl")
    parser.add_argument("--base-ledger", default=None)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="recompute the stability report from existing ledgers (no generation)",
    )
    parser.add_argument("--report", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    models_config = load_config("models.yaml")
    calibration = load_config("calibration.yaml")
    model = next(
        (item for item in models_config["models"] if item.get("id") == args.model_id), None
    )
    if model is None:
        raise SystemExit(f"unknown model id: {args.model_id}")

    prefixes = {
        str(row["prefix_id"]): row
        for row in read_jsonl_dicts(resolve_repo_path(args.prefixes))
    }
    selected = select_jitter_prefixes(prefixes)
    rendered = [
        row
        for row in read_jsonl_dicts(resolve_repo_path(args.rendered))
        if str(row["prefix_id"]) in selected
    ]
    if args.limit:
        keep = sorted(selected)[: args.limit]
        rendered = [row for row in rendered if str(row["prefix_id"]) in keep]

    base_ledger = resolve_repo_path(
        args.base_ledger or (RUNS_DIR / "main" / args.model_id / "ledger.jsonl")
    )
    base_rows = {
        (row.prefix_id, row.arm): row
        for row in read_ledger(base_ledger)
        if row.step == 0
    }
    manifest_hash = sha256_text_file(resolve_repo_path(args.manifest))
    ledger_path = resolve_repo_path(
        args.out or (RUNS_DIR / "main" / "jitter" / args.model_id / "ledger.jsonl")
    )
    if args.report_only:
        if not ledger_path.exists():
            raise SystemExit(f"jitter ledger missing: {ledger_path}")
        jitter_rows = read_ledger(ledger_path)
        report = stability_report(base_rows, jitter_rows)
        report.update(
            {
                "model_id": args.model_id,
                "stage": "09d_jitter",
                "mode": "report_only",
                "recorded_utc": utc_now(),
                "git_commit": git_commit(),
                "manifest_hash": manifest_hash,
                "jitter_seed": int(calibration["calibration"]["seed"]) + JITTER_SEED_OFFSET,
                "prefixes": len({row.prefix_id for row in jitter_rows}),
                "generations": len(jitter_rows),
                "gate_min": 0.90,
                "passed": report["rate"] is not None and report["rate"] >= 0.90,
                "ledger": str(ledger_path),
            }
        )
        report_path = resolve_repo_path(args.report) if args.report else (
            ARTIFACTS_DIR / "analysis" / f"jitter_stability_{args.model_id}.json"
        )
        write_json(report_path, report)
        print(f"[09d_jitter] report-only {args.model_id} {report['rate']} n={report['n']} -> {report_path}")
        return 0
    if ledger_path.exists():
        raise SystemExit(f"jitter ledger already exists: {ledger_path}")

    if args.backend == "fake":
        backend = FakeBackend('{"final_answer": "done"}')
    else:
        from toolobs.infer.vllm_backend import VLLMBackend  # noqa: PLC0415 - GPU host only

        backend = VLLMBackend(
            model,
            max_tokens=int(models_config["decoding"]["max_tokens"]),
            seed=int(calibration["calibration"]["seed"]) + JITTER_SEED_OFFSET,
            max_num_seqs=int(models_config["serving"]["max_num_seqs"]),
        )

    stats = run_rendered_rows(
        rendered,
        backend=backend,
        model_id=args.model_id,
        run_id=f"jitter-{args.model_id}",
        stage="jitter",
        manifest_hash=manifest_hash,
        ledger_path=ledger_path,
        upstream_dir=resolve_repo_path("data/upstream/tau-bench"),
        prompt_version=str(calibration["calibration"]["prompt_version"]),
        parser_version=str(calibration["calibration"]["parser_version"]),
        batch_size=int(models_config["serving"]["batch_size"]),
        excluded_tools=models_config["serving"].get("excluded_tools", []),
    )
    report = stability_report(base_rows, read_ledger(ledger_path))
    report.update(
        {
            "model_id": args.model_id,
            "stage": "09d_jitter",
            "recorded_utc": utc_now(),
            "git_commit": git_commit(),
            "manifest_hash": manifest_hash,
            "jitter_seed": int(calibration["calibration"]["seed"]) + JITTER_SEED_OFFSET,
            "prefixes": len(selected),
            "generations": stats.total,
            "gate_min": 0.90,
            "passed": report["rate"] is not None and report["rate"] >= 0.90,
            "ledger": str(ledger_path),
        }
    )
    report_path = resolve_repo_path(args.report) if args.report else (
        ARTIFACTS_DIR / "analysis" / f"jitter_stability_{args.model_id}.json"
    )
    write_json(report_path, report)
    print(f"[09d_jitter] {args.model_id} {report['rate']} n={report['n']} -> {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
