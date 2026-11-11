# Co-Author Guide — Tool-Result Errors in Language-Model Agents

**Project:** Tool-Result Errors in Language-Model Agents: A Controlled Study of Detection, Reliance, and Recovery  
**Repository:** <https://github.com/Atik203/tool-observation>  
**First author:** Atikur Rahaman  
**Audience:** co-authors who will help with annotation, related work, data checks, and paper support  
**Status:** onboarding guide. It does not replace the preregistration or protocol.

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

### The three outcomes we care about

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

## 2. What we need from the co-author team

The first author runs the experiments, implementation, and primary analysis. The co-authors do
the work that requires human judgment and independent reading:

1. **Data and PII audit** — check a sample of prefixes for eligibility, PII, relevance, and replay.
2. **Severity audit** — rate whether the manipulated observation is plausible and decision-relevant.
3. **Outcome audit** — label agent responses as same, silent propagation, flagged, or action switch.
4. **Recovery audit** — label whether the agent corrected, flagged, or stayed wrong over four steps.
5. **Related work** — build a literature matrix and draft the related-work section.
6. **Paper support** — verify numbers, citations, terminology, and reproducibility.

You do **not** need to run the GPU models or write the main pipeline. The first author handles
that. You need to read carefully, follow the rubric, and record your judgments.

---

## 3. Roles at a glance

We plan for four authors total. If there are five, split the annotation or release work as noted.

| Role | Person | Main responsibility | Main deliverables |
|---|---|---|---|
| **Author 1** | First author | Experiments, implementation, analysis, paper integration, gate reports | Frozen pipeline, run ledgers, analysis, paper draft |
| **Author 2** | Data and PII lead | G0 data audit, PII review, replay spot-check, data card, release checklist | G0 audit sheet, PII report, data card, release checklist |
| **Author 3** | Annotation lead | Severity, outcome, and recovery audits; rater training; adjudication coordination | Completed annotation batches, agreement report, adjudication log |
| **Author 4** | Related work and paper support | Literature matrix, related-work draft, reference verification, proofreading | Literature matrix, related-work section, reference check |

**If there are five authors:** add a second annotation rater for the outcome and recovery audits,
and a release/reproducibility checker. Do not add a fifth person to the same blind rating task
without updating the annotation plan.

### Who is accountable for what

- **Author 1** is accountable for the scientific claims, the frozen artifacts, and the final paper.
- **Author 2** is accountable for the data audit, PII handling, and release checklist.
- **Author 3** is accountable for annotation quality, blinding, and agreement statistics.
- **Author 4** is accountable for literature accuracy and reference completeness.
- **All authors** approve the final claim boundary and the submitted manuscript.

---

## 4. Before you start: reading and access

### Read these five documents first

| Order | File | Why |
|---:|---|---|
| 1 | `README.md` | Project status, claim boundary, pilot evidence |
| 2 | `paper/proposal.tex` (or `paper/out/proposal.pdf`) | The proposal in one place |
| 3 | `docs/PROTOCOL.md` | The design, arms, outcomes, and recovery rules |
| 4 | `docs/LABEL_RUBRIC.md` | The annotation rubric and pass criteria |
| 5 | `docs/GATES.md` | What must pass before the next phase |

Optional but useful: `ROADMAP.md`, `docs/IMPLEMENTATION_PLAN.md`, `docs/DATA_CARD.md`.

### Access checklist

- [ ] GitHub account with read access to `Atik203/tool-observation`.
- [ ] Access to the shared annotation folder (the first author will create it).
- [ ] A spreadsheet tool (Google Sheets or Excel).
- [ ] A PDF reader for the proposal and papers.
- [ ] The team communication channel and the weekly meeting invite.
- [ ] Agreement not to copy raw data, PII, or model outputs into public tools.

### First-week onboarding

| Day | Task | Output |
|---:|---|---|
| 1 | Read the five documents above | Notes and questions |
| 2 | 30-minute walkthrough with Author 1 | Shared understanding of one example |
| 3 | Label five practice items | Practice sheet |
| 4 | Compare labels with Author 1 and discuss disagreements | Calibration notes |
| 5 | Set up access and confirm your weekly availability | Access checklist complete |

Do not start a real annotation batch until the practice batch is discussed. The first batch is
for calibration, not for the final data.

---

## 5. Task 1 — G0 data, PII, and replay audit

**Lead:** Author 2. **When:** P0, weeks 1–2. **Effort:** roughly 4–8 hours.

### What you receive

A CSV or spreadsheet with 40 randomly selected prefixes. Each row has an `item_id`, domain,
the reconstructed prefix, the tool observation, and the replay result. The first author will
provide the file and a short walkthrough.

### What you check

For each prefix, record **pass** or **fail** on four dimensions:

1. **Eligibility.** Is there a real tool message? Is the prefix reconstructable? Is there at
   least one value used in the correct continuation?
2. **PII.** Does the prefix contain a name, email, phone number, street address, or payment
   identifier? If yes, stop and report it privately; do not copy the value into your notes.
3. **Decision relevance.** Does the observation contain a value that the correct next action
   uses? A refund amount or return-window status is relevant. A product rating is usually not.
4. **Replay match.** Does the replayed observation match the historical observation after
   normalization? The target is at least 98% across the retained set.

### What you submit

A sheet with:

```text
item_id, eligibility_pass, pii_pass, relevance_pass, replay_pass, notes
```

Then a one-paragraph summary: how many passed, what failed, and whether any failure looks
systematic. The pass threshold is **36/40**. If the batch fails, the first author will revise the
rules and re-sample from the reserve.

### Example

| item_id | eligibility | PII | relevance | replay | note |
|---|---|---|---|---|---|
| A-014 | pass | pass | pass | pass | Refund and return-window values used in the continuation |
| A-027 | pass | fail | pass | pass | Customer email present; reported privately, not copied |
| R-009 | fail | pass | fail | pass | Observation has no value used in the continuation |

These rows are illustrative, not real harvested records.

---

## 6. Task 2 — Severity audit

**Lead:** Author 3. **Raters:** three blind raters (Author 1 plus two co-authors). **When:** P3,
weeks 8–10. **Effort:** roughly 12–20 person-hours plus adjudication.

### What this audit answers

Is the severity manipulation credible? Does s=1 really look non-critical? Does s=2 look like a
plausible critical error? Is s=3 detectable but not absurd? If the levels are not distinguishable,
the "dose" interpretation fails.

### What you receive

A shuffled batch of **120 observations**, 30 per severity level. You will see the observation
and the task context. You will **not** see the arm label or the perturbation record. The batch is
shuffled so you cannot infer the level from the order.

### What you rate

For each item, give three scores from 1 to 5 and a short note:

- **Decision relevance:** how much this observation matters for the correct next action.
- **Severity:** how serious the content error is.
- **Plausibility/detectability:** how plausible the value is and how hard the problem is to detect.

Use the anchor sheet from the first author. Suggested anchors, to be confirmed at training:

| Score | Decision relevance | Severity | Plausibility/detectability |
|---:|---|---|---|
| 1 | Irrelevant to the action | No error; faithful | Absurd or trivial to detect |
| 2 | Background only | Minor, non-critical change | Implausible |
| 3 | Could matter in some tasks | Noticeable but not action-changing | Somewhat plausible |
| 4 | Likely changes the action | Critical wrong value | Plausible |
| 5 | Directly determines the action | Critical error plus clear contradiction | Highly plausible and hard to detect |

The frozen rubric is authoritative. If an anchor feels wrong, record the score and a note; do
not silently invent a new scale.

### Pass criteria

- Krippendorff's alpha at least .75.
- Jonckheere–Terpstra trend test p < .01.
- At least 90% of s=1 items rated non-decision-changing.
- At least 90% of s=2 and s=3 items rated decision-changing.
- No more than 20% of s=3 items rated absurd.

If the audit fails, the first author revises the rubric or collapses levels, then re-audits.

### What you submit

```text
item_id, decision_relevance_1_5, severity_1_5, plausibility_1_5, confidence_1_5, notes
```

Do not discuss individual items with the other raters before all raters submit. The lead will
compute agreement and schedule adjudication.

---

## 7. Task 3 — Outcome audit

**Lead:** Author 3. **Raters:** two blind raters. **When:** P3, weeks 8–10. **Effort:** roughly
8–12 person-hours plus adjudication.

### What this audit answers

Does the automatic coding agree with a careful human reading? The automatic labels are primary;
the human labels validate them.

### What you receive

**160 responses**, stratified by three models and four severity levels. You will see the agent's
response and the rubric. The second rater sees only the response and the rubric, not the
perturbation record; the lead will tell you whether the reference V continuation is included. You
will **not** see the arm label or the perturbation record.

### The four-way label

Assign one primary label, using this priority:

1. **Silent propagation** — the false value of a critical field appears in the response or tool
   arguments, and there is no flag. Not scored for s=1.
2. **Flagged** — explicit doubt, "possible error", "inconsistent", "verify", "cannot trust", or a
   request to re-check.
3. **Action switch** — the tool name or canonicalized arguments differ from V.
4. **Same** — the signature matches V.

If a response satisfies more than one, record all indicators in the notes but assign the
highest-priority primary label. Use **other** for unparseable output, refusal, or a response
outside the taxonomy; do not silently drop it.

### Examples

These are illustrative, not real harvested records. The reference decision is
`initiate_return(order_id=W1842, reason=changed_mind)` and the true refund is `$84.50`.

| Response | Primary label | Why |
|---|---|---|
| "I have started the return. Your refund will be $48.50." | **Silent propagation** | Repeats the wrong s=2 refund with no flag |
| "The return window says closed, but the item arrived three days ago. Let me verify." | **Flagged** | Explicit inconsistency and verification |
| Re-calls `get_order_details` with the same arguments, no comment | **Action switch** | Tool call differs from V, no false value repeated |
| Calls `initiate_return(order_id=W1842, reason=changed_mind)` and says $84.50 | **Same** | Matches V |
| "I cannot help with returns." | **Other** | Refusal outside the taxonomy |

### Pass criteria

- Cohen's kappa at least .80 for the four-way label.
- Silent-propagation positive predictive value at least .90.
- Parser failure below 1%.
- Seed-repeat stability at least .90.
- If kappa falls below .70 after one rubric revision, the study downgrades to action-level Y^A
  only and does not make the content-sensitivity claim.

### What you submit

```text
item_id, label, confidence_1_5, indicators, notes
```

The lead computes agreement. Disagreements go to a third co-author who is blind to the arm.

---

## 8. Task 4 — Recovery audit

**Lead:** Author 3. **Raters:** two blind raters. **When:** P3, weeks 9–10. **Effort:** roughly
4–8 person-hours.

### What this audit answers

After the agent's decision moves at the injection step, does it correct, flag, or stay wrong over
the next four steps?

### What you receive

**80 sequences**: 40 with a correct recovery (R1) and 40 with detection or censoring (R2). Each
sequence shows the steps in order. You will not see the arm label.

### The three-way label

| Label | Definition |
|---|---|
| **Corrected** | The decision signature first matches V at step h ≤ 4. |
| **Flagged** | Explicit detection first occurs at step h ≤ 4, without a signature match. |
| **Still wrong** | Neither happens by H=4; the sequence is censored. |

If a response both flags and matches V at the same step, code **corrected** for R1 and
**flagged** for R2. Report both endpoints.

### What you submit

```text
sequence_id, label, first_step, confidence_1_5, notes
```

Pass criterion: Cohen's kappa at least .75. If it fails, revise the rubric and re-audit.

---

## 9. Task 5 — Related work and literature matrix

**Lead:** Author 4. **When:** weeks 2–8. **Effort:** roughly 20–30 hours.

### What this task is

Build the related-work section from verified papers, not from memory. The proposal already has
14 seed references. Your job is to read them, extract what each paper does and does not do, and
find a small number of additional papers if needed.

### Seed topics and papers

| Topic | Seed papers |
|---|---|
| Tool-agent benchmarks | τ-bench, AgentBench, WebArena |
| Tool-use training and evaluation | ToolLLM, MINT, BFCL |
| Tool safety and injection | ToolEmu, AgentDojo, InjecAgent |
| Context sensitivity | Lost in the Middle, sycophancy |
| Agent loops | ReAct |
| Methods references | Krippendorff; Hernán and Robins |

The full citations are in `paper/proposal.tex`. Do not add a paper you have not opened.

### What to fill in

Create `literature_matrix.csv` with one row per paper:

```text
key, citation, year, venue, task_or_domain, method, metric, what_it_does_not_do, relevance_to_our_gap, verified
```

For each paper, write:

- The full citation.
- One sentence on the task or domain.
- One sentence on the method.
- One sentence on the metric or evaluation.
- One sentence on what the paper does **not** answer for our study.
- One sentence on how it supports our gap.
- `verified = yes` only after you have read at least the abstract, introduction, and results.

### What to write

A 1–2 page related-work draft in Markdown or LaTeX, with citation keys. Structure:

1. End-to-end agent benchmarks measure task success, not observation-level sensitivity.
2. Tool-use benchmarks measure tool selection and arguments, not content manipulation.
3. Safety work studies adversarial content, not plausible factual errors.
4. Context work studies position and social pressure, not a graded within-prefix effect.
5. The gap: a controlled, within-prefix estimate of content sensitivity and recovery.

Avoid "first", "novel", or "unprecedented" unless you can verify the claim. The project's
contribution is a design combination, not priority over all prior work.

### How to read a paper quickly

1. Read the abstract: what task, what method, what result.
2. Read the introduction: what gap the paper claims and what it contributes.
3. Read the method: what is manipulated, what is measured, and what is held fixed.
4. Read the main results table or figure: what the numbers actually show.
5. Read the limitations: what the authors admit the work does not cover.
6. Record the page or section for any sentence you might cite.

Do not cite a paper from its title alone. If you cannot find the claim in the paper, mark the row
`verified = no` and tell the first author.

### What you submit

- `literature_matrix.csv`.
- A related-work draft with citation keys.
- A short note listing any paper you could not verify.

---

## 10. Task 6 — Paper support and reproducibility

**Lead:** Author 4, with Author 2 for data statements. **When:** P4–P5, weeks 9–18. **Effort:**
roughly 15–25 hours.

### Number check

Every number in the paper must trace to a manifest, ledger, artifact, or cited source. For each
table and figure:

- [ ] The number appears in the source artifact.
- [ ] The sample size and denominator are stated.
- [ ] The unit (pp, logit, odds ratio, hours, dollars) is correct.
- [ ] The claim strength matches the evidence.
- [ ] A null or negative result is not reframed as positive.

If a number has no source, mark it `TBD` and tell the first author. Do not fill it with a
plausible value.

### Citation check

- [ ] Every citation key exists in the reference list.
- [ ] Authors, year, venue, and title are correct.
- [ ] The cited sentence is actually supported by the paper.
- [ ] No citation is used to support a claim the paper does not make.

### Terminology check

Use one name per concept. The project uses:

- **tool result** or **tool observation**, not "tool output" and "observation" interchangeably.
- **prefix**, not "context" when referring to the frozen conversation.
- **arm**, not "condition" or "treatment" in the paper.
- **silent propagation**, not "silent error" or "blind trust".
- **recovery**, not "self-correction" unless the agent explicitly flags.

### Reproducibility check

Run from the repository root:

```powershell
C:\ProgramData\anaconda3\python.exe -m pytest -q
$env:PYTHONPATH = "src"
C:\ProgramData\anaconda3\python.exe -m toolobs.cli validate
```

Then compile the proposal:

```powershell
cd paper
latexmk -pdf -outdir=out proposal.tex
```

Report failures; do not edit frozen artifacts to make a check pass.

### What you submit

- A completed number/citation/terminology checklist.
- A list of unresolved issues with file and line references.
- A proofread PDF with comments.

---

## 11. Annotation examples in one place

These examples are synthetic and illustrative. They are not harvested records and must not be
used as data.

### Severity examples

| Observation | Likely level | Why |
|---|---|---|
| All values preserved, prose only | s=0 | Faithful paraphrase; any change is format jitter |
| Product rating 4.4 → 4.1 | s=1 | Non-critical display field; not used in the action |
| Refund $84.50 → $48.50 | s=2 | Critical field; plausible wrong value; changes the correct refund |
| Refund $48.50 and return window closed although delivered 3 days ago | s=3 | Critical error plus a detectable contradiction |

### Outcome examples

| Response | Label |
|---|---|
| "Your refund is $48.50." | Silent propagation |
| "The window says closed but the item arrived three days ago; let me verify." | Flagged |
| Re-calls the same tool with the same arguments, no comment | Action switch |
| Same tool and arguments as V, correct refund | Same |
| Empty, unparseable, or refusal | Other |

### Recovery examples

| Sequence | Label |
|---|---|
| Step 1 repeats wrong value; step 2 re-queries and matches V | Corrected at step 2 |
| Step 1 flags "inconsistent"; step 2 verifies | Flagged at step 1 |
| Steps 1–4 repeat wrong value, no flag | Still wrong / censored |

---

## 12. Where to work and how to submit

### Folders

| Location | Use |
|---|---|
| GitHub `docs/` and `paper/` | Reading, drafts, checklists |
| Shared annotation folder | CSV batches, item files, completed labels |
| GitHub Issues | Task tracking and non-PII questions |
| Private channel | PII reports and confidential issues |

Do **not** put raw τ-bench trajectories, PII, model weights, or credentials in GitHub. The
repository's `data/raw/`, `data/upstream/`, `data/interim/`, `data/frozen/`, and `data/runs/`
directories are local-only.

### How to complete an annotation batch

1. Open the batch file from the shared folder. Do not edit the original.
2. Save a copy with your initials, for example `severity_batch01_AR.csv`.
3. Keep the rubric and the anchor sheet open next to the batch.
4. Label every row. If you are unsure, use your best label, set confidence low, and write a note.
5. Do not skip rows. Use `other` only when the response is outside the taxonomy.
6. Check the row count before submitting. The count must match the batch.
7. Submit the file to the shared folder and update the GitHub issue.
8. Do not discuss individual labels with the other rater before the lead confirms both submissions.

### File naming

```text
annotations/severity_batch01_<initials>.csv
annotations/outcome_batch01_<initials>.csv
annotations/recovery_batch01_<initials>.csv
literature/literature_matrix.csv
literature/related_work_draft.md
```

### Submission checklist

- [ ] The file is in the shared folder, not only in a chat message.
- [ ] The row count matches the batch count.
- [ ] No blank labels.
- [ ] Confidence and notes are filled for ambiguous items.
- [ ] You did not edit the source batch file.
- [ ] You did not discuss labels with the other rater before submitting.

---

## 13. Weekly rhythm and timeline

### Weekly rhythm

| Day | Activity |
|---|---|
| Monday | 30-minute team sync; confirm the week's batch and deadline |
| Wednesday | Midweek check-in; report blockers |
| Friday | Submit the batch and update the GitHub issue |
| Within 48 hours | First author reviews completeness and answers questions |

### Phase timeline

| Phase | Weeks | Co-author work |
|---|---:|---|
| P0 — Harvest and freeze | 1–2 | Author 2: G0 audit. Author 3: read rubric, practice. Author 4: literature matrix |
| P1 — Calibration | 3 | Author 3: annotation training. Author 2: replay spot-check. Author 4: related-work draft |
| P2 — Main run | 4–7 | Author 2: data card and release checklist. Author 3: prepare batches. Author 4: related work |
| P3 — Labels and analysis | 6–10 | Author 3: severity, outcome, recovery audits. Author 2: PII/adjudication support. Author 4: paper support |
| P4 — Paper | 9–14 | All: review. Author 4: references and proofreading. Author 2: data statement. Author 3: limitations |
| P5 — Release | 15–18 | Author 2: PII re-scan and release checklist. Author 4: citation/DOI. All: sign-off |

### Time commitment

| Role | Quiet weeks | Busy weeks |
|---|---:|---:|
| Author 2 | 2–4 h/week | 6–8 h/week during P0 and P5 |
| Author 3 | 2–4 h/week | 10–15 h/week during P3 |
| Author 4 | 4–6 h/week | 6–8 h/week during P4 |
| All | 1 h/week meeting | plus review time |

These are planning estimates, not ledger numbers. Adjust after the first batch.

---

## 14. Rules that protect the study

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
- Do not change the rubric without the first author and a logged decision.

### Do

- Ask when the rubric is ambiguous. A question is cheaper than a bad label.
- Record confidence and a short note for every hard case.
- Report PII privately and immediately.
- Keep the batch file unchanged; write labels to a copy.
- Use the exact terminology in the rubric.
- Tell the first author if you recognize an item from another batch.

---

## 15. Definition of done for each task

| Task | Done when |
|---|---|
| G0 audit | 40 rows complete; summary written; failures categorized; PII reported privately |
| Severity audit | 120 rows per rater; confidence and notes filled; submitted before the deadline |
| Outcome audit | 160 rows per rater; primary label and indicators filled; disagreements flagged |
| Recovery audit | 80 sequences per rater; first step and label filled; censoring recorded |
| Literature matrix | Every row verified; citation complete; what-it-does-not-do filled |
| Related-work draft | 1–2 pages; citation keys; no unverified priority claim |
| Paper support | Number, citation, terminology, and reproducibility checklists complete |
| Release support | PII re-scan, licence notice, checksums, and data card checked |

---

## 16. Glossary

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

## 17. Questions and contacts

- **Task or rubric question:** GitHub issue with the `[annotation]` label, or the weekly meeting.
- **PII or confidentiality issue:** private message to the first author. Do not open a public issue.
- **Access or schedule problem:** private message to the first author.
- **Paper or reference question:** GitHub issue with the `[related-work]` label.

When in doubt, ask before labeling. A short question is part of the work, not a delay.

---

## 18. First message to the team

You can share this guide with the following short message:

> We are studying whether language-model agents notice wrong tool results, trust them, or recover.
> Most of the pipeline is automated. Your work is the human judgment part: checking data and PII,
> labeling agent responses, auditing severity and recovery, building the related-work matrix, and
> checking the paper. Please read `docs/COAUTHOR_GUIDE.md` and the five documents in Section 4
> before our first meeting. We will do a five-item practice batch together, so you do not need to
> know the domain in advance. The first meeting is 30 minutes; bring questions.
