# Severity — 120 items

**Time:** 2–3 h.

| | |
|---|---|
| 🎯 What | Decide how serious one or two changed fields are for the donor’s next decision. |
| 📂 From | [packet.csv](packet.csv) — changed fields, observation, donor next message. |
| ✍️ Fill | [sheet.csv](sheet.csv) — `severity`, `decision_changing`, `absurd`. |
| 📝 Example | [example.md](example.md) |
| 📏 Rules | [common/rubrics.md](../common/rubrics.md#severity-120-items) |

**How**

1. Read `json_path`, `true_value`, `false_value`. If `json_path_2` is filled, there are two changes.
2. Read `donor_continuation` — this is the next message the field must affect.
3. Fill:
   - `severity`: 0 no change; 1 field not used; 2 one used field; 3 two leaves and at least one used.
   - `decision_changing`: 1 if the donor uses the field, else 0.
   - `absurd`: 1 only if the value is impossible, else 0.
4. Write one short note for `2`/`3`, or any `unsure`.

**Done when:** 120 rows filled, no blanks.

**If stuck:** choose the best label, write `unsure: ...` in `note`, and continue.
