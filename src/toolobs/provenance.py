"""Provenance helpers for artifacts and freeze checks.

Every reported number must trace to a ledger or manifest row. These helpers
attach the commit, config hashes, and file hash to an artifact record.
"""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .hashing import sha256_file, sha256_text
from .paths import REPO_ROOT, RUNS_DIR


def git_commit(root: Path = REPO_ROOT) -> str:
    """Return the current git commit, or ``unknown`` outside a checkout."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and value else "unknown"


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def repo_relative(path: str | Path) -> str:
    """Return a POSIX path relative to the repository when possible."""
    candidate = Path(path).resolve()
    try:
        return candidate.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return candidate.as_posix()


def artifact_record(
    path: str | Path,
    *,
    config_hashes: dict[str, str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a provenance record for one artifact file."""
    artifact = Path(path)
    record: dict[str, Any] = {
        "path": repo_relative(artifact),
        "sha256": sha256_file(artifact),
        "bytes": artifact.stat().st_size,
        "git_commit": git_commit(),
        "config_hashes": config_hashes or {},
        "recorded_utc": utc_now(),
    }
    if extra:
        record.update(extra)
    return record


def write_json(path: str | Path, data: Any) -> Path:
    """Write deterministic JSON to a path, creating parents."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return target


def manifest_sidecar(manifest_path: str | Path) -> dict[str, Any]:
    """Return the sidecar record for a frozen manifest.

    A manifest cannot contain its own hash; the sidecar is the authoritative
    freeze record.
    """
    manifest = Path(manifest_path)
    return {
        "manifest_path": repo_relative(manifest),
        "manifest_sha256": sha256_file(manifest),
        "manifest_bytes": manifest.stat().st_size,
        "git_commit": git_commit(),
        "recorded_utc": utc_now(),
    }


def target_output_ledgers() -> list[Path]:
    """Return any target-model ledger files that would invalidate a freeze."""
    return sorted(RUNS_DIR.glob("**/ledger.jsonl"))


def assert_no_target_outputs() -> None:
    """Raise if target-model output exists before the G0 freeze."""
    ledgers = target_output_ledgers()
    if ledgers:
        paths = ", ".join(repo_relative(path) for path in ledgers)
        raise RuntimeError(f"target-model output exists before freeze: {paths}")


def hash_text_file(path: str | Path) -> str:
    """Hash a text file with newline normalization."""
    return sha256_text(Path(path).read_text(encoding="utf-8"))
