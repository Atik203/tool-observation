# How to fill a sheet

1. Open `packet.csv` and `sheet.csv` in Excel, LibreOffice, or Google Sheets.
2. Keep the first row (the header). Do not add or remove columns.
3. Fill one row per `item_id`. The `item_id` is already filled for you.
4. Use only the allowed values:
   - `0` / `1` for yes/no checks
   - `0` / `1` / `2` / `3` for severity
   - `R1` / `R2` / `censored` for recovery
5. No blanks. If you are unsure, choose the best answer and write `unsure: ...` in `note`.
6. Save as **CSV UTF-8** with the same filename.
7. Do not edit `packet.csv`. It is the evidence.
8. Do not rename the file or add extra columns.

**Check before sending**

- [ ] Every row has an answer.
- [ ] No new columns.
- [ ] File still opens in Excel/Sheets.
- [ ] You did not use an AI assistant.
