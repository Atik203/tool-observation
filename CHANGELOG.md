# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Because the project is pre-confirmatory, minor versions may change the scaffold structure before
the v1.0 dataset and paper release.

## Dataset releases

### [1.0.2] - 2026-11-23

- Path-leak errata: the v1.0.1 distributed copies exposed absolute build-machine/server
  paths (16 occurrences in 8 files). The release builder now replaces repository roots,
  server home directory prefixes, and drive-rooted paths with `[repo]` in every staged
  text file, records the counts in `path_rescan.json`, and L1 fails on any residual.
  Generated source artifacts are unchanged. Version DOI `10.5281/zenodo.24449882`
  (concept `10.5281/zenodo.24449466`); v1.0.1 (`10.5281/zenodo.24449467`) is superseded.

### [1.0.1] - 2026-11-23

- Redacted one scrubber-artifact email fragment (given name + digits) in the distributed release
  copy as `person_redacted_0001`; the builder applies the redaction on every build and
  `pii_rescan.json` reports the counts. The frozen source is unchanged and still verifies against
  the manifest hash; it is not distributed. See `docs/DECISIONS.md` D-046 and the package
  `CHANGELOG.md`.
- Added `ATTRIBUTION.md` (ToolResult-800 authors, upstream τ-bench MIT with the Sierra copyright
  line, the three model families and licenses, and the changes-made statement);
  `DATA_LICENSE.md` and `docs/DATA_CARD.md` now describe the release accurately.

### [1.0.0] - 2026-11-22

- First staged public release package (880 scrubbed prefixes, manifests, scrubbed ledger
  extracts, labels, analysis JSONs, T6 packets, prereg and amendments, checksums).

## [Unreleased]

### Added

- Foundation record contracts for prefixes, perturbations, ledger rows, samples, source pins,
  model pins, and the frozen manifest.
- Typed config loader with cross-file validation and stable config hashing.
- Provenance helpers for commit SHA, artifact hashes, manifest sidecars, and pre-freeze checks.
- τ-bench source pinning: commit SHA, four trajectory hashes, six task-database hashes, harness
  digest, and a tracked `data/manifests/source_pin.json`.
- Trajectory parser that reproduces the preregistered frame (13,605 candidates; 11,318
  JSON-parseable; 3,692 profile-tool candidates) and materializes hash-verified prefixes from
  the pinned checkout.
- Automatic value-used relevance with a draft path-based PII policy, and a deterministic PII
  scrubber with a leak scan. Draft output: 5,516 eligible (airline 1,434; retail 4,082), zero
  residual direct identifiers.
- Replay harness that executes pinned τ-bench tool calls from a fresh task database and compares
  normalized observations. Eligible-pool replay: 5,511/5,516 (99.91%); airline cap-10 442.
- Deterministic stratified sampler: 800 primary + 80 reserve, 400/400 domain, cap 10/task.
- Deterministic prose renderer and perturbation generator: 4,400 arms, 2,640 perturbation
  records, 100% s=0 value-set equality, no PII perturbations.
- G0 human audit packet and scoring path; audit remains pending human labels.
- Disjoint 60-prefix calibration selection and freeze dry-run manifest builder; final manifest is
  gated on the human audit.
- Next-decision prompt/parser/ledger, fake and lazy vLLM backends, calibration gate evaluator,
  outcome labels, conditional-logit slope with prefix-cluster bootstrap, and recovery/KM/RMST/
  Weibull estimators, all CPU-tested.
- Frozen scrubbed prefix payload (880 prefixes, five arm observations) and a release packager
  that verifies manifest/payload hashes and PII before copying.
- AI pre-audit helper for the 40-item G0 packet; the official human sheet remains blank.
- Updated 8–9B model trio pinned (Qwen3.5-9B, Ministral-3-8B, Llama-3.1-8B AWQ); all three pass
  non-study 24k/batch-4 fit checks on the H200 slice, and Qwen3.5 runs with thinking disabled. No
  study workload has run.
- Contract tests for hashing, schemas, config invariants, paths, CLI, field registry, pinning,
  parsing, relevance, scrubbing, replay comparison, sampling, rendering, inference, calibration,
  outcomes, slope, and recovery.

### Planned

- G1 calibration and G2 main run after the G0 human audit and freeze.

## [0.1.0] - 2026-11-09

### Added

- Initial public repository scaffold for the tool-result study (ToolResult-800).
- Governance: README, ROADMAP, AGENTS, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, CITATION,
  MIT code license, CC BY 4.0 documentation and data notices.
- `toolobs` Python package skeleton with `--version` and `validate` CLI commands.
- Pipeline script stubs `00_pin_source` through `10_release`.
- Configuration for base settings, models, harvest, arms, field registry, calibration, main run,
  and analysis.
- Documentation drafts: implementation plan, protocol, gates, label rubric, data card, runbook,
  decision log.
- CI workflow for Python 3.12, issue templates, and pull request template.
- Conda environment, placeholder CPU/GPU lock templates, Makefile, and PowerShell task runner.

### Notes

- No confirmatory results. The pilot (N=60, qwen3.5:4b) is documented only as a screening signal.
- `data/` raw, upstream, interim, frozen, and run directories are intentionally empty and
  gitignored; only manifests and `.gitkeep` files are tracked.

[Unreleased]: https://github.com/Atik203/tool-observation/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Atik203/tool-observation/releases/tag/v0.1.0
