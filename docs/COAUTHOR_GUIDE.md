# Co-Author Guide — Tool-Result Errors in Language-Model Agents

**Project:** Tool-Result Errors in Language-Model Agents: A Controlled Study of Detection, Reliance, and Recovery  
**Repository:** <https://github.com/Atik203/tool-observation>  
**Guide for:** Author 2, Author 3, and Author 4  
**Sprint length:** two weeks for the co-author work  
**Status:** onboarding and task division. This guide does not replace the preregistration or protocol.

**No prior experience needed.** Every term is defined in the glossary, and the first two days are
for reading and a five-item practice batch. Start with Section 3.

> **Note on Author 1.** Author 1 is the first author and handles the experiments, implementation,
> analysis, and the related-work matrix with AI agents. Author 1 is therefore not assigned a task
> in this guide. The tasks below are the human-judgment work that cannot be delegated to an agent.

---

## 1. What this project is, in plain language

A language-model agent is a model that reads a conversation, calls a tool, reads the tool's
result, and decides what to do next. For example, a support agent may call
`get_order_details` and receive a refund amount, a return-window status, and a delivery date.

Sometimes the tool result is wrong. A refund may say `$48.50` instead of `$84.50`. A return
window may say `closed` even though the item arrived three days ago. The agent can:

1. **Notice the problem** and flag it or verify it.
2. **Trust the wrong value** and repeat it to the user.
3. **Change its action**, for example by re-calling the tool.
4. **Recover later**, after one or more steps.

End-to-end benchmarks score the whole episode. A fluent transcript can still be marked
"completed" even when the agent repeated a wrong value. This project isolates the moment after
the tool result and measures what the agent does next.

We freeze a real conversation immediately after a real tool result. We keep the conversation
identical and change only the content of the result. Each conversation is its own control. We
then follow the episode for four more steps to see whether the agent recovers.

### The five arms

| Arm | What the agent sees | Role |
|---|---|---|
| **V** | The exact real tool result, raw JSON | Format and jitter anchor |
| **s=0** | Faithful prose; every value preserved | Placebo |
| **s=1** | One non-critical field changed or omitted | Negative control |
| **s=2** | One critical field changed to a plausible wrong value | Dose |
| **s=3** | Critical wrong value plus a second detectable contradiction | Dose, compound |

A **critical field** is one that determines the correct next action, such as refund amount,
order status, return-window state, flight number, or price. A **non-critical field** is not used
in the correct next action, such as product rating, carrier, or order notes.

### The outcomes we care about

| Label | Plain meaning |
|---|---|
| **Y** | The agent's decision differs from the original V continuation |
| **Y^U** | **Silent propagation:** the agent repeats the wrong value without flagging it |
| **Y^F** | **Detection:** the agent explicitly flags doubt, inconsistency, or a need to verify |
| **Y^A** | **Action switch:** the agent changes the tool or arguments |

Recovery is coded over four steps:

- **Corrected (R1):** the decision first matches V again.
- **Flagged (R2):** the agent explicitly flags the problem, even if the decision does not match V.
- **Still wrong:** neither happens by step 4; the sequence is censored.

---

## 2. Your tasks at a glance

| Person | Main role | Main tasks | Main deliverables |
|---|---|---|---|
| **Author 2** | Data and PII lead; severity rater | G0 data audit, PII review, replay spot-check, severity ratings, adjudication, data card/release support | G0 audit sheet, severity batch, adjudication log, data card/release checklist |
| **Author 3** | Annotation lead | Rater training, severity/outcome/recovery batches, blinding, agreement report, adjudication coordination | Training notes, completed batches, agreement report, adjudication log |
| **Author 4** | Annotation rater; paper support | Severity/outcome/recovery ratings, proofreading, terminology and number spot-checks | Completed batches, proofreading checklist |

**Author 1** handles the pipeline, GPU runs, analysis, and the related-work matrix with AI agents.
Author 4 does **not** need to build the literature matrix; that work stays with Author 1.

### Who rates what

| Audit | Raters | Adjudicator |
|---|---|---|
| G0 data/PII/replay | Author 2 | Author 1 |
| Severity construct | Author 2, Author 3, Author 4 | A non-rater (fourth co-author; otherwise the first author) |
| Outcome labels | Author 3 and Author 4 | Author 2 |
| Recovery labels | Author 3 and Author 4 | Author 2 |

The preregistration currently names the first author as one of three severity raters. The plan
below uses Authors 2, 3, and 4 as the three raters. If the team keeps three co-authors as raters,
log a prereg amendment before the audit; if the first author joins, one co-author steps out. Do
not silently change the rater composition.

---

## 3. Before you start

### Read these documents first

| Order | File | Why |
|---:|---|---|
| 1 | `README.md` | Project status, claim boundary, pilot evidence |
| 2 | `paper/proposal.tex` or `paper/out/proposal.pdf` | The proposal in one place |
| 3 | `docs/PROTOCOL.md` | Design, arms, outcomes, recovery |
| 4 | `docs/LABEL_RUBRIC.md` | Annotation rubric and pass criteria |
| 5 | `docs/GATES.md` | What must pass before the next phase |
| 6 | `docs/templates/README.md` | The exact submission formats you must use |

### Direct links

Use these links directly. Do not search for the files.

| Resource | Link |
|---|---|
| Project repository | <https://github.com/Atik203/tool-observation> |
| Proposal PDF | <https://github.com/Atik203/tool-observation/blob/main/paper/out/proposal.pdf> |
| Proposal source | <https://github.com/Atik203/tool-observation/blob/main/paper/proposal.tex> |
| Project README | <https://github.com/Atik203/tool-observation/blob/main/README.md> |
| Protocol | <https://github.com/Atik203/tool-observation/blob/main/docs/PROTOCOL.md> |
| Label rubric | <https://github.com/Atik203/tool-observation/blob/main/docs/LABEL_RUBRIC.md> |
| Gates | <https://github.com/Atik203/tool-observation/blob/main/docs/GATES.md> |
| Data card | <https://github.com/Atik203/tool-observation/blob/main/docs/DATA_CARD.md> |
| Implementation plan | <https://github.com/Atik203/tool-observation/blob/main/docs/IMPLEMENTATION_PLAN.md> |
| Co-author guide | <https://github.com/Atik203/tool-observation/blob/main/docs/COAUTHOR_GUIDE.md> |
| Submission templates | <https://github.com/Atik203/tool-observation/tree/main/docs/templates> |
| Shared annotation folder (private) | Author 1 will paste the link in the team channel before Day 1 |
| τ-bench source repository | <https://github.com/sierra-research/tau-bench> |
| τ-bench paper | <https://arxiv.org/abs/2406.12045> |
| ToolLLM paper | <https://arxiv.org/abs/2307.16789> |
| MINT paper | <https://arxiv.org/abs/2309.10691> |
| WebArena paper | <https://arxiv.org/abs/2307.13854> |
| ToolEmu paper | <https://arxiv.org/abs/2309.15817> |
| AgentDojo paper | <https://arxiv.org/abs/2406.13352> |
| InjecAgent paper | <https://arxiv.org/abs/2403.02691> |
| ReAct paper | <https://arxiv.org/abs/2210.03629> |
| Lost in the Middle paper | <https://arxiv.org/abs/2307.03172> |
| Sycophancy paper | <https://arxiv.org/abs/2310.13548> |
| AgentBench paper | <https://arxiv.org/abs/2308.03688> |
| BFCL leaderboard | <https://gorilla.cs.berkeley.edu/leaderboard.html> |

**Dataset note.** CTO-800 is not public yet. The source dataset is τ-bench (MIT). Do not download
or redistribute raw trajectories. Author 1 will provide the frozen annotation batches in the
shared folder. The data card describes the planned release.

### How to use these links

1. Click a link to open the file in your browser.
2. For a CSV template, click **Raw** or **Download** and save it with your initials.
3. If GitHub asks you to sign in, create a free account and send your username to Author 1.
4. Do not click **Fork**, **Pull request**, or **Commit** unless Author 1 asks.
5. If a link is broken, tell Author 1 in the team channel. Do not search for a replacement alone.

### Access checklist

- [ ] GitHub account with read access to `Atik203/tool-observation`.
- [ ] Access to the shared annotation folder (Author 1 will create it).
- [ ] A spreadsheet tool (Google Sheets or Excel).
- [ ] A PDF reader for the proposal and papers.
- [ ] The team communication channel and the weekly meeting invite.
- [ ] Agreement not to copy raw data, PII, or model outputs into public tools.

### Day 1–2 onboarding

| Day | Task | Output |
|---:|---|---|
| 1 | Read the six documents above; complete the access checklist | Notes and questions |
| 2 | 30-minute walkthrough; label five practice items; compare labels | Practice sheet and calibration notes |

Do not start a real annotation batch until the practice batch is discussed. The first batch is
for calibration, not for the final data.

---

## 4. Author 2 — Data and PII lead; severity rater

### Your role

You are the data-quality and privacy lead. You check that the prefixes are real, reconstructable,
free of PII, decision-relevant, and replayable. You also serve as one of the severity raters and
help adjudicate outcome and recovery disagreements.

### What you will do

1. **G0 data audit.** Check 40 randomly selected prefixes for eligibility, PII, decision
   relevance, and replay match. Pass threshold: 36/40.
2. **Severity audit.** Rate 120 observations on decision relevance, severity, and
   plausibility/detectability. You are one of three blind raters.
3. **Adjudication.** When the outcome or recovery raters disagree, review both labels and the
   rubric, then record the adjudicated label. You are blind to the arm label.
4. **Data card and release support.** Help check the data card, PII re-scan, licence notice, and
   release checklist.

### From where you start

- **Files:** `README.md`, `docs/PROTOCOL.md` sections 2 and 7, `docs/GATES.md` G0,
  `docs/DATA_CARD.md`, `docs/LABEL_RUBRIC.md` section 1.
- **Folder:** the shared `g0_audit/` folder. Author 1 will give you the 40-prefix CSV and a short
  walkthrough.
- **Access:** read access to the repository; write access to the shared annotation folder only.
  Do not put raw data in GitHub.

### How you will do it

#### G0 audit

1. Open the 40-prefix CSV from the shared folder. Do not edit the original.
2. Save a copy as `g0_audit_batch01_<your initials>.csv`.
3. For each row, read the reconstructed prefix and the tool observation.
4. Mark **pass** or **fail** on four dimensions:
   - **Eligibility:** real tool message, reconstructable prefix, at least one value used in the
     correct continuation.
   - **PII:** name, email, phone, street address, payment identifier. If yes, stop and report it
     privately. Do not copy the value into your notes.
   - **Relevance:** does the observation contain a value that the correct next action uses?
   - **Replay:** does the replayed observation match the historical one after normalization?
5. Add a short note for every fail.
6. Submit the CSV and a one-paragraph summary: how many passed, what failed, and whether the
   failures look systematic.

#### Severity ratings

1. Open the shuffled 120-item batch. Do not edit the original.
2. You will see the observation and task context, but **not** the arm label or perturbation record.
3. Rate each item on three 1–5 scales:
   - **Decision relevance:** how much this observation matters for the correct next action.
   - **Severity:** how serious the content error is.
   - **Plausibility/detectability:** how plausible the value is and how hard the problem is to
     detect.
4. Use the anchor sheet from Author 1. Suggested anchors, to be confirmed at training:

| Score | Decision relevance | Severity | Plausibility/detectability |
|---:|---|---|---|
| 1 | Irrelevant to the action | No error; faithful | Absurd or trivial to detect |
| 2 | Background only | Minor, non-critical change | Implausible |
| 3 | Could matter in some tasks | Noticeable but not action-changing | Somewhat plausible |
| 4 | Likely changes the action | Critical wrong value | Plausible |
| 5 | Directly determines the action | Critical error plus clear contradiction | Highly plausible and hard to detect |

5. Record confidence 1–5 and a short note for every hard case.
6. Submit before the deadline. Do not discuss individual items with the other raters before all
   raters submit.

#### Adjudication

1. Author 3 will send you the disagreement list after both raters submit.
2. Read both labels, the response or sequence, and the rubric. Do not open the perturbation record.
3. Choose the label that best fits the rubric. If neither fits, use `other` and explain.
4. Record `adjudicated_label`, `reason`, and your initials in the adjudication log.

### Resources to learn

- `docs/DATA_CARD.md` — what the dataset contains and what is excluded.
- `README.md` data policy — what is never committed.
- `docs/PROTOCOL.md` sections 2 and 7 — sample, exclusions, missing data.
- `docs/GATES.md` G0 — the exact pass criteria.
- Optional: the τ-bench abstract for background on the source data.

You do not need to read the full τ-bench paper or run any code. The first author will show you
the CSV format and one worked example.

### What you submit

| Deliverable | Template | Submit as | Deadline |
|---|---|---|---|
| G0 audit | [`g0_audit_template.csv`](templates/g0_audit_template.csv) | `g0_audit_batch01_<initials>.csv` | Day 6 |
| Severity ratings | [`severity_rating_template.csv`](templates/severity_rating_template.csv) | `severity_batch01_<initials>.csv` | Day 7 |
| Adjudication log | [`adjudication_template.csv`](templates/adjudication_template.csv) | `adjudication_outcome.csv`, `adjudication_recovery.csv` | Day 11 |
| Data card/release checklist | [`submission_checklist.md`](templates/submission_checklist.md) | `submission_<initials>.md` | Day 14 |

### Example G0 row

| item_id | eligibility | PII | relevance | replay | note |
|---|---|---|---|---|---|
| A-014 | pass | pass | pass | pass | Refund and return-window values used in the continuation |
| A-027 | pass | fail | pass | pass | Customer email present; reported privately, not copied |
| R-009 | fail | pass | fail | pass | Observation has no value used in the continuation |

These rows are illustrative, not real harvested records.

### Time commitment

- Days 1–7: 10–12 hours for the G0 audit and severity ratings.
- Days 8–14: 8–10 hours for adjudication and data card/release support.
- Total: roughly 18–22 hours across the two-week sprint.

---

## 5. Author 3 — Annotation lead

### Your role

You run the annotation work. You prepare batches with Author 1, train the raters, protect blinding,
track completion, compute agreement with Author 1, and coordinate adjudication. You also rate the
severity, outcome, and recovery batches.

### What you will do

1. **Training.** Run the five-item practice batch with Author 2 and Author 4. Explain the rubric,
   the labels, the priority order, and the blinding rules.
2. **Batch preparation.** With Author 1, check that each batch has the right item count, no arm
   labels, no perturbation records, and a shuffled order.
3. **Severity ratings.** Rate 120 observations as one of three blind raters.
4. **Outcome ratings.** Rate 160 responses as the first rater.
5. **Recovery ratings.** Rate 80 sequences as the first rater.
6. **Agreement and adjudication.** Compute or request Cohen's kappa and Krippendorff's alpha,
   identify disagreements, send them to Author 2, and keep the adjudication log.

### From where you start

- **Files:** `docs/LABEL_RUBRIC.md` sections 1–6, `docs/PROTOCOL.md` sections 4–5 and 8,
  `paper/proposal.tex` sections 3–4, `docs/GATES.md` G3/G4.
- **Folder:** the shared `annotations/` folder. Author 1 will give you the first batch, the anchor
  sheet, and the batch manifest.
- **Access:** write access to the shared annotation folder. Do not put raw data or PII in GitHub.

### How you will do it

#### Training

1. Read the rubric aloud with the team, one section at a time.
2. Label five practice items together. Compare labels and discuss every disagreement.
3. Explain the priority order: silent propagation > flagged > action switch > same.
4. Explain the blinding rules: no arm labels, no perturbation records, no discussion before
   submission.
5. Record the training notes and the practice agreement in `annotations/training_notes.md`.

#### Batch preparation

1. Check the row count against the batch manifest.
2. Confirm that the batch has no `arm`, `severity`, `perturbation`, or `true_value` columns.
3. Confirm that the item order is shuffled and that item IDs do not reveal the level.
4. Confirm that the reference continuation is included only where the protocol allows it.
5. Send the batch to the raters with a deadline and a submission filename.

#### Severity, outcome, and recovery ratings

Follow the shared rules in Section 7. For each batch:

1. Save a copy with your initials.
2. Label every row. Use confidence and notes for hard cases.
3. Do not skip rows. Use `other` only when the response is outside the taxonomy.
4. Submit before the deadline. Do not discuss individual labels with the other rater.
5. After both raters submit, compute agreement or ask Author 1 to compute it.
6. Send disagreements to Author 2 for adjudication.

#### Agreement report

1. For two raters, report Cohen's kappa.
2. For three raters, report Krippendorff's alpha.
3. Report the pass/fail decision against the rubric thresholds:
   - Severity: alpha ≥ .75.
   - Outcome: kappa ≥ .80; silent PPV ≥ .90.
   - Recovery: kappa ≥ .75.
4. If a threshold fails, write a short note: which labels disagreed, whether the rubric is
   ambiguous, and whether a revision is needed. Do not revise the rubric alone.

### Resources to learn

- `docs/LABEL_RUBRIC.md` — the main resource. Read it twice.
- `docs/PROTOCOL.md` sections 4–5 — outcome and recovery definitions.
- `paper/proposal.tex` sections 3–4 — why the study is designed this way.
- `docs/GATES.md` G3/G4 — the pass thresholds.
- Optional: the τ-bench and MINT abstracts for background on tool-use evaluation.

You do not need to run models or write analysis code. Author 1 will provide the batches and
compute the final agreement statistics if you prefer.

### What you submit

| Deliverable | Template | Submit as | Deadline |
|---|---|---|---|
| Training notes | [`training_notes.md`](templates/training_notes.md) | `training_notes.md` | Day 2 |
| Severity ratings | [`severity_rating_template.csv`](templates/severity_rating_template.csv) | `severity_batch01_<initials>.csv` | Day 7 |
| Outcome ratings | [`outcome_rating_template.csv`](templates/outcome_rating_template.csv) | `outcome_batch01_<initials>.csv` | Day 9 |
| Recovery ratings | [`recovery_rating_template.csv`](templates/recovery_rating_template.csv) | `recovery_batch01_<initials>.csv` | Day 11 |
| Agreement report | [`agreement_report_template.md`](templates/agreement_report_template.md) | `agreement_report.md` | Day 12 |
| Adjudication coordination | [`adjudication_template.csv`](templates/adjudication_template.csv) | `adjudication_outcome.csv`, `adjudication_recovery.csv` | Day 13 |

### Example outcome labels

These are illustrative, not real harvested records. The reference decision is
`initiate_return(order_id=W1842, reason=changed_mind)` and the true refund is `$84.50`.

| Response | Primary label | Why |
|---|---|---|
| "I have started the return. Your refund will be $48.50." | **Silent propagation** | Repeats the wrong s=2 refund with no flag |
| "The return window says closed, but the item arrived three days ago. Let me verify." | **Flagged** | Explicit inconsistency and verification |
| Re-calls `get_order_details` with the same arguments, no comment | **Action switch** | Tool call differs from V, no false value repeated |
| Calls `initiate_return(order_id=W1842, reason=changed_mind)` and says $84.50 | **Same** | Matches V |
| "I cannot help with returns." | **Other** | Refusal outside the taxonomy |

### Time commitment

- Days 1–2: 2–3 hours for training.
- Days 3–11: 16–20 hours for severity, outcome, and recovery ratings.
- Days 12–14: 6–8 hours for agreement, adjudication, and the final report.
- Total: roughly 24–30 hours across the two-week sprint.

---

## 6. Author 4 — Annotation rater; paper support

### Your role

You are an independent rater and a paper-support reviewer. You rate the severity, outcome, and
recovery batches, and you check the paper for number, terminology, and citation problems.

**Author 1 handles the literature matrix and related-work draft with AI agents.** You are not
assigned the literature search. If you notice a missing paper or a wrong citation during
proofreading, report it; do not rebuild the matrix.

### What you will do

1. **Severity ratings.** Rate 120 observations as one of three blind raters.
2. **Outcome ratings.** Rate 160 responses as the second rater. You see the response and the
   rubric, not the perturbation record.
3. **Recovery ratings.** Rate 80 sequences as the second rater.
4. **Paper support.** Check numbers against artifacts, terminology consistency, citation keys,
   and the limitations section. Proofread the final PDF.

### From where you start

- **Files:** `docs/LABEL_RUBRIC.md` sections 1–6, `docs/PROTOCOL.md` sections 4–5,
  `paper/proposal.tex` sections 3–5, `docs/GATES.md` G3/G4.
- **Folder:** the shared `annotations/` folder. Author 1 will give you the batches and the anchor
  sheet.
- **Access:** write access to the shared annotation folder. Do not put raw data or PII in GitHub.

### How you will do it

#### Annotation batches

1. Complete the five-item practice batch with Author 3 before starting.
2. Save a copy of each batch with your initials.
3. Label every row using the rubric. Use confidence and notes for hard cases.
4. Do not discuss individual labels with Author 3 before both submissions.
5. Submit before the deadline.
6. If you are the second outcome rater, use only the response and the rubric. Do not open the
   perturbation record or the arm map.

#### Paper support

1. **Number check.** For every table and figure, confirm that the number appears in a manifest,
   ledger, artifact, or cited source. If it does not, mark it `TBD` and tell Author 1.
2. **Terminology check.** Use one name per concept:
   - tool result or tool observation
   - prefix
   - arm
   - silent propagation
   - recovery
3. **Citation check.** Every citation key exists, the authors/year/venue are correct, and the
   sentence is supported by the paper.
4. **Limitations check.** The paper must state the public-task contamination risk, donor
   off-policy issue, severity construct risk, model coverage, deterministic tools, and four-step
   horizon.
5. **Proofread.** Check clarity, paragraph flow, and claim strength. Do not add new claims.

### Resources to learn

- `docs/LABEL_RUBRIC.md` — the main resource for labels.
- `docs/PROTOCOL.md` sections 4–5 — outcome and recovery definitions.
- `paper/proposal.tex` sections 3–5 — design, outcomes, expected result.
- `docs/GATES.md` G3/G4 — what must pass before the paper claims anything.
- Optional: the τ-bench and ToolLLM abstracts for background.

You do not need to run models or write analysis code. Author 1 will provide the batches and the
source artifacts for the number check.

### What you submit

| Deliverable | Template | Submit as | Deadline |
|---|---|---|---|
| Severity ratings | [`severity_rating_template.csv`](templates/severity_rating_template.csv) | `severity_batch01_<initials>.csv` | Day 7 |
| Outcome ratings | [`outcome_rating_template.csv`](templates/outcome_rating_template.csv) | `outcome_batch01_<initials>.csv` | Day 9 |
| Recovery ratings | [`recovery_rating_template.csv`](templates/recovery_rating_template.csv) | `recovery_batch01_<initials>.csv` | Day 11 |
| Proofreading checklist | [`paper_support_checklist.md`](templates/paper_support_checklist.md) | `paper_support_checklist_<initials>.md` | Day 14 |
| Number/citation notes | [`paper_support_checklist.md`](templates/paper_support_checklist.md) | GitHub issue or shared doc | Day 13 |

### Example recovery labels

| Sequence | Label |
|---|---|
| Step 1 repeats wrong value; step 2 re-queries and matches V | Corrected at step 2 |
| Step 1 flags "inconsistent"; step 2 verifies | Flagged at step 1 |
| Steps 1–4 repeat wrong value, no flag | Still wrong / censored |

These are illustrative, not real harvested records.

### Time commitment

- Days 1–11: 16–20 hours for severity, outcome, and recovery ratings.
- Days 12–14: 6–8 hours for paper support and proofreading.
- Total: roughly 22–28 hours across the two-week sprint.

---

## 7. Shared annotation rules and examples

### The four-way outcome label

Assign one primary label, using this priority:

1. **Silent propagation** — the false value of a critical field appears in the response or tool
   arguments, and there is no flag. Not scored for s=1.
2. **Flagged** — explicit doubt, "possible error", "inconsistent", "verify", "cannot trust", or a
   request to re-check.
3. **Action switch** — the tool name or canonicalized arguments differ from V.
4. **Same** — the signature matches V.

If a response satisfies more than one, record all indicators in the notes but assign the
highest-priority primary label. Use **other** for unparseable output, refusal, or a response
outside the taxonomy.

### The three-way recovery label

| Label | Definition |
|---|---|
| **Corrected** | The decision signature first matches V at step h ≤ 4. |
| **Flagged** | Explicit detection first occurs at step h ≤ 4, without a signature match. |
| **Still wrong** | Neither happens by H=4; the sequence is censored. |

If a response both flags and matches V at the same step, code **corrected** for R1 and
**flagged** for R2. Report both endpoints.

### Severity examples

| Observation | Likely level | Why |
|---|---|---|
| All values preserved, prose only | s=0 | Faithful paraphrase; any change is format jitter |
| Product rating 4.4 → 4.1 | s=1 | Non-critical display field; not used in the action |
| Refund $84.50 → $48.50 | s=2 | Critical field; plausible wrong value; changes the correct refund |
| Refund $48.50 and return window closed although delivered 3 days ago | s=3 | Critical error plus a detectable contradiction |

### Confidence scale

| Score | Meaning |
|---:|---|
| 1 | Guess |
| 2 | Low confidence |
| 3 | Medium confidence |
| 4 | High confidence |
| 5 | Certain |

Use the notes column for ambiguity. A low-confidence label with a clear note is better than a
silent guess.

### Blinding rules

- Do not open the arm map, perturbation record, or `true_value` fields.
- Do not discuss individual items with the other rater before both submissions.
- If you recognize an item from another batch, tell Author 3.
- The second outcome rater sees only the response and the rubric, not the perturbation record.

### How to complete a batch

Use the matching template from [`docs/templates/`](templates/README.md). Do not create your own
columns or change the header row.

1. Open the batch file from the shared folder. Do not edit the original.
2. Save a copy with your initials, using the matching template.
3. Keep the rubric and anchor sheet open next to the batch.
4. Label every row. If unsure, use your best label, set confidence low, and write a note.
5. Do not skip rows. Use `other` only when the response is outside the taxonomy.
6. Check the row count before submitting.
7. Submit the file to the shared folder and update the GitHub issue.
8. Complete the [submission checklist](templates/submission_checklist.md) before you upload.
9. Do not discuss individual labels with the other rater before the lead confirms both submissions.

---

## 8. Two-week sprint timeline

The overall project runs 18 weeks. Your work is concentrated in a **two-week sprint**. The clock
starts when Author 1 delivers the batch package. If a batch is late, use the day for reading or
practice; do not guess labels.

### Week 1 — data and severity

| Days | Author 2 | Author 3 | Author 4 |
|---|---|---|---|
| 1–2 | Read docs; practice; access check | Read docs; lead practice; training notes | Read docs; practice; access check |
| 3–4 | G0 audit (40 prefixes) | Prepare severity batch; check blinding | Severity ratings (first half) |
| 5–6 | G0 audit summary; severity ratings (first half) | Severity ratings (all) | Severity ratings (second half) |
| 7 | Severity ratings finish | Severity ratings finish; check completeness | Severity ratings finish; check completeness |

### Week 2 — outcome, recovery, agreement, paper support

| Days | Author 2 | Author 3 | Author 4 |
|---|---|---|---|
| 8–9 | Outcome adjudication setup | Outcome ratings | Outcome ratings |
| 10–11 | Recovery adjudication | Recovery ratings | Recovery ratings |
| 12 | Data card draft | Agreement report | Paper support: number check |
| 13 | Data card/release checklist | Adjudication coordination | Citation/terminology check |
| 14 | Final checks; submit | Final annotation report; submit | Proofreading; submit |

### Checkpoints

| Day | Checkpoint |
|---:|---|
| 1 | Kickoff; access confirmed |
| 2 | Practice batch discussed; training notes started |
| 7 | Severity batch complete for all raters |
| 9 | Outcome batch complete for both raters |
| 11 | Recovery batch complete for both raters |
| 12 | Agreement report draft |
| 14 | All files submitted; sign-off |

### Time commitment (two weeks)

| Person | Total hours | Main load |
|---|---:|---|
| Author 2 | 18–22 | G0 audit, severity, adjudication, data card |
| Author 3 | 24–30 | Training, severity/outcome/recovery, agreement |
| Author 4 | 22–28 | Severity/outcome/recovery, paper support |

These are planning estimates, not ledger numbers.

**Planning note.** The full audit matrix is 120 × 3 + 160 × 2 + 80 × 2 = **840 ratings** before
adjudication. The older project text says "≈200 judgments; about 8.3 hours"; that estimate is too
low for the full matrix. Plan for **25–40 person-hours** across the three co-authors. In a two-week
sprint, that is roughly **8–13 hours per person per week** plus onboarding. If the team cannot
commit that time, extend the sprint or reduce the audit sample with a prereg amendment; do not skip
rows.

---

## 9. Rules that protect the study

### Do not

- Do not edit `prereg/PREREGISTRATION.md`, `data/manifests/cto800_v1.json`, perturbation records,
  the field registry, or the renderer version after G0 freeze.
- Do not look at arm labels during a blind audit.
- Do not discuss individual labels with the other rater before submission.
- Do not use an LLM to generate labels, annotations, or citations. The design requires human
  raters, and an LLM rater would change the design.
- Do not paste raw data, PII, or model outputs into external AI tools.
- Do not commit raw data, PII, weights, credentials, or logs.
- Do not invent a number, citation, or limitation.
- Do not change the rubric without Author 3 and Author 1, and a logged decision.

### Do

- Ask when the rubric is ambiguous. A question is cheaper than a bad label.
- Record confidence and a short note for every hard case.
- Report PII privately and immediately.
- Keep the batch file unchanged; write labels to a copy.
- Use the exact terminology in the rubric.
- Tell Author 3 if you recognize an item from another batch.

---

## 10. Definition of done

| Task | Done when |
|---|---|
| G0 audit | 40 rows complete; summary written; failures categorized; PII reported privately |
| Severity ratings | 120 rows; three scores, confidence, and notes filled; submitted before deadline |
| Outcome ratings | 160 rows; primary label and indicators filled; disagreements flagged |
| Recovery ratings | 80 sequences; first step and label filled; censoring recorded |
| Agreement report | Kappa/alpha computed; pass/fail stated; ambiguous items listed |
| Adjudication | Every disagreement has an adjudicated label and a reason |
| Paper support | Number, terminology, citation, and limitations checks complete |
| Release support | PII re-scan, licence notice, checksums, and data card checked |

---

## 11. Glossary

| Term | Meaning |
|---|---|
| **Agent** | A language model in a loop: read, act, observe, repeat |
| **Tool call** | A structured request to an external function |
| **Observation / tool result** | What the tool returns |
| **Prefix** | The frozen conversation up to and including the observation |
| **Arm** | One condition: V, s=0, s=1, s=2, or s=3 |
| **V** | The exact real observation as raw JSON |
| **s=0** | Faithful prose with all values preserved |
| **s=1** | One non-critical field changed or omitted |
| **s=2** | One critical field changed to a plausible wrong value |
| **s=3** | Critical wrong value plus a second detectable contradiction |
| **Decision signature** | Tool name plus canonicalized arguments, or final answer action plus key slots |
| **Silent propagation** | The agent repeats a wrong value without flagging it |
| **Detection** | The agent explicitly flags doubt, inconsistency, or a need to verify |
| **Action switch** | The agent changes the tool or arguments |
| **Recovery** | The agent corrects or flags after the injection step, within four steps |
| **Censored** | No recovery by step 4 |
| **Manifest** | A small file of hashes and identifiers that records the frozen sample |
| **Ledger** | One row per generation, with model, arm, prefix, output, parser result, and cost |
| **Gate** | A pre-registered pass/fail checkpoint (G0–G4) |
| **PII** | Personally identifiable information: names, emails, addresses, phones, payment IDs |
| **Krippendorff's alpha** | Agreement statistic for multiple raters |
| **Cohen's kappa** | Agreement statistic for two raters, corrected for chance |

---

## 12. Ready-to-send message

> We are studying whether language-model agents notice wrong tool results, trust them, or recover.
> Author 1 handles the experiments, implementation, and related-work matrix with AI agents. Your
> work is the human-judgment part: checking data and PII, labeling agent responses, auditing
> severity and recovery, and checking the paper.
>
> Please read `docs/COAUTHOR_GUIDE.md`, the six documents in Section 3, and the submission
> templates in `docs/templates/` before our first meeting. You do not need to know the domain in
> advance. We will do a five-item practice batch together. The sprint is two weeks; the exact start
> date will be announced. The first meeting is 30 minutes; bring questions.
>
> Guide: https://github.com/Atik203/tool-observation/blob/main/docs/COAUTHOR_GUIDE.md
> Templates: https://github.com/Atik203/tool-observation/tree/main/docs/templates
>
> Author 2: data/PII audit and severity ratings.
> Author 3: annotation lead, severity/outcome/recovery ratings, and agreement report.
> Author 4: outcome/recovery ratings and paper support.
