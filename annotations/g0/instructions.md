# G0 audit — 40 items

**Time:** 45–60 min.

| | |
|---|---|
| 🎯 What | Check four things for each prefix: eligibility, PII, relevance, replay. |
| 📂 From | [packet.csv](packet.csv) — one row per prefix. |
| ✍️ Fill | [sheet.csv](sheet.csv) — one row per `item_id`. |
| 📝 Example | [example.md](example.md) |
| 📏 Rules | [common/rubrics.md](../common/rubrics.md#g0-audit-40-items) |

**How**

1. Open `packet.csv`. Read `observation` and `continuation`.
2. In `sheet.csv`, put `1` or `0` in each of the four columns.
3. Write one short note for every `0`.
4. For `replay_pass`, read `replay_diff` only. `exact` or `normalized` = 1; anything else = 0.

**Done when:** 40 rows filled, no blanks, no new columns.

**If stuck:** choose the best answer, write `unsure: ...` in `note`, and continue.
