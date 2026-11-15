#!/usr/bin/env python
"""Stage 09 — calibration and main generation runner.

Input:  data/interim/calibration_rendered.jsonl or data/interim/rendered.jsonl
Output: data/runs/{stage}/{model}/ledger.jsonl; calibration report

`--backend fake` exercises the prompt/parser/ledger path on CPU. `--backend vllm`
loads the pinned AWQ model lazily and is only used after the user authorizes GPU
work and the model revisions are pinned. Calibration is one model at a time; use
`--all-models` to run the three configured families.

GATE (calibration): parse >=95%, placebo jitter <=20%, s=3 switch 10-80%,
refusal <5% per model.
"""

from __future__ import annotations

import argparse
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
from toolobs.infer.runner import FakeBackend, run_rendered_rows  # noqa: E402
from toolobs.paths import (  # noqa: E402
    ARTIFACTS_DIR,
    INTERIM_DIR,
    MANIFEST_DIR,
    RUNS_DIR,
    resolve_repo_path,
)
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402


def _model_configs(model_ids: list[str] | None) -> list[dict]:
    models = load_config("models.yaml").get("models", [])
    if model_ids is None:
        return models
    wanted = set(model_ids)
    selected = [model for model in models if model.get("id") in wanted]
    missing = wanted - {model.get("id") for model in selected}
    if missing:
        raise SystemExit(f"unknown model ids: {sorted(missing)}")
    return selected


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
    parser.add_argument("--model-id", action="append", default=None)
    parser.add_argument("--all-models", action="store_true")
    parser.add_argument("--backend", choices=("fake", "vllm"), default="fake")
    parser.add_argument("--rendered", default=None)
    parser.add_argument("--ledger", default=None)
    parser.add_argument("--manifest", default=str(MANIFEST_DIR / "toolresult800_v1.json"))
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Append to an existing ledger, skipping completed (prefix, arm, step) rows.",
    )
    parser.add_argument("--fake-response", default='{"tool": "get_reservation_details", "arguments": {"reservation_id": "TEST"}}')
    parser.add_argument("--report", default=str(ARTIFACTS_DIR / "audit" / "g1_calibration.json"))
    args = parser.parse_args(argv)

    if args.all_models and args.backend == "vllm":
        raise SystemExit(
            "vLLM keeps GPU memory per process; use scripts/09a_run_all.py "
            "to run one model per process"
        )

    calibration_config = load_config("calibration.yaml")
    calibration = calibration_config["calibration"]
    calibration_gates = calibration_config["gates"]
    models = _model_configs(None if args.all_models else args.model_id)
    if not models:
        raise SystemExit("no model selected")
    rendered_path = resolve_repo_path(
        args.rendered
        or (INTERIM_DIR / ("calibration_rendered.jsonl" if args.stage == "calibration" else "rendered.jsonl"))
    )
    rows = read_jsonl_dicts(rendered_path)
    if args.limit:
        rows = rows[: args.limit]
    manifest_hash = _manifest_hash(args.stage, args.manifest)
    models_config = load_config("models.yaml")
    started = time.perf_counter()
    ledgers: dict[str, Path] = {}

    for model in models:
        model_id = str(model["id"])
        ledger_path = resolve_repo_path(
            args.ledger
            or (RUNS_DIR / args.stage / model_id / "ledger.jsonl")
        )
        completed: set[tuple[str, str, int]] = set()
        if ledger_path.exists():
            existing = read_ledger(ledger_path)
            model_rows = [row for row in existing if row.model_id == model_id]
            if model_rows and not args.resume:
                print(
                    f"[09_run] FAIL: ledger already has {len(model_rows)} rows for "
                    f"{model_id} at {ledger_path}; pass --resume to continue it, or "
                    "move it / pass a new --ledger"
                )
                return 1
            if args.resume:
                completed = {(row.prefix_id, row.arm, row.step) for row in model_rows}
        if args.backend == "fake":
            backend = FakeBackend(args.fake_response)
        else:
            from toolobs.infer.vllm_backend import VLLMBackend  # noqa: PLC0415

            backend = VLLMBackend(
                model,
                max_tokens=int(models_config["decoding"]["max_tokens"]),
                seed=int(calibration["seed"]),
                max_num_seqs=int(models_config["serving"]["max_num_seqs"]),
            )
        stats = run_rendered_rows(
            rows,
            backend=backend,
            model_id=model_id,
            run_id=f"{args.stage}-{model_id}-{calibration['seed']}",
            stage=args.stage,
            manifest_hash=manifest_hash,
            ledger_path=ledger_path,
            upstream_dir=resolve_repo_path("data/upstream/tau-bench"),
            prompt_version=str(calibration["prompt_version"]),
            parser_version=str(calibration["parser_version"]),
            batch_size=int(models_config["serving"]["batch_size"]),
            skip_completed=completed,
            excluded_tools=models_config["serving"].get("excluded_tools", []),
        )
        ledgers[model_id] = ledger_path
        print(f"[09_run] {model_id} {stats.as_dict()}")

    elapsed = time.perf_counter() - started
    if args.stage == "calibration":
        all_rows = []
        for path in dict.fromkeys(ledgers.values()):
            all_rows.extend(read_ledger(path))
        report = evaluate_all_models(
            all_rows,
            [str(model["id"]) for model in models],
            gates={
                "parse_rate_min": float(calibration_gates["parse_rate_min"]),
                "placebo_jitter_max": float(calibration_gates["placebo_jitter_max"]),
                "negative_control_jitter_max": float(
                    calibration_gates["negative_control_jitter_max"]
                ),
                "s3_switch_min": float(calibration_gates["s3_switch_min"]),
                "s3_switch_max": float(calibration_gates["s3_switch_max"]),
                "refusal_rate_max": float(calibration_gates["refusal_rate_max"]),
            },
        )
        report.update(
            {
                "stage": "g1_calibration",
                "recorded_utc": utc_now(),
                "git_commit": git_commit(),
                "wall_seconds": elapsed,
                "manifest_hash": manifest_hash,
                "ledgers": {key: str(value) for key, value in ledgers.items()},
            }
        )
        write_json(resolve_repo_path(args.report), report)
        print(f"[09_run] calibration passed {report['passed']}")
        print(f"[09_run] wrote {resolve_repo_path(args.report)}")
        return 0 if report["passed"] else 1

    print(f"[09_run] main stage wall_seconds {elapsed:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
