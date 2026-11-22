#!/usr/bin/env python
"""Stage 16 - task-utility endpoint (P2-15) with blinded adequacy coding.

CPU-only, stdlib + repo libs. No GPU, no new generations: every deterministic
number is recomputed from the frozen step-0 main ledgers, the frozen prefix
payload (true V observations), the frozen perturbation records, the donor
factual continuations in ``data/interim/candidates.jsonl``, and the automatic
outcome coding shared with stage 13 (parser v4 / signature v2).

Design (D-044, logged before any coding): two layers.

(a) Deterministic donor-path adherence on all semantic s3-switched pairs
(primary sample, reserve excluded). The donor continuation is the demonstrated
next decision on the TRUE observation: a tool call scores by tool-name match, a
free-text donor message scores by answer-type match (model ``final_answer`` vs
a tool action). The primary contrast is the paired s0-to-s3 drop, so
rendering/capability gaps cancel within pair. The donor path is one valid
path, not certified task success (donor-trajectory success was not verified).

(b) Blinded single-agent adequacy coding on 120 distinct primary prefixes
(40/model, parsed at both arms) x 2 arms = 240 codes, plus 40 blinded re-codes
for intra-rater agreement. Packets carry a blind id only; the packet-to-pair
map stays sealed until coding is done. Model id, arm, and donor continuation
are hidden. Rubric (frozen in D-044): 2 = adequate, 1 = degraded,
0 = harmful, 9 = unjudgeable. Parse failures/refusals are auto-coded 1
(degraded: no action taken) by rule and excluded from the agent pool.

Subcommands: ``sample`` (draw sample, emit blind packets + sealed map),
``recodes`` (draw 40 blinded re-code packets), ``analyze`` (join codes with
the deterministic layers and write ``new_evidence.json``).
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from toolobs.analysis.outcomes import compute_outcomes  # noqa: E402
from toolobs.config import load_config  # noqa: E402
from toolobs.harvest.parse import read_jsonl_dicts  # noqa: E402
from toolobs.infer.ledger import read_ledger  # noqa: E402
from toolobs.paths import ARTIFACTS_DIR, MANIFEST_DIR, RUNS_DIR, resolve_repo_path  # noqa: E402
from toolobs.provenance import git_commit, utc_now, write_json  # noqa: E402
from toolobs.schemas import PerturbationRecord  # noqa: E402

PROVENANCE = "single-agent blinded coding + script-computed endpoints, author-overseen"
SAMPLE_SEED = 20261122
PER_MODEL = 40
RECODE_N = 40
CRITICAL_ARM = "s3"

PACKETS_NAME = "task_utility_packets.json"
MAP_NAME = "task_utility_map.json"
CODES_NAME = "task_utility_codes.json"
RECODE_PACKETS_NAME = "task_utility_recodes_packets.json"
RECODE_MAP_NAME = "task_utility_recodes_map.json"
RECODES_NAME = "task_utility_recodes.json"
EVIDENCE_NAME = "new_evidence.json"

VALID_CODES = (0, 1, 2, 9)


def wilson_ci(k: int, n: int, z: float = 1.96) -> dict[str, float | None]:
    """Wilson score interval for a binomial share (matches stage-14/17 convention)."""
    if n <= 0:
        return {"rate": None, "lo": None, "hi": None}
    p = k / n
    den = 1.0 + z * z / n
    centre = (p + z * z / (2.0 * n)) / den
    half = z * ((p * (1.0 - p) / n + z * z / (4.0 * n * n)) ** 0.5) / den
    return {
        "rate": round(p, 6),
        "lo": round(max(0.0, centre - half), 6),
        "hi": round(min(1.0, centre + half), 6),
    }


def mcnemar_exact(b: int, c: int) -> float | None:
    """Two-sided exact McNemar p-value via the binomial tail (b + c discordant)."""
    n = b + c
    if n == 0:
        return None
    tail = sum(math.comb(n, k) for k in range(max(b, c), n + 1)) / (2.0**n)
    return round(min(1.0, 2.0 * tail), 6)


def cohen_kappa(first: list[int], second: list[int]) -> dict[str, float | None]:
    """Cohen's kappa over labels {0, 1, 2}; pairs with a 9 are excluded upstream."""
    n = len(first)
    if n == 0:
        return {"n": 0, "agreement": None, "kappa": None}
    agree = sum(1 for a, b in zip(first, second, strict=True) if a == b)
    po = agree / n
    labels = (0, 1, 2)
    pe = sum(
        (sum(1 for a in first if a == lab) / n) * (sum(1 for b in second if b == lab) / n)
        for lab in labels
    )
    kappa = (po - pe) / (1.0 - pe) if pe < 1.0 else None
    return {
        "n": n,
        "agreement": round(po, 6),
        "kappa": round(kappa, 6) if kappa is not None else None,
    }


def classify_wd(label) -> str:
    """Exclusive wrong-direction class (mirrors scripts/17_wrong_direction.py)."""
    if label.y_action:
        return "action"
    if label.y_flag:
        return "caught"
    if label.y_silent:
        return "silent"
    return "other"


def donor_reference(factual_continuation: str) -> tuple[str, str | None]:
    """Parse the donor continuation into (kind, tool).

    kind is 'tool' (donor used a tool call), 'text' (donor wrote a free-text
    message), or 'bad' (missing/unparseable). Tool names are lower-normalized.
    """
    if not factual_continuation:
        return ("bad", None)
    try:
        message = json.loads(factual_continuation)
    except (json.JSONDecodeError, TypeError):
        return ("bad", None)
    calls = message.get("tool_calls") if isinstance(message, dict) else None
    if calls:
        try:
            name = calls[0]["function"].get("name") or ""
        except (KeyError, TypeError, AttributeError):
            return ("bad", None)
        return ("tool", name.strip().lower() or None)
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return ("text", None)
    return ("bad", None)


def model_decision(row) -> tuple[str, str | None]:
    """Parse a step-0 ledger row into (kind, tool).

    kind is 'tool' (model emitted a task tool call), 'answer' (model emitted a
    final answer: ``tool`` is '' with an action ``verb``, or a ``final_answer``
    key), or 'invalid' (unparsed/refusal). Tool names lower-normalized.
    """
    if not row.parsed:
        return ("invalid", None)
    try:
        decision = json.loads(row.decision_json)
    except (json.JSONDecodeError, TypeError):
        return ("invalid", None)
    if not isinstance(decision, dict):
        return ("invalid", None)
    tool = decision.get("tool")
    if isinstance(tool, str) and tool.strip().lower() not in ("", "final_answer"):
        return ("tool", tool.strip().lower())
    if isinstance(tool, str) and tool.strip().lower() == "final_answer":
        return ("answer", None)
    if "final_answer" in decision:
        return ("answer", None)
    if isinstance(tool, str) and tool.strip() == "" and "verb" in decision:
        # Parser v4 final-answer signature: empty tool + action verb.
        return ("answer", None)
    return ("invalid", None)


def donor_match(donor: tuple[str, str | None], model: tuple[str, str | None]) -> bool | None:
    """Donor-path adherence: tool-name match for tool donors, type match else.

    Returns None when the comparison is undefined (bad donor or invalid model).
    """
    donor_kind, donor_tool = donor
    model_kind, model_tool = model
    if donor_kind == "bad" or model_kind == "invalid":
        return None
    if donor_kind == "tool":
        if donor_tool is None:
            return None
        return model_kind == "tool" and model_tool == donor_tool
    return model_kind == "answer"


def load_inputs(ledger_root, model_ids: list[str], reserve_ids: set[str]):
    """Load step-0 ledger rows (primary sample), perturbations, prefixes, donors."""
    rows = []
    for model_id in model_ids:
        path = Path(ledger_root) / model_id / "ledger.jsonl"
        if not path.exists():
            raise SystemExit(f"missing ledger: {path}")
        rows.extend(row for row in read_ledger(path) if row.step == 0)
    rows = [row for row in rows if row.prefix_id not in reserve_ids]
    perturbations = [
        PerturbationRecord.from_dict(item)
        for item in read_jsonl_dicts(resolve_repo_path(MANIFEST_DIR / "perturbations.jsonl"))
    ]
    prefixes = {}
    with (resolve_repo_path("data/frozen/prefixes.jsonl")).open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            prefixes[record["prefix_id"]] = record
    donors = {}
    with (resolve_repo_path("data/interim/candidates.jsonl")).open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            donors[record["prefix_id"]] = record.get("factual_continuation") or ""
    return rows, perturbations, prefixes, donors


def user_request_text(prefix: dict, cap: int = 2000) -> str:
    """Concatenate user-role turns (the task request); tool results are role 'tool'."""
    turns = [
        str(message.get("content") or "")
        for message in prefix.get("messages", [])
        if message.get("role") == "user" and message.get("content")
    ]
    text = "\n---\n".join(turn.strip() for turn in turns if turn.strip())
    if len(text) > cap:
        text = text[:cap] + "\n[... truncated]"
    return text


def packet_decision_text(row, cap: int = 1000) -> str:
    """Compact blinded decision rendering for a coding packet."""
    kind, tool = model_decision(row)
    if kind == "invalid":
        return f"[no valid action: parser_status={row.parser_status}] " + (row.output_text or "")[:cap]
    if kind == "answer":
        return "final_answer: " + (row.output_text or "")[:cap]
    try:
        args = json.loads(row.decision_json).get("args", {})
    except (json.JSONDecodeError, TypeError, AttributeError):
        args = {}
    rendered = f"tool: {tool}\nargs: {json.dumps(args, sort_keys=True, default=str)}"
    if len(rendered) > cap:
        rendered = rendered[:cap] + "\n[... truncated]"
    return rendered


def switched_pairs(rows, perturbations):
    """Semantic s3-switched (prefix, model) pairs with parsed decisions at s0/s3."""
    labels = compute_outcomes(rows, perturbations)
    by_key = {(row.prefix_id, row.model_id, row.arm): row for row in rows}
    pairs = []
    auto_degraded = 0
    for label in labels:
        if label.arm != CRITICAL_ARM or not label.y_any:
            continue
        row_s0 = by_key.get((label.prefix_id, label.model_id, "s0"))
        row_s3 = by_key.get((label.prefix_id, label.model_id, CRITICAL_ARM))
        if row_s0 is None or row_s3 is None:
            continue
        if not row_s0.parsed or not row_s3.parsed:
            auto_degraded += 1
            continue
        pairs.append(label)
    return pairs, auto_degraded, by_key


def select_sample(pairs, per_model: int = PER_MODEL, seed: int = SAMPLE_SEED):
    """Stratified 40/model sample over distinct prefixes (deterministic)."""
    models = sorted({label.model_id for label in pairs})
    used: set[str] = set()
    sample = []
    for model_id in models:
        pool = sorted(
            (label for label in pairs if label.model_id == model_id),
            key=lambda item: item.prefix_id,
        )
        rng = random.Random(f"{seed}|{model_id}")
        rng.shuffle(pool)
        taken = 0
        for label in pool:
            if label.prefix_id in used:
                continue
            used.add(label.prefix_id)
            sample.append(label)
            taken += 1
            if taken >= per_model:
                break
        if taken < per_model:
            raise SystemExit(f"pool exhausted for {model_id}: {taken}/{per_model}")
    return sample


def emit_packets(sample, prefixes, by_key, out_packets: Path, out_map: Path, prefix: str) -> None:
    """Write blinded coding packets plus the sealed pair map."""
    packets = []
    mapping = {}
    for index, label in enumerate(sample):
        blind_id = f"{prefix}{index:03d}"
        record = prefixes[label.prefix_id]
        true_result = str((record.get("arm_observations") or {}).get("V", ""))
        if len(true_result) > 3000:
            true_result = true_result[:3000] + "\n[... truncated]"
        row = by_key[(label.prefix_id, label.model_id, label.arm)]
        packets.append(
            {
                "blind_id": blind_id,
                "user_request": user_request_text(record),
                "true_tool_result": true_result,
                "model_decision": packet_decision_text(row),
            }
        )
        mapping[blind_id] = {
            "prefix_id": label.prefix_id,
            "model_id": label.model_id,
            "arm": label.arm,
        }
    write_json(out_packets, {"packets": packets, "n": len(packets)})
    write_json(out_map, {"map": mapping, "n": len(mapping)})
    print(f"wrote {out_packets} ({len(packets)} blind packets) + sealed {out_map}")


def cmd_sample(args) -> int:
    configured = [str(model["id"]) for model in load_config("models.yaml")["models"]]
    model_ids = args.models or configured
    manifest = json.loads(resolve_repo_path(MANIFEST_DIR / "toolresult800_v1.json").read_text(encoding="utf-8"))
    reserve_ids = set(manifest.get("reserve_ids", []))
    rows, perturbations, prefixes, _donors = load_inputs(args.ledger_root, model_ids, reserve_ids)
    pairs, auto_degraded, by_key = switched_pairs(rows, perturbations)
    sample = select_sample(pairs)
    emit_packets(
        [label for label in sample],
        prefixes,
        {(label.prefix_id, label.model_id, label.arm): by_key[(label.prefix_id, label.model_id, label.arm)] for label in sample},
        resolve_repo_path(args.packets or (ARTIFACTS_DIR / "analysis" / PACKETS_NAME)),
        resolve_repo_path(args.map or (ARTIFACTS_DIR / "analysis" / MAP_NAME)),
        prefix="U",
    )
    # Paired s0 rows for the same sampled prefixes/models.
    s0_labels = []
    by_pair = {(label.prefix_id, label.model_id): label for label in sample}
    labels = compute_outcomes(rows, perturbations)
    for label in labels:
        if label.arm == "s0" and (label.prefix_id, label.model_id) in by_pair:
            s0_labels.append(label)
    emit_packets(
        sorted(s0_labels, key=lambda item: (item.model_id, item.prefix_id)),
        prefixes,
        by_key,
        resolve_repo_path(args.s0_packets or (ARTIFACTS_DIR / "analysis" / "task_utility_s0_packets.json")),
        resolve_repo_path(args.s0_map or (ARTIFACTS_DIR / "analysis" / "task_utility_s0_map.json")),
        prefix="B",
    )
    print(f"pool s3-switched both-parsed pairs: {len(pairs)}; auto-degraded unparsed: {auto_degraded}")
    return 0


def cmd_recodes(args) -> int:
    packets_path = resolve_repo_path(args.packets or (ARTIFACTS_DIR / "analysis" / PACKETS_NAME))
    s0_path = resolve_repo_path(args.s0_packets or (ARTIFACTS_DIR / "analysis" / "task_utility_s0_packets.json"))
    for path in (packets_path, s0_path):
        if not path.exists():
            raise SystemExit(f"missing packets (run sample first): {path}")
    packets = json.loads(packets_path.read_text(encoding="utf-8"))["packets"]
    s0_packets = json.loads(s0_path.read_text(encoding="utf-8"))["packets"]
    rng = random.Random(f"{SAMPLE_SEED}|recodes")
    rng.shuffle(packets)
    rng.shuffle(s0_packets)
    chosen = packets[: RECODE_N // 2] + s0_packets[: RECODE_N // 2]
    rng.shuffle(chosen)
    recode_packets = []
    recode_map = {}
    for index, packet in enumerate(chosen):
        blind_id = f"R{index:03d}"
        recode_packets.append({**packet, "blind_id": blind_id})
        recode_map[blind_id] = packet["blind_id"]
    write_json(resolve_repo_path(args.out or (ARTIFACTS_DIR / "analysis" / RECODE_PACKETS_NAME)), {"packets": recode_packets, "n": len(recode_packets)})
    write_json(resolve_repo_path(args.map or (ARTIFACTS_DIR / "analysis" / RECODE_MAP_NAME)), {"map": recode_map, "n": len(recode_map)})
    print(f"wrote {RECODE_N} blinded re-code packets")
    return 0


def load_codes(path: Path, packet_ids: set[str], what: str) -> dict[str, dict]:
    if not path.exists():
        raise SystemExit(f"missing {what} (agent coding not done): {path}")
    codes = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(codes, dict):
        raise SystemExit(f"{what} must be a JSON object keyed by blind id")
    unknown = sorted(set(codes) - packet_ids)
    if unknown:
        raise SystemExit(f"{what} has {len(unknown)} unknown blind ids: {unknown[:5]}")
    missing = sorted(packet_ids - set(codes))
    if missing:
        raise SystemExit(f"{what} missing {len(missing)} packets: {missing[:5]}")
    for blind_id, entry in codes.items():
        if not isinstance(entry, dict) or entry.get("code") not in VALID_CODES:
            raise SystemExit(f"{what}[{blind_id}] invalid code (want one of {VALID_CODES})")
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            raise SystemExit(f"{what}[{blind_id}] missing reason")
    return codes


def cmd_analyze(args) -> int:
    configured = [str(model["id"]) for model in load_config("models.yaml")["models"]]
    model_ids = args.models or configured
    manifest = json.loads(resolve_repo_path(MANIFEST_DIR / "toolresult800_v1.json").read_text(encoding="utf-8"))
    reserve_ids = set(manifest.get("reserve_ids", []))
    rows, perturbations, _prefixes, donors = load_inputs(args.ledger_root, model_ids, reserve_ids)
    labels = compute_outcomes(rows, perturbations)
    by_key = {(row.prefix_id, row.model_id, row.arm): row for row in rows}
    label_by_key = {(label.prefix_id, label.model_id, label.arm): label for label in labels}

    # (a) Deterministic donor-path adherence on all s3-switched pairs.
    det_pairs = []
    skipped_bad_donor = 0
    for label in labels:
        if label.arm != CRITICAL_ARM or not label.y_any:
            continue
        row_s0 = by_key.get((label.prefix_id, label.model_id, "s0"))
        row_s3 = by_key.get((label.prefix_id, label.model_id, CRITICAL_ARM))
        if row_s0 is None or row_s3 is None:
            continue
        donor = donor_reference(donors.get(label.prefix_id, ""))
        match_s0 = donor_match(donor, model_decision(row_s0))
        match_s3 = donor_match(donor, model_decision(row_s3))
        if match_s0 is None or match_s3 is None:
            skipped_bad_donor += 1
            continue
        det_pairs.append(
            {
                "prefix_id": label.prefix_id,
                "model_id": label.model_id,
                "donor_kind": donor[0],
                "wd_class": classify_wd(label),
                "flagged": bool(label.y_flag),
                "match_s0": match_s0,
                "match_s3": match_s3,
            }
        )

    def det_summary(cells) -> dict:
        n = len(cells)
        k_s0 = sum(1 for p in cells if p["match_s0"])
        k_s3 = sum(1 for p in cells if p["match_s3"])
        bb = sum(1 for p in cells if p["match_s0"] and not p["match_s3"])
        cc = sum(1 for p in cells if not p["match_s0"] and p["match_s3"])
        return {
            "n": n,
            "match_s0": wilson_ci(k_s0, n),
            "match_s3": wilson_ci(k_s3, n),
            "drop_pp": round((k_s0 - k_s3) / n, 6) if n else None,
            "mcnemar_b": bb,
            "mcnemar_c": cc,
            "mcnemar_p": mcnemar_exact(bb, cc),
        }

    by_model_det = {m: det_summary([p for p in det_pairs if p["model_id"] == m]) for m in model_ids}
    by_donor = {
        kind: det_summary([p for p in det_pairs if p["donor_kind"] == kind]) for kind in ("tool", "text")
    }

    # (b) Agent adequacy coding on the blinded sample.
    packets_path = resolve_repo_path(args.packets or (ARTIFACTS_DIR / "analysis" / PACKETS_NAME))
    map_path = resolve_repo_path(args.map or (ARTIFACTS_DIR / "analysis" / MAP_NAME))
    s0_packets_path = resolve_repo_path(args.s0_packets or (ARTIFACTS_DIR / "analysis" / "task_utility_s0_packets.json"))
    s0_map_path = resolve_repo_path(args.s0_map or (ARTIFACTS_DIR / "analysis" / "task_utility_s0_map.json"))
    packets = {p["blind_id"]: p for p in json.loads(packets_path.read_text(encoding="utf-8"))["packets"]}
    pmap = json.loads(map_path.read_text(encoding="utf-8"))["map"]
    s0_packets = {p["blind_id"]: p for p in json.loads(s0_packets_path.read_text(encoding="utf-8"))["packets"]}
    s0_map = json.loads(s0_map_path.read_text(encoding="utf-8"))["map"]
    codes = load_codes(resolve_repo_path(args.codes or (ARTIFACTS_DIR / "analysis" / CODES_NAME)), set(packets), "codes")
    s0_codes = load_codes(resolve_repo_path(args.s0_codes or (ARTIFACTS_DIR / "analysis" / "task_utility_s0_codes.json")), set(s0_packets), "s0 codes")

    coded = []
    for blind_id, entry in codes.items():
        info = pmap[blind_id]
        label = label_by_key.get((info["prefix_id"], info["model_id"], info["arm"]))
        s0_blind = next(b for b, m in s0_map.items() if m["prefix_id"] == info["prefix_id"] and m["model_id"] == info["model_id"])
        coded.append(
            {
                "blind_id": blind_id,
                "prefix_id": info["prefix_id"],
                "model_id": info["model_id"],
                "code_s3": entry["code"],
                "reason_s3": entry["reason"],
                "code_s0": s0_codes[s0_blind]["code"],
                "reason_s0": s0_codes[s0_blind]["reason"],
                "wd_class": classify_wd(label) if label is not None else None,
                "flagged": bool(label.y_flag) if label is not None else None,
            }
        )
    n_coded = len(coded)
    n_judge = [p for p in coded if p["code_s3"] != 9 and p["code_s0"] != 9]

    def adequacy_summary(cells, arm_key: str) -> dict:
        judgeable = [p for p in cells if p[arm_key] != 9]
        n = len(judgeable)
        out = {"n_coded": len(cells), "n_judgeable": n, "unjudgeable": sum(1 for p in cells if p[arm_key] == 9)}
        for code, name in ((2, "adequate"), (1, "degraded"), (0, "harmful")):
            out[name] = wilson_ci(sum(1 for p in judgeable if p[arm_key] == code), n)
        return out

    pooled_s0 = adequacy_summary(n_judge, "code_s0")
    pooled_s3 = adequacy_summary(n_judge, "code_s3")
    bb = sum(1 for p in n_judge if p["code_s0"] == 2 and p["code_s3"] != 2)
    cc = sum(1 for p in n_judge if p["code_s0"] != 2 and p["code_s3"] == 2)
    by_model_agent = {
        m: {
            "s0": adequacy_summary([p for p in n_judge if p["model_id"] == m], "code_s0"),
            "s3": adequacy_summary([p for p in n_judge if p["model_id"] == m], "code_s3"),
        }
        for m in model_ids
    }
    # Utility x wrong-direction: harmful/degraded share among WD vs caught/ambiguous.
    wd_cells = [p for p in n_judge if p["wd_class"] in ("action", "silent")]
    other_cells = [p for p in n_judge if p["wd_class"] in ("caught", "other")]
    wd_bad = sum(1 for p in wd_cells if p["code_s3"] in (0, 1))
    other_bad = sum(1 for p in other_cells if p["code_s3"] in (0, 1))
    # Deterministic x agent cross-check: donor-match vs adequate at s3.
    det_by_pair = {(p["prefix_id"], p["model_id"]): p for p in det_pairs}
    cross = []
    for item in n_judge:
        det = det_by_pair.get((item["prefix_id"], item["model_id"]))
        if det is not None:
            cross.append((det["match_s3"], item["code_s3"] == 2))
    cross_both = sum(1 for m, a in cross if m and a)
    cross_match_only = sum(1 for m, a in cross if m and not a)

    # (c) Reliability: blinded re-codes.
    recode_packets_path = resolve_repo_path(args.recode_packets or (ARTIFACTS_DIR / "analysis" / RECODE_PACKETS_NAME))
    recode_map_path = resolve_repo_path(args.recode_map or (ARTIFACTS_DIR / "analysis" / RECODE_MAP_NAME))
    recode_packets = json.loads(recode_packets_path.read_text(encoding="utf-8"))["packets"]
    recode_map = json.loads(recode_map_path.read_text(encoding="utf-8"))["map"]
    recodes = load_codes(resolve_repo_path(args.recodes or (ARTIFACTS_DIR / "analysis" / RECODES_NAME)), {p["blind_id"] for p in recode_packets}, "recodes")
    first_codes = {**{b: codes[b]["code"] for b in packets}, **{b: s0_codes[b]["code"] for b in s0_packets}}
    rel_first, rel_second = [], []
    rel_unjudge = 0
    origin = {}
    for blind_id, orig_id in recode_map.items():
        origin[blind_id] = orig_id
        a, bb_code = first_codes[orig_id], recodes[blind_id]["code"]
        if a == 9 or bb_code == 9:
            rel_unjudge += 1
            continue
        rel_first.append(a)
        rel_second.append(bb_code)
    reliability = cohen_kappa(rel_first, rel_second)
    reliability["unjudgeable_pairs"] = rel_unjudge

    report = {
        "stage": "task_utility",
        "recorded_utc": utc_now(),
        "git_commit": git_commit(),
        "models": model_ids,
        "include_reserve": False,
        "analysis_prefixes": len({row.prefix_id for row in rows}),
        "provenance": PROVENANCE,
        "hours": {
            "gpu_hours": 0.0,
            "cpu_only": True,
            "note": "no new generations; deterministic layers recomputed from "
            "frozen ledgers; adequacy coding is single-agent blinded, "
            "author-overseen (no multi-session panel: T6 forbids subagents)",
        },
        "deterministic": {
            "endpoint": "donor-path adherence: tool-name match for tool-call donors, "
            "answer-type match for free-text donors; paired s0-to-s3 contrast.",
            "s3_switched_pairs": len(det_pairs),
            "skipped_bad_donor_or_invalid": skipped_bad_donor,
            "pooled": det_summary(det_pairs),
            "by_model": by_model_det,
            "by_donor_kind": by_donor,
        },
        "agent_coding": {
            "endpoint": "blinded adequacy coding (2 adequate / 1 degraded / "
            "0 harmful / 9 unjudgeable); rubric frozen in D-044.",
            "n_prefixes": len({p['prefix_id'] for p in coded}),
            "n_coded_pairs": n_coded,
            "n_judgeable_pairs": len(n_judge),
            "pooled_s0": pooled_s0,
            "pooled_s3": pooled_s3,
            "paired_adequacy_loss_b": bb,
            "paired_adequacy_gain_c": cc,
            "paired_adequacy_mcnemar_p": mcnemar_exact(bb, cc),
            "by_model": by_model_agent,
            "wd_crosstab": {
                "wd_n": len(wd_cells),
                "wd_bad_s3": wilson_ci(wd_bad, len(wd_cells)),
                "other_n": len(other_cells),
                "other_bad_s3": wilson_ci(other_bad, len(other_cells)),
            },
            "donor_match_x_adequate_s3": {
                "n": len(cross),
                "match_and_adequate": cross_both,
                "match_but_not_adequate": cross_match_only,
            },
        },
        "reliability": reliability,
    }
    out_path = resolve_repo_path(args.out or (ARTIFACTS_DIR / "analysis" / EVIDENCE_NAME))
    write_json(out_path, report)
    print(
        f"donor adherence s0 {report['deterministic']['pooled']['match_s0']['rate']:.1%} -> "
        f"s3 {report['deterministic']['pooled']['match_s3']['rate']:.1%} "
        f"(n={len(det_pairs)}); adequate s0 {pooled_s0['adequate']['rate']:.1%} -> "
        f"s3 {pooled_s3['adequate']['rate']:.1%} (n={len(n_judge)}); "
        f"kappa={reliability['kappa']}"
    )
    print(f"wrote {out_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("sample", "recodes", "analyze"):
        child = sub.add_parser(name)
        child.add_argument("--models", nargs="*", default=None)
        child.add_argument("--ledger-root", default=str(RUNS_DIR / "main"))
        child.add_argument("--packets", default=None)
        child.add_argument("--map", default=None)
        child.add_argument("--s0-packets", default=None)
        child.add_argument("--s0-map", default=None)
        child.add_argument("--codes", default=None)
        child.add_argument("--s0-codes", default=None)
        child.add_argument("--recode-packets", default=None)
        child.add_argument("--recode-map", default=None)
        child.add_argument("--recodes", default=None)
        child.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    if args.command == "sample":
        return cmd_sample(args)
    if args.command == "recodes":
        return cmd_recodes(args)
    return cmd_analyze(args)


if __name__ == "__main__":
    raise SystemExit(main())