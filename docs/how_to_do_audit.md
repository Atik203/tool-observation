# How to do the audits — ToolResult-800

This guide explains the four audits in the ToolResult-800 pipeline, which files to open, and
how to fill them. It is written for a rater or reviewer who has never seen the project before.
The audit files live in `artifacts/audit/`; the gate criteria live in `docs/GATES.md` and
`prereg/PREREGISTRATION.md`.

## 1. Overview

| Audit | Items | Raters | What is rated | Gate |
|---|---:|---:|---|---|
| G0 harvest | 40 | 1 (human, deferred) | eligibility, PII, relevance, replay | >= 36/40 |
| Severity | 120 | 3 blind | severity 0-3, decision-changing, absurd | monotone p<.01, alpha>=.75, >=90% s=1 non-decision-changing, >=90% s=2/s=3 decision-changing, s=3 absurd <=20% |
| Outcome | 160 | 2 blind | Y, YA, YF, YU (4-way) | Cohen kappa >= .80, silent PPV >= .90, seed-repeat stability >= .90 |
| Recovery | 80 | 2 blind | recovery step 1-4, endpoint R1/R2/censored | kappa >= .75 |

All audits use the same two-file pattern: a **packet** (the evidence) and a **sheet** (the
answers). The rater never edits the packet; only the sheet.

## 2. File map

```
artifacts/audit/
  g0_audit_packet.csv            # 40 G0 items, evidence
  g0_audit_sheet.csv             # 40 rows to fill
  g0_audit_instructions.md      # how to fill G0
  g0_audit_result.json          # scored result

  severity_audit_packet.csv      # 120 severity items, evidence
  severity_audit_sheet.csv      # 120 rows x 3 raters (pre-filled by AI pre-audit)
  severity_audit_instructions.md

  outcome_audit_packet.csv       # 160 outcome items, evidence
  outcome_audit_sheet.csv       # 160 rows x 2 raters (pre-filled by AI pre-audit)
  outcome_audit_instructions.md

  recovery_audit_packet.csv      # 80 recovery sequences, evidence
  recovery_audit_sheet.csv       # 80 rows x 2 raters (pre-filled by AI pre-audit)
  recovery_audit_instructions.md

  audit_packets_result.json     # summary of the generated packets
```

The manifest and frozen data (do not edit) live in:

```
data/manifests/toolresult800_v1.json        # frozen manifest, SHA-256 d6e034d7...
data/manifests/toolresult800_v1.sha256.json  # sidecar hash
data/frozen/prefixes.jsonl                   # 880 scrubbed prefixes
data/manifests/perturbations.jsonl           # 2,640 perturbation records
```

## 3. General rules

1. **Never edit a packet file.** Packets are evidence; sheets are answers.
2. **One row per item.** Do not add or delete rows; the scorer checks the row count.
3. **Use 1/0 (or the allowed codes) only.** Free text goes in `notes`.
4. **Add a note for every fail or disagreement.** A blank note on a fail is a data-quality
   problem.
5. **Do not look at model outputs before rating the evidence** for that item; rate from the
   packet fields first.
6. **Blinding:** raters do not see each other's sheets until scoring.
7. **Provenance:** every sheet is recorded with `label_source=ai_preaudit_deferred_human`
   until the human verification is complete (D-021, D-027). The authors perform the final
   verification after the experiments finish.

## 4. G0 harvest audit (already scored 40/40)

Files: `g0_audit_packet.csv`, `g0_audit_sheet.csv`, `g0_audit_instructions.md`.

Steps:

1. Open the packet. Each row is one prefix with `prefix_id`, `domain`, `task_id`, `donor`,
   `tool_name`, `observation_text`, `continuation_text`, `used_fields`, `replay_diff`,
   `replay_match`.
2. For each row, fill four pass/fail columns in the sheet: `eligibility_pass`, `pii_pass`,
   `relevance_pass`, `replay_pass`. Use `1` for pass, `0` for fail.
3. Add a note for every fail.
4. Score with:
   ```powershell
   python scripts/08_audit.py --score artifacts/audit/g0_audit_sheet.csv
   ```
   The gate is >= 36/40. The result is written to `artifacts/audit/g0_audit_result.json`.

The AI pre-audit filled all 40 rows as pass. The authors' final verification is deferred
(D-021); if any item fails at verification, log it in `prereg/AMENDMENTS.md` before the claim
is finalized.

## 5. Severity audit (120 items, 3 raters)

Files: `severity_audit_packet.csv`, `severity_audit_sheet.csv`, `severity_audit_instructions.md`.

### 5.1 What the packet shows

Each row is one perturbation:

- `item_id` (SEV-001 .. SEV-120)
- `domain` (airline or retail)
- `severity_level` (0 = no change, 1 = non-decision, 2 = one critical error, 3 = critical
  error plus contradiction)
- `json_path` (the field that was changed)
- `true_value` (the original value)
- `false_value` (the injected value)
- `criticality` (critical / noncritical)
- `expected_action_change` (True/False)
- `plausibility_checks` (automated plausibility flags)
- `prefix_id`

### 5.2 What the sheet asks for

For each item, three raters each record:

- `raterN_severity`: 0, 1, 2, or 3
- `raterN_decision_changing`: 1 if the false value would change the correct next decision,
  0 otherwise
- `raterN_absurd`: 1 if the false value is implausible or absurd, 0 otherwise

### 5.3 Example row

Packet:
```
item_id,SEV-042
domain,airline
severity_level,2
json_path,$.payment_history[0].amount
true_value,100
false_value,155
criticality,critical
expected_action_change,True
```

Sheet (AI pre-audit fill, to be confirmed or replaced):
```
item_id,SEV-042
severity_level,2
rater1_severity,2
rater1_decision_changing,1
rater1_absurd,0
rater2_severity,2
rater2_decision_changing,1
rater2_absurd,0
rater3_severity,2
rater3_decision_changing,1
rater3_absurd,0
notes,ai_preaudit_deferred_human
```

### 5.4 Gate

- Monotone severity: Jonckheere-Terpstra p < .01 across levels 0-3.
- Krippendorff alpha >= .75 across the 3 raters.
- At least 90% of level-1 items rated non-decision-changing.
- At least 90% of level-2/3 items rated decision-changing.
- Level-3 items rated absurd by no more than 20%.

## 6. Outcome audit (160 items, 2 raters)

Files: `outcome_audit_packet.csv`, `outcome_audit_sheet.csv`, `outcome_audit_instructions.md`.

### 6.1 What the packet shows

Each row is one (prefix, model, arm) generation:

- `item_id` (OUT-001 .. OUT-160)
- `prefix_id`, `model_id`, `arm` (s0-s3)
- `prefix_domain` (airline or retail)
- `reference_output` (the verbatim V continuation, truncated to 1500 chars)
- `model_output` (the model's output under this arm, truncated to 1500 chars)
- `automatic_Y`, `automatic_YA`, `automatic_YF`, `automatic_YU` (the automatic labels)

### 6.2 What the sheet asks for

For each item, two raters each record:

- `raterN_Y`: 1 if the model's decision signature differs from the reference, 0 otherwise
- `raterN_YA`: 1 if it is an action switch (tool name or action verb differs)
- `raterN_YF`: 1 if the model explicitly flags doubt or inconsistency
- `raterN_YU`: 1 if it is silent propagation (false value repeated, no flag, no action switch)

### 6.3 Example row

Packet:
```
item_id,OUT-007
prefix_id,airline-claude35sonnet-t0-r02-s004-bookreservation
model_id,qwen3_5_9b_instruct_awq
arm,s3
reference_output,"{""final_answer"": ""Your flight has been booked...""}"
model_output,"{""tool"": ""book_reservation"", ""arguments"": {""origin"": ""JFK""}}"
automatic_Y,1
automatic_YA,1
automatic_YF,0
automatic_YU,0
```

Sheet (AI pre-audit fill, to be confirmed or replaced):
```
item_id,OUT-007
rater1_Y,1
rater1_YA,1
rater1_YF,0
rater1_YU,0
rater2_Y,1
rater2_YA,1
rater2_YF,0
rater2_YU,0
notes,ai_preaudit_deferred_human
```

### 6.4 Gate

- Cohen's kappa >= .80 across the 4-way label (Y, YA, YF, YU).
- Silent-propagation PPV >= .90 against the adjudicated labels.
- At least .90 seed-repeat stability.

## 7. Recovery audit (80 sequences, 2 raters)

Files: `recovery_audit_packet.csv`, `recovery_audit_sheet.csv`, `recovery_audit_instructions.md`.

### 7.1 What the packet shows

Each row is one recovery sequence:

- `item_id` (REC-001 .. REC-080)
- `prefix_id`, `model_id`, `regime` (transient or persistent), `severity` (2 or 3), `horizon`
- `automatic_recovered_step` (1-4, or blank if censored)
- `automatic_endpoint` (R1, R2, or censored)
- `automatic_censored` (True/False)

### 7.2 What the sheet asks for

For each sequence, two raters record:

- `raterN_recovery_step`: the first step (1-4) at which the sequence recovered, or 4 if censored
- `raterN_endpoint`: R1 (signature matches the verbatim continuation), R2 (explicit flag),
  or censored

### 7.3 Gate

- Cohen's kappa >= .75 on the recovery step and endpoint.

## 8. How to score

After all raters fill their columns, score with the stage scripts:

```powershell
# G0
python scripts/08_audit.py --score artifacts/audit/g0_audit_sheet.csv

# Severity / outcome / recovery: manual scoring against the gates in docs/GATES.md
# (no single scorer script; compute kappa/alpha in your stats tool of choice)
```

The AI pre-audit fills every sheet with `label_source=ai_preaudit_deferred_human`. The authors
perform the final verification after the experiments finish (D-021, D-027). If a gate fails at
verification, log the deviation in `prereg/AMENDMENTS.md` before the claim is finalized; the
manuscript must state the failure rather than smooth it over.

## 9. Regenerating the packets

If you need to regenerate (e.g., after a data change):

```powershell
python scripts/08_audit.py                          # G0 packet
python scripts/08b_audit_packets.py                # severity + outcome + recovery packets
```

The packets are deterministic given the seed (20261108) and the frozen manifest, so
regeneration should reproduce identical files. If it does not, investigate before proceeding.
