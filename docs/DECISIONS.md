# Decision log

Architectural and research decisions for `tool-observation`. Add new entries at the top. Any
decision that touches the preregistration, frozen data, or analysis plan also requires an entry
in `prereg/AMENDMENTS.md` before the affected analysis runs.

---

## D-005 — Dataset brand is CTO-800; repository remains tool-observation

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The dataset needs a citable brand distinct from the software repository. Naming
  the repo `cto-800` would conflate the code, the study, and the released data.
- **Decision:** The dataset is **CTO-800**. The repository is **`Atik203/tool-observation`**, the
  Python package is **`toolobs`**, and the study short name is **E2**.
- **Consequences:** Release artifacts use the CTO-800 name; the repo URL and package name stay
  stable. Documentation must not call the repository "cto-800".

---

## D-004 — No post-freeze edits to data, perturbations, or analysis

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The study's credibility depends on the freeze being real. Post-hoc changes to the
  sample or severity labels would invalidate the confirmatory claim.
- **Decision:** After G0, `data/manifests/cto800_v1.json`, perturbation records, the field
  registry, the renderer version, prompts, and the analysis plan are immutable. Any deviation is
  written to this file and `prereg/AMENDMENTS.md` before the affected analysis, stating the
  trigger, change, affected analyses, and whether it was blind to target outcomes.
- **Consequences:** Reproducibility fixes that do not alter frozen artifacts are allowed and
  recorded in `CHANGELOG.md`. A change that alters a frozen artifact requires a new dataset
  version, not an edit.

---

## D-003 — Pilot claim boundary: screening signal, not a law

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The pilot (N=60, qwen3.5:4b, synthetic prefixes) found consult 54/60, placebo
  jitter 0/60, error switch 5/60 = 8.3% [1.3, 15.3] pp, McNemar p=.0625. The result is marginal
  and the CI includes a 1.3 pp effect. Letter coding missed silent fact propagation, and there is
  no recovery data.
- **Decision:** The pilot is reported as a **screening signal** and a kill-gate result only. It
  is not evidence of a dose-response law, not a slope estimate, and not a model comparison. The
  confirmatory study does not pool pilot and main data.
- **Consequences:** Every public description of the pilot carries the caveats. A null
  confirmatory result is reported as null; the pilot is not used to rescue it.

---

## D-002 — Project storage on `G:` with public export from `tool-observation`

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The project needs local space for raw trajectories, model outputs, and run
  ledgers, while the public repository must stay small and PII-free. The G: drive has ample free
  space; the research workspace on E: is a separate project and must not be modified.
- **Decision:** Local root is **`G:\PROJECT\tool-observation`**. Raw, upstream, interim, frozen,
  and run data stay under `data/` and are gitignored. Only manifests, docs, code, and governance
  files are tracked. The public repo is `Atik203/tool-observation`.
- **Consequences:** Do not place raw data or weights in the repo. Do not modify
  `E:\PROJECT\Research-Ideas` or `E:\PROJECT\energy-optimal-rag`. Storage/egress is budgeted at
  $2–3; large caches are deleted after hashes and ledgers are archived.

---

## D-001 — Repository name and scope

- **Date:** 2026-11-09
- **Status:** accepted
- **Context:** The study needs a public, citable repository that separates the software from the
  CTO-800 dataset brand and does not imply a universal law.
- **Decision:** Create **`Atik203/tool-observation`** as a public repo for the fixed-prefix
  causal study (E2). Scope is bounded to three open-weight 7–8B models, τ-bench airline/retail,
  next-decision sensitivity, and four-step recovery. Code is MIT; documentation and derived data
  are CC BY 4.0; upstream τ-bench remains MIT.
- **Consequences:** No frontier models, model ranking, end-to-end success, or live-API claims in
  this repository. Follow-up work gets a separate scope.
