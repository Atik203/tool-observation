#!/usr/bin/env python
"""Stage 14 — G4 recovery report from the recovery event ledgers.

Primary endpoint: the transient s=3 risk set. Secondary: transient s=2 and the
persistent s=3 set. The discrete-time exponential fit is the preregistered model;
Kaplan-Meier, RMST and the Weibull shape likelihood-ratio test are reported
regardless.

Gates:
  * at least 50% of the primary risk set recovers by H=4;
  * Weibull shape not rejected (p >= .01).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.analysis.recovery import recovery_report  # noqa: E402
from toolobs.config import load_config  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, RUNS_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402
from toolobs.schemas import RecoveryEvent  # noqa: E402

RECOVERY_GATES = {"recovered_by_h4_min": 0.50, "weibull_shape_rejected_p_max": 0.01}


def _read_events(path: Path) -> list[RecoveryEvent]:
    if not path.exists():
        return []
    return [RecoveryEvent.from_dict(item) for item in _jsonl(path)]


def _jsonl(path: Path) -> list[dict[str, object]]:
    import json

    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _group_report(events: list[RecoveryEvent]) -> dict[str, object]:
    report = recovery_report(events)
    km = report["kaplan_meier"]
    survival_h4 = float(km[-1]["survival"]) if km else 0.0
    recovered = 1.0 - survival_h4
    weibull = report["weibull"]
    gates = {
        "recovered_by_h4": recovered
        >= RECOVERY_GATES["recovered_by_h4_min"] - 1e-9,
        "weibull_shape_not_rejected": float(weibull["p_value"])
        >= RECOVERY_GATES["weibull_shape_rejected_p_max"] - 1e-9,
    }
    report["recovered_by_h4"] = round(recovered, 6)
    report["survival_h4"] = round(survival_h4, 6)
    report["gates"] = gates
    report["passed"] = all(gates.values())
    return report


def _markdown(groups: dict[str, dict[str, object]]) -> str:
    lines = [
        "# G4 — Recovery report",
        "",
        f"Recorded: {utc_now()}",
        "",
        "Primary endpoint is the transient s=3 risk set. Recovery by H=4 is "
        "1 - Kaplan-Meier survival at step 4.",
        "",
        "| Group | n | Recovered by H=4 | KM survival H=4 | RMST | Exponential hazard | "
        "Weibull shape | Weibull p | Gate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name, report in groups.items():
        if report.get("missing"):
            lines.append(f"| {name} | 0 | — | — | — | — | — | — | no data |")
            continue
        exp = report["exponential"]
        weibull = report["weibull"]
        lines.append(
            f"| {name} | {report['n']} | {report['recovered_by_h4']:.1%} | "
            f"{report['survival_h4']:.1%} | {report['rmst']:.3f} | "
            f"{exp['hazard']:.4f} | {weibull['shape']:.2f} | {weibull['p_value']:.3g} | "
            f"{'PASS' if report['passed'] else 'FAIL'} |"
        )
    lines += [
        "",
        "Gates: ≥50% of the primary risk set recovers by H=4; Weibull shape not rejected "
        "(p ≥ .01). A failed gate is reported as a failed gate.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", nargs="*", default=None)
    parser.add_argument("--event-root", default=str(RUNS_DIR / "main" / "recovery"))
    parser.add_argument("--horizon", type=int, default=4)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    configured = [str(model["id"]) for model in load_config("models.yaml")["models"]]
    model_ids = args.models or configured
    event_root = resolve_repo_path(args.event_root)

    groups: dict[str, dict[str, object]] = {}
    for model_id in model_ids:
        transient = _read_events(event_root / model_id / "transient.jsonl")
        persistent = _read_events(event_root / model_id / "persistent.jsonl")
        for label, events, severity in (
            ("transient_s3", [e for e in transient if e.severity == 3], 3),
            ("transient_s2", [e for e in transient if e.severity == 2], 2),
            ("persistent_s3", [e for e in persistent if e.severity == 3], 3),
        ):
            if not events:
                groups[f"{model_id}|{label}"] = {"n": 0, "passed": False, "missing": True}
                continue
            report = _group_report(events)
            report["model_id"] = model_id
            report["regime"] = label
            report["severity"] = severity
            report["horizon"] = args.horizon
            groups[f"{model_id}|{label}"] = report

    primary = {
        name: report
        for name, report in groups.items()
        if name.endswith("transient_s3") and report.get("n", 0) > 0
    }
    overall_passed = bool(primary) and all(
        report.get("passed") for report in primary.values()
    )
    payload = {
        "stage": "g4_recovery",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "horizon": args.horizon,
        "gates": RECOVERY_GATES,
        "groups": groups,
        "primary_groups": sorted(primary),
        "primary_passed": overall_passed,
        "models": model_ids,
    }
    out_path = resolve_repo_path(
        args.out or (ARTIFACTS_DIR / "analysis" / "g4_recovery.json")
    )
    write_json(out_path, payload)
    markdown_path = out_path.with_suffix(".md")
    markdown_path.write_text(_markdown(groups), encoding="utf-8", newline="\n")

    for name, report in groups.items():
        print(f"[14_recovery] {name} n={report['n']} report={report.get('passed')}")
    print(f"[14_recovery] primary_passed {overall_passed}")
    print(f"[14_recovery] wrote {out_path} and {markdown_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
