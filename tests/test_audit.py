"""Blind-audit statistics and stage-08c tests."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from toolobs.analysis.audit import (
    cohen_kappa,
    consensus_severity,
    fourway,
    jt_test,
    kripp_alpha,
    majority,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_cohen_kappa_known_cases() -> None:
    kappa, _ = cohen_kappa(["a", "b", "a", "b"], ["a", "b", "a", "b"])
    assert kappa == 1.0
    # r1 = A A B B, r2 = A B A B -> po = .5, pe = .5, kappa = 0
    kappa, detail = cohen_kappa(["A", "A", "B", "B"], ["A", "B", "A", "B"])
    assert abs(kappa) < 1e-12
    assert detail["po"] == 0.5
    assert detail["pe"] == 0.5


def test_krippendorff_alpha_known_cases() -> None:
    perfect = [[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3]]
    assert kripp_alpha(perfect, "nominal") == 1.0
    assert kripp_alpha(perfect, "interval") == 1.0
    # Two raters, units aa / ab / bb / bb: hand-computed coincidence-matrix
    # alpha (nominal) = 1 - .25 / .535714 = .533333.
    two_raters = [["a", "a"], ["a", "b"], ["b", "b"], ["b", "b"]]
    assert abs(kripp_alpha(two_raters, "nominal") - 0.533333) < 1e-5
    # All raters disagree on every unit -> alpha must not exceed 0.
    assert kripp_alpha([[0, 1, 2], [1, 2, 0], [2, 0, 1]], "nominal") <= 0


def test_jonckheere_terpstra() -> None:
    perfect = [[0] * 30, [1] * 30, [2] * 30, [3] * 30]
    report = jt_test(perfect, n_permutations=2000)
    assert report["J"] == 5400.0
    assert report["p_permutation_one_sided"] == 0.0
    assert report["z"] > 5

    constant = [[1] * 30, [1] * 30, [1] * 30, [1] * 30]
    report = jt_test(constant, n_permutations=200)
    assert abs(report["z"]) < 1e-9
    assert abs(report["p_asymptotic_one_sided"] - 0.5) < 1e-9
    assert report["p_permutation_one_sided"] == 1.0

    # For two groups the no-tie variance reduces to the Mann-Whitney variance.
    report = jt_test([[1, 2, 4], [3, 5, 6]], n_permutations=10)
    assert abs(report["expected_J"] - 4.5) < 1e-9
    assert abs(report["sd"] ** 2 - 5.25) < 1e-9


def test_majority_and_consensus() -> None:
    assert majority([0, 0, 1]) == 0
    assert majority([1, 1, 0]) == 1
    assert consensus_severity([2, 2, 3]) == 2
    assert consensus_severity([1, 2, 3]) == 2


def test_fourway_priority() -> None:
    assert fourway({"Y": "0", "YA": "0", "YF": "0", "YU": "0"}) == "N"
    assert fourway({"Y": "1", "YA": "1", "YF": "1", "YU": "0"}) == "YA"
    assert fourway({"Y": "1", "YA": "0", "YF": "1", "YU": "0"}) == "YF"
    assert fourway({"Y": "1", "YA": "0", "YF": "0", "YU": "1"}) == "YU"
    assert fourway({"Y": "1", "YA": "0", "YF": "0", "YU": "0"}) == "Y_other"


def _write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_blind_audit_score_end_to_end(tmp_path) -> None:
    audit_dir = tmp_path / "audit"
    blind_dir = audit_dir / "blind"
    jitter_dir = tmp_path / "analysis"
    blind_dir.mkdir(parents=True)
    jitter_dir.mkdir(parents=True)

    severity_items = []
    for level in range(4):
        for index in range(3):
            item_id = f"SEV-{len(severity_items) + 1:03d}"
            severity_items.append(
                {"item_id": item_id, "severity_level": str(level)}
            )
    with (blind_dir / "severity_items.jsonl").open("w", encoding="utf-8") as handle:
        for item in severity_items:
            handle.write(json.dumps(item) + "\n")
    for number in (1, 2, 3):
        rows = []
        for item in severity_items:
            level = int(item["severity_level"])
            rows.append(
                {
                    "item_id": item["item_id"],
                    "severity": str(level),
                    "decision_changing": "1" if level >= 2 else "0",
                    "absurd": "0",
                    "note": "",
                }
            )
        _write_csv(
            blind_dir / f"rater{number}_severity.csv",
            ["item_id", "severity", "decision_changing", "absurd", "note"],
            rows,
        )

    outcome_items = []
    outcome_labels = [
        ("0", "0", "0", "0"),
        ("1", "1", "0", "0"),
        ("1", "0", "1", "0"),
        ("1", "0", "0", "1"),
        ("0", "0", "0", "0"),
        ("0", "0", "0", "0"),
    ]
    for index, (y, ya, yf, yu) in enumerate(outcome_labels, start=1):
        outcome_items.append(
            {
                "item_id": f"OUT-{index:03d}",
                "arm": "s3",
                "automatic_Y": y,
                "automatic_YA": ya,
                "automatic_YF": yf,
                "automatic_YU": yu,
            }
        )
    with (blind_dir / "outcome_items.jsonl").open("w", encoding="utf-8") as handle:
        for item in outcome_items:
            handle.write(json.dumps(item) + "\n")
    for number in (1, 2):
        rows = []
        for item in outcome_items:
            rows.append(
                {
                    "item_id": item["item_id"],
                    "Y": item["automatic_Y"],
                    "YA": item["automatic_YA"],
                    "YF": item["automatic_YF"],
                    "YU": item["automatic_YU"],
                    "note": "",
                }
            )
        _write_csv(
            blind_dir / f"rater{number}_outcome.csv",
            ["item_id", "Y", "YA", "YF", "YU", "note"],
            rows,
        )

    recovery_items = [
        {"item_id": "REC-001", "automatic_recovered_step": "1", "automatic_endpoint": "R1"},
        {"item_id": "REC-002", "automatic_recovered_step": "", "automatic_endpoint": "censored"},
        {"item_id": "REC-003", "automatic_recovered_step": "3", "automatic_endpoint": "R2"},
    ]
    with (blind_dir / "recovery_items.jsonl").open("w", encoding="utf-8") as handle:
        for item in recovery_items:
            handle.write(json.dumps(item) + "\n")
    for number in (1, 2):
        rows = [
            {"item_id": "REC-001", "recovery_step": "1", "endpoint": "R1", "note": ""},
            {"item_id": "REC-002", "recovery_step": "4", "endpoint": "censored", "note": ""},
            {"item_id": "REC-003", "recovery_step": "3", "endpoint": "R2", "note": ""},
        ]
        _write_csv(
            blind_dir / f"rater{number}_recovery.csv",
            ["item_id", "recovery_step", "endpoint", "note"],
            rows,
        )

    (jitter_dir / "jitter_stability_m0.json").write_text(
        json.dumps({"rate": 0.95, "n": 100, "passed": True, "mode": "report_only"}),
        encoding="utf-8",
    )
    (audit_dir / "human_verification.json").write_text(
        json.dumps(
            {
                "verifier": "author",
                "provenance": "author check",
                "verdict": "accepted",
                "recorded_utc": "2026-11-18T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    script = REPO_ROOT / "scripts" / "08c_blind_audit_score.py"
    spec = importlib.util.spec_from_file_location("blind_audit_script", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    out = tmp_path / "result.json"
    result = module.main(
        [
            "--audit-dir",
            str(audit_dir),
            "--blind-dir",
            str(blind_dir),
            "--jitter-dir",
            str(jitter_dir),
            "--out",
            str(out),
        ]
    )
    assert result == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["severity"]["passed"] is True
    assert payload["outcome"]["passed"] is True
    assert payload["recovery"]["passed"] is True
    assert payload["human_verification"]["status"] == "verified"
    assert payload["human_verification"]["provenance"] == "author check"
    assert payload["outcome"]["silent_ppv"]["strict_both_raters"] == 1.0
    assert (audit_dir / "severity_audit_sheet.csv").exists()
    assert (audit_dir / "outcome_audit_sheet.csv").exists()
    assert (audit_dir / "recovery_audit_sheet.csv").exists()

    # Rater files with a suffix are read when requested (label-free round).
    import shutil

    for name in (
        "rater1_severity.csv",
        "rater2_severity.csv",
        "rater3_severity.csv",
        "rater1_outcome.csv",
        "rater2_outcome.csv",
        "rater1_recovery.csv",
        "rater2_recovery.csv",
    ):
        shutil.copy(blind_dir / name, blind_dir / name.replace(".csv", "_x.csv"))
    out_suffix = tmp_path / "result_suffix.json"
    result = module.main(
        [
            "--audit-dir",
            str(audit_dir),
            "--blind-dir",
            str(blind_dir),
            "--jitter-dir",
            str(jitter_dir),
            "--rater-suffix",
            "_x",
            "--out",
            str(out_suffix),
        ]
    )
    assert result == 0
    suffixed = json.loads(out_suffix.read_text(encoding="utf-8"))
    assert suffixed["outcome"]["passed"] is True

    # A superseded verification record must not be reported as verified.
    (audit_dir / "human_verification.json").write_text(
        json.dumps(
            {
                "verifier": "author",
                "verdict": "accepted",
                "status": "superseded",
                "superseded_note": "test",
            }
        ),
        encoding="utf-8",
    )
    out_pending = tmp_path / "result_pending.json"
    result = module.main(
        [
            "--audit-dir",
            str(audit_dir),
            "--blind-dir",
            str(blind_dir),
            "--jitter-dir",
            str(jitter_dir),
            "--out",
            str(out_pending),
        ]
    )
    assert result == 0
    pending = json.loads(out_pending.read_text(encoding="utf-8"))
    assert pending["human_verification"]["status"] == "pending"
