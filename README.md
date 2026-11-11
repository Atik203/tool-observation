# Tool-Observation Sensitivity in Language-Model Agents

**A fixed-prefix causal study of how tool-output content changes an agent's next decision — and how long recovery takes.**

[![CI](https://github.com/Atik203/tool-observation/actions/workflows/ci.yml/badge.svg)](https://github.com/Atik203/tool-observation/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](pyproject.toml)

> **Research status: pre-confirmatory (scaffold, v0.1.0).** No confirmatory results exist yet.
> The only empirical evidence is a 60-prefix pilot. It is a screening signal, **not** a
> dose-response law. The confirmatory run has not started; gates G0–G4 are defined but unpassed.

## The question

An agent calls a tool, reads the observation, and chooses the next action. Benchmarks usually
score the whole episode. They do not tell us whether the agent notices a wrong price, a wrong
date, or a policy that contradicts the observation. This project freezes the conversation
immediately after a **real** tool observation, varies only the observation's **content** under a
fixed prose rendering, and measures the causal effect on the next decision within the same
prefix. It then follows the episode for four steps to estimate recovery.

## Pilot evidence (screening only)

The pilot used **N=60** synthetic WebArena-lite / τ-style prefixes, **qwen3.5:4b**, greedy
decoding, three collapsed action codes (trust / re-call / flag). It is a kill-gate, not an
estimate of the confirmatory slope.

| Quantity | Pilot result |
|---|---:|
| Consult rate | 54/60 = 90.0% |
| Placebo jitter, P vs T | 0/60 = 0% |
| Error switch, E vs T | 5/60 = 8.3% |
| Gap, 95% CI | 8.3 pp [1.3, 15.3] |
| McNemar | b=5, c=0; exact p=.0625 |
| Human spot-check | 12/12 labels agree |

**Read this carefully.** N=60 with p=.0625 is marginal; the CI is compatible with a 1.3 pp
effect. Letter coding is conservative — the spot-check found silent fact propagation that the
action code missed, so 8.3 pp is an action-level lower bound, not a content-sensitivity
estimate. One model, synthetic prefixes, and no recovery data mean the pilot cannot distinguish
a graded law from a handful of flips. **It is a screening signal, not a dose-response law.**

## Confirmatory design

| Element | Specification |
|---|---|
| Sample | **800 real τ-bench prefixes**: 400 airline + 400 retail; 80 held in reserve |
| Arms | **V** verbatim JSON anchor · **s=0** faithful prose · **s=1** non-critical change · **s=2** critical wrong value · **s=3** critical + contradiction |
| Models | Qwen2.5-7B-Instruct-AWQ · Mistral-7B-Instruct-v0.3-AWQ · Llama-3.1-8B-Instruct-AWQ (4-bit, greedy) |
| Pairing | Every arm is generated from the same frozen prefix; target models never generate the prefix |
| Recovery | **H=4** steps; transient injection primary, persistent injection on 25%; R1 correct decision, R2 detection |
| Generation envelope | **34,800** generations (12,000 base + 19,200 transient recovery + 2,400 persistent + 1,200 jitter repeats) |
| Primary estimand | Conditional-logistic slope of content switch on severity, clustered by prefix; pooled first, then per-model |
| Budget | **$23 base / $50 hard cap**; 35–45 GPU-hours on a 24 GB rental; no paid API |
| Analysis | Discrete-time survival for recovery half-life, Weibull shape check, pre-registered multiplicity sequence |

The full design and stop rules are in [`docs/PROTOCOL.md`](docs/PROTOCOL.md) and
[`ROADMAP.md`](ROADMAP.md). Power calculations are in
[`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md).

### Claim boundary

If the gates pass, the paper claims a **bounded content-sensitivity and recovery result for three
open-weight 7–8B model families on τ-bench airline and retail**, estimated within-prefix. It does
**not** claim a universal law, a model ranking, invariance across tasks or domains, transfer to
frontier models, or end-to-end task-success effects. A null or flat slope is a publishable
measurement result and will be reported as such.

## Repository map

```
tool-observation/
├─ configs/             # YAML config (base, models, harvest, arms, field registry, calibration, main, analysis)
├─ src/toolobs/         # Python package: taubench, harvest, render, infer, code, analysis, release
├─ scripts/             # 00_pin_source … 10_release pipeline entry points
├─ tests/               # smoke tests; fixtures will be added with the pipeline
├─ data/                # local-only data staging (raw/upstream/interim/frozen/runs are gitignored)
├─ artifacts/           # audit, analysis, env, cost, paper outputs (gitignored except READMEs and .gitkeep)
├─ docs/                # protocol, gates, rubric, data card, runbook, decisions, plan, proposal
├─ prereg/              # preregistration text and amendments log
├─ paper/               # proposal and manuscript source
├─ release/             # CTO-800 release checklist and packaging notes
└─ .github/             # CI and contribution templates
```

**CTO-800** is the dataset brand. The repository is named `tool-observation`; the dataset is not
the repository.

## Quick start

```powershell
conda env create -f environment.yml
conda activate tool-observation
pip install -e ".[dev]"
python -m toolobs.cli validate
pytest -q
```

On the local Windows machine the base interpreter is
`C:\ProgramData\anaconda3\python.exe` (Python 3.12). The local RTX 3060 (6 GB) is for smoke tests
only; the main run uses a 24 GB rental. See [`docs/RUNBOOK.md`](docs/RUNBOOK.md).

Make targets: `make setup`, `make test`, `make lint`, `make validate`, `make clean`.
PowerShell equivalents: `.\tasks.ps1 setup|test|lint|validate|clean`.

## Data policy

- Raw τ-bench trajectories, upstream checkouts, interim files, frozen prefixes, and run ledgers
  are **never committed**. They live under `data/` and are gitignored.
- `data/manifests/` is the only data directory tracked by git: it holds small, non-PII manifests,
  hashes, and freeze records.
- Model weights, adapters, caches, `.env` files, tokens, and rental credentials are never
  committed.
- τ-bench trajectories can contain names, emails, addresses, phone numbers, and payment
  identifiers. Raw trajectories are treated as PII-bearing even before scrubbing.
- The public CTO-800 release contains only scrubbed, licensed derived data. Upstream τ-bench data
  remains MIT and is not re-licensed by this project.

See [`data/README.md`](data/README.md) and [`DATA_LICENSE.md`](DATA_LICENSE.md).

## Roadmap

[`ROADMAP.md`](ROADMAP.md) contains the phase plan (P0–P5), the 10-day G0 sprint, gates G0–G4,
budget, risks, out-of-scope list, and change control.

Proposal: [`paper/proposal.tex`](paper/proposal.tex) and
[`paper/out/proposal.pdf`](paper/out/proposal.pdf). Supervisor-facing summary:
[`docs/proposal.md`](docs/proposal.md).

Co-author onboarding and task division:
[`docs/COAUTHOR_GUIDE.md`](docs/COAUTHOR_GUIDE.md).

## Citation

If you use this repository before the paper is available, cite the software metadata in
[`CITATION.cff`](CITATION.cff). A paper citation will be added when a draft exists.

## License

- **Code:** MIT — see [`LICENSE`](LICENSE).
- **Documentation and derived data:** CC BY 4.0 — see [`LICENSE-DOCS`](LICENSE-DOCS) and
  [`DATA_LICENSE.md`](DATA_LICENSE.md).
- **Upstream τ-bench:** MIT; upstream licenses and notices are preserved.

## Contact

Atikur Rahaman — atikurrahaman0305@gmail.com

Contributions follow [`CONTRIBUTING.md`](CONTRIBUTING.md) and the
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md). Report vulnerabilities privately via
[`SECURITY.md`](SECURITY.md).
