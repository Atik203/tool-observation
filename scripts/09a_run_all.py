#!/usr/bin/env python
"""Stage 09a — run each model in its own process.

vLLM keeps the engine core alive for the life of the process; loading a second
model in the same process can fail with `CUBLAS_STATUS_ALLOC_FAILED` even after
the first model is deleted. This orchestrator launches one `09_run.py` process
per configured model, so GPU memory is released between families, then combines
the calibration ledgers into the G1 report.
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
from toolobs.harvest.parse import read_jsonl_dicts  # noqa: E402
from toolobs.hashing import sha256_text_file  # noqa: E402
from toolobs.infer.calibration import evaluate_all_models  # noqa: E402
from toolobs.infer.ledger import read_ledger  # noqa: E402
from toolobs.paths import (  # noqa: E402
    ARTIFACTS_DIR,
    INTERIM_DIR,
    MANIFEST_DIR,
    RUNS_DIR,
    resolve_repo_path,
)
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402


def _manifest_hash(stage: str, path: str | None) -> str:
    if path:
        candidate = resolve_repo_path(path)
        if candidate.is_file():
            return sha256_text_file(candidate)
    if stage == "main":
        raise SystemExit("main run requires the frozen manifest")
    return "calibration-unfrozen"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stage", choices=("calibration", "main"), default="calibration")
    parser.add_argument("--backend", choices=("fake", "vllm"), default="vllm")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--manifest", default=str(MANIFEST_DIR / "toolresult800_v1.json"))
    parser.add_argument("--rendered", default=None)
    parser.add_argument(
        "--ledger-root",
        default=None,
        help="Root containing <stage>/<model>/ledger.jsonl; defaults to data/runs.",
    )
    parser.add_argument(
        "--score-only",
        action="store_true",
        help="Skip generation and score the existing ledgers under --ledger-root.",
    )
    parser.add_argument(
        "--report", default=str(ARTIFACTS_DIR / "audit" / "g1_calibration.json")
    )
    args = parser.parse_args(argv)

    models = load_config("models.yaml").get("models", [])
    if not models:
        raise SystemExit("no models configured")
    model_ids = [str(model["id"]) for model in models]
    started = time.perf_counter()
    temp_report = ARTIFACTS_DIR / "audit" / "_per_model_calibration.json"
    ledger_root = (
        resolve_repo_path(args.ledger_root) if args.ledger_root else RUNS_DIR
    )
    if not args.score_only:
        rendered_path = resolve_repo_path(
            args.rendered
            or (
                INTERIM_DIR
                / (
                    "calibration_rendered.jsonl"
                    if args.stage == "calibration"
                    else "rendered.jsonl"
                )
            )
        )
        expected_rows = args.limit or len(read_jsonl_dicts(rendered_path))

    for model_id in (model_ids if not args.score_only else []):
        ledger_path = ledger_root / args.stage / model_id / "ledger.jsonl"
        if ledger_path.exists() and len(read_ledger(ledger_path)) >= expected_rows:
            print(f"[09a_run_all] {model_id}: ledger complete, skipping", flush=True)
            continue
        command = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "09_run.py"),
            "--stage",
            args.stage,
            "--model-id",
            model_id,
            "--backend",
            args.backend,
            "--manifest",
            args.manifest,
            "--report",
            str(temp_report),
        ]
        if args.limit:
            command.extend(["--limit", str(args.limit)])
        if args.rendered:
            command.extend(["--rendered", args.rendered])
        if args.resume:
            command.append("--resume")
        print(f"[09a_run_all] {model_id}: {' '.join(command[2:])}", flush=True)
        completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
        if completed.returncode != 0:
            if ledger_path.exists() and len(read_ledger(ledger_path)) >= expected_rows:
                print(
                    f"[09a_run_all] {model_id}: completed but per-model gate failed; "
                    "continuing to combine the report",
                    flush=True,
                )
            else:
                print(f"[09a_run_all] FAIL: {model_id} exited {completed.returncode}")
                return completed.returncode

    if args.stage != "calibration":
        print(f"[09a_run_all] main stage wall_seconds {time.perf_counter() - started:.1f}")
        return 0

    calibration_config = load_config("calibration.yaml")
    gates = calibration_config["gates"]
    rows = []
    ledgers = {}
    for model_id in model_ids:
        path = ledger_root / args.stage / model_id / "ledger.jsonl"
        ledgers[model_id] = str(path)
        rows.extend(read_ledger(path))
    report = evaluate_all_models(
        rows,
        model_ids,
        gates={
            "parse_rate_min": float(gates["parse_rate_min"]),
            "placebo_jitter_max": float(gates["placebo_jitter_max"]),
            "s3_switch_min": float(gates["s3_switch_min"]),
            "s3_switch_max": float(gates["s3_switch_max"]),
            "refusal_rate_max": float(gates["refusal_rate_max"]),
        },
    )
    report.update(
        {
            "stage": "g1_calibration",
            "recorded_utc": utc_now(),
            "git_commit": git_commit(),
            "wall_seconds": time.perf_counter() - started,
            "manifest_hash": _manifest_hash(args.stage, args.manifest),
            "ledgers": ledgers,
        }
    )
    report_path = resolve_repo_path(args.report)
    write_json(report_path, report)
    print(f"[09a_run_all] calibration passed {report['passed']}")
    print(f"[09a_run_all] wrote {report_path}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
