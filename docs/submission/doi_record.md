# DOI deposit record — ToolResult-800 v1.0.1

**Status 2026-11-23: STAGED — not yet minted.** Upload `release/ToolResult-800-v1.0.1/`
(125 files, `SHA256SUMS` verified) to Zenodo/OSF, mint the DOI, then record it here,
in `CITATION.cff`, `docs/DATA_CARD.md`, and the paper's Data availability bullet.
Resolve-check (DOI URL returns the record) is part of the author's upload step.

## DataCite metadata (deposit as-is)

- **Title:** ToolResult-800: Counterfactual Tool-Observation Dataset, 800 Frozen Prefixes
- **Creators:**
  - Md. Atikur Rahaman (ORCID 0009-0008-2945-4117), United International University — Contact
  - Ohidujjaman Tuhin (ORCID 0000-0002-8776-7145), United International University
- **Version:** 1.0.1 (staged 2026-11-23; builder `stage-18 v2`, commit recorded in
  `release_record.json`)
- **Abstract:** Fixed-prefix counterfactual dataset for measuring whether the content of a
  real tool observation changes a language-model agent's next decision. 800 primary + 80
  reserve τ-bench prefixes (airline/retail), five observation arms (verbatim JSON, faithful
  prose, non-critical change, critical error, critical-plus-contradiction), frozen
  perturbation records, scrubbed ledger extracts from three open-weight 8–9B models (21,611
  generations), audit packets/sheets, and all analysis JSONs. Confirmatory analysis complete
  with three failed gate criteria reported; measurement framing, no causal claim.
- **Licenses:** CC BY 4.0 (project additions); MIT (upstream τ-bench; full text bundled).
- **Related identifiers:**
  - Repository: https://github.com/Atik203/tool-observation
  - Upstream: https://github.com/sierra-research/tau-bench @ 59a200c6d575d595120f1cb70fea53cef0632f6b
  - Preregistration: frozen commit 1673856, tag prereg-freeze-v1, hash e0d107c6 (in-repo)
  - Paper: Tool-Result Errors in Language-Model Agents (measurement study; under submission)
- **Manifest hash (authoritative):**
  `d6e034d7f1132b314ad1f82bf14faa0f6762975ee7b404b54cc365acfac5487a`
- **Package checksum:** see `release/ToolResult-800-v1.0.1/SHA256SUMS` (125 files).

## Mint log

| Step | Status | Date/actor |
|---|---|---|
| Package staged + validated (22/22 with `--rerun`) | done (agent) | 2026-11-22 |
| v1.0.1 redaction rebuild staged + validated (17/17 L1) | done (agent) | 2026-11-23 |
| Upload to archive | pending (author) | |
| DOI minted | pending (author) | DOI: ______ |
| DOI resolves (URL returns record) | pending (author) | |
| DOI recorded in CITATION.cff / data card / paper | pending (author) | |
