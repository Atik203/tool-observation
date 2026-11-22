# G0 — one example

This is a made-up example. Do not copy the answer; use the rules.

**Packet row**

| item_id | observation | continuation | used_fields | replay_diff |
|---|---|---|---|---|
| G0-000 | `{"order_id": "#W123", "status": "pending", "name": "person_ab12"}` | “Order #W123 is still pending. Do you want to cancel it?” | `["$.order_id", "$.status"]` | `exact` |

**Sheet row**

| item_id | eligibility_pass | pii_pass | relevance_pass | replay_pass | note |
|---|---:|---:|---:|---:|---|
| G0-000 | 1 | 1 | 1 | 1 | Order and status are both used. |

(`domain` is pre-filled in your sheet — do not change it. `note` may be empty when every check is `1`.)

**Why**

- It ends after a real tool result and asks a decision question → `eligibility_pass=1`.
- `person_ab12` is a synthetic token, not a raw name → `pii_pass=1`.
- Both listed fields appear in the continuation → `relevance_pass=1`.
- `replay_diff=exact` → `replay_pass=1`.
