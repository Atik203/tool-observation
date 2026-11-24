"""Skip helpers for the bare-CI environment.

CI installs the package with ``--no-deps`` and runs ``pytest`` with only the
stdlib (plus pytest) available; generated inputs (``data/runs/``,
``artifacts/analysis/*.json``, ``release/``) are gitignored and absent from a
fresh clone. Tests that need either must skip instead of failing — the repo
must import and run ``pytest`` without numpy, pandas, yaml, torch, or vLLM
(see AGENTS.md). Locally, where everything is present, nothing skips.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _have(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


requires_yaml = pytest.mark.skipif(
    not _have("yaml"),
    reason="pyyaml not installed (bare CI env; scripts need it to read configs/)",
)

requires_matplotlib = pytest.mark.skipif(
    not _have("matplotlib"),
    reason="matplotlib not installed (bare CI env; figure scripts need it)",
)


def requires_files(*relpaths: str):
    """Skip when any repo-relative input path is absent from this checkout."""
    missing = [p for p in relpaths if not (REPO_ROOT / p).exists()]
    return pytest.mark.skipif(
        bool(missing),
        reason="generated inputs absent in this checkout: " + ", ".join(missing),
    )
