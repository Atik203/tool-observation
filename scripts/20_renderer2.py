#!/usr/bin/env python
"""Stage 20 - P6.7 second deterministic renderer (field-list) run.

Modes
-----
``render``  Build `toolresult-fieldlist-v1` rows for a deterministic 150-prefix
            sample and prove that the v1 prose rendering of the same arms
            reproduces the frozen `arm_observations` bit-for-bit.
``run``     Generate one model over the rendered rows (one vLLM process per
            model, as stage 09a). Ledgers and per-model wall time go under
            `data/runs/renderer2/` (gitignored).
``all``     `render`, then one `run` per configured model, then `analyze`.
``analyze`` Compare renderer-2 and renderer-1 ledgers on the same prefixes and
            write `artifacts/analysis/renderer2.json`.

This is exploratory robustness evidence. It never pools with the confirmatory
slope and it does not modify the frozen manifest, perturbations, or prereg.
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.analysis.renderer2 import (  # noqa: E402
    paired_rate_difference,
    paired_slope_difference,
    parser_summary,
    slope_rows,
    summarize_table,
    unit_table,
)
from toolobs.analysis.slope import bootstrap_slope  # noqa: E402
from toolobs.config import config_hashes, load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl_dicts, write_jsonl_dicts  # noqa: E402
from toolobs.hashing import sha256_file, sha256_text  # noqa: E402
from toolobs.infer.ledger import read_ledger  # noqa: E402
from toolobs.infer.parse_output import signature_from_json, signatures_differ  # noqa: E402
from toolobs.infer.prompt import PROMPT_VERSION  # noqa: E402
from toolobs.infer.runner import PARSER_VERSION, FakeBackend, run_rendered_rows  # noqa: E402
from toolobs.paths import (  # noqa: E402
    ARTIFACTS_DIR,
    FROZEN_DIR,
    INTERIM_DIR,
    MANIFEST_DIR,
    RUNS_DIR,
    resolve_repo_path,
)
from toolobs.provenance import git_commit, repo_relative, utc_now, write_json  # noqa: E402
from toolobs.render.render import ARMS, RENDERER_VERSION  # noqa: E402
from toolobs.render.render2 import (  # noqa: E402
    RENDERER2_VERSION,
    build_arms2,
    render_arm_messages2,
)
from toolobs.schemas import PrefixRecord  # noqa: E402

STAGE = "renderer2"
DEFAULT_N = 150
DEFAULT_SEED = 20261108
FORMAT_BOUND_PP = 10.0
RENDERED_PATH = INTERIM_DIR / "renderer2_rendered.jsonl"
CHANGES_PATH = INTERIM_DIR / "renderer2_changes.jsonl"
REPORT_PATH = ARTIFACTS_DIR / "audit" / "renderer2_report.json"
ARTIFACT_PATH = ARTIFACTS_DIR / "analysis" / "renderer2.json"
LEDGER_ROOT = RUNS_DIR / STAGE
MAIN_ROOT = RUNS_DIR / "main"


def _model_configs(model_ids: list[str] | None = None) -> list[dict]:
    models = load_config("models.yaml").get("models", [])
    if not model_ids:
        return models
    wanted = set(model_ids)
    selected = [model for model in models if str(model.get("id")) in wanted]
    missing = wanted - {str(model.get("id")) for model in selected}
    if missing:
        raise SystemExit(f"unknown model ids: {sorted(missing)}")
    return selected


def _manifest_hash() -> str:
    path = MANIFEST_DIR / "toolresult800_v1.json"
    if not path.is_file():
        raise SystemExit(f"missing frozen manifest: {path}")
    return sha256_file(path)


def _load_frozen() -> dict[str, dict]:
    rows = read_jsonl_dicts(FROZEN_DIR / "prefixes.jsonl")
    return {str(row["prefix_id"]): row for row in rows}


def _load_records() -> dict[str, PrefixRecord]:
    rows = read_jsonl_dicts(INTERIM_DIR / "sample.jsonl")
    return {
        str(row["prefix_id"]): PrefixRecord.from_dict(row)
        for row in rows
        if str(row.get("split", "")) == "primary"
    }


def select_prefixes(
    records: dict[str, PrefixRecord],
    frozen: dict[str, dict],
    *,
    n: int,
    seed: int,
) -> list[str]:
    """Pick a deterministic, domain-balanced primary-prefix sample."""
    eligible = {
        prefix_id: record
        for prefix_id, record in records.items()
        if prefix_id in frozen and record.domain
    }
    domains = sorted({record.domain for record in eligible.values()})
    if not domains:
        raise ValueError("no eligible prefixes")
    if n > len(eligible):
        raise ValueError(f"n={n} exceeds {len(eligible)} eligible prefixes")
    by_domain: dict[str, list[str]] = {domain: [] for domain in domains}
    for prefix_id, record in eligible.items():
        by_domain[record.domain].append(prefix_id)
    rng = random.Random(seed)
    base, remainder = divmod(n, len(domains))
    selected: list[str] = []
    for position, domain in enumerate(domains):
        ids = sorted(by_domain[domain])
        rng.shuffle(ids)
        take = base + (1 if position < remainder else 0)
        selected.extend(ids[:take])
    return sorted(selected)


def mode_render(args: argparse.Namespace) -> int:
    frozen = _load_frozen()
    records = _load_records()
    prefix_ids = select_prefixes(records, frozen, n=args.n, seed=args.seed)
    rows = []
    changes = []
    errors: list[str] = []
    reproduction_mismatches: list[str] = []
    value_set_failures: list[str] = []
    unchanged_surfaces: list[str] = []

    for prefix_id in prefix_ids:
        record = records[prefix_id]
        frozen_row = frozen[prefix_id]
        if str(frozen_row.get("renderer_version", "")) != RENDERER_VERSION:
            errors.append(f"{prefix_id}: frozen renderer {frozen_row.get('renderer_version')}")
            continue
        arm_set = build_arms2(record, seed=args.seed)
        if arm_set.errors:
            errors.extend(f"{prefix_id}: {error}" for error in arm_set.errors)
            continue
        if not arm_set.s0_value_set_ok:
            value_set_failures.append(prefix_id)
        for arm in ARMS:
            prose_text = arm_set.prose_observations.get(arm)
            frozen_text = str(frozen_row["arm_observations"][arm])
            if prose_text != frozen_text:
                reproduction_mismatches.append(f"{prefix_id}:{arm}")
            if arm != "V" and arm_set.observations.get(arm) == prose_text:
                unchanged_surfaces.append(f"{prefix_id}:{arm}")
        arm_rows = render_arm_messages2(record, list(frozen_row["messages"]), arm_set)
        if len(arm_rows) != len(ARMS):
            errors.append(f"{prefix_id}: {len(arm_rows)} arms rendered")
            continue
        rows.extend(row.to_dict() for row in arm_rows)
        for change in arm_set.changes:
            changes.append({"prefix_id": prefix_id, **change})

    by_arm = Counter(str(row["arm"]) for row in rows)
    report = {
        "stage": "p6.7_renderer2_render",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "selection_rule": (
            "seeded shuffle within domain over the 800 primary frozen prefixes, "
            "reserve excluded, balanced by domain"
        ),
        "seed": args.seed,
        "n_prefixes": len(prefix_ids),
        "prefix_ids": prefix_ids,
        "prefix_ids_sha256": sha256_text("\n".join(prefix_ids)),
        "domain_counts": dict(
            sorted(Counter(records[prefix_id].domain for prefix_id in prefix_ids).items())
        ),
        "renderer1_version": RENDERER_VERSION,
        "renderer2_version": RENDERER2_VERSION,
        "renderer2_hash": sha256_file(REPO_ROOT / "src" / "toolobs" / "render" / "render2.py"),
        "manifest_hash": _manifest_hash(),
        "config_hashes": config_hashes(),
        "rendered_rows": len(rows),
        "by_arm": dict(sorted(by_arm.items())),
        "changes": len(changes),
        "value_set_failures": value_set_failures[:20],
        "value_set_failure_count": len(value_set_failures),
        "v1_reproduction_mismatches": reproduction_mismatches[:20],
        "v1_reproduction_mismatch_count": len(reproduction_mismatches),
        "unchanged_surfaces": unchanged_surfaces[:20],
        "unchanged_surface_count": len(unchanged_surfaces),
        "errors": errors[:50],
        "error_count": len(errors),
    }
    write_json(REPORT_PATH, report)

    if errors or reproduction_mismatches or value_set_failures or unchanged_surfaces:
        print(
            "[20_renderer2] FAIL: "
            f"errors={len(errors)} reproduction={len(reproduction_mismatches)} "
            f"value_set={len(value_set_failures)} unchanged_surface={len(unchanged_surfaces)}"
        )
        for item in (errors + reproduction_mismatches + value_set_failures)[:20]:
            print(f"  - {item}")
        return 1
    write_jsonl_dicts(rows, RENDERED_PATH)
    write_jsonl_dicts(changes, CHANGES_PATH)
    print(f"[20_renderer2] prefixes {len(prefix_ids)} rows {len(rows)} by_arm {dict(by_arm)}")
    print(f"[20_renderer2] wrote {RENDERED_PATH}")
    print(f"[20_renderer2] wrote {REPORT_PATH}")
    return 0


def _completed_keys(ledger_path: Path) -> set[tuple[str, str, int]]:
    if not ledger_path.exists():
        return set()
    return {(row.prefix_id, row.arm, row.step) for row in read_ledger(ledger_path)}


def mode_run(args: argparse.Namespace) -> int:
    models = _model_configs([args.model_id])
    if len(models) != 1:
        raise SystemExit("run mode needs exactly one --model-id")
    model = models[0]
    model_id = str(model["id"])
    rows = read_jsonl_dicts(RENDERED_PATH)
    if not rows:
        raise SystemExit(f"no rendered rows at {RENDERED_PATH}; run --mode render first")
    ledger_path = LEDGER_ROOT / model_id / "ledger.jsonl"
    completed = _completed_keys(ledger_path) if args.resume else set()
    if ledger_path.exists() and not args.resume:
        raise SystemExit(
            f"ledger exists at {ledger_path}; pass --resume or remove the shard"
        )

    models_config = load_config("models.yaml")
    started = time.perf_counter()
    if args.backend == "fake":
        backend = FakeBackend(args.fake_response)
        load_seconds = 0.0
    else:
        from toolobs.infer.vllm_backend import VLLMBackend  # noqa: PLC0415

        load_started = time.perf_counter()
        backend = VLLMBackend(
            model,
            max_tokens=int(models_config["decoding"]["max_tokens"]),
            seed=int(models_config["decoding"]["seed"]),
            max_num_seqs=int(models_config["serving"]["max_num_seqs"]),
        )
        load_seconds = time.perf_counter() - load_started

    generation_started = time.perf_counter()
    stats = run_rendered_rows(
        rows,
        backend=backend,
        model_id=model_id,
        run_id=f"{STAGE}-{model_id}-{args.seed}",
        stage=STAGE,
        manifest_hash=_manifest_hash(),
        ledger_path=ledger_path,
        upstream_dir=resolve_repo_path("data/upstream/tau-bench"),
        prompt_version=PROMPT_VERSION,
        parser_version=PARSER_VERSION,
        batch_size=int(models_config["serving"]["batch_size"]),
        skip_completed=completed,
        excluded_tools=models_config["serving"].get("excluded_tools", []),
    )
    generation_seconds = time.perf_counter() - generation_started
    wall_seconds = time.perf_counter() - started
    stats_path = ledger_path.parent / "run_stats.json"
    prior = (
        json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {}
    )
    call_record = {
        "recorded_utc": utc_now(),
        "rows_completed": stats.total,
        "load_seconds": round(load_seconds, 3),
        "generation_seconds": round(generation_seconds, 3),
        "wall_seconds": round(wall_seconds, 3),
        "gpu_hours": round((load_seconds + generation_seconds) / 3600.0, 6),
    }
    calls = list(prior.get("calls", [])) + [call_record]
    total_gpu_hours = sum(float(call["gpu_hours"]) for call in calls)
    write_json(
        stats_path,
        {
            "stage": "p6.7_renderer2_run",
            "recorded_utc": utc_now(),
            "git_commit": git_commit(),
            "model_id": model_id,
            "repo_id": model.get("repo_id"),
            "revision": model.get("revision"),
            "renderer2_version": RENDERER2_VERSION,
            "prompt_version": PROMPT_VERSION,
            "parser_version": PARSER_VERSION,
            "manifest_hash": _manifest_hash(),
            "backend": args.backend,
            "rows_expected": len(rows),
            "rows_completed_this_call": stats.total,
            "ledger": repo_relative(ledger_path),
            "load_seconds": call_record["load_seconds"],
            "generation_seconds": call_record["generation_seconds"],
            "wall_seconds": call_record["wall_seconds"],
            "gpu_hours": round(total_gpu_hours, 6),
            "calls": calls,
            "stats": stats.as_dict(),
        },
    )
    print(f"[20_renderer2] {model_id} rows {stats.total} wall {wall_seconds:.1f}s")
    print(f"[20_renderer2] gpu_hours {(load_seconds + generation_seconds) / 3600.0:.4f}")
    print(f"[20_renderer2] wrote {ledger_path}")
    return 0


def mode_all(args: argparse.Namespace) -> int:
    if mode_render(args) != 0:
        return 1
    for model in _model_configs():
        model_id = str(model["id"])
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--mode",
            "run",
            "--model-id",
            model_id,
            "--backend",
            args.backend,
            "--seed",
            str(args.seed),
            "--resume",
        ]
        print(f"[20_renderer2] spawning {model_id}", flush=True)
        completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
        if completed.returncode != 0:
            print(f"[20_renderer2] FAIL: {model_id} exited {completed.returncode}")
            return completed.returncode
    args.mode = "analyze"
    return mode_analyze(args)


def _shard_rows(model_id: str, prefix_ids: set[str]) -> list:
    path = LEDGER_ROOT / model_id / "ledger.jsonl"
    if not path.exists():
        return []
    rows = read_ledger(path)
    return [row for row in rows if row.prefix_id in prefix_ids and row.step == 0]


def _hash(path: Path) -> dict:
    return {
        "path": repo_relative(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def mode_analyze(args: argparse.Namespace) -> int:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    prefix_ids = list(report["prefix_ids"])
    prefix_set = set(prefix_ids)
    all_models = [str(model["id"]) for model in _model_configs()]
    rendered2: dict[str, list] = {}
    rendered1: dict[str, list] = {}
    missing: list[str] = []
    incomplete: dict[str, dict] = {}
    per_model_hours: dict[str, dict] = {}
    for model_id in all_models:
        rows2 = _shard_rows(model_id, prefix_set)
        if not rows2:
            missing.append(model_id)
            continue
        rendered2[model_id] = rows2
        expected = len(prefix_ids) * len(ARMS)
        if len(rows2) < expected:
            incomplete[model_id] = {"rows": len(rows2), "expected": expected}
        stats_path = LEDGER_ROOT / model_id / "run_stats.json"
        if stats_path.exists():
            stats = json.loads(stats_path.read_text(encoding="utf-8"))
            per_model_hours[model_id] = {
                "gpu_hours": stats.get("gpu_hours"),
                "wall_seconds": stats.get("wall_seconds"),
                "generation_seconds": stats.get("generation_seconds"),
                "load_seconds": stats.get("load_seconds"),
            }
    for model_id in all_models:
        path = MAIN_ROOT / model_id / "ledger.jsonl"
        if not path.exists():
            missing.append(f"{model_id}:renderer1")
            continue
        rows1 = [row for row in read_ledger(path) if row.prefix_id in prefix_set and row.step == 0]
        if rows1:
            rendered1[model_id] = rows1

    kept_models = [model_id for model_id in all_models if model_id in rendered2 and model_id in rendered1]
    if not kept_models:
        raise SystemExit("no model has both renderer-1 and renderer-2 rows on the sampled prefixes")

    rows2 = [row for model_id in kept_models for row in rendered2[model_id]]
    rows1 = [row for model_id in kept_models for row in rendered1[model_id]]
    table2 = unit_table(rows2)
    table1 = unit_table(rows1)
    summary2 = summarize_table(table2, replicates=args.replicates, seed=args.seed)
    summary1 = summarize_table(table1, replicates=args.replicates, seed=args.seed)

    v_anchor: dict[str, dict] = {}
    for model_id in kept_models:
        reference2 = {
            row.prefix_id: row
            for row in rendered2[model_id]
            if row.arm == "V" and row.parsed
        }
        reference1 = {
            row.prefix_id: row
            for row in rendered1[model_id]
            if row.arm == "V" and row.parsed
        }
        common = sorted(set(reference2) & set(reference1))
        same = sum(
            not signatures_differ(
                signature_from_json(reference2[prefix].decision_json),
                signature_from_json(reference1[prefix].decision_json),
            )
            for prefix in common
        )
        v_anchor[model_id] = {
            "n": len(common),
            "same": same,
            "agreement": (same / len(common)) if common else None,
        }

    format_per_model: dict[str, dict] = {}
    for model_id in kept_models:
        difference = paired_rate_difference(
            table2,
            table1,
            "s0",
            model=model_id,
            replicates=args.replicates,
            seed=args.seed,
        )
        rate2 = summary2["arm_switch_rates"][model_id]["s0"]["rate"]
        rate1 = summary1["arm_switch_rates"][model_id]["s0"]["rate"]
        difference.update({"renderer2_s0_rate": rate2, "renderer1_s0_rate": rate1})
        format_per_model[model_id] = difference
    format_pooled = paired_rate_difference(
        table2, table1, "s0", replicates=args.replicates, seed=args.seed
    )
    format_pooled["note"] = (
        "pooled paired difference across models; per-model rates are in per_model"
    )

    slope_per_model: dict[str, dict] = {}
    for model_id in kept_models:
        difference = paired_slope_difference(
            table2,
            table1,
            model_id,
            replicates=args.replicates,
            seed=args.seed,
        )
        difference.update(
            {
                "renderer2_slope": summary2["slope"]["per_model"][model_id],
                "renderer1_slope": summary1["slope"]["per_model"][model_id],
            }
        )
        slope_per_model[model_id] = difference
    pooled_bootstrap2 = bootstrap_slope(
        slope_rows(table2), replicates=args.replicates, seed=args.seed
    ).as_dict()
    pooled_bootstrap1 = bootstrap_slope(
        slope_rows(table1), replicates=args.replicates, seed=args.seed
    ).as_dict()

    format_checks = {}
    for model_id in kept_models:
        difference = format_per_model[model_id]["difference"]
        format_checks[model_id] = (
            difference is not None and abs(difference) <= FORMAT_BOUND_PP / 100.0
        )
    slope_checks = {}
    for model_id in kept_models:
        beta2 = slope_per_model[model_id]["renderer2_slope"]["beta"]
        interval = summary1["slope"]["per_model_bootstrap"][model_id]
        slope_checks[model_id] = (
            beta2 is not None
            and beta2 > 0
            and interval.get("ci_low") is not None
            and interval["ci_low"] <= beta2 <= interval["ci_high"]
        )
    pooled_beta2 = summary2["slope"]["pooled"]["beta"]
    pooled_slope_ok = (
        pooled_beta2 is not None
        and pooled_beta2 > 0
        and pooled_bootstrap1.get("ci_low") is not None
        and pooled_bootstrap1["ci_low"] <= pooled_beta2 <= pooled_bootstrap1["ci_high"]
    )
    complete = not missing and not incomplete
    holds = complete and all(format_checks.values()) and all(slope_checks.values()) and pooled_slope_ok
    if not complete:
        holds = None

    artifact = {
        "stage": "p6.7_renderer2",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "exploratory": True,
        "pooled_with_confirmatory": False,
        "renderer1_version": RENDERER_VERSION,
        "renderer2_version": RENDERER2_VERSION,
        "renderer2_hash": report.get("renderer2_hash"),
        "prompt_version": PROMPT_VERSION,
        "parser_version": PARSER_VERSION,
        "signature_version": "toolresult800-signature-v2",
        "manifest_hash": _manifest_hash(),
        "sample": {
            "n_prefixes": len(prefix_ids),
            "domains": report.get("domain_counts"),
            "seed": report.get("seed"),
            "selection_rule": report.get("selection_rule"),
            "prefix_ids": prefix_ids,
            "prefix_ids_sha256": report.get("prefix_ids_sha256"),
        },
        "models": kept_models,
        "missing": missing,
        "incomplete": incomplete,
        "gpu_hours": {
            "per_model": per_model_hours,
            "total": round(
                sum(item.get("gpu_hours") or 0.0 for item in per_model_hours.values()), 6
            ),
            "note": "load + generation wall time measured inside the run process",
        },
        "parse_summary": {
            "renderer2": parser_summary(rows2),
            "renderer1": parser_summary(rows1),
        },
        "v_anchor_agreement": {
            "definition": (
                "share of parsed V decisions whose signature is identical across the two "
                "renderers; V is the same raw JSON prompt in both, so this measures "
                "generation-level repeatability at temperature 0"
            ),
            "per_model": v_anchor,
        },
        "renderer2": summary2,
        "renderer1_same_prefixes": summary1,
        "renderer1_pooled_bootstrap": pooled_bootstrap1,
        "format_sensitivity": {
            "definition": "paired s0-vs-V switch rate difference (renderer2 - renderer1)",
            "per_model": format_per_model,
            "pooled": format_pooled,
        },
        "slope_robustness": {
            "definition": "paired conditional-logit beta difference (renderer2 - renderer1)",
            "per_model": slope_per_model,
            "pooled": {
                "renderer2_beta": pooled_beta2,
                "renderer1_beta": summary1["slope"]["pooled"]["beta"],
                "renderer2_bootstrap": pooled_bootstrap2,
                "renderer1_bootstrap": pooled_bootstrap1,
            },
        },
        "robustness_bound": {
            "criterion": (
                "holds if every per-model s0 format-sensitivity shift is <=10 pp and "
                "pooled and every per-model renderer-2 slope is positive and inside the "
                "renderer-1 95% prefix-bootstrap interval"
            ),
            "format_bound_pp": FORMAT_BOUND_PP,
            "format_checks": format_checks,
            "slope_checks": slope_checks,
            "pooled_slope_check": pooled_slope_ok,
            "holds": holds,
            "reason_if_not": None
            if holds
            else (
                "incomplete run: " + ", ".join(missing + list(incomplete))
                if not complete
                else "one or more pre-stated format/slope checks failed"
            ),
        },
        "ledger_hashes": {
            "renderer2": {
                model_id: _hash(LEDGER_ROOT / model_id / "ledger.jsonl")
                for model_id in kept_models
            },
            "renderer1": {
                model_id: _hash(MAIN_ROOT / model_id / "ledger.jsonl")
                for model_id in kept_models
            },
            "renderer2_rendered": _hash(RENDERED_PATH) if RENDERED_PATH.exists() else None,
        },
        "limitations": [
            "exploratory 150-prefix sample; wider intervals than the confirmatory run",
            "one alternative surface form only; not a general renderer population",
            "renderer-1 comparators are recomputed on the same prefixes, not the full 800",
            "no utility or task-success endpoint; switch is decision-level only",
        ],
    }
    write_json(args.out or ARTIFACT_PATH, artifact)

    print(f"[20_renderer2] models {kept_models} missing {missing} incomplete {incomplete}")
    for model_id in kept_models:
        rates = summary2["arm_switch_rates"][model_id]
        print(
            f"[20_renderer2] {model_id} s0 {rates['s0']['rate']:.3f} "
            f"s3 {rates['s3']['rate']:.3f} beta2 {summary2['slope']['per_model'][model_id]['beta']:.4f} "
            f"beta1 {summary1['slope']['per_model'][model_id]['beta']:.4f}"
        )
    print(f"[20_renderer2] robustness bound holds={holds}")
    print(f"[20_renderer2] gpu_hours {artifact['gpu_hours']['total']}")
    print(f"[20_renderer2] wrote {args.out or ARTIFACT_PATH}")
    return 0 if holds is not False else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--mode", choices=("render", "run", "analyze", "all"), default="all"
    )
    parser.add_argument("--n", type=int, default=DEFAULT_N)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--replicates", type=int, default=2000)
    parser.add_argument("--model-id", default=None)
    parser.add_argument("--backend", choices=("vllm", "fake"), default="vllm")
    parser.add_argument(
        "--fake-response",
        default='{"tool": "get_reservation_details", "arguments": {"reservation_id": "TEST"}}',
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--out", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.mode == "render":
        return mode_render(args)
    if args.mode == "run":
        return mode_run(args)
    if args.mode == "analyze":
        return mode_analyze(args)
    return mode_all(args)


if __name__ == "__main__":
    sys.exit(main())
