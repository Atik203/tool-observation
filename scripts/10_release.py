#!/usr/bin/env python
"""Stage 10 — build the ToolResult-800 release package.

Input:  data/manifests/toolresult800_v1.json + sidecar, frozen prefixes,
        perturbations, source pin, data card, licenses
Output: release/toolresult800-v1/ with CHECKSUMS.sha256

The package contains only scrubbed derived data, manifests, and documentation.
Raw τ-bench trajectories, PII, model weights, and run ledgers are excluded.
The script refuses to run without a passed human audit and a verified manifest.

GATE: manifest and payload hashes verify; PII rescan is clean; licenses present.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.harvest.freeze import hash_renderer  # noqa: E402
from toolobs.harvest.parse import hash_jsonl_dicts, read_jsonl_dicts  # noqa: E402
from toolobs.harvest.scrub import count_direct_identifiers  # noqa: E402
from toolobs.hashing import sha256_file, sha256_text_file  # noqa: E402
from toolobs.paths import (  # noqa: E402
    CONFIG_DIR,
    FROZEN_DIR,
    INTERIM_DIR,
    MANIFEST_DIR,
    PREREG_DIR,
    RELEASE_DIR,
    resolve_repo_path,
)
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_strings(child)
    elif isinstance(value, str):
        yield value


def _pii_hits(rows: Iterable[dict[str, Any]]) -> int:
    return sum(count_direct_identifiers(text) for row in rows for text in _iter_strings(row))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", default=str(MANIFEST_DIR / "toolresult800_v1.json"))
    parser.add_argument("--out", default=str(RELEASE_DIR / "toolresult800-v1"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    manifest_path = resolve_repo_path(args.manifest)
    output_dir = resolve_repo_path(args.out)
    if not manifest_path.is_file():
        print(f"[10_release] FAIL: frozen manifest missing at {manifest_path}")
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest.get("audit", {}).get("gate_pass"):
        print("[10_release] FAIL: manifest audit gate is not passed")
        return 1
    if not manifest.get("freeze", {}).get("no_target_outputs_before_freeze"):
        print("[10_release] FAIL: freeze record does not assert no target outputs")
        return 1

    frozen_path = FROZEN_DIR / "prefixes.jsonl"
    perturbations_path = MANIFEST_DIR / "perturbations.jsonl"
    sample_path = INTERIM_DIR / "sample.jsonl"
    required = [frozen_path, perturbations_path, sample_path, MANIFEST_DIR / "source_pin.json"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        print(f"[10_release] FAIL: missing release inputs: {missing}")
        return 1

    frozen_rows = read_jsonl_dicts(frozen_path)
    perturbation_rows = read_jsonl_dicts(perturbations_path)
    checks = {
        "frozen_prefixes": hash_jsonl_dicts(frozen_rows) == manifest.get("frozen_prefixes_hash"),
        "perturbations": sha256_text_file(perturbations_path) == manifest.get("perturbations_hash"),
        "sample": sha256_text_file(sample_path) == manifest.get("sample_hash"),
        "source_pin": sha256_text_file(MANIFEST_DIR / "source_pin.json")
        == manifest.get("source_pin_hash"),
        "prereg": sha256_text_file(PREREG_DIR / "PREREGISTRATION.md")
        == manifest.get("prereg_hash"),
        "field_registry": sha256_text_file(CONFIG_DIR / "field_registry.yaml")
        == manifest.get("field_registry_hash"),
        "renderer": hash_renderer(
            REPO_ROOT / "src" / "toolobs" / "render" / "render.py",
            REPO_ROOT / "src" / "toolobs" / "render" / "perturb.py",
        )
        == manifest.get("renderer_hash"),
    }
    pii_hits = _pii_hits(frozen_rows) + _pii_hits(perturbation_rows)
    if not all(checks.values()) or pii_hits:
        print(f"[10_release] FAIL: checks {checks}, pii_hits {pii_hits}")
        return 1

    files = {
        manifest_path: "toolresult800_v1.json",
        manifest_path.with_suffix(".sha256.json"): "toolresult800_v1.sha256.json",
        MANIFEST_DIR / "source_pin.json": "source_pin.json",
        perturbations_path: "perturbations.jsonl",
        frozen_path: "frozen/prefixes.jsonl",
        REPO_ROOT / "docs" / "DATA_CARD.md": "DATA_CARD.md",
        REPO_ROOT / "LICENSE": "LICENSE",
        REPO_ROOT / "DATA_LICENSE.md": "DATA_LICENSE.md",
        REPO_ROOT / "CITATION.cff": "CITATION.cff",
    }
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        print(f"[10_release] FAIL: missing package files: {missing}")
        return 1

    print(f"[10_release] checks {checks}")
    print(f"[10_release] pii_hits {pii_hits}")
    print(f"[10_release] frozen_prefixes {len(frozen_rows)}")
    print(f"[10_release] perturbations {len(perturbation_rows)}")
    if args.dry_run:
        print("[10_release] dry-run: no files copied")
        return 0

    if output_dir.exists():
        print(f"[10_release] FAIL: output directory already exists: {output_dir}")
        return 1
    checksums: list[str] = []
    for source, relative in files.items():
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        checksums.append(f"{sha256_file(target)}  {relative}")
    (output_dir / "CHECKSUMS.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    (output_dir / "README.md").write_text(
        "# ToolResult-800 v1.0\n\n"
        f"Frozen: {manifest.get('created_utc')}\n\n"
        "This package contains scrubbed derived prefixes, perturbation records, manifests, and\n"
        "documentation. It does not contain raw τ-bench trajectories, PII, model weights, or run\n"
        "ledgers. See `DATA_CARD.md` for scope and limitations.\n",
        encoding="utf-8",
    )
    write_json(
        output_dir / "release_record.json",
        {
            "created_utc": utc_now(),
            "git_commit": git_commit(),
            "manifest_hash": sha256_file(manifest_path),
            "files": {relative: sha256_file(output_dir / relative) for relative in files.values()},
        },
    )
    print(f"[10_release] wrote {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
