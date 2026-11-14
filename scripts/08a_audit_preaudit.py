#!/usr/bin/env python
"""Stage 08a — AI pre-audit of the 40-item G0 packet.

This is a screening aid, not the required human audit. It writes a draft sheet
and a Markdown report; it never writes `g0_audit_result.json` and never freezes
the manifest. The authors must review the draft and fill the official sheet.

Checks per item:
- eligibility: sampled primary, eligible, replay-matched, non-empty decision,
  prefix ends at a tool message whose content equals the V observation;
- PII: no email/phone patterns and every declared PII leaf is a token;
- relevance: used/critical/noncritical fields are present;
- replay: match and a normalized diff taxonomy.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.config import load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl, read_jsonl_dicts  # noqa: E402
from toolobs.harvest.relevance import PiiPolicy, flatten_leaves  # noqa: E402
from toolobs.harvest.scrub import count_direct_identifiers  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, INTERIM_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402

TOKEN = re.compile(r"^(?:person|email|phone|address|dob|payment|user)_[0-9a-f]{12}$")
REPLAY_OK = {"exact", "json_normalized", "text_normalized"}

COLUMNS = (
    "item_id",
    "prefix_id",
    "domain",
    "eligibility_pass",
    "pii_pass",
    "relevance_pass",
    "replay_pass",
    "confidence",
    "notes",
    "evidence",
)


def _read_packet(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _check_item(
    packet_row: dict[str, str],
    record,
    prefix_row: dict,
    policy: PiiPolicy,
) -> dict[str, str]:
    notes: list[str] = []
    evidence: list[str] = []

    eligibility = True
    if record.split != "primary":
        eligibility = False
        notes.append("not a primary split")
    if not record.eligible:
        eligibility = False
        notes.append("record not eligible")
    if not record.replay_match:
        eligibility = False
        notes.append("replay did not match")
    if not packet_row.get("observation_text") or not packet_row.get("continuation_text"):
        eligibility = False
        notes.append("empty observation or continuation")
    messages = prefix_row.get("messages") or []
    if not messages or messages[-1].get("role") != "tool":
        eligibility = False
        notes.append("prefix does not end at a tool message")
    else:
        v_observation = (prefix_row.get("arm_observations") or {}).get("V", "")
        if messages[-1].get("content") != v_observation:
            eligibility = False
            notes.append("last tool content differs from V observation")
    try:
        continuation = json.loads(record.scrubbed_factual_continuation)
    except json.JSONDecodeError:
        continuation = {}
    if not continuation.get("content") and not continuation.get("tool_calls"):
        eligibility = False
        notes.append("continuation has no decision")
    evidence.append(f"arms={len(prefix_row.get('arm_observations') or {})}")
    evidence.append(f"messages={len(messages)}")

    pii = True
    direct = count_direct_identifiers(packet_row["observation_text"]) + count_direct_identifiers(
        packet_row["continuation_text"]
    )
    if direct:
        pii = False
        notes.append(f"direct identifier patterns: {direct}")
    observation = json.loads(record.scrubbed_observation_json)
    pii_leaves = 0
    for leaf in flatten_leaves(observation):
        if not policy.matches(leaf.path_pattern):
            continue
        pii_leaves += 1
        if not isinstance(leaf.value, str) or not TOKEN.match(leaf.value):
            pii = False
            notes.append(f"PII leaf not tokenized: {leaf.path_pattern}")
    evidence.append(f"pii_leaves={pii_leaves}")

    relevance = True
    if not record.used_fields:
        relevance = False
        notes.append("no used fields")
    if not record.critical_fields:
        relevance = False
        notes.append("no critical fields")
    if not record.noncritical_fields:
        relevance = False
        notes.append("no noncritical fields")
    evidence.append(
        f"used={len(record.used_fields)} critical={len(record.critical_fields)} "
        f"noncritical={len(record.noncritical_fields)}"
    )

    replay = bool(record.replay_match and record.replay_diff in REPLAY_OK)
    if not replay:
        notes.append(f"replay diff {record.replay_diff!r}")
    evidence.append(f"replay_diff={record.replay_diff}")

    passed = sum((eligibility, pii, relevance, replay))
    confidence = "high" if passed == 4 and not notes else "medium" if passed >= 3 else "low"
    return {
        "item_id": packet_row["item_id"],
        "prefix_id": packet_row["prefix_id"],
        "domain": packet_row["domain"],
        "eligibility_pass": "1" if eligibility else "0",
        "pii_pass": "1" if pii else "0",
        "relevance_pass": "1" if relevance else "0",
        "replay_pass": "1" if replay else "0",
        "confidence": confidence,
        "notes": "; ".join(notes),
        "evidence": "; ".join(evidence),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--packet", default=str(ARTIFACTS_DIR / "audit" / "g0_audit_packet.csv")
    )
    parser.add_argument("--sample", default=str(INTERIM_DIR / "sample.jsonl"))
    parser.add_argument(
        "--prefixes", default=str(INTERIM_DIR / "frozen_prefixes_preview.jsonl")
    )
    parser.add_argument(
        "--out", default=str(ARTIFACTS_DIR / "audit" / "g0_audit_ai_preaudit.csv")
    )
    parser.add_argument(
        "--markdown", default=str(ARTIFACTS_DIR / "audit" / "g0_audit_ai_preaudit.md")
    )
    args = parser.parse_args(argv)

    packet_path = resolve_repo_path(args.packet)
    sample_path = resolve_repo_path(args.sample)
    prefix_path = resolve_repo_path(args.prefixes)
    out_path = resolve_repo_path(args.out)
    markdown_path = resolve_repo_path(args.markdown)

    policy = PiiPolicy.from_config(load_config("field_registry.yaml"))
    packet = _read_packet(packet_path)
    sample = {record.prefix_id: record for record in read_jsonl(sample_path)}
    prefixes = {
        str(row["prefix_id"]): row for row in read_jsonl_dicts(prefix_path)
    }
    rows: list[dict[str, str]] = []
    for packet_row in packet:
        prefix_id = packet_row["prefix_id"]
        record = sample.get(prefix_id)
        prefix_row = prefixes.get(prefix_id)
        if record is None or prefix_row is None:
            rows.append(
                {
                    "item_id": packet_row["item_id"],
                    "prefix_id": prefix_id,
                    "domain": packet_row["domain"],
                    "eligibility_pass": "0",
                    "pii_pass": "0",
                    "relevance_pass": "0",
                    "replay_pass": "0",
                    "confidence": "low",
                    "notes": "missing sample or prefix payload",
                    "evidence": "",
                }
            )
            continue
        rows.append(_check_item(packet_row, record, prefix_row, policy))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    passed = sum(
        1
        for row in rows
        if all(row[key] == "1" for key in ("eligibility_pass", "pii_pass", "relevance_pass", "replay_pass"))
    )
    failures = [row for row in rows if any(row[key] == "0" for key in ("eligibility_pass", "pii_pass", "relevance_pass", "replay_pass"))]
    lines = [
        "# G0 AI pre-audit (draft, not the human gate)",
        "",
        f"- Items: {len(rows)}",
        f"- Four-check passes: {passed}/{len(rows)}",
        f"- Failures/attention: {len(failures)}",
        f"- Generated: {utc_now()}",
        f"- Git commit: `{git_commit()}`",
        "",
        "This sheet is a screening aid. The official `g0_audit_sheet.csv` remains blank and the",
        "G0 audit gate remains pending human sign-off.",
        "",
        "| Item | Domain | Eligibility | PII | Relevance | Replay | Confidence | Notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['item_id']} | {row['domain']} | {row['eligibility_pass']} | "
            f"{row['pii_pass']} | {row['relevance_pass']} | {row['replay_pass']} | "
            f"{row['confidence']} | {row['notes']} |"
        )
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(
        ARTIFACTS_DIR / "audit" / "g0_audit_ai_preaudit.json",
        {
            "stage": "08a_ai_preaudit",
            "recorded_utc": utc_now(),
            "git_commit": git_commit(),
            "items": len(rows),
            "four_check_passes": passed,
            "attention": len(failures),
            "official_audit_status": "pending_human",
        },
    )
    print(f"[08a_preaudit] items {len(rows)}")
    print(f"[08a_preaudit] four_check_passes {passed}")
    print(f"[08a_preaudit] attention {len(failures)}")
    print(f"[08a_preaudit] wrote {out_path}")
    print(f"[08a_preaudit] wrote {markdown_path}")
    print("[08a_preaudit] official audit remains pending_human")
    return 0


if __name__ == "__main__":
    sys.exit(main())
