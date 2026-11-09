## Summary

<!-- What does this PR change, and why? -->

## Scope check

- [ ] This PR **does / does not** touch frozen data, the preregistration, or analysis code.
      <!-- If yes: link the amendment in prereg/AMENDMENTS.md or explain why this is pre-freeze work. -->
- [ ] The change stays within the claim boundary in `ROADMAP.md`.
- [ ] No reported number lacks a ledger or manifest source.

## Type

- [ ] `feat` — new capability
- [ ] `fix` — bug fix
- [ ] `docs` — documentation only
- [ ] `exp` — experiment config, run, or analysis change
- [ ] `chore` — tooling, CI, dependencies

## Testing

- [ ] `python -m compileall -q src`
- [ ] `pytest -q`
- [ ] `python -m toolobs.cli validate`
- [ ] New or updated test covers the change.
- [ ] Tests do not require a GPU, network, model download, or raw data.

## Data and security

- [ ] No raw data, model weights, `.env`, tokens, PII, or run outputs are included.
- [ ] Any new dependency is justified and does not break the no-deps CI smoke test.
- [ ] If this touches a release artifact, the PII re-scan in `release/README.md` was run.

## Docs

- [ ] README/config comments/docstrings updated where behavior changed.
- [ ] `CHANGELOG.md` updated for user-visible changes.

## Notes for reviewers

<!-- Known limitations, follow-ups, or parts you want scrutinized. -->
