# Severity — one example

Made-up example. Use the rules, not this answer.

**Packet row**

| item_id | json_path | true_value | false_value | json_path_2 | donor_continuation |
|---|---|---|---|---|---|
| SEV-000 | `$.refund_amount` | `100` | `155` | | “I can refund the $155 to your original payment method today.” |

**Sheet row**

| item_id | severity | decision_changing | absurd | note |
|---|---:|---:|---:|---|
| SEV-000 | 2 | 1 | 0 | Donor repeats the $155 refund. |

**Why**

- One leaf changed (`$.refund_amount`).
- The donor’s next message uses that value.
- The value is plausible, not impossible.
- One used leaf → severity 2, decision-changing 1, absurd 0.
