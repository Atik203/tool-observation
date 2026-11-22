# Recovery — 80 items

**Time:** 2–3 h.

| | |
|---|---|
| 🎯 What | Find the first step where the model returns to the reference decision or flags the problem. |
| 📂 From | [packet.csv](packet.csv) — reference decision and steps 1–4. |
| ✍️ Fill | [sheet.csv](sheet.csv) — `recovery_step`, `endpoint`, `note`. |
| 📝 Example | [example.md](example.md) |
| 📏 Rules | [common/rubrics.md](../common/rubrics.md#recovery-80-items) · [how to fill](../common/how_to_fill.md) · [glossary](../common/glossary.md) |

**How**

1. Read `reference_decision`.
2. Read `steps_text` from step 1 upward. Fewer than 4 steps shown is normal: the sequence ends early when the model recovers, gives a final answer, or fails to parse.
3. Compare ignoring upper/lower case (`#W123` and `#w123` are the same).
4. Find the first step where:
   - the decision matches `reference_decision` → `R1`
   - or `flag=yes` → `R2`
5. Fill all three columns: `recovery_step`, `endpoint`, `note`. For `note`, write `both` if both happen at the same step, `unsure: ...` if unsure, otherwise leave it empty.
6. If `parsed=no`, stop; nothing after it counts.
7. If nothing by step 4 → `endpoint=censored`, `recovery_step=4`.

**Done when:** 80 rows filled, no blanks in answer cells, no new columns.

**If stuck:** choose the best label, write `unsure: ...` in `note`, and continue.
