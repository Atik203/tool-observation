"""Typed config loading and cross-file contract checks.

PyYAML is imported lazily so the package keeps a stdlib-only import surface.
"""

from __future__ import annotations

from typing import Any

from .hashing import sha256_record
from .paths import CONFIG_DIR, REQUIRED_CONFIGS


class ConfigError(ValueError):
    """Raised when a config is missing, unreadable, or inconsistent."""


def _yaml():
    try:
        import yaml  # noqa: PLC0415 - lazy by design
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ConfigError("PyYAML is required to load configs") from exc
    return yaml


def load_config(name: str) -> dict[str, Any]:
    """Load one required config by filename."""
    if name not in REQUIRED_CONFIGS:
        raise ConfigError(f"unknown config: {name}")
    path = CONFIG_DIR / name
    if not path.is_file():
        raise ConfigError(f"missing config: {path}")
    loaded = _yaml().safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ConfigError(f"config must be a mapping: {name}")
    return loaded


def load_all_configs() -> dict[str, dict[str, Any]]:
    """Load every required config."""
    return {name: load_config(name) for name in REQUIRED_CONFIGS}


def config_hash(config: dict[str, Any]) -> str:
    """Stable hash of a config mapping."""
    return sha256_record(config)


def config_hashes(configs: dict[str, dict[str, Any]] | None = None) -> dict[str, str]:
    """Return a hash per required config file."""
    data = configs if configs is not None else load_all_configs()
    return {name: config_hash(data[name]) for name in REQUIRED_CONFIGS}


def _get(mapping: dict[str, Any], path: str, default: Any = None) -> Any:
    current: Any = mapping
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def validate_configs(configs: dict[str, dict[str, Any]] | None = None) -> list[str]:
    """Return contract violations; an empty list means the configs are consistent."""
    data = configs if configs is not None else load_all_configs()
    errors: list[str] = []

    harvest = data["harvest.yaml"]
    main = data["main.yaml"]
    calibration = data["calibration.yaml"]
    models = data["models.yaml"]
    arms = data["arms.yaml"]
    base = data["base.yaml"]
    analysis = data["analysis.yaml"]

    # Sample and domain balance.
    sample_size = _get(harvest, "harvest.sample_size")
    freeze_size = _get(harvest, "harvest.freeze_size")
    reserve_size = _get(harvest, "harvest.reserve_size")
    airline = _get(harvest, "harvest.domain_target.airline")
    retail = _get(harvest, "harvest.domain_target.retail")
    if sample_size != 880:
        errors.append(f"harvest.sample_size must be 880, got {sample_size!r}")
    if freeze_size != 800:
        errors.append(f"harvest.freeze_size must be 800, got {freeze_size!r}")
    if reserve_size != 80:
        errors.append(f"harvest.reserve_size must be 80, got {reserve_size!r}")
    if (airline, retail) != (400, 400):
        errors.append(f"harvest domain target must be 400/400, got {airline!r}/{retail!r}")

    # Main run envelope.
    total = _get(main, "generation_budget.total")
    components = [
        _get(main, "generation_budget.base"),
        _get(main, "generation_budget.recovery_transient"),
        _get(main, "generation_budget.recovery_persistent"),
        _get(main, "generation_budget.jitter_repeats"),
    ]
    if total != 34800:
        errors.append(f"main generation_budget.total must be 34800, got {total!r}")
    if all(isinstance(value, int) for value in components) and sum(components) != total:
        errors.append(f"generation_budget components sum to {sum(components)}, not {total}")

    # Calibration.
    if _get(calibration, "calibration.n_prefixes") != 60:
        errors.append("calibration.n_prefixes must be 60")
    if _get(calibration, "calibration.models") != 3:
        errors.append("calibration.models must be 3")
    if _get(calibration, "calibration.arms") != 5:
        errors.append("calibration.arms must be 5")
    if _get(calibration, "calibration.generations") != 900:
        errors.append("calibration.generations must be 900")

    # Models and arms.
    model_rows = models.get("models") or []
    if len(model_rows) != 3:
        errors.append(f"models.yaml must define 3 models, got {len(model_rows)}")
    model_ids = [row.get("id") for row in model_rows if isinstance(row, dict)]
    if len(set(model_ids)) != len(model_ids):
        errors.append("model ids must be unique")
    arm_rows = arms.get("arms") or []
    arm_ids = [row.get("id") for row in arm_rows if isinstance(row, dict)]
    if arm_ids != ["V", "s0", "s1", "s2", "s3"]:
        errors.append(f"arms.yaml ids must be V,s0,s1,s2,s3; got {arm_ids!r}")

    # Budget / compute contract.
    if _get(main, "budget.base_usd") != 0:
        errors.append("main.budget.base_usd must be 0 (university H200)")
    if _get(main, "budget.hard_cap_usd") != 0:
        errors.append("main.budget.hard_cap_usd must be 0")
    if _get(main, "budget.stop_at_spend_usd") != 0:
        errors.append("main.budget.stop_at_spend_usd must be 0")
    if _get(main, "budget.stop_at_gpu_hours") != 45:
        errors.append("main.budget.stop_at_gpu_hours must be 45")
    if _get(main, "budget.storage_cap_gb") != 200:
        errors.append("main.budget.storage_cap_gb must be 200")

    # Seed parity.
    seeds = {
        "base": _get(base, "project.seed"),
        "harvest": _get(harvest, "harvest.random_seed"),
        "calibration": _get(calibration, "calibration.seed"),
        "main": _get(main, "run.seed"),
        "analysis": _get(analysis, "analysis.seed"),
    }
    if len(set(seeds.values())) != 1:
        errors.append(f"seed mismatch across configs: {seeds!r}")

    # Primary analysis contract.
    if _get(analysis, "analysis.primary_estimand") != "pooled_slope":
        errors.append("analysis.primary_estimand must be pooled_slope")

    return errors


def require_valid_configs(configs: dict[str, dict[str, Any]] | None = None) -> None:
    """Raise ConfigError if any contract check fails."""
    errors = validate_configs(configs)
    if errors:
        raise ConfigError("; ".join(errors))
