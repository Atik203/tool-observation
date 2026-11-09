# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Because the project is pre-confirmatory, minor versions may change the scaffold structure before
the v1.0 dataset and paper release.

## [Unreleased]

### Planned

- G0 harvest implementation and frozen CTO-800 v1 manifest.
- Replay harness against the τ-bench task databases.
- Deterministic prose renderer and perturbation generator.
- G1 calibration harness for three 7–8B AWQ models.

## [0.1.0] - 2026-11-09

### Added

- Initial public repository scaffold for the tool-observation sensitivity study (E2).
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
