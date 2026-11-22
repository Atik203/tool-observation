#!/usr/bin/env python
"""Stage 17 - wrong-direction (utility-flavored) endpoint from perturbation records.

CPU-only, stdlib-only. No GPU, no new generations: every number is recomputed
from the frozen step-0 main ledgers, the frozen perturbation records, and the
automatic outcome coding shared with stage 13 (parser v4 / signature v2).

Motivation (C10): the primary outcome is a decision-signature deviation from
the donor verbatim continuation V, not task error. The perturbation records
already store the design expectation ``expected_action_change`` for every
critical arm (s2/s3): trusting the injected false value changes the correct
next action. Every critical-arm record in the frozen manifest carries
``expected_action_change=true`` (asserted fail-loud below), so a critical-arm
switch that is NOT an explicit flag moved in the anticipated direction class:

- wrong-direction (WD): exclusive action switch (C^A) or silent propagation
  (C^U) - the decision moved with the corruption rather than catching it;
- caught: exclusive flag-only (C^F) - correct skepticism;
- ambiguous: other signature change (C^O).

The endpoint is descriptive (no p-value gate): the share of critical-arm
switches that are wrong-direction, pooled and per model / per arm, with Wilson
95% intervals, plus the caught share. Silent propagation (Y^U) is the confirmed
wrong-direction subset; action switches are the anticipated-direction class.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.analysis.outcomes import compute_outcomes  # noqa: E402
from toolobs.config import load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl_dicts  # noqa: E402
from toolobs.infer.ledger import read_ledger  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, MANIFEST_DIR, RUNS_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402
from toolobs.schemas import PerturbationRecord  # noqa: E402

PROVENANCE = "multi-role agent panel, author-overseen"
CRITICAL_ARMS = ("s2", "s3")


def wilson_ci(k: int, n: int, z: float = 1.96) -> dict[str, float | None]:
    """Wilson score interval for a binomial share (matches stage-14 convention)."""
    if n <= 0:
        return {"rate": None, "lo": None, "hi": None}
    p = k / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / den
    half = z * ((p * (1.0 - p) / n + z * z / (4.0 * n * n)) ** 0.5) / den
    return {
        "rate": round(p, 6),
        "lo": round(max(0.0, centre - half), 6),
        "hi": round(min(1.0, centre + half), 6),
    }


def classify(label) -> str:
    """Exclusive wrong-direction class for one switched critical-arm label."""
    if label.y_action:
        return "action"
    if label.y_flag:
        return "caught"
    if label.y_silent:
        return "silent"
    return "other"


def summarize(labels: list) -> dict[str, object]:
    """Wrong-direction summary for a list of switched critical-arm labels."""
    classes = [classify(label) for label in labels]
    n = len(classes)
    n_wd = sum(1 for c in classes if c in ("action", "silent"))
    n_caught = sum(1 for c in classes if c == "caught")
    n_silent = sum(1 for c in classes if c == "silent")
    return {
        "switches": n,
        "wrong_direction": n_wd,
        "wrong_direction_share": wilson_ci(n_wd, n),
        "caught": n_caught,
        "caught_share": wilson_ci(n_caught, n),
        "silent": n_silent,
        "silent_share": wilson_ci(n_silent, n),
        "action": sum(1 for c in classes if c == "action"),
        "other": sum(1 for c in classes if c == "other"),
    }


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
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    configured = [str(model["id"]) for model in load_config("models.yaml")["models"]]
    model_ids = args.models or configured
    ledger_root = resolve_repo_path(args.ledger_root)
    manifest = json.loads(resolve_repo_path(args.manifest).read_text(encoding="utf-8"))
    reserve_ids = set(manifest.get("reserve_ids", []))

    rows = []
    for model_id in model_ids:
        path = ledger_root / model_id / "ledger.jsonl"
        if not path.exists():
            raise SystemExit(f"missing ledger: {path}")
        rows.extend(row for row in read_ledger(path) if row.step == 0)
    if not args.include_reserve and reserve_ids:
        rows = [row for row in rows if row.prefix_id not in reserve_ids]

    perturbations = [
        PerturbationRecord.from_dict(item)
        for item in read_jsonl_dicts(resolve_repo_path(args.perturbations))
    ]
    critical_records = [item for item in perturbations if item.arm in CRITICAL_ARMS]
    unexpected = [
        item.record_id for item in critical_records if not item.expected_action_change
    ]
    if unexpected:
        raise SystemExit(
            "critical-arm records without expected_action_change=true: "
            + ", ".join(unexpected[:10])
        )

    labels = compute_outcomes(rows, perturbations)
    critical = [label for label in labels if label.arm in CRITICAL_ARMS]
    switched = [label for label in critical if label.y_any]
    if not switched:
        raise SystemExit("no critical-arm switches; check ledger inputs")

    by_model: dict[str, dict[str, object]] = {}
    for model_id in model_ids:
        cell = [label for label in switched if label.model_id == model_id]
        by_model[model_id] = summarize(cell)
    by_arm: dict[str, dict[str, object]] = {}
    for arm in CRITICAL_ARMS:
        by_arm[arm] = summarize([label for label in switched if label.arm == arm])

    report = {
        "stage": "wrong_direction",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "models": model_ids,
        "include_reserve": bool(args.include_reserve),
        "reserve_ids": len(reserve_ids),
        "analysis_prefixes": len({row.prefix_id for row in rows}),
        "critical_records": len(critical_records),
        "critical_expected_action_change_true": len(critical_records) - len(unexpected),
        "critical_labeled": len(critical),
        "critical_switches": len(switched),
        "endpoint": "wrong-direction = exclusive action switch (C^A) or silent "
        "propagation (C^U) on a critical arm whose perturbation record "
        "anticipates an action change; caught = flag-only (C^F); "
        "ambiguous = other (C^O).",
        "pooled": summarize(switched),
        "by_model": by_model,
        "by_arm": by_arm,
        "provenance": PROVENANCE,
    }
    out_path = resolve_repo_path(args.out or (ARTIFACTS_DIR / "analysis" / "wrong_direction.json"))
    write_json(out_path, report)
    pooled = report["pooled"]
    print(
        f"wrong-direction {pooled['wrong_direction']}/{pooled['switches']} "
        f"({pooled['wrong_direction_share']['rate']:.1%}); "
        f"caught {pooled['caught']}/{pooled['switches']}"
    )
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
