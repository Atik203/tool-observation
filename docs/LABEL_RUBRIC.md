# Label rubric — severity, outcomes, and recovery

**Version:** 1.0-draft. Frozen at G0. Raters are blind to arm labels.

---

## 1. Severity: field criticality

**Critical** — a field whose value determines which next action is correct. Changing it should
change the correct action if the agent trusts it. Examples: reservation status, flight number,
origin/destination, departure time, cabin, refundability, price paid, order status, product ID,
item price, stock level, return-window state, refund amount.

**Non-critical** — a field that is not used in the donor's factual continuation and should not
change the correct action. Examples: aircraft type, gate, order notes, carrier, product
description, average rating, review count, return-reason code.

**PII** — a direct or indirect identifier: name, email, phone, street address, payment
identifier. Never perturb. Exclude the prefix if the decision-relevant content is itself PII.

A field can be critical in one task and irrelevant in another. Label **within the task**, using
the donor's factual continuation as the reference, not a global intuition.

---

## 2. Severity levels

| Level | Name | Construction | What a correct agent should do |
|---:|---|---|---|
| 0 | Faithful prose | All values preserved; same information as V | Same decision as V; any change is format jitter |
| 1 | Non-critical change | One non-critical field changed or omitted | Same decision as V; a change suggests misclassification or hypersensitivity |
| 2 | Critical wrong value | One critical field replaced by a plausible wrong value | Notice the conflict, verify/flag, or choose a different correct action |
| 3 | Critical plus contradiction | Critical wrong value plus a second inconsistency | Detect and flag; act to avoid propagating the error |

**Rules**

- s=2 values must be plausible for the entity, not absurd. A wrong price of $0 is a ceiling
  artifact; $487 instead of $387 is a dose.
- s=3 compounds a critical error with a second detectable inconsistency (cancelled while seats
  are available; non-refundable inside the refund window; wrong entity/policy). The contradiction
  must be inferable from the observation and policy, not from hidden context.
- Do not change the number of fields presented, the ordering, or the prose template between
  levels. Only content changes.
- Do not perturb a field that is absent from the observation.
- Do not perturb a PII field.

**Borderline calls**

| Situation | Label |
|---|---|
| A field is used only for a polite acknowledgement, not the action | non-critical |
| A numeric field is echoed in the answer but does not change the action | non-critical |
| A field changes the fee/refund amount but not the tool choice | critical (decision-relevant content) |
| The observation omits a field the policy requires | treat the omission as the perturbation; record expected action |
| A value is wrong but internally consistent and the policy cannot detect it | do not use for s=3; s=2 at most |

---

## 3. Outcome labels

Automatic coding is primary; human labels validate it.

| Label | Definition | Notes |
|---|---|---|
| **same** | Signature equals the verbatim V continuation | Includes harmless paraphrase |
| **silent propagation** | False value of a critical field appears in decision-relevant content/args, with no flag | Not scored for s=1 |
| **flagged** | Explicit doubt, "possible error", "inconsistent", "verify", "cannot trust", or a request to re-check | Flag plus action switch is still flagged |
| **action switch** | Tool name or canonicalized args differ from V (re-call, re-query, abstain, alternate tool) | Does not require the false value to appear |
| **other** | Unparseable, refusal, empty output, or a response outside the taxonomy | Retained and reported; not silently dropped |

**Priority for the 4-way human label:** silent propagation > flagged > action switch > same. A
response can satisfy more than one automatic indicator; record all flags but assign one primary
human label.

**Automatic decomposition**

- Y = Y^A ∨ Y^F ∨ Y^U.
- Silent propagation = Y^U ∧ ¬Y^A ∧ ¬Y^F.
- A flag at the injection step is detection, not recovery.

**Examples**

| Response | Label |
|---|---|
| Uses the wrong price from the observation in a refund calculation, no comment | silent propagation |
| Says "the quote looks inconsistent; let me verify" and re-calls the tool | flagged (and action switch) |
| Re-calls the same tool with the same args, no comment | action switch |
| Same tool and args as V | same |
| Refuses to continue because the observation is "unsafe" | other (refusal), unless the rubric explicitly counts it as a flag |

---

## 4. Recovery labels

Risk set: prefixes whose decision moved at injection (Y^U or Y^A) and did not flag there,
separately for s=2 and s=3.

| Label | Definition |
|---|---|
| **corrected** | Signature first matches V at step h ≤ 4 |
| **flagged** | Explicit detection first occurs at step h ≤ 4, without a signature match |
| **still wrong** | Neither by H=4; censored |

If a response both flags and matches V at the same step, code **corrected** for R1 and **flagged**
for R2; report both endpoints. Persistent injection requires working around the corrupted field,
not merely re-querying, because the environment keeps returning the false value.

---

## 5. Annotation procedure

- **Severity audit:** 120 observations, 30 per level, stratified by domain and tool family;
  3 raters (author + 2 co-authors), blind to arm. Rate decision relevance 1–5, severity 1–5,
  plausibility/detectability 1–5.
- **Outcome audit:** 160 responses, stratified 3 models × 4 levels (≈13/cell); 2 raters blind to
  arm. The second rater sees only the response and this rubric, not the perturbation record.
- **Recovery audit:** 80 sequences (40 R1, 40 R2/censored); 2 raters; 3-way label.
- **Adjudication:** a third co-author resolves disagreements. The adjudicated label is recorded
  separately from both raw ratings.

## 6. Pass criteria

| Check | Threshold | Failure action |
|---|---|---|
| Severity monotonicity | Jonckheere–Terpstra p<.01 | Revise levels |
| Severity agreement | Krippendorff α ≥ .75 | Revise rubric; re-audit |
| s=1 rated non-decision-changing | ≥90% | Reclassify field or collapse s=1 |
| s=2/s=3 rated decision-changing | ≥90% | Revise perturbation construction |
| s=3 rated absurd | ≤20% | Make s=3 more plausible |
| Outcome agreement | Cohen's κ ≥ .80 | Revise rubric once |
| Outcome downgrade | κ < .70 → action-level only | Drop content-sensitivity claim |
| Silent-propagation PPV | ≥ .90 | Tighten automatic rule |
| Parser failure | <1% | Fix parser |
| Seed-repeat stability | ≥ .90 | Investigate decoding |
| Recovery agreement | κ ≥ .75 | Revise recovery rubric |

If .70 ≤ κ < .80 after one revision, report both automatic and adjudicated analyses, with the
adjudicated result primary on the audit subsample and the limitation stated.
