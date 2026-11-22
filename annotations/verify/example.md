# Verify — one example

Made-up example. Use the rules.

**Packet row**

| item_id | evidence_text | agent_label |
|---|---|---|
| OUT-000 | Reference: `get_order_details {"order_id": "#W123"}` · Model: `get_product_details {"product_id": "9988"}` · Injected false value: `"#W999"` | `Y=0; YA=0; YF=0; YU=0` |

**Sheet row**

| item_id | task | your_label | agree | note |
|---|---|---|---|---|
| OUT-000 | outcome | `Y=1; YA=1; YF=0; YU=0` | disagree | Tool name changed; agent said no change. |

**Why**

- The model uses a different tool → `Y=1`, `YA=1`.
- No flag, and the false value is not repeated → `YF=0`, `YU=0`.
- The agent label says no change, so it is wrong → `disagree`.
