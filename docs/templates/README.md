# Submission templates

These are the only formats the co-author team should use. Download the template, save a copy
with your initials, fill every row, and upload it to the shared annotation folder. Do not change
the column names.

**Guide:** [`docs/COAUTHOR_GUIDE.md`](../COAUTHOR_GUIDE.md)  
**Repository:** <https://github.com/Atik203/tool-observation>

---

## Which template do I use?

| Task | Template | Who uses it | Submit as |
|---|---|---|---|
| G0 data/PII/replay audit | [`g0_audit_template.csv`](g0_audit_template.csv) | Author 2 | `g0_audit_batch01_<initials>.csv` |
| Severity ratings | [`severity_rating_template.csv`](severity_rating_template.csv) | Author 2, 3, 4 | `severity_batch01_<initials>.csv` |
| Outcome ratings | [`outcome_rating_template.csv`](outcome_rating_template.csv) | Author 3, 4 | `outcome_batch01_<initials>.csv` |
| Recovery ratings | [`recovery_rating_template.csv`](recovery_rating_template.csv) | Author 3, 4 | `recovery_batch01_<initials>.csv` |
| Adjudication | [`adjudication_template.csv`](adjudication_template.csv) | Author 2 | `adjudication_outcome.csv`, `adjudication_recovery.csv` |
| Agreement report | [`agreement_report_template.md`](agreement_report_template.md) | Author 3 | `agreement_report.md` |
| Training notes | [`training_notes.md`](training_notes.md) | Author 3 | `training_notes.md` |
| Paper support | [`paper_support_checklist.md`](paper_support_checklist.md) | Author 4 | `paper_support_checklist_<initials>.md` |
| Final submission | [`submission_checklist.md`](submission_checklist.md) | All | `submission_<initials>.md` |

---

## How to submit

1. Open the template link.
2. Download it or make a copy in the shared folder.
3. Rename it using the pattern in the table above. Replace `<initials>` with your initials.
4. Fill every row. Do not delete rows or add columns.
5. Check that the row count matches the batch manifest.
6. Upload the file to the shared annotation folder.
7. Post the file name and row count in the GitHub issue for your task.
8. Keep the original batch file unchanged.

**Shared folder:** Author 1 will paste the link in the GitHub issue and in the team channel
before Day 1. Do not use a public folder for raw data or PII.

---

## Rules

- Do not change the header row.
- Do not add extra columns.
- Do not leave a label blank. Use `other` if the response is outside the taxonomy.
- Use the exact label strings from the rubric.
- Do not put names, emails, phone numbers, addresses, or payment identifiers in `notes`.
- Do not email or chat raw data. Use the shared folder.
- If you are unsure, set confidence low and write a short note.

---

## Exact label strings

### Outcome

```text
silent_propagation
flagged
action_switch
same
other
```

### Recovery

```text
corrected
flagged
still_wrong
```

### Pass/fail columns

```text
pass
fail
```

---

## Need help?

- **Rubric question:** GitHub issue with the `[annotation]` label.
- **PII issue:** private message to Author 1. Do not open a public issue.
- **Access issue:** private message to Author 1.
- **Paper-support question:** GitHub issue with the `[paper]` label.
