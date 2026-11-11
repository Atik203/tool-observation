# Amendments log - ToolResult-800

The preregistration is frozen at the end of G0. Any change after the freeze is recorded here
**before** the affected analysis runs. An amendment is not a silent edit: it states the trigger,
the original text, the replacement, the analyses affected, and whether the change was made blind
to target-model outcomes.

## Pre-freeze branding note

- **Date:** 2026-11-11
- **Change:** Dataset brand renamed from CTO-800 to **ToolResult-800**; "E2" retired.
- **Analyses affected:** none. No scientific design, sample, analysis, or claim change.
- **Blind to outcomes:** yes; no target-model outcomes have been generated.
- **Record:** `docs/DECISIONS.md` D-006.

## Status

- **Frozen version:** TBD (tag `prereg-freeze-v1`, commit SHA + SHA-256 recorded at G0).
- **Amendments since freeze:** none.

## Format

| ID | Date | Trigger | Original text | Replacement | Analyses affected | Blind to outcomes? | Approved by |
|---|---|---|---|---|---|---|---|
| A-001 | YYYY-MM-DD | What happened | Quote or section | New text | Primary/secondary/exploratory | Yes/No | Name |

## Rules

- Amendments are numbered sequentially and never deleted.
- A change made after seeing the primary outcome is labeled **post-outcome** and cannot support
  the confirmatory claim.
- Every amendment is summarized in `docs/DECISIONS.md` and reported in the paper.
- If an amendment changes the sample, renderer, field registry, or primary analysis, the paper
  reports both the preregistered and amended analyses where feasible.
