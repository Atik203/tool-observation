"""Path and CLI smoke tests."""

from __future__ import annotations

import pytest

from toolobs.cli import main
from toolobs.paths import CONFIG_DIR, REPO_ROOT, config_path, require_repo_root


def test_repo_root_is_a_checkout() -> None:
    assert require_repo_root() == REPO_ROOT
    assert (REPO_ROOT / "pyproject.toml").is_file()


def test_config_path_exists() -> None:
    assert config_path("base.yaml").is_file()
    assert config_path("base.yaml").parent == CONFIG_DIR


def test_version_exits_cleanly() -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0


def test_validate_exits_zero() -> None:
    assert main(["validate"]) == 0
