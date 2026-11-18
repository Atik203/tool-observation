#!/usr/bin/env python
"""Stage 09e — recompute recovery events from rescored recovery ledgers.

Use after stage 09c when the decision-signature semantics change: the per-step
rows are unchanged, but R1/R2 coding depends on the current signature. Original
event files can be preserved with ``--backup-suffix`` (copied once).

Example:
  python scripts/09e_recovery_events.py --backup-suffix parser-v3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.analysis.recovery_events import replay_recovery_events  # noqa: E402
from toolobs.hashing import canonical_json  # noqa: E402
from toolobs.infer.ledger import read_ledger  # noqa: E402
from toolobs.paths import RUNS_DIR, resolve_repo_path  # noqa: E402

REGIMES = ("transient", "persistent")


def _read_events(path: Path) -> dict[tuple[str, int], dict]:
    if not path.exists():
        return {}
    events = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            events[(str(payload["prefix_id"]), int(payload["severity"]))] = payload
    return events


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ledger-root", default=str(RUNS_DIR / "main"))
    parser.add_argument("--event-root", default=str(RUNS_DIR / "main" / "recovery"))
    parser.add_argument("--backup-suffix", default="")
    parser.add_argument("--check", action="store_true", help="report changes without writing")
    args = parser.parse_args(argv)

    ledger_root = resolve_repo_path(args.ledger_root)
    event_root = resolve_repo_path(args.event_root)
    total = changed = 0
    for model_dir in sorted(ledger_root.iterdir()):
        if not model_dir.is_dir():
            continue
        ledger_path = model_dir / "ledger.jsonl"
        if not ledger_path.exists():
            continue
        reference_hashes = {
            row.prefix_id: row.signature_hash
            for row in read_ledger(ledger_path)
            if row.arm == "V"
        }
        for regime in REGIMES:
            recovery_path = model_dir / f"recovery_{regime}.jsonl"
            event_path = event_root / model_dir.name / f"{regime}.jsonl"
            if not recovery_path.exists() or not event_path.exists():
                continue
            original = _read_events(event_path)
            rows = read_ledger(recovery_path)
            state_hashes = {
                key: str(payload.get("state_hash", "")) for key, payload in original.items()
            }
            events = replay_recovery_events(
                rows,
                reference_hashes,
                model_id=model_dir.name,
                regime=regime,
                state_hashes=state_hashes,
            )
            for event in events:
                total += 1
            if args.check:
                for event in events:
                    old = original.get((event.prefix_id, event.severity))
                    if old is None:
                        continue
                    if (
                        old.get("recovered_step"),
                        old.get("endpoint"),
                        bool(old.get("censored")),
                    ) != (event.recovered_step, event.endpoint, event.censored):
                        changed += 1
                continue
            if args.backup_suffix:
                backup = event_path.with_name(
                    f"{event_path.stem}_{args.backup_suffix}{event_path.suffix}"
                )
                if not backup.exists():
                    backup.write_bytes(event_path.read_bytes())
            event_path.parent.mkdir(parents=True, exist_ok=True)
            with event_path.open("w", encoding="utf-8", newline="\n") as handle:
                for event in events:
                    handle.write(canonical_json(event.to_dict()) + "\n")
            print(f"[09e] {model_dir.name} {regime}: {len(events)} events -> {event_path}")
    if args.check:
        print(f"[09e] check: {changed} of {total} events would change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
