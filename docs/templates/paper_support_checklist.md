# Paper support checklist

**Paper version / commit:**  
**Reviewer:** Author 4  
**Date:**  
**Guide:** [`docs/COAUTHOR_GUIDE.md`](../COAUTHOR_GUIDE.md)

---

## 1. Numbers

For every table, figure, and number in the abstract:

- [ ] The number appears in a manifest, ledger, artifact, or cited source.
- [ ] The denominator or sample size is stated.
- [ ] The unit is correct (pp, logit, odds ratio, hours, dollars).
- [ ] The claim strength matches the evidence.
- [ ] A null or negative result is not reframed as positive.
- [ ] No number is marked `TBD` without a note explaining what will resolve it.

| Location | Number | Source | Check |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

## 2. Citations

- [ ] Every citation key exists in the reference list.
- [ ] Authors, year, venue, and title are correct.
- [ ] The cited sentence is supported by the paper.
- [ ] No citation is used for a claim the paper does not make.
- [ ] No `[VERIFY CITATION]` placeholder remains.

| Citation key | Checked | Note |
|---|---|---|
|  |  |  |
|  |  |  |

## 3. Terminology

- [ ] "tool result" or "tool observation" is used consistently.
- [ ] "prefix" is used for the frozen conversation.
- [ ] "arm" is used for V, s=0, s=1, s=2, s=3.
- [ ] "silent propagation" is used consistently.
- [ ] "recovery" is used consistently.
- [ ] Symbols and acronyms are defined at first use.

## 4. Limitations

- [ ] Public-task contamination risk is stated.
- [ ] Donor off-policy issue is stated.
- [ ] Severity construct risk is stated.
- [ ] Model coverage is stated.
- [ ] Deterministic tools are stated.
- [ ] Four-step horizon is stated.
- [ ] No universal-law, ranking, frontier-transfer, or end-to-end-success claim.

## 5. Reproducibility

- [ ] `pytest -q` passes.
- [ ] `python -m toolobs.cli validate` passes.
- [ ] The proposal compiles to PDF.
- [ ] The commands in the README work.
- [ ] No frozen artifact was edited to make a check pass.

## 6. Final sign-off

| Check | Reviewer | Date |
|---|---|---|
| Numbers |  |  |
| Citations |  |  |
| Terminology |  |  |
| Limitations |  |  |
| Reproducibility |  |  |
