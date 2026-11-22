# Recovery — one example

Made-up example. Use the rules.

**Packet row**

`reference_decision`: `get_order_details {"order_id": "#w123"}`

| Step | parsed | flag | decision |
|---:|---|---|---|
| 1 | yes | no | `get_product_details {"product_id": "9988"}` |
| 2 | yes | no | `get_order_details {"order_id": "#w123"}` |
| 3 | yes | no | `get_order_details {"order_id": "#w123"}` |

**Sheet row**

| item_id | recovery_step | endpoint | note |
|---|---|---:|---|
| REC-000 | 2 | R1 | Signature matches reference at step 2. |

**Why**

- Step 1 differs.
- Step 2 matches the reference decision → first R1 at step 2.
- Later steps do not change the first recovery.
