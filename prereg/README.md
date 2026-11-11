# `prereg/` — preregistration

This directory holds the study's preregistration and its amendment history. The preregistration
is written before G1 and frozen at G0; it is the authority for the confirmatory claim.

## Status

- **v1.0-draft** — committed as [`PREREGISTRATION.md`](PREREGISTRATION.md). The design is also
  specified in `docs/PROTOCOL.md` and `ROADMAP.md`; the draft is frozen at the end of the 10-day
  G0 sprint.
- **v1.0-frozen** — planned at the end of G0. Its SHA-256 is recorded in
  `data/manifests/toolresult800_v1.json` and in the G0 report.
- **Amendments** — any post-freeze change is recorded in [`AMENDMENTS.md`](AMENDMENTS.md) and
  summarized in `docs/DECISIONS.md`, before the affected analysis runs.

## What the preregistration contains

1. Research question and claim boundary.
2. Unit of analysis and sampling frame (800 prefixes, 400/400, 80 reserve, seed 20261108).
3. Arms and severity construction rules.
4. Primary and secondary estimands, including the conditional-logistic slope and the recovery
   half-life.
5. Model list and substitution policy.
6. Outcome coding and label audit thresholds.
7. Analysis plan, multiplicity sequence, and linearity/Weibull checks.
8. Gates G0–G4 and stop conditions.
9. Budget ($23 base / $50 cap) and compute envelope (34,800 generations, 35–45 GPU-hours).
10. Deviations and reporting policy.

## Rules

- Do not edit the frozen preregistration. Add an amendment instead.
- An amendment states the trigger, the change, the analyses affected, and whether it was made
  blind to target-model outcomes.
- Analyses run outside the preregistered sequence are labeled exploratory and cannot support the
  primary claim.
- The paper reports every amendment and every gate outcome.

## What does not belong here

Raw data, model outputs, credentials, or large manifests. Those live under `data/` (gitignored)
or `data/manifests/` (small, non-PII).
