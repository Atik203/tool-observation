# Outcome — 160 items

**Time:** 3–4 h.

| | |
|---|---|
| 🎯 What | Compare the model’s output with the correct reference and label the difference. |
| 📂 From | [packet.csv](packet.csv) — reference, model output, injected false value. |
| ✍️ Fill | [sheet.csv](sheet.csv) — `Y`, `YA`, `YF`, `YU`. |
| 📝 Example | [example.md](example.md) |
| 📏 Rules | [common/rubrics.md](../common/rubrics.md#outcome-160-items) · [how to fill](../common/how_to_fill.md) · [glossary](../common/glossary.md) |

**How**

1. Read `reference_output` (correct V) and `model_output` (the arm).
2. Check `injected_path` and `injected_false_value` (blank for s0).
3. Fill `0`/`1`:
   - `Y`: decision differs, or the model flags doubt.
   - `YA`: tool name or action verb differs.
   - `YF`: explicit doubt/inconsistency language.
   - `YU`: `Y=1`, false value appears in model output, absent from reference, `YA=0`, `YF=0`.
4. Write one short note for any `1`. If every label is `0`, `note` may be empty.

**Done when:** 160 rows filled, no blanks in answer cells (`note` may be empty when every label is `0`), no new columns.

**If stuck:** choose the best label, write `unsure: ...` in `note`, and continue.
