# AGENTS.md — Operating instructions for AI agents

This file is the project-specific contract for AI coding agents working in
`G:\PROJECT\tool-observation`. It supplements the repository `README.md`; it does not override
the preregistration.

## 1. Read before changing anything

Read, in this order:

1. `README.md` — claim boundary, pilot status, data policy.
2. `ROADMAP.md` — phases, gates, budget, change control.
3. `docs/IMPLEMENTATION_PLAN.md` — data layout and pipeline.
4. `docs/GATES.md` — pass/fail criteria and stop rules.

If a task conflicts with the preregistration or a frozen manifest, stop and report the conflict
instead of editing around it.

## 2. Environment

- **Local interpreter:** `C:\ProgramData\anaconda3\python.exe` (Python 3.12).
- **Package:** `toolobs` in `src/toolobs/` (src layout).
- **Local GPU:** RTX 3060, 6 GB. Use it for import/smoke tests and tiny forward passes only.
  Do not attempt the main run locally.
- **Main run:** a single 24 GB rental (RTX 3090/4090), AWQ 4-bit, vLLM, batch 8–16, 8–12k
  context. One model at a time.
- The repository must import and run `pytest` without numpy, pandas, yaml, torch, or vLLM.
  Keep heavyweight imports lazy.

## 3. Never commit

- `data/raw/`, `data/upstream/`, `data/interim/`, `data/frozen/`, `data/runs/`
- `runs/`, model weights, adapters, checkpoints, HF caches
- raw τ-bench trajectories or any unscrubbed tool output
- PII, names, emails, addresses, phone numbers, payment identifiers
- `.env`, tokens, API keys, SSH keys, rental credentials, cloud configs
- large binary artifacts (parquet releases belong in the release process, not git)

`data/manifests/` is tracked, but only for small, non-PII JSON/YAML manifests and hashes.

## 4. Preserve the preregistration and frozen artifacts

- Do not edit `prereg/PREREGISTRATION.md`, `data/manifests/toolresult800_v1.json`, perturbation
  records, the field registry, or the frozen renderer version after G0 freeze.
- Do not "fix" a manifest hash to make a test pass.
- Any deviation goes in `docs/DECISIONS.md` and `prereg/AMENDMENTS.md`, before the affected
  analysis runs.
- Never re-label, re-sample, or drop a frozen prefix without a logged amendment.

## 5. Evidence rules

- **No fabricated results.** Every number in a README, doc, figure, or paper must trace to a raw
  run ledger, a manifest, or a cited external source.
- Do not fill placeholders with plausible-looking values. Mark unknowns `TBD` and explain what
  will resolve them.
- Report gate failures and null results; do not bury them.
- Keep the pilot numbers exactly as recorded: 54/60 consult, 0/60 placebo jitter, 5/60 error
  switch, 8.3 pp [1.3, 15.3], McNemar p=.0625, N=60, qwen3.5:4b, synthetic prefixes.

## 6. Commands

```powershell
# From G:\PROJECT\tool-observation
python -m toolobs.cli validate
python -m toolobs.cli --version
pytest -q
make test
.\tasks.ps1 test
```

Use the full interpreter path if `python` is not the 3.12 environment:

```powershell
C:\ProgramData\anaconda3\python.exe -m pytest -q
```

## 7. Commit conventions

Use Conventional Commits:

- `feat:` new capability
- `fix:` bug fix
- `docs:` documentation only
- `exp:` experiment config, run, or analysis change
- `chore:` tooling, CI, dependencies, scaffolding

Examples:

```
feat: add deterministic prose renderer
fix: canonicalize numeric args before signature comparison
docs: clarify G1 refusal gate
exp: record calibration shard 2 cost
chore: pin ruff in dev extras
```

Do not commit generated data, logs, or secrets. Do not rewrite published history.

## 8. Definition of done

A task is done only when all four hold:

1. **Code** — implemented, typed where practical, and consistent with the existing layout.
2. **Test** — a focused test is added or updated, and `pytest -q` passes.
3. **Docs** — the relevant README/docstring/config comment is updated.
4. **Ledger** — if the task produces a result, the run ledger or manifest row exists and the
   reported number cites it.

If a task cannot meet all four, say which one is missing and why.

## 9. Scope discipline

- Do not add paid APIs, external judges, or new model families without a prereg amendment.
- Do not expand the sample beyond 800 + 80 reserve.
- Do not add "dashboard", "benchmark leaderboard", or model-ranking features; they are out of
  scope.
- Prefer stdlib and existing dependencies; justify any new dependency in the PR.
