"""Field registry shape checks."""

from __future__ import annotations

import pytest

yaml = pytest.importorskip("yaml")

from toolobs.config import load_config  # noqa: E402


def test_registry_has_both_domains() -> None:
    registry = load_config("field_registry.yaml")
    assert set(registry["domains"]) == {"airline", "retail"}


def test_each_tool_entry_has_lists() -> None:
    registry = load_config("field_registry.yaml")
    for domain, payload in registry["domains"].items():
        assert payload["tools"], f"{domain} has no tools"
        for tool_name, tool in payload["tools"].items():
            for key in ("critical", "noncritical", "pii"):
                assert isinstance(tool.get(key, []), list), f"{domain}/{tool_name}/{key}"


def test_critical_field_names_are_unique_per_tool() -> None:
    registry = load_config("field_registry.yaml")
    for domain, payload in registry["domains"].items():
        for tool_name, tool in payload["tools"].items():
            names = [row["field"] for row in tool.get("critical", [])]
            assert len(names) == len(set(names)), f"duplicate critical field in {domain}/{tool_name}"
