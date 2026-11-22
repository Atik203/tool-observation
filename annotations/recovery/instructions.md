# Recovery — 80 items

**Time:** 2–3 h.

| | |
|---|---|
| 🎯 What | Find the first step where the model returns to the reference decision or flags the problem. |
| 📂 From | [packet.csv](packet.csv) — reference decision and steps 1–4. |
| ✍️ Fill | [sheet.csv](sheet.csv) — `recovery_step`, `endpoint`. |
| 📝 Example | [example.md](example.md) |
| 📏 Rules | [common/rubrics.md](../common/rubrics.md#recovery-80-items) |

**How**

1. Read `reference_decision`.
2. Read `steps_text` from step 1 to 4.
3. Find the first step where:
   - the decision matches `reference_decision` → `R1`
   - or `flag=yes` → `R2`
4. If both happen at the same step, choose `R1` and write `both` in `note`.
5. If `parsed=no`, stop; nothing after it counts.
6. If nothing by step 4 → `endpoint=censored`, `recovery_step=4`.

**Done when:** 80 rows filled, no blanks.

**If stuck:** choose the best label, write `unsure: ...` in `note`, and continue.
