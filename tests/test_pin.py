"""Pin contract tests on a temporary fake checkout."""

from __future__ import annotations

from pathlib import Path

import pytest

from toolobs.taubench.pin import (
    PinError,
    compute_pin,
    harness_digest,
    harness_hashes,
    load_pin,
    update_config_pin,
    verify_pin,
    write_pin,
)

TRAJECTORY = "historical_trajectories/gpt-4o-airline.json"

TASK_FILES = (
    "tau_bench/envs/airline/data/flights.json",
    "tau_bench/envs/airline/data/reservations.json",
    "tau_bench/envs/airline/data/users.json",
    "tau_bench/envs/retail/data/orders.json",
    "tau_bench/envs/retail/data/products.json",
    "tau_bench/envs/retail/data/users.json",
)

HARNESS_FILES = (
    "tau_bench/envs/airline/env.py",
    "tau_bench/envs/airline/tools/get_order_details.py",
    "tau_bench/envs/retail/env.py",
    "tau_bench/types.py",
)


def _checkout(root: Path) -> Path:
    for relative in (TRAJECTORY, *TASK_FILES, *HARNESS_FILES):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"payload:{relative}\n", encoding="utf-8")
    return root


def test_compute_and_verify_pin(tmp_path: Path) -> None:
    _checkout(tmp_path)
    pin = compute_pin(
        tmp_path,
        repo_url="https://example.invalid/tau-bench",
        trajectory_files=(TRAJECTORY,),
        commit_sha="a" * 40,
        require_clean=False,
    )
    assert pin.commit_sha == "a" * 40
    assert set(pin.trajectory_hashes) == {TRAJECTORY}
    assert len(pin.task_db_hashes) == 6
    assert len(pin.harness_hash) == 64
    assert verify_pin(pin, tmp_path) == []


def test_verify_pin_detects_file_change(tmp_path: Path) -> None:
    _checkout(tmp_path)
    pin = compute_pin(
        tmp_path,
        repo_url="https://example.invalid/tau-bench",
        trajectory_files=(TRAJECTORY,),
        commit_sha="a" * 40,
        require_clean=False,
    )
    (tmp_path / TRAJECTORY).write_text("changed\n", encoding="utf-8")
    problems = verify_pin(pin, tmp_path)
    assert any("trajectory hash mismatch" in problem for problem in problems)


def test_harness_hash_is_order_independent(tmp_path: Path) -> None:
    _checkout(tmp_path)
    hashes = harness_hashes(tmp_path)
    assert list(hashes) == sorted(hashes)
    assert harness_digest(hashes) == harness_digest(dict(reversed(list(hashes.items()))))


def test_pin_round_trip(tmp_path: Path) -> None:
    _checkout(tmp_path)
    pin = compute_pin(
        tmp_path,
        repo_url="https://example.invalid/tau-bench",
        trajectory_files=(TRAJECTORY,),
        commit_sha="a" * 40,
        require_clean=False,
    )
    path = write_pin(pin, tmp_path / "PIN.json")
    restored = load_pin(path)
    assert restored == pin


def test_missing_task_database_is_an_error(tmp_path: Path) -> None:
    _checkout(tmp_path)
    (tmp_path / TASK_FILES[0]).unlink()
    with pytest.raises(PinError):
        compute_pin(
            tmp_path,
            repo_url="https://example.invalid/tau-bench",
            trajectory_files=(TRAJECTORY,),
            commit_sha="a" * 40,
            require_clean=False,
        )


def test_update_config_pin_preserves_comments(tmp_path: Path) -> None:
    path = tmp_path / "harvest.yaml"
    path.write_text(
        "# header\nsource:\n  pin: TBD  # pinned on day 1\n  name: tau-bench\n",
        encoding="utf-8",
    )
    update_config_pin(path, "b" * 40)
    text = path.read_text(encoding="utf-8")
    assert f"pin: {'b' * 40}  # pinned on day 1" in text
    assert "# header" in text
