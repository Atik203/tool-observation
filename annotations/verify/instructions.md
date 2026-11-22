# Verify agent labels — 20 items

**Time:** 45–60 min.

| | |
|---|---|
| 🎯 What | Check whether an agent’s outcome label is correct. |
| 📂 From | [packet.csv](packet.csv) — evidence and `agent_label`. |
| ✍️ Fill | [sheet.csv](sheet.csv) — `your_label`, `agree`, `note`. |
| 📝 Example | [example.md](example.md) |
| 📏 Rules | [common/rubrics.md](../common/rubrics.md#outcome-160-items) · [how to fill](../common/how_to_fill.md) · [glossary](../common/glossary.md) |

**How**

1. Read `evidence_text`: reference, model output, injected false value.
2. Read `agent_label` (for example `Y=1; YA=0; YF=1; YU=0`).
3. Decide the correct label yourself using the Outcome rules.
4. Fill:
   - `your_label`: write your four labels in the same format.
   - `agree`: `agree` if the agent is correct, `disagree` if it is wrong.
   - `note`: one short reason if `disagree`; otherwise leave it empty.

**Done when:** 20 rows filled, no blanks in answer cells (`note` may be empty when `agree` is `agree`).

**If stuck:** choose the best label, write `unsure: ...` in `note`, and continue.
