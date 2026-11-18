#!/usr/bin/env python
"""Stage 13 — G3 confirmatory analysis from the main ledgers.

Reads one ledger per model, computes the automatic outcome labels, the
severity slope (conditional logit with prefix-cluster inference), the
prefix-cluster bootstrap interval, Holm adjustment across models, and the
descriptive per-arm switch/detection/silent-propagation rates.

Nothing here regenerates text: every number traces to a ledger row written by
stage 09. A model whose ledger is short of the expected 4,400 rows is reported
as incomplete and excluded unless --allow-partial is passed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.analysis.outcomes import compute_outcomes, outcome_counts  # noqa: E402
from toolobs.analysis.slope import (  # noqa: E402
    bootstrap_slope,
    holm_adjust,
    per_model_slopes,
    pooled_slope,
    rows_from_outcomes,
)
from toolobs.config import load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl_dicts  # noqa: E402
from toolobs.infer.ledger import read_ledger  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, MANIFEST_DIR, RUNS_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402
from toolobs.schemas import PerturbationRecord  # noqa: E402

EXPECTED_ROWS = 4400
ARMS = ("s0", "s1", "s2", "s3")


def _arm_table(counts: dict[str, dict[str, int]]) -> dict[str, dict[str, float | int]]:
    """Convert per-model/per-arm counts into rates."""
    table: dict[str, dict[str, float | int]] = {}
    for key, values in counts.items():
        n = values["n"]
        table[key] = {
            **values,
            "switch_rate": round(values["any"] / n, 6) if n else None,
            "action_rate": round(values["action"] / n, 6) if n else None,
            "flag_rate": round(values["flag"] / n, 6) if n else None,
            "silent_rate": round(values["silent"] / n, 6) if n else None,
        }
    return table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", nargs="*", default=None)
    parser.add_argument("--ledger-root", default=str(RUNS_DIR / "main"))
    parser.add_argument("--perturbations", default=str(MANIFEST_DIR / "perturbations.jsonl"))
    parser.add_argument("--manifest", default=str(MANIFEST_DIR / "toolresult800_v1.json"))
    parser.add_argument(
        "--include-reserve",
        action="store_true",
        help="include the 80 reserve prefixes (not the preregistered analysis sample)",
    )
    parser.add_argument("--expected-rows", type=int, default=EXPECTED_ROWS)
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261108)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    configured = [str(model["id"]) for model in load_config("models.yaml")["models"]]
    model_ids = args.models or configured
    ledger_root = resolve_repo_path(args.ledger_root)
    manifest = json.loads(resolve_repo_path(args.manifest).read_text(encoding="utf-8"))
    reserve_ids = set(manifest.get("reserve_ids", []))

    rows = []
    coverage: dict[str, dict[str, object]] = {}
    used: list[str] = []
    for model_id in model_ids:
        path = ledger_root / model_id / "ledger.jsonl"
        if not path.exists():
            coverage[model_id] = {"rows": 0, "complete": False, "reason": "missing"}
            continue
        model_rows = [row for row in read_ledger(path) if row.step == 0]
        complete = len(model_rows) >= args.expected_rows
        coverage[model_id] = {
            "rows": len(model_rows),
            "complete": complete,
            "ledger": str(path),
        }
        if not complete and not args.allow_partial:
            continue
        rows.extend(model_rows)
        used.append(model_id)

    if not used:
        raise SystemExit("no complete ledger to analyze; pass --allow-partial to override")

    if not args.include_reserve and reserve_ids:
        rows = [row for row in rows if row.prefix_id not in reserve_ids]

    perturbations = [
        PerturbationRecord.from_dict(item)
        for item in read_jsonl_dicts(resolve_repo_path(args.perturbations))
    ]
    labels = compute_outcomes(rows, perturbations)
    counts = outcome_counts(labels)
    slope_rows = rows_from_outcomes(labels)

    pooled = pooled_slope(slope_rows)
    per_model = per_model_slopes(slope_rows)
    bootstrap = bootstrap_slope(
        slope_rows, replicates=args.bootstrap, seed=args.seed, pooled=True
    )
    per_model_holm = holm_adjust(
        {model_id: result.p_value for model_id, result in per_model.items()}
    )

    # Silent propagation is defined for the critical arms only (s2, s3).
    critical = [label for label in labels if label.arm in ("s2", "s3")]
    switched = [label for label in critical if label.y_any]
    silent = [label for label in switched if label.y_silent]
    silent_share = round(len(silent) / len(switched), 6) if switched else None

    report = {
        "stage": "g3_analysis",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "models": used,
        "coverage": coverage,
        "expected_rows": args.expected_rows,
        "allow_partial": bool(args.allow_partial),
        "include_reserve": bool(args.include_reserve),
        "reserve_ids": len(reserve_ids),
        "analysis_prefixes": len({row.prefix_id for row in rows}),
        "n_labels": len(labels),
        "n_slope_rows": len(slope_rows),
        "arm_table": _arm_table(counts),
        "pooled": pooled.as_dict(),
        "per_model": {key: value.as_dict() for key, value in per_model.items()},
        "per_model_holm": per_model_holm,
        "bootstrap": bootstrap.as_dict(),
        "silent_propagation": {
            "critical_n": len(critical),
            "switched_n": len(switched),
            "silent_n": len(silent),
            "silent_share_of_switch": silent_share,
        },
        "bootstrap_replicates": args.bootstrap,
        "seed": args.seed,
    }
    out_path = resolve_repo_path(
        args.out or (ARTIFACTS_DIR / "analysis" / "g3_analysis.json")
    )
    write_json(out_path, report)

    print(f"[13_analyze] models {used} labels {len(labels)} rows {len(slope_rows)}")
    print(f"[13_analyze] pooled beta {pooled.beta:.4f} se {pooled.se_cluster:.4f} p {pooled.p_value:.4g}")
    for model_id, result in per_model.items():
        print(
            f"[13_analyze] {model_id} beta {result.beta:.4f} "
            f"se {result.se_cluster:.4f} p {result.p_value:.4g} "
            f"holm {per_model_holm[model_id]:.4g}"
        )
    print(
        f"[13_analyze] bootstrap CI [{bootstrap.ci_low:.4f}, {bootstrap.ci_high:.4f}] "
        f"p2 {bootstrap.p_two_sided:.4g}"
    )
    print(f"[13_analyze] silent share {silent_share} of {len(switched)} switches")
    print(f"[13_analyze] wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
