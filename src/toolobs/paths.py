"""Repository path resolution.

All paths are resolved relative to the repository root, never the current
working directory, so scripts behave the same from any shell.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CONFIG_DIR = REPO_ROOT / "configs"
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
UPSTREAM_DIR = DATA_DIR / "upstream"
INTERIM_DIR = DATA_DIR / "interim"
FROZEN_DIR = DATA_DIR / "frozen"
MANIFEST_DIR = DATA_DIR / "manifests"
RUNS_DIR = DATA_DIR / "runs"
ARTIFACTS_DIR = REPO_ROOT / "artifacts"
SCRIPTS_DIR = REPO_ROOT / "scripts"
PREREG_DIR = REPO_ROOT / "prereg"
PAPER_DIR = REPO_ROOT / "paper"
RELEASE_DIR = REPO_ROOT / "release"

REQUIRED_CONFIGS = (
    "base.yaml",
    "models.yaml",
    "harvest.yaml",
    "arms.yaml",
    "field_registry.yaml",
    "calibration.yaml",
    "main.yaml",
    "analysis.yaml",
)


def config_path(name: str) -> Path:
    """Return the path to a named config file."""
    return CONFIG_DIR / name


def require_repo_root() -> Path:
    """Return the repository root, raising if the layout is not recognisable."""
    if not (REPO_ROOT / "pyproject.toml").exists():
        raise RuntimeError(f"not a tool-observation checkout: {REPO_ROOT}")
    return REPO_ROOT


def ensure_local_dirs() -> None:
    """Create local-only data/artifact directories that are gitignored."""
    for path in (
        RAW_DIR,
        UPSTREAM_DIR,
        INTERIM_DIR,
        FROZEN_DIR,
        MANIFEST_DIR,
        RUNS_DIR,
        ARTIFACTS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
