"""Pin the τ-bench upstream source, task databases, and harness.

The pin is the provenance root for G0. It records the commit SHA, hashes of
the four historical trajectory files, hashes of the task databases used by
replay, and a digest of the environment/tool harness code. A later mismatch is
a hard error, not a warning.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from ..hashing import sha256_record, sha256_text_file
from ..provenance import git_commit, utc_now, write_json
from ..schemas import PinRecord

TRAJECTORY_FILES: tuple[str, ...] = (
    "historical_trajectories/gpt-4o-airline.json",
    "historical_trajectories/gpt-4o-retail.json",
    "historical_trajectories/sonnet-35-new-airline.json",
    "historical_trajectories/sonnet-35-new-retail.json",
)

TASK_DB_FILES: dict[str, tuple[str, ...]] = {
    "airline": (
        "tau_bench/envs/airline/data/flights.json",
        "tau_bench/envs/airline/data/reservations.json",
        "tau_bench/envs/airline/data/users.json",
    ),
    "retail": (
        "tau_bench/envs/retail/data/orders.json",
        "tau_bench/envs/retail/data/products.json",
        "tau_bench/envs/retail/data/users.json",
    ),
}

HARNESS_GLOBS: tuple[str, ...] = (
    "tau_bench/envs/**/*.py",
    "tau_bench/types.py",
)

DEFAULT_LICENSE = "MIT"


class PinError(RuntimeError):
    """Raised when the upstream source cannot be pinned or does not verify."""


def git_dirty(root: str | Path) -> list[str]:
    """Return modified or untracked paths in a git checkout."""
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=Path(root),
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if completed.returncode != 0:
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


def trajectory_hashes(root: str | Path, files: tuple[str, ...] = TRAJECTORY_FILES) -> dict[str, str]:
    """Hash every pinned trajectory file by repository-relative path."""
    base = Path(root)
    hashes: dict[str, str] = {}
    for relative in files:
        path = base / relative
        if not path.is_file():
            raise PinError(f"missing trajectory file: {relative}")
        hashes[relative] = sha256_text_file(path)
    return hashes


def task_db_hashes(
    root: str | Path,
    files: dict[str, tuple[str, ...]] = TASK_DB_FILES,
) -> dict[str, str]:
    """Hash every task-database file used by replay."""
    base = Path(root)
    hashes: dict[str, str] = {}
    for domain, relatives in files.items():
        for relative in relatives:
            path = base / relative
            if not path.is_file():
                raise PinError(f"missing task database for {domain}: {relative}")
            hashes[relative] = sha256_text_file(path)
    return hashes


def harness_hashes(root: str | Path, globs: tuple[str, ...] = HARNESS_GLOBS) -> dict[str, str]:
    """Hash the harness source files that define tool and environment behavior."""
    base = Path(root)
    hashes: dict[str, str] = {}
    for pattern in globs:
        for path in base.glob(pattern):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            relative = path.relative_to(base).as_posix()
            hashes[relative] = sha256_text_file(path)
    if not hashes:
        raise PinError("harness hash set is empty")
    return dict(sorted(hashes.items()))


def harness_digest(hashes: dict[str, str]) -> str:
    """Combine per-file harness hashes into one stable digest."""
    return sha256_record(hashes)


def compute_pin(
    upstream_dir: str | Path,
    *,
    repo_url: str,
    trajectory_files: tuple[str, ...] = TRAJECTORY_FILES,
    commit_sha: str | None = None,
    license_name: str = DEFAULT_LICENSE,
    require_clean: bool = True,
    pinned_utc: str | None = None,
) -> PinRecord:
    """Build a source pin for a local τ-bench checkout."""
    root = Path(upstream_dir)
    if not root.is_dir():
        raise PinError(f"upstream checkout not found: {root}")

    if commit_sha is None:
        commit_sha = git_commit(root)
        if commit_sha == "unknown":
            raise PinError("could not resolve the upstream commit SHA")
    if require_clean:
        dirty = git_dirty(root)
        if dirty:
            joined = ", ".join(dirty[:5])
            raise PinError(f"upstream checkout is dirty: {joined}")

    trajectories = trajectory_hashes(root, trajectory_files)
    databases = task_db_hashes(root)
    harness = harness_hashes(root)
    return PinRecord(
        repo_url=repo_url,
        commit_sha=commit_sha,
        license=license_name,
        trajectory_hashes=trajectories,
        task_db_hashes=databases,
        harness_hash=harness_digest(harness),
        pinned_utc=pinned_utc or utc_now(),
    )


def verify_pin(
    record: PinRecord,
    upstream_dir: str | Path,
    *,
    check_commit: bool = True,
) -> list[str]:
    """Return every mismatch between a pin and a local checkout."""
    root = Path(upstream_dir)
    problems: list[str] = []

    if check_commit:
        actual_commit = git_commit(root)
        if actual_commit != "unknown" and actual_commit != record.commit_sha:
            problems.append(f"commit: expected {record.commit_sha}, got {actual_commit}")

    for relative, expected in record.trajectory_hashes.items():
        path = root / relative
        if not path.is_file():
            problems.append(f"missing trajectory: {relative}")
        elif sha256_text_file(path) != expected:
            problems.append(f"trajectory hash mismatch: {relative}")

    for relative, expected in record.task_db_hashes.items():
        path = root / relative
        if not path.is_file():
            problems.append(f"missing task database: {relative}")
        elif sha256_text_file(path) != expected:
            problems.append(f"task database hash mismatch: {relative}")

    try:
        actual_harness = harness_digest(harness_hashes(root))
    except PinError as exc:
        problems.append(str(exc))
    else:
        if actual_harness != record.harness_hash:
            problems.append("harness hash mismatch")

    return problems


def assert_pin_matches(record: PinRecord, upstream_dir: str | Path) -> None:
    """Raise PinError if a checkout does not match its pin."""
    problems = verify_pin(record, upstream_dir)
    if problems:
        raise PinError("; ".join(problems))


def write_pin(record: PinRecord, path: str | Path) -> Path:
    """Write a pin as deterministic JSON."""
    return write_json(path, record.to_dict())


def load_pin(path: str | Path) -> PinRecord:
    """Load a pin record from JSON."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PinError(f"pin must be a JSON object: {path}")
    return PinRecord.from_dict(payload)


def update_config_pin(config_path: str | Path, commit_sha: str) -> None:
    """Replace the single ``pin:`` value in a config, preserving comments."""
    path = Path(config_path)
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(r"^(\s*pin:\s*)(\S+)(.*)$", re.MULTILINE)
    if len(pattern.findall(text)) != 1:
        raise PinError(f"expected exactly one pin line in {path}")

    def replacement(match: re.Match[str]) -> str:
        return f"{match.group(1)}{commit_sha}{match.group(3)}"

    path.write_text(pattern.sub(replacement, text, count=1), encoding="utf-8")
