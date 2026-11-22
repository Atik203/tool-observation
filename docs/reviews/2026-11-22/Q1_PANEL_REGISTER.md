# Q1/A* review panel — verified findings and implementation register

**Date:** 2026-11-22
**Inputs:** four independent deep reviews (methods/statistics, contribution, craft, integrity) run read-only on `main` at `dd5175e`.
**Assumption applied:** human annotation/audit is covered (kit distributed; sheets pending return). AI-only provenance was not re-litigated; residual audit risks are flagged only where the text itself is weak.
**Verification:** every load-bearing claim below was re-checked against the tree. Confirmed claims carry line evidence; two review claims were corrected (see §5).

## 1. Panel verdict

Unanimous **major revision**. No reviewer said reject; none said accept. The measurement framing, failure disclosure, and artifact survive. Four classes block Q1/A*:

1. **The package cannot be externally checked** (DOI unminted, release gitignored, no clean-room compile).
2. **The prereg record does not match the analysis** (amendment omissions, hash mismatch, unamended risk-set change).
3. **Three estimands are not bounded** (mover-only threshold slope, silent share conditional on switch, recovery with informative censoring).
4. **Generality and consequence are single-stream** (one renderer; utility `n=115` same-session; wrong-direction tautological).

## 2. Verified critical findings

### V1 — Package is not externally reproducible — CONFIRMED

- `release/ToolResult-800-v1.0/` exists locally (125 files) but `.gitignore:155-159` ignores it entirely.
- `docs/submission/doi_record.md:3-6` = "STAGED — not yet minted". `docs/DATA_CARD.md:21,43` = DOI TBD.
- `docs/submission/checklist.md:20-24` admits clean-room compile never ran (no TeX toolchain).
- Consequence: a reviewer cloning the repo gets code and docs but no analysis JSONs, no ledgers, no packets.

### V2 — Amendment record incomplete — CONFIRMED

- `prereg/AMENDMENTS.md` Status block says "Amendments since freeze: A-006" while A-004 is itself labeled "post-freeze, after G1 calibration" in the same file.
- Frozen commit mismatch: `AMENDMENTS.md` = `1673856`; `prereg/DEPOSIT_NOTE.md:3` = `1675376`. One is wrong; the hash chain is unverifiable until fixed.
- No amendment rows for post-freeze analysis decisions: D-036 (800-primary sample), D-039/D-043 (label-free primary round), D-040 (recovery censoring), D-044 (T6 endpoint), parser <1% criterion provenance.
- `ROADMAP.md:132-135` requires every deviation in both `DECISIONS.md` **and** `AMENDMENTS.md`. The second half was not done.

### V3 — PII-like fragment ships — CONFIRMED

- String `person_0f41e336893e.ahmed6699@example.com` is present in:
  `data/frozen/prefixes.jsonl`, `release/ToolResult-800-v1.0/frozen/prefixes.jsonl`,
  `release/.../packets/task_utility_packets.json`, and `release/.../pii_rescan.json`.
- `docs/DATA_CARD.md` promises "No raw PII is released" while `D-045:49-53` flags the fragment as kept for freeze integrity.
- `docs/GATES.md` stop rule: a PII leak stops the release. This must be redacted with a version bump, not shipped flagged.

### V4 — Two recovery number sets coexist — CONFIRMED

- Hash risk set (v1): `27.3/34.7/27.2` crude, KM `32.4/47.6/28.2` at `toolresults.tex:287,443,1162,1507,2260,2280`.
- Semantic risk set (v2): `24.4/32.9/21.3` crude, KM `28.2/44.6/22.0` at `:2034-2036,2082-2086`.
- `docs/submission/cover_letter.md` mixes v1 crude with a v2 KM range. One primary set must be chosen (recommend v2 semantic, per T2) and the other demoted to a reconciliation footnote everywhere.

### V5 — Strata count inconsistent — CONFIRMED

- `toolresults.tex:1560,1563` say "617 prefix×model strata … 617 vary"; `:1669` says "649 of the 2,297 strata"; `:1596` prints `617/2,458` (strata over rows). Reconcile to one denominator definition.

### V6 — No Discussion/Limitations section; 25 tables; abstract over length — CONFIRMED

- Sections: Introduction, Conventional Method, Proposed Method, Experiment, Results, Conclusion. Interpretation and limitations are `\paragraph{}` blocks inside Results.
- 25 `table` environments (comment at `:15` still says 24), 10 figures.
- Abstract = 365 words; typical Elsevier cap 200–250.
- Fig. 9: truncated y-axis (disclosed), and KM survival plotted while tables report `1-S_KM(4)` recovery — renaming needed.

### V7 — Utility endpoint and wrong-direction limits — CONFIRMED

- `scripts/17_wrong_direction.py:130` asserts every critical record has `expected_action_change=true`, so "wrong direction" is definitional, not independently verified.
- `tab:utility`: `n=115` judgeable, single-agent same-session coding (κ=.92 on 38 re-codes is intra-rater), donor-match null p=.89, adequacy 55.7→28.7%.

## 3. Corrections to the panel

**C1 — "Ledgers absent, refits impossible" is wrong.**
`data/runs/main` holds full ledgers locally (13,200 base rows + recovery + jitter, 12 files, ~28 MB). Row-level refits (cluster-robust LRT, severity reclassification with CIs, IPW/bounds, Aalen–Johansen) are feasible on this machine. The limitation is publication, not data. P6.3 therefore upgrades from "cannot" to "do it".

**C2 — "PII in committed tree" is overstated.**
The fragment appears only in gitignored frozen/release data, not in any committed file. The blocker is the release package and the data card wording, not repository history.

## 4. Implementation register (P6)

Priority order; P6.1–P6.5 need no GPU.

| ID | Work | Exit criterion | GPU |
|---|---|---|---|
| **P6.1** | Record integrity: fix AMENDMENTS Status + frozen hash; add A-007 (sample 800), A-008 (label-free primary), A-009 (recovery censoring), A-010 (T6 exploratory endpoint), A-011 (parser criterion provenance) | Status lists all post-freeze amendments; hash matches manifest; every D-0xx post-freeze decision has an amendment row | 0 h |
| **P6.2** | Unify number sets: v2 semantic crude primary everywhere; v1 hash demoted to reconciliation note; fix 617/649/2,458; update cover letter and gate-status | One primary triple in abstract, gates, results, conclusion, letter; reconciliation footnote only | 0 h |
| **P6.3** | Row-level refits from local ledgers: cluster-bootstrap LRT; severity reclassification with CIs; IPW + Manski bounds for 5.5% missingness; Aalen–Johansen competing-risk recovery (or crude-only); paired recovery tests | Each refit replaces a point-only sensitivity; CIs reported; ledgers hashed in release | 0 h |
| **P6.4** | PII redaction + version bump to v1.0.1; redaction changelog; test guard so the fragment cannot recur; human re-scan record | Zero hits in release; guard test fails on reintroduction; data card accurate | 0 h |
| **P6.5** | Package and publish: mint DOI (Zenodo), upload release incl. ledgers/JSONs/packets, Overleaf clean-room compile, validation from clean clone | DOI resolves; clean-room compile 0 undefined; `validate-release` passes from downloaded package | 0 h |
| **P6.6** | Craft: add Discussion + Limitations sections; move 13–15 tables to supplement; Fig. 9 full scale + rename to `1-S_KM`; abstract ≤250 words; keywords `tau-bench`; cover letter cleanup | 10–12 main tables; headed Discussion/Limitations; abstract within cap; no survival/recovery ambiguity | 0 h |
| **P6.7** | Generality: second deterministic renderer on 100–200 prefixes (highest-value A* run); optional independent utility replication | Renderer-robustness bound reported; if not run, claim restricted to one template in title-level language | 2–4 h |
| **P6.8** | Sign-offs: authorship/ORCID/CRediT, ethics determination, license venue confirmation, cover letter journal fill | All checklist items signed | 0 h |

**Sequencing:** P6.1 → P6.2 → P6.4 → P6.3 → P6.5 → P6.6 → P6.7 → P6.8. P6.7 can run in parallel on `uiu-h200` while P6.3/P6.5 proceed locally.

## 5. What must not be lost

- Failure-first reporting (parser 1.55%, severity 88.3%, recovery crude) in abstract, gate table, limitations, cover letter.
- A-006 candor: pre-fix β=0.684 alongside 0.877, artifact-not-retained disclosed.
- In-sample circularity disclosure and the held-out audit plan.
- Hash-vs-semantic bridge, censoring-reason table, never-run bounds, parse-worst-case.
- Per-model McNemar primary, cluster bootstrap for β, strict/lenient/reserve sensitivities.
- Release engineering scaffold (`18_build_release.py`, `TABLE_MAP.md`, `SHA256SUMS`) — it only needs a public host.

## 6. Residual limits that survive even after P6

- One renderer unless P6.7 runs; three 8–9B AWQ models; two domains; no frontier control.
- Utility `n=115`; wrong-direction definitional; held-out human audit still a future item despite the annotation program.
- External prereg deposit can be minted with the DOI, but no timestamped registry preceded the run.
