# Co-author annotation guide

**Status:** the annotation kit in this folder is final. This guide orients co-authors; it does not
replace the kit. Anything here that disagrees with a task's `instructions.md` or
`common/rubrics.md` — the kit wins.

**No prior experience needed.** Start with the [kit README](README.md) and your task's
`instructions.md` + `example.md`.

## 1. What you are doing

We freeze a real agent conversation right after a tool result, change the result's content, and
measure what the agent does next. Your job is human judgment the pipeline cannot do: check the
frozen data and label what the agent did. Fill one `sheet.csv` per task and send it back. That is
the whole job.

## 2. Pick your task

| Task | Items | Time | Start here |
|---|---|---:|---|
| G0 audit | 40 | 45–60 min | [g0/instructions.md](g0/instructions.md) |
| Severity | 120 | 2–3 h | [severity/instructions.md](severity/instructions.md) |
| Outcome | 160 | 3–4 h | [outcome/instructions.md](outcome/instructions.md) |
| Recovery | 80 | 2–3 h | [recovery/instructions.md](recovery/instructions.md) |
| Verify agent labels | 20 | 45–60 min | [verify/instructions.md](verify/instructions.md) |

Each task folder has the same four files: `instructions.md` (what to do), `packet.csv` (the
evidence), `sheet.csv` (the file you fill), `example.md` (one worked row).

First time: read [how to fill](common/how_to_fill.md), [glossary](common/glossary.md), and
[rules](common/rubrics.md) — then your task's `example.md` before touching the sheet.

## 3. Roles

- **Annotators (you):** fill your assigned sheet(s) independently. Do not open another rater's
  sheet and do not discuss individual items until everyone has submitted.
- **Project owner:** prepares packets, computes agreement (Cohen's κ, Krippendorff's α),
  adjudicates disagreements, and logs decisions. Send questions and PII reports to them, not to
  other raters.

## 4. Rules that protect the study

1. **No AI assistance** filling sheets — you are the human check. Do not paste packet content
   into any AI tool.
2. **Do not edit `packet.csv`.** Fill `sheet.csv` only; keep `item_id`, add no columns.
3. **PII:** if you see a raw name, email, phone, address, payment ID, or date of birth, mark the
   row failed, report it privately to the owner immediately, and never copy the value anywhere.
4. **Frozen files are read-only:** `prereg/PREREGISTRATION.md`,
   `data/manifests/toolresult800_v1.json`, perturbation records, field registry, renderer.
   Questions go to the owner, who logs them in `docs/DECISIONS.md`.
5. **No blanks** in answer cells (`note` may be empty only where your task allows it). Unsure?
   Choose the best label and write `unsure: ...` in `note`.
6. **No fabricated numbers.** Every figure in the paper must trace to a ledger, manifest, or
   artifact — if a packet looks wrong, stop and report it instead of guessing.

## 5. Done means

| Task | Done when |
|---|---|
| G0 | 40 rows filled; every `0` has a one-line note |
| Severity | 120 rows: `severity` + `decision_changing` + `absurd` |
| Outcome | 160 rows: `Y`, `YA`, `YF`, `YU` |
| Recovery | 80 rows: `recovery_step` + `endpoint` |
| Verify | 20 rows: `your_label` + `agree`/`disagree` |

Save as **CSV UTF-8** under the same filename and send it to the project owner.

## 6. Background (optional)

- [Glossary](common/glossary.md) — every term used in the kit.
- [Protocol](../docs/PROTOCOL.md) — design, arms, outcomes, recovery.
- [Label rubric](../docs/LABEL_RUBRIC.md) — full annotation reference.
- [Gates](../docs/GATES.md) — pass/fail checkpoints (G0–G4).
- [Data card](../docs/DATA_CARD.md) — what the dataset contains and excludes.
- Old per-role templates (G0/severity/outcome/recovery sheets, adjudication, agreement report)
  remain in [docs/templates](../docs/templates/README.md) for the owner; annotators work from
  this folder's `sheet.csv` files, not from those templates.
