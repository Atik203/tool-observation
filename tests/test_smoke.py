"""Smoke tests: these must pass with only the standard library installed.

CI installs the package with ``--no-deps`` and runs pytest, so this module must
not import numpy, pandas, yaml, torch, or any other heavy dependency.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import toolobs  # noqa: E402
from toolobs.paths import CONFIG_DIR, REQUIRED_CONFIGS  # noqa: E402


def test_version() -> None:
    assert toolobs.__version__ == "0.1.0"
    assert isinstance(toolobs.__version__, str)


def test_required_configs_exist() -> None:
    missing = [name for name in REQUIRED_CONFIGS if not (CONFIG_DIR / name).is_file()]
    assert not missing, f"missing configs: {missing}"
    for name in REQUIRED_CONFIGS:
        assert (CONFIG_DIR / name).stat().st_size > 0, f"empty config: {name}"
