"""Cross-file config contract tests."""

from __future__ import annotations

import pytest

yaml = pytest.importorskip("yaml")

from toolobs.config import (  # noqa: E402
    config_hash,
    config_hashes,
    load_all_configs,
    validate_configs,
)


def test_all_configs_load_and_validate() -> None:
    configs = load_all_configs()
    assert set(configs) == {
        "base.yaml",
        "models.yaml",
        "harvest.yaml",
        "arms.yaml",
        "field_registry.yaml",
        "calibration.yaml",
        "main.yaml",
        "analysis.yaml",
    }
    assert validate_configs(configs) == []


def test_config_hashes_are_stable() -> None:
    configs = load_all_configs()
    first = config_hashes(configs)
    second = config_hashes(configs)
    assert first == second
    assert all(len(value) == 64 for value in first.values())


def test_contract_catches_sample_size_drift() -> None:
    configs = load_all_configs()
    configs["harvest.yaml"]["harvest"]["sample_size"] = 879
    errors = validate_configs(configs)
    assert any("sample_size" in error for error in errors)


def test_contract_catches_generation_drift() -> None:
    configs = load_all_configs()
    configs["main.yaml"]["generation_budget"]["total"] = 34801
    errors = validate_configs(configs)
    assert any("generation_budget" in error for error in errors)


def test_ministral_uses_conservative_serving() -> None:
    configs = load_all_configs()
    models = {model["id"]: model for model in configs["models.yaml"]["models"]}
    model = models["ministral_3_8b_instruct_2512_awq"]
    assert model["enforce_eager"] is True
    assert model["max_num_seqs"] == 4
    assert model["max_num_batched_tokens"] == 4096
    assert model["chat_template_kwargs"] == {"reasoning_effort": "none"}


def test_llama_uses_conservative_serving() -> None:
    configs = load_all_configs()
    models = {model["id"]: model for model in configs["models.yaml"]["models"]}
    model = models["llama_3_1_8b_instruct_awq"]
    assert model["enforce_eager"] is True
    assert model["max_num_seqs"] == 4
    assert model["max_num_batched_tokens"] == 4096


def test_config_hash_changes_when_value_changes() -> None:
    configs = load_all_configs()
    before = config_hash(configs["main.yaml"])
    configs["main.yaml"]["budget"]["stop_at_gpu_hours"] = 44
    after = config_hash(configs["main.yaml"])
    assert before != after
