"""Command-line entry point for toolobs.

Import-time rule: standard library only. YAML is imported lazily inside
``validate`` so the package can be imported on a machine with no scientific
dependencies (including the minimal CI job).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .paths import CONFIG_DIR, REQUIRED_CONFIGS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="toolobs",
        description="Tool-result study (ToolResult-800) utilities.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"toolobs {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    validate = subparsers.add_parser(
        "validate",
        help="check that required config files exist and parse",
        description=(
            "Check the required YAML configs. Existence is always checked; YAML "
            "parsing is performed only when PyYAML is installed."
        ),
    )
    validate.add_argument(
        "--strict",
        action="store_true",
        help="treat a missing PyYAML installation as a failure",
    )
    return parser


def _validate(strict: bool = False) -> int:
    print(f"toolobs {__version__}")
    print(f"config directory: {CONFIG_DIR}")

    missing: list[str] = []
    for name in REQUIRED_CONFIGS:
        if not (CONFIG_DIR / name).is_file():
            missing.append(name)

    if missing:
        print(f"missing config files ({len(missing)}):")
        for name in missing:
            print(f"  - {name}")
        return 1

    print(f"required config files present: {len(REQUIRED_CONFIGS)}/{len(REQUIRED_CONFIGS)}")

    try:
        import yaml  # noqa: PLC0415 — lazy by design
    except ImportError:
        message = "PyYAML not installed; skipped YAML parsing (existence check only)."
        if strict:
            print(f"ERROR: {message}")
            return 1
        print(f"note: {message}")
        return 0

    invalid: list[tuple[str, str]] = []
    for name in REQUIRED_CONFIGS:
        path = CONFIG_DIR / name
        try:
            with path.open("r", encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            invalid.append((name, str(exc).splitlines()[0]))
            continue
        if loaded is None:
            invalid.append((name, "empty document"))

    if invalid:
        print(f"invalid YAML ({len(invalid)}):")
        for name, reason in invalid:
            print(f"  - {name}: {reason}")
        return 1

    print(f"valid YAML: {len(REQUIRED_CONFIGS)}/{len(REQUIRED_CONFIGS)}")
    print("validation OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        return _validate(strict=args.strict)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
