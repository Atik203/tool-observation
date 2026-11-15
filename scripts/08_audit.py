#!/usr/bin/env python
"""Stage 08 — G0 human audit packet and scoring.

Input:  data/interim/sample.jsonl, data/interim/rendered.jsonl
Output: artifacts/audit/g0_audit_packet.csv,
        artifacts/audit/g0_audit_sheet.csv,
        artifacts/audit/g0_audit_instructions.md

The packet contains 20 airline + 20 retail primary prefixes selected with the
project seed. A human checks eligibility, PII, relevance, and replay, then
fills the sheet. `--score` reads the completed sheet and applies the >=36/40
gate. The script never invents audit labels.

GATE: >=36/40 (90%) on the completed human sheet.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import config_hashes, load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, INTERIM_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402

AUDIT_COLUMNS = (
    "item_id",
    "domain",
    "eligibility_pass",
    "pii_pass",
    "relevance_pass",
    "replay_pass",
    "notes",
)

PACKET_COLUMNS = (
    "item_id",
    "prefix_id",
    "domain",
    "task_id",
    "donor",
    "tool_name",
    "observation_text",
    "continuation_text",
    "used_fields",
    "replay_diff",
    "replay_match",
)


def _continuation_text(record) -> str:
    try:
        message = json.loads(record.scrubbed_factual_continuation)
    except json.JSONDecodeError:
        return record.scrubbed_factual_continuation
    if not isinstance(message, dict):
        return record.scrubbed_factual_continuation
    parts: list[str] = []
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        parts.append(content)
    for call in message.get("tool_calls") or []:
        function = call.get("function") or {}
        name = function.get("name")
        arguments = function.get("arguments")
        if name:
            parts.append(str(name))
        if arguments:
            parts.append(str(arguments))
    return "\n".join(parts)


def _select(records, seed: int, per_domain: int = 20):
    selected = []
    for domain in ("airline", "retail"):
        pool = sorted(
            (record for record in records if record.domain == domain and record.split == "primary"),
            key=lambda record: record.prefix_id,
        )
        random.Random(f"{seed}|g0_audit|{domain}").shuffle(pool)
        selected.extend(pool[:per_domain])
    return selected


def _write_csv(path: Path, columns, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in columns})


def _score(path: Path, minimum: int = 36, label_source: str = "human") -> int:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 40:
        print(f"[08_audit] FAIL: expected 40 scored rows, got {len(rows)}")
        return 1
    passed = 0
    for row in rows:
        values = [
            str(row.get(key, "")).strip().lower()
            for key in ("eligibility_pass", "pii_pass", "relevance_pass", "replay_pass")
        ]
        if all(value in {"1", "yes", "true", "pass"} for value in values):
            passed += 1
    result = {
        "stage": "08_audit_score",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "items": len(rows),
        "passed": passed,
        "minimum": minimum,
        "gate_pass": passed >= minimum,
        "label_source": label_source,
    }
    write_json(ARTIFACTS_DIR / "audit" / "g0_audit_result.json", result)
    print(f"[08_audit] scored {len(rows)} items; passed {passed}; minimum {minimum}")
    print(f"[08_audit] gate_pass {passed >= minimum}")
    return 0 if passed >= minimum else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sample", default=str(INTERIM_DIR / "sample.jsonl"))
    parser.add_argument("--packet", default=str(ARTIFACTS_DIR / "audit" / "g0_audit_packet.csv"))
    parser.add_argument("--sheet", default=str(ARTIFACTS_DIR / "audit" / "g0_audit_sheet.csv"))
    parser.add_argument(
        "--instructions",
        default=str(ARTIFACTS_DIR / "audit" / "g0_audit_instructions.md"),
    )
    parser.add_argument("--score", default=None)
    parser.add_argument("--minimum", type=int, default=36)
    parser.add_argument(
        "--label-source",
        default="human",
        help="Provenance recorded in the score result, e.g. human or ai_preaudit_deferred_human.",
    )
    args = parser.parse_args(argv)

    if args.score:
        return _score(
            resolve_repo_path(args.score),
            minimum=args.minimum,
            label_source=args.label_source,
        )

    sample_path = resolve_repo_path(args.sample)
    packet_path = resolve_repo_path(args.packet)
    sheet_path = resolve_repo_path(args.sheet)
    instructions_path = resolve_repo_path(args.instructions)

    config = load_config("harvest.yaml")
    seed = int(config["harvest"]["random_seed"])
    records = read_jsonl(sample_path)
    selected = _select(records, seed, per_domain=20)

    packet_rows = []
    sheet_rows = []
    for index, record in enumerate(selected, start=1):
        item_id = f"G0-{index:03d}"
        packet_rows.append(
            {
                "item_id": item_id,
                "prefix_id": record.prefix_id,
                "domain": record.domain,
                "task_id": record.task_id,
                "donor": record.donor,
                "tool_name": record.tool_name,
                "observation_text": record.scrubbed_observation_json,
                "continuation_text": _continuation_text(record),
                "used_fields": json.dumps(
                    [field.get("json_path") for field in record.used_fields],
                    ensure_ascii=False,
                ),
                "replay_diff": record.replay_diff,
                "replay_match": str(record.replay_match),
            }
        )
        sheet_rows.append({"item_id": item_id, "domain": record.domain})

    _write_csv(packet_path, PACKET_COLUMNS, packet_rows)
    _write_csv(sheet_path, AUDIT_COLUMNS, sheet_rows)
    instructions_path.parent.mkdir(parents=True, exist_ok=True)
    instructions_path.write_text(
        "# G0 audit instructions\n\n"
        "Review each row in `g0_audit_packet.csv` and fill `g0_audit_sheet.csv`.\n\n"
        "- `eligibility_pass`: the prefix ends immediately after a real tool observation and the\n"
        "  donor continuation is a real next message, not empty. Donor continuations may be\n"
        "  natural language or provider-specific tool syntax; only target-model outputs use the\n"
        "  JSON contract, so do not fail an item because the donor text is not JSON.\n"
        "- `pii_pass`: no raw name, email, phone, street address, payment identifier, or DOB is\n"
        "  visible; synthetic tokens are expected.\n"
        "- `relevance_pass`: the listed used fields are genuinely used in the continuation, and the\n"
        "  observation has at least one decision-relevant field.\n"
        "- `replay_pass`: the replayed observation matches the historical observation under the\n"
        "  reported diff.\n\n"
        "Use `1` for pass and `0` for fail. Add a short note for every fail. The gate is >=36/40.\n"
        "Score with:\n\n"
        "```powershell\n"
        "python scripts/08_audit.py --score artifacts/audit/g0_audit_sheet.csv\n"
        "```\n",
        encoding="utf-8",
    )
    write_json(
        ARTIFACTS_DIR / "audit" / "g0_audit_packet.json",
        {
            "stage": "08_audit_packet",
            "recorded_utc": utc_now(),
            "git_commit": git_commit(),
            "config_hashes": config_hashes(),
            "items": len(packet_rows),
            "by_domain": {
                domain: sum(1 for row in packet_rows if row["domain"] == domain)
                for domain in ("airline", "retail")
            },
            "audit_status": "pending_human",
            "minimum": args.minimum,
        },
    )
    print(f"[08_audit] items {len(packet_rows)}")
    print(f"[08_audit] wrote {packet_path}")
    print(f"[08_audit] wrote {sheet_path}")
    print(f"[08_audit] wrote {instructions_path}")
    print("[08_audit] audit_status pending_human")
    return 0


if __name__ == "__main__":
    sys.exit(main())
