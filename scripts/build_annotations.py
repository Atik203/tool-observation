"""Build the human annotation kit under annotations/."""

import csv
import json
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AD = ROOT / "artifacts" / "audit"
BLIND = AD / "blind"
OUT = ROOT / "annotations"

for sub in ("g0", "severity", "outcome", "recovery", "verify", "common", "_trial"):
    (OUT / sub).mkdir(parents=True, exist_ok=True)


def read_jsonl(path):
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")


def scrub(value):
    """Redact email-like strings from human-facing text."""
    if value is None:
        return ""
    return EMAIL.sub("[email redacted]", str(value))


def write_csv(path, fieldnames, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


# ---------------------------------------------------------------- G0
g0 = list(csv.DictReader((AD / "g0_audit_packet.csv").open(encoding="utf-8", newline="")))
write_csv(
    OUT / "g0" / "packet.csv",
    [
        "item_id",
        "domain",
        "task_id",
        "donor",
        "tool_name",
        "observation",
        "continuation",
        "used_fields",
        "replay_diff",
    ],
    [
        {
            "item_id": r["item_id"],
            "domain": r["domain"],
            "task_id": r["task_id"],
            "donor": r["donor"],
            "tool_name": r["tool_name"],
            "observation": scrub(r["observation_text"]),
            "continuation": scrub(r["continuation_text"]),
            "used_fields": r["used_fields"],
            "replay_diff": r["replay_diff"],
        }
        for r in g0
    ],
)
write_csv(
    OUT / "g0" / "sheet.csv",
    ["item_id", "domain", "eligibility_pass", "pii_pass", "relevance_pass", "replay_pass", "note"],
    [{"item_id": r["item_id"], "domain": r["domain"]} for r in g0],
)

# ---------------------------------------------------------------- Severity
sev = read_jsonl(BLIND / "severity_items_v4.jsonl")
write_csv(
    OUT / "severity" / "packet.csv",
    [
        "item_id",
        "domain",
        "json_path",
        "true_value",
        "false_value",
        "json_path_2",
        "true_value_2",
        "false_value_2",
        "observation_excerpt",
        "donor_continuation",
    ],
    [
        {
            "item_id": r["item_id"],
            "domain": r["domain"],
            "json_path": r["json_path"],
            "true_value": r["true_value"],
            "false_value": r["false_value"],
            "json_path_2": r.get("json_path_2", ""),
            "true_value_2": r.get("true_value_2", ""),
            "false_value_2": r.get("false_value_2", ""),
            "observation_excerpt": scrub(r.get("observation_excerpt", "")),
            "donor_continuation": scrub(r.get("donor_continuation", "")),
        }
        for r in sev
    ],
)
write_csv(
    OUT / "severity" / "sheet.csv",
    ["item_id", "severity", "decision_changing", "absurd", "note"],
    [{"item_id": r["item_id"]} for r in sev],
)

# ---------------------------------------------------------------- Outcome
out = read_jsonl(BLIND / "outcome_items_unlabeled.jsonl")
perts = {}
for rec in read_jsonl(ROOT / "data" / "manifests" / "perturbations.jsonl"):
    perts[(rec["prefix_id"], rec["arm"])] = rec
rows = []
for r in out:
    p = perts.get((r["prefix_id"], r["arm"]), {})
    rows.append(
        {
            "item_id": r["item_id"],
            "prefix_id": r["prefix_id"],
            "model_id": r["model_id"],
            "arm": r["arm"],
            "prefix_domain": r["prefix_domain"],
            "injected_path": p.get("json_path", "") if p else "",
            "injected_true_value": scrub(json.dumps(p.get("true_value"), ensure_ascii=False)) if p else "",
            "injected_false_value": scrub(json.dumps(p.get("false_value"), ensure_ascii=False)) if p else "",
            "reference_output": scrub(r["reference_output"]),
            "model_output": scrub(r["model_output"]),
        }
    )
write_csv(
    OUT / "outcome" / "packet.csv",
    [
        "item_id",
        "prefix_id",
        "model_id",
        "arm",
        "prefix_domain",
        "injected_path",
        "injected_true_value",
        "injected_false_value",
        "reference_output",
        "model_output",
    ],
    rows,
)
write_csv(
    OUT / "outcome" / "sheet.csv",
    ["item_id", "Y", "YA", "YF", "YU", "note"],
    [{"item_id": r["item_id"]} for r in out],
)

# ---------------------------------------------------------------- Recovery
rec = read_jsonl(BLIND / "recovery_items_unlabeled.jsonl")


def steps_text(raw):
    steps = json.loads(raw) if isinstance(raw, str) else raw
    lines = []
    for step in steps:
        decision = step.get("decision", "")
        try:
            decision = json.loads(decision) if isinstance(decision, str) else decision
        except Exception:
            pass
        lines.append(
            f"Step {step.get('step')} | parsed={step.get('parsed')} | flag={step.get('flag')} | "
            f"decision={json.dumps(decision, ensure_ascii=False)} | output={str(step.get('output',''))[:220]}"
        )
    return "\n".join(lines)


write_csv(
    OUT / "recovery" / "packet.csv",
    [
        "item_id",
        "prefix_id",
        "model_id",
        "regime",
        "severity",
        "horizon",
        "reference_output",
        "reference_decision",
        "steps_text",
    ],
    [
        {
            "item_id": r["item_id"],
            "prefix_id": r["prefix_id"],
            "model_id": r["model_id"],
            "regime": r["regime"],
            "severity": r["severity"],
            "horizon": r["horizon"],
            "reference_output": scrub(r["reference_output"]),
            "reference_decision": scrub(r["reference_decision"]),
            "steps_text": scrub(steps_text(r["steps_json"])),
        }
        for r in rec
    ],
)
write_csv(
    OUT / "recovery" / "sheet.csv",
    ["item_id", "recovery_step", "endpoint", "note"],
    [{"item_id": r["item_id"]} for r in rec],
)

# ---------------------------------------------------------------- Verify outcome
out_rows = {r["item_id"]: r for r in rows}
out_sheet = list(csv.DictReader((AD / "outcome_audit_sheet.csv").open(encoding="utf-8", newline="")))
agree = [
    r
    for r in out_sheet
    if all(r[f"rater1_{f}"] == r[f"rater2_{f}"] for f in ("Y", "YA", "YF", "YU"))
]
rng = random.Random(20261122)
sample = rng.sample(agree, min(20, len(agree)))
sample.sort(key=lambda r: r["item_id"])
verify_rows = []
for s in sample:
    p = out_rows[s["item_id"]]
    label = f"Y={s['rater1_Y']}; YA={s['rater1_YA']}; YF={s['rater1_YF']}; YU={s['rater1_YU']}"
    evidence = (
        f"Reference: {scrub(p['reference_output'])[:420]}\n"
        f"Model: {scrub(p['model_output'])[:420]}\n"
        f"Injected false value: {scrub(p['injected_false_value']) or '(none)'}"
    )
    verify_rows.append(
        {
            "item_id": s["item_id"],
            "task": "outcome",
            "evidence_text": evidence,
            "agent_label": label,
        }
    )
write_csv(
    OUT / "verify" / "packet.csv",
    ["item_id", "task", "evidence_text", "agent_label"],
    verify_rows,
)
write_csv(
    OUT / "verify" / "sheet.csv",
    ["item_id", "task", "your_label", "agree", "note"],
    [{"item_id": r["item_id"], "task": "outcome"} for r in verify_rows],
)

print("wrote", OUT)
print("g0", len(g0), "severity", len(sev), "outcome", len(out), "recovery", len(rec), "verify", len(verify_rows))
