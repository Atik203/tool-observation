# Contributing to tool-observation

Thanks for considering a contribution. This is a research repository with a frozen
pre-registration; the rules below protect the integrity of the confirmatory analysis.

## 1. Ground rules

- Read `README.md`, `ROADMAP.md`, `docs/GATES.md`, and `AGENTS.md` first.
- Be civil; the project follows `CODE_OF_CONDUCT.md`.
- Do not commit data, model weights, credentials, or PII. See `SECURITY.md`.
- Do not alter frozen artifacts or the preregistration. Propose an amendment in
  `prereg/AMENDMENTS.md` and `docs/DECISIONS.md` instead.
- Open an issue before a large change so scope can be agreed.

## 2. Setup

```powershell
git clone https://github.com/Atik203/tool-observation.git
Set-Location tool-observation
conda env create -f environment.yml
conda activate tool-observation
pip install -e ".[dev]"
python -m toolobs.cli validate
pytest -q
```

On the maintainer's Windows machine the base interpreter is
`C:\ProgramData\anaconda3\python.exe` (Python 3.12). CI uses Python 3.12 on Ubuntu and installs
the package with `--no-deps`, so the package and smoke tests must work without numpy, pandas, or
PyYAML.

## 3. Branches and commits

- Branch from `main`: `feat/<short-name>`, `fix/<short-name>`, `docs/<short-name>`,
  `exp/<short-name>`.
- Keep branches focused; rebase on `main` before opening a PR.
- Use Conventional Commits: `feat:`, `fix:`, `docs:`, `exp:`, `chore:`.
- Write commit messages about intent, not file names.

## 4. Tests and style

```powershell
pytest -q
python -m compileall -q src
ruff check .
```

- Add a test for every behavior change.
- Tests must not require a GPU, network, model download, or raw data.
- Use `tests/fixtures/` for tiny synthetic fixtures only; never add real trajectories.
- Format with `ruff format` if available; otherwise keep the surrounding style.
- Python 3.12, type hints where practical, no wildcard imports.
- Keep heavyweight imports (`numpy`, `pandas`, `yaml`, `torch`, `vllm`) inside functions or
  optional modules so `import toolobs` stays cheap.

## 5. Pull request checklist

Every PR must state explicitly:

- [ ] **Does this PR touch frozen data, the preregistration, or analysis code?** (yes/no; if yes,
      link the amendment or explain why it is pre-freeze work.)
- [ ] Tests added or updated and `pytest -q` passes.
- [ ] Docs/config comments updated.
- [ ] No raw data, model weights, `.env`, tokens, PII, or run outputs added.
- [ ] `python -m compileall -q src` passes.
- [ ] The change is within the claim boundary in `ROADMAP.md`.
- [ ] No reported number lacks a ledger/manifest source.

A PR that changes analysis code after G0 freeze is not merged without a prereg amendment.

## 6. Data and preregistration rules

- `data/raw/`, `data/upstream/`, `data/interim/`, `data/frozen/`, `data/runs/` are local-only.
- `data/manifests/` may be committed only for small, non-PII manifests and hashes.
- Do not re-sample, re-label, or drop frozen prefixes to improve a result.
- Do not run exploratory analyses on the primary outcome and report them as confirmatory.
- Any post-freeze deviation is logged before the analysis, with the trigger and the affected
  analyses.
- Release candidates go through `release/README.md` and the PII re-scan.

## 7. Issue reporting

Use the GitHub issue forms:

- Bug report: reproduction, expected vs actual, environment, commit.
- Feature request: motivation, scope, whether it touches the preregistration.

For security issues, do **not** open a public issue; follow `SECURITY.md`.

## 8. Code of conduct

By participating you agree to `CODE_OF_CONDUCT.md`. Report unacceptable behavior to
atikurrahaman0305@gmail.com.
