# `data/` — local data staging

This directory holds data that is **too large, too sensitive, or too reproducible to commit**.
Only small non-PII manifests and `.gitkeep` placeholders are tracked.

## Layout

| Path | Contents | Git |
|---|---|---|
| `raw/` | Downloaded upstream archives and scratch copies | ignored |
| `upstream/` | Pinned τ-bench checkout, task databases, `PIN.json` | ignored |
| `interim/` | Parsed candidates, scrubbed table, eligible table, replay table | ignored |
| `frozen/` | Frozen prefix payloads and rendered prompts | ignored |
| `manifests/` | `sample_880.json`, `toolresult800_v1.json`, `perturbations.jsonl`, model pins, hashes | **tracked** |
| `runs/` | Calibration/main ledgers, raw traces, recovery traces | ignored |

## What may be committed to `data/manifests/`

- Small JSON/YAML/CSV manifests of IDs, counts, strata, and hashes.
- Freeze records and model revision pins.
- Checksums that let another machine verify a local copy.
- No raw observations, no PII, no model outputs, no large arrays.

If a manifest exceeds a few megabytes or contains free text from a trajectory, it does not belong
in git. Put the payload under `frozen/` and keep only its hash in `manifests/`.

## Freeze discipline

`data/manifests/toolresult800_v1.json` is written once at G0 and never edited afterward. It records the
800 primary prefixes, message and observation hashes, perturbation-record hashes, renderer
version, field-registry hash, and the preregistration hash. Corrections require a new version and
an amendment.

## PII

Raw τ-bench trajectories can contain names, emails, addresses, phone numbers, and payment
identifiers. Treat `raw/`, `upstream/`, and every unscrubbed intermediate as PII-bearing. Never
copy them into a commit, issue, notebook, screenshot, or release. See `SECURITY.md` and
`DATA_LICENSE.md`.

## Rebuilding

The pipeline is designed to rebuild `interim/` and `frozen/` from `upstream/` plus the pinned
manifests. If a rebuild produces a different hash, stop and investigate the environment or pin;
do not update the manifest to match a drifted rebuild.
