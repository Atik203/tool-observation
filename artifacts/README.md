# `artifacts/` — generated outputs

Everything here is generated. The directory is gitignored except for this README, the
subdirectory `.gitkeep` files, and (later) small final tables that the team explicitly decides to
track.

| Path | Contents |
|---|---|
| `audit/` | G0 40-item audit, scrub report, replay report, G1 calibration report, label audits |
| `analysis/` | Slope tables, recovery curves, κ/α reports, figures, notebooks, G3/G4 reports |
| `env/` | H200 environment record, driver/CUDA/vLLM versions, environment snapshots, lock provenance |
| `cost/` | Per-shard and cumulative GPU-hour/storage ledgers, G2 stop records |
| `paper/` | Generated figures and tables for the manuscript |

## Rules

- Every artifact states the commit, config hash, and manifest hash that produced it.
- A number in a paper or README must trace to a raw ledger row or a manifest; an artifact is a
  derived view, not the source of truth.
- Do not hand-edit a generated table. Regenerate it from the pipeline.
- Audit and analysis artifacts may contain model outputs. Treat them as potentially sensitive
  until scrubbed; never commit free text from a trajectory.
- Cost artifacts are the evidence for the $0 cash budget and the 45 GPU-hour / 200 GB stop.
- The release package is built from a clean checkout plus local data after a PII re-scan; do not
  publish `artifacts/` wholesale.

## Naming

Use `stage_purpose_date.json|md|csv`, for example `g0_audit_2026-11-12.csv`,
`g1_calibration_2026-11-18.json`, `main_cost_2026-11-30.json`. Avoid spaces and personal names in
filenames.
