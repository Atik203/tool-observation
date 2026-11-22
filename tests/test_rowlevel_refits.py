"""Tests for the stage-19 row-level refits (P6.3).

The heavy lifting is exercised on small synthetic fixtures; one smoke test
loads the real local ledgers when they are present and checks the row/label
counts.  No full analysis run is invoked here.
"""

from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from toolobs.analysis.slope import SlopeRow, conditional_logit

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "19_rowlevel_refits.py"
_spec = importlib.util.spec_from_file_location("rowlevel_refits_script", _SCRIPT)
assert _spec and _spec.loader
rowlevel = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = rowlevel
_spec.loader.exec_module(rowlevel)


def _synthetic_records(
    *, prefixes: int = 40, seed: int = 7, curvature: float = 0.0
) -> list[tuple[str, str, str, int, int]]:
    """A small severity fixture with a known generative pattern."""
    rng = random.Random(seed)
    records = []
    for index in range(prefixes):
        prefix = f"airline-donor-t{index:02d}-r01-s{index:03d}-task"
        model = "model-a"
        for severity in range(4):
            linear = 0.55 * severity + curvature * severity * severity - 1.2
            probability = 1.0 / (1.0 + math.exp(-linear))
            outcome = int(rng.random() < probability)
            records.append((prefix, model, f"s{severity}", severity, outcome))
    return records


def test_conditional_logit_matches_slope_module() -> None:
    records = _synthetic_records(prefixes=60, seed=11)
    groups = rowlevel.groups_from_records(records)
    fitted = rowlevel.fit_conditional(groups, rowlevel.LINEAR)

    slope_rows = [
        SlopeRow(
            group_id=f"{prefix}|{model}",
            cluster_id=prefix,
            model_id=model,
            severity=severity,
            y=outcome,
        )
        for prefix, model, _arm, severity, outcome in records
    ]
    reference = conditional_logit(slope_rows)
    assert abs(fitted["beta"][0] - reference.beta) < 1e-8
    assert abs(fitted["se_cluster"][0] - reference.se_cluster) < 1e-8
    assert fitted["n_groups"] == reference.n_groups
    assert fitted["n_rows"] == reference.n_rows


def test_conditional_logit_mle_matches_grid_search() -> None:
    # A single stratum with outcome pattern (0, 0, 1, 1) has a one-dimensional
    # conditional likelihood; compare the Newton solution with a brute grid.
    records = [
        ("p1", "m", "s0", 0, 0),
        ("p1", "m", "s1", 1, 1),
        ("p1", "m", "s2", 2, 0),
        ("p1", "m", "s3", 3, 1),
    ]
    groups = rowlevel.groups_from_records(records)
    fitted = rowlevel.fit_conditional(groups, rowlevel.LINEAR)

    def loglik(beta: float) -> float:
        group = groups[0]
        values = [beta * value for value in group.s]
        maximum = max(values)
        log_z = maximum + math.log(sum(math.exp(value - maximum) for value in values))
        return values[group.obs] - log_z

    grid = [(-5.0 + 10.0 * index / 20000.0) for index in range(20001)]
    best = max(grid, key=loglik)
    assert abs(fitted["beta"][0] - best) < 1e-3


def test_categorical_linearity_wald_rejects_curvature() -> None:
    linear_records = _synthetic_records(prefixes=90, seed=5, curvature=0.0)
    curved_records = _synthetic_records(prefixes=90, seed=5, curvature=0.35)

    def statistic(records):
        groups = rowlevel.groups_from_records(records)
        fitted = rowlevel.fit_conditional(groups, rowlevel.CATEGORICAL)
        return rowlevel.categorical_linearity_wald(fitted)["statistic"]

    assert statistic(curved_records) > statistic(linear_records)


def test_simulate_groups_preserves_event_count() -> None:
    records = _synthetic_records(prefixes=12, seed=3)
    groups = rowlevel.groups_from_records(records)
    rng = random.Random(4)
    simulated = rowlevel.simulate_groups(groups, beta=0.4, rng=rng)
    assert len(simulated) == len(groups)
    for original, copy in zip(groups, simulated, strict=True):
        assert sum(copy.y) == sum(original.y)
        assert copy.subsets[copy.obs] == tuple(
            index for index, value in enumerate(copy.y) if value
        )


def test_bootstrap_lrt_smoke_is_bounded() -> None:
    records = _synthetic_records(prefixes=25, seed=9)
    groups = rowlevel.groups_from_records(records)
    by_prefix = rowlevel.groups_by_prefix(
        groups, sorted({record[0] for record in records})
    )
    observed = rowlevel.fit_designs(groups)
    result = rowlevel.bootstrap_lrt(
        by_prefix, observed, reps=5, seed=12, label="fixture"
    )
    assert result["reps_requested"] == 5
    assert result["reps_valid"] >= 1
    for key in (
        "bootstrap_p_categorical_vs_linear",
        "bootstrap_p_quadratic_vs_linear",
    ):
        assert 0.0 <= result[key] <= 1.0


def test_mcnemar_exact_known_values() -> None:
    assert rowlevel.mcnemar_exact(0, 0) == 1.0
    assert abs(rowlevel.mcnemar_exact(5, 0) - 0.0625) < 1e-12
    assert rowlevel.mcnemar_exact(10, 10) == 1.0
    assert abs(rowlevel.mcnemar_exact(3, 8) - rowlevel.mcnemar_exact(8, 3)) < 1e-15


def _sequence(
    status: str, time: int, *, prefix: str = "p", reason: str = ""
) -> rowlevel.Sequence:
    return rowlevel.Sequence(
        prefix=prefix,
        model="m",
        regime="transient",
        severity=3,
        time=time,
        status=status,
        endpoint="R1" if status == "recovery" else "censored",
        reason=reason,
    )


def test_aalen_johansen_known_fixture() -> None:
    sequences = (
        [_sequence("recovery", 1, prefix=f"r1-{i}") for i in range(2)]
        + [_sequence("competing", 1, prefix="c1", reason="parse_fail")]
        + [_sequence("recovery", 2, prefix=f"r2-{i}") for i in range(3)]
        + [_sequence("censored", 2, prefix=f"z-{i}", reason="ran_to_H4") for i in range(4)]
    )
    rows = rowlevel.aalen_johansen(sequences)
    assert rows[0]["at_risk"] == 10
    assert rows[0]["recovery_events"] == 2
    assert rows[0]["competing_events"] == 1
    assert abs(rows[0]["cif_recovery"] - 0.2) < 1e-12
    assert abs(rows[0]["cif_competing"] - 0.1) < 1e-12
    assert rows[1]["at_risk"] == 7
    assert abs(rows[1]["cif_recovery"] - 0.5) < 1e-12
    assert abs(rows[-1]["cif_recovery"] - 0.5) < 1e-12


def test_aalen_johansen_equals_crude_with_horizon_only_censoring() -> None:
    sequences = (
        [_sequence("recovery", 1, prefix=f"r1-{i}") for i in range(2)]
        + [_sequence("recovery", 3, prefix=f"r3-{i}") for i in range(3)]
        + [_sequence("competing", 2, prefix=f"c-{i}", reason="final_answer") for i in range(3)]
        + [_sequence("censored", 4, prefix=f"z-{i}", reason="ran_to_H4") for i in range(12)]
    )
    result = rowlevel.aalen_johansen(sequences)[-1]
    assert abs(result["cif_recovery"] - 5 / 20) < 1e-12
    assert abs(result["cif_competing"] - 3 / 20) < 1e-12


def test_weighted_arm_rates_and_manski_known() -> None:
    cells = []
    for arm in ("s0", "s1", "s2", "s3"):
        for index in range(4):
            cells.append(
                {
                    "prefix": f"p{index}",
                    "model": "m",
                    "arm": arm,
                    "observed": index < 3,
                    "y": (1 if arm == "s3" and index < 2 else 0)
                    if index < 3
                    else None,
                    "reason": None if index < 3 else "arm_unparsed",
                    "domain": "airline",
                    "donor": "d",
                    "task": "t1",
                    "severity": rowlevel.SEVERITY[arm],
                }
            )
    weights = [1.0, 2.0, 1.0, 0.0]
    rates = rowlevel._weighted_arm_rates(cells, weights * 4)
    assert abs(rates["s3"]["rate"] - 0.75) < 1e-12
    assert abs(rates["s0"]["rate"] - 0.0) < 1e-12
    bounds = rowlevel._manski(cells)
    assert bounds["s3"]["lower"] == 2 / 4
    assert bounds["s3"]["upper"] == 3 / 4
    assert bounds["s0"]["lower"] == 0.0
    assert bounds["s0"]["upper"] == 1 / 4


def test_rubin_pool_known_values() -> None:
    draws = [
        ([1.0], [[0.04]]),
        ([3.0], [[0.04]]),
    ]
    pooled = rowlevel._rubin_pool(draws, ["beta"])
    # Qbar = 2, Ubar = .04, B = 2, T = .04 + 1.5 * 2 = 3.04.
    assert pooled[0]["name"] == "beta"
    assert abs(pooled[0]["beta"] - 2.0) < 1e-12
    assert abs(pooled[0]["within_var"] - 0.04) < 1e-12
    assert abs(pooled[0]["between_var"] - 2.0) < 1e-12
    assert abs(pooled[0]["se"] - math.sqrt(3.04)) < 1e-12


def _synthetic_inputs(
    prefixes: list[str],
    models: list[str],
    labels: list[SimpleNamespace],
    *,
    rows_by_key: dict[tuple[str, str, str], SimpleNamespace] | None = None,
) -> rowlevel.Inputs:
    label_by_key = {
        (label.prefix_id, label.model_id, label.arm): label for label in labels
    }
    return rowlevel.Inputs(
        models=models,
        prefixes=prefixes,
        reserve_ids=set(),
        rows=[],
        n_step0_rows=0,
        rows_by_key=rows_by_key or {},
        labels=labels,
        label_by_key=label_by_key,
        perturbations=[],
        files=[],
    )


def test_severity_reclassification_end_to_end_fixture(monkeypatch) -> None:
    prefixes = [f"airline-claude35sonnet-t{i:02d}-r01-s001-task" for i in range(24)]
    models = ["model-a"]
    labels = []
    for index, prefix in enumerate(prefixes):
        for arm in rowlevel.ARMS:
            outcome = int(arm in ("s2", "s3") and index % 3 == 0)
            labels.append(
                SimpleNamespace(
                    prefix_id=prefix,
                    model_id="model-a",
                    arm=arm,
                    y_any=bool(outcome),
                )
            )
    inputs = _synthetic_inputs(prefixes, models, labels)
    audit = {
        "levels": {"I1": "2", "I2": "3"},
        "prefix_by_item": {"I1": prefixes[0], "I2": prefixes[1]},
        "passes": {
            "majority": {
                "items": ["I1", "I2"],
                "k": 2,
                "n": 2,
                "by_arm": {"s2": 1, "s3": 1},
                "combos": [(prefixes[0], "s2"), (prefixes[1], "s3")],
            }
        },
        "files": [],
    }
    monkeypatch.setattr(rowlevel, "_load_severity_passes", lambda: audit)

    report = rowlevel.severity_reclassification(inputs, imputations=2, seed=7)
    assert report["audited_items"] == 2
    assert report["audited_main"] == 2
    assert report["audited_reserve"] == 0
    assert report["unaudited_combos"] == len(prefixes) * 2 - 2
    payload = report["passes"]["majority"]
    assert payload["audited_only"]["inactive_rows"] == 2
    assert len(payload["audited_only"]["realized"]["coefficients"]) == 3
    assert set(payload["audited_only"]["arm_specific"]) == {"s2", "s3"}
    assert "converged" in payload["audited_only"]["realized"]
    assert "separated" in payload["audited_only"]["realized"]["inactive_critical"]
    assert len(payload["extrapolated"]["realized"]["coefficients"]) == 3
    assert payload["extrapolated"]["mi_converged"] >= 1


def test_missingness_end_to_end_fixture() -> None:
    prefixes = [
        "airline-claude35sonnet-t01-r01-s001-task",
        "airline-claude35sonnet-t02-r01-s001-task",
        "airline-claude35sonnet-t03-r01-s001-task",
        "airline-claude35sonnet-t04-r01-s001-task",
        "retail-gpt4o-t10-r01-s001-task",
        "retail-gpt4o-t11-r01-s001-task",
        "retail-gpt4o-t12-r01-s001-task",
        "retail-gpt4o-t13-r01-s001-task",
    ]
    labels = []
    rows_by_key: dict[tuple[str, str, str], SimpleNamespace] = {}
    for index, prefix in enumerate(prefixes):
        reference = SimpleNamespace(parsed=index != 1, decision_json="{}")
        rows_by_key[(prefix, "model-a", "V")] = reference
        for arm in rowlevel.ARMS:
            parsed = not (index == 2 and arm == "s1")
            rows_by_key[(prefix, "model-a", arm)] = SimpleNamespace(
                parsed=parsed, decision_json="{}"
            )
            observed = index != 1 and parsed
            if observed:
                outcome = int(arm in ("s2", "s3") and index % 2 == 0)
                labels.append(
                    SimpleNamespace(
                        prefix_id=prefix,
                        model_id="model-a",
                        arm=arm,
                        y_any=bool(outcome),
                    )
                )
    inputs = _synthetic_inputs(prefixes, ["model-a"], labels, rows_by_key=rows_by_key)
    report = rowlevel.missingness(
        inputs, rate_bootstrap=5, slope_bootstrap=3, seed=7
    )
    assert report["cells"]["potential"] == len(prefixes) * 4
    assert report["cells"]["missing"] == 5
    assert report["cells"]["reasons"] == {"v_unparsed": 4, "arm_unparsed": 1}
    assert report["ipw"]["rates"]["s3"]["rate"] is not None
    assert report["manski"]["design_robust"] is True
    assert report["slope"]["ipw"]["bootstrap_reps"] >= 1


def test_aalen_johansen_differs_from_crude_with_early_censoring() -> None:
    sequences = (
        [_sequence("recovery", 1, prefix=f"r1-{i}") for i in range(2)]
        + [_sequence("censored", 1, prefix=f"z1-{i}", reason="ran_to_H4") for i in range(2)]
        + [_sequence("recovery", 2, prefix=f"r2-{i}") for i in range(3)]
        + [_sequence("competing", 2, prefix=f"c2-{i}", reason="final_answer") for i in range(3)]
    )
    result = rowlevel.aalen_johansen(sequences)[-1]
    crude = 5 / 10
    assert abs(result["cif_recovery"] - 0.60) < 1e-12
    assert abs(result["cif_recovery"] - crude) > 0.09
    assert abs(result["cif_competing"] - 0.40) < 1e-12


def test_severity_pass_counts_real_audit() -> None:
    audit_dir = Path(__file__).resolve().parents[1] / "artifacts" / "audit"
    required = [
        audit_dir / "blind" / "severity_items.jsonl",
        audit_dir / "severity_audit_sheet.csv",
        audit_dir / "verification" / "severity_verification.csv",
        audit_dir / "verification" / "severity_verification_slices.csv",
    ]
    if not all(path.exists() for path in required):
        pytest.skip("severity audit sheets not present")
    passes = rowlevel._load_severity_passes()
    assert passes["passes"]["majority"]["k"] == 7
    assert passes["passes"]["sheet_visible_verifier"]["k"] == 11
    assert passes["passes"]["blind_verifier"]["k"] == 16


def test_real_ledger_smoke_counts() -> None:
    runs = Path(__file__).resolve().parents[1] / "data" / "runs" / "main"
    if not runs.exists():
        pytest.skip("local run ledgers not present")
    inputs = rowlevel.load_inputs()
    assert inputs.n_step0_rows == 13200
    assert len(inputs.rows) == 12000
    assert len(inputs.labels) == 9075
    assert len({label.prefix_id for label in inputs.labels}) == 800
    counts = {arm: 0 for arm in rowlevel.ARMS}
    for label in inputs.labels:
        counts[label.arm] += 1
    assert counts == {"s0": 2274, "s1": 2267, "s2": 2267, "s3": 2267}
    cells = rowlevel.build_cells(inputs)
    assert len(cells) == 9600
    assert sum(1 for cell in cells if not cell["observed"]) == 525


def test_artifact_hashes_if_present() -> None:
    artifact = (
        Path(__file__).resolve().parents[1]
        / "artifacts"
        / "analysis"
        / "rowlevel_refits.json"
    )
    if not artifact.exists():
        pytest.skip("rowlevel artifact not generated on this checkout")
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    files = payload["inputs"]["files"]
    assert files
    assert len({item["path"] for item in files}) == len(files)
    for item in files:
        assert len(item["sha256"]) == 64
        assert int(item["sha256"], 16) >= 0
        assert item["bytes"] > 0
