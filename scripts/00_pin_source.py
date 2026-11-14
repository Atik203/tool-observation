#!/usr/bin/env python
"""Stage 00 — pin the upstream τ-bench source.

Input:  configs/harvest.yaml (source.repository, source.pin)
Output: data/upstream/PIN.json and data/manifests/source_pin.json

GATE: pin resolves and all four trajectory files, task databases, and harness
files hash-match. The pin contains no PII.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import load_config  # noqa: E402
from toolobs.paths import CONFIG_DIR, MANIFEST_DIR, UPSTREAM_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import utc_now  # noqa: E402
from toolobs.taubench.pin import (  # noqa: E402
    PinError,
    compute_pin,
    load_pin,
    update_config_pin,
    verify_pin,
    write_pin,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", default="configs/harvest.yaml")
    parser.add_argument("--upstream", default=str(UPSTREAM_DIR / "tau-bench"))
    parser.add_argument("--out", default=str(UPSTREAM_DIR / "PIN.json"))
    parser.add_argument("--manifest-out", default=str(MANIFEST_DIR / "source_pin.json"))
    parser.add_argument("--update-config", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args(argv)

    config = load_config(Path(args.config).name)
    source = config["source"]
    upstream = resolve_repo_path(args.upstream)
    out = resolve_repo_path(args.out)
    manifest_out = resolve_repo_path(args.manifest_out)

    try:
        existing_path = manifest_out if manifest_out.is_file() else out
        existing = load_pin(existing_path) if existing_path.is_file() else None
    except (OSError, ValueError, PinError):
        existing = None
    try:
        pin = compute_pin(
            upstream,
            repo_url=source["repository"],
            trajectory_files=tuple(source["trajectory_files"]),
            license_name=source.get("license", "MIT"),
            require_clean=not args.allow_dirty,
            pinned_utc=existing.pinned_utc if existing is not None else None,
        )
    except PinError as exc:
        print(f"[00_pin_source] FAIL: {exc}")
        return 1

    # Preserve the original pin timestamp when nothing changed; refresh it when
    # the source, harness, or databases moved.
    if existing is not None and existing.to_dict() != pin.to_dict():
        pin.pinned_utc = utc_now()

    configured = source.get("pin")
    if configured not in (None, "TBD", pin.commit_sha) and not args.update_config:
        print(
            "[00_pin_source] FAIL: config pin does not match checkout "
            f"({configured} != {pin.commit_sha}); pass --update-config to change it"
        )
        return 1

    write_pin(pin, out)
    write_pin(pin, manifest_out)
    problems = verify_pin(pin, upstream)
    if problems:
        print("[00_pin_source] FAIL: pin verification failed")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    if args.update_config and configured != pin.commit_sha:
        update_config_pin(CONFIG_DIR / "harvest.yaml", pin.commit_sha)
        print(f"[00_pin_source] updated configs/harvest.yaml pin -> {pin.commit_sha}")

    print(f"[00_pin_source] commit {pin.commit_sha}")
    print(f"[00_pin_source] trajectories {len(pin.trajectory_hashes)}")
    print(f"[00_pin_source] task databases {len(pin.task_db_hashes)}")
    print(f"[00_pin_source] harness hash {pin.harness_hash}")
    print(f"[00_pin_source] wrote {out}")
    print(f"[00_pin_source] wrote {manifest_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
