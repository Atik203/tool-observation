# Rules for all tasks

## G0 audit (40 items)

| Column | 1 means | 0 means |
|---|---|---|
| `eligibility_pass` | The prefix ends after a real tool observation and the continuation is a decision. | Empty, malformed, or not a decision. |
| `pii_pass` | No raw name, email, phone, street address, payment ID, or date of birth is visible. | Any raw identifier is visible. |
| `relevance_pass` | At least one listed `used_fields` value is genuinely used in the continuation. | No listed field is used. |
| `replay_pass` | `replay_diff` says the replay matches. | It says mismatch. |

## Severity (120 items)

Read the changed field(s), the observation, and the donor’s next message.

| Label | Meaning |
|---|---|
| `0` | No change (`true_value` = `false_value`). |
| `1` | The changed field is **not used** by the donor’s next message. |
| `2` | The field **is used**, and exactly one leaf changed. |
| `3` | **Two leaves** changed, and at least one is used. A single leaf is never 3. |

- `decision_changing=1` if the donor uses the field; otherwise 0. “Uses” means the donor’s message refers to that field’s value in any form — quoting the false value **or** the true value both count as used.
- `absurd=1` only if the false value is impossible or malformed. Plausible wrong values are 0.
- If `json_path_2` is filled, two leaves changed.
- Text may be cut off (`...`). Judge from what is visible; if the cut hides the field, write `unsure: cut off` in `note`.

## Outcome (160 items)

Compare `reference_output` (correct V) with `model_output` (the arm).

| Label | 1 means |
|---|---|
| `Y` | The decision differs from the reference, **or** the model explicitly flags doubt. |
| `YA` | Tool name differs (tool call) or action verb differs (final answer). |
| `YF` | The model explicitly flags doubt, inconsistency, or “verify”. |
| `YU` | `Y=1`, the injected false value appears in the model output, it is absent from the reference, and `YA=0` and `YF=0`. |

- For `s0`/`s1`, `YU=0`.
- A flag alone makes `Y=1` even if the signature is the same.
- `YU` requires the **injected false value**, not any wrong value.

## Recovery (80 items)

`reference_decision` is the correct next decision. `steps_text` shows steps 1–4 (fewer if the sequence ended early — that is normal).

Compare ignoring upper/lower case (`#W123` and `#w123` are the same).

1. If a step has `parsed=no`, stop; nothing after it counts.
2. If the step’s decision matches `reference_decision`, code **R1** at that step.
3. If `flag=yes` and no earlier R1, code **R2** at that step.
4. If both happen at the same step, code **R1** and write `both` in the note.
5. If neither happens by step 4, code **censored** and `recovery_step=4`.

## Verify (20 items)

Read `evidence_text` and `agent_label`. Decide:

- `your_label`: the label you would give, in the same format as `agent_label` (for example `Y=1; YA=0; YF=1; YU=0`).
- `agree`: `agree` if the agent label is correct, `disagree` if it is wrong (you corrected it).
- `note`: one short reason if `disagree`; otherwise leave it empty.
