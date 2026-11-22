# Preregistration freeze and deposit note (P4.4)

- **Frozen version:** commit `1675376` (2026-11-15), tag `prereg-freeze-v1`,
  prereg hash `e0d107c6` (authoritative; the document header's DRAFT/TBD
  lines are stale and are not amended, per the no-edit rule).
- **External registry:** none. The deposit is in-repo until the release DOI
  (Task 7): `prereg/PREREGISTRATION.md` (frozen) + `prereg/AMENDMENTS.md`
  (A-001–A-006) + `data/manifests/toolresult800_v1.json` (hash sidecar).
- **This task (P4.4) adds no amendment.** Outcome-definition handling is by
  reported sensitivity, not by rule change: strict flag-excluding coding
  (≈ signature-only $Y$) leaves the slope unchanged (0.876 vs 0.877), and
  $Y^O$ is decomposed separately. See
  `artifacts/analysis/inference_robustness.json` (regenerable via
  `scripts/16_inference_robustness.py`).
- **Pre-fix record (M22):** the pre-fix automatic coder gave pooled
  $\hat\beta = 0.684$ [0.584, 0.797]; the artifact was not retained. The
  number is cited from A-006/ROADMAP and disclosed as pre-fix, not
  reconstructed.
- **Audit circularity (M9):** the post-fix coder was conformed on the same
  160 outcome items used to certify $\kappa=.987$/PPV=1.00 — the audit is
  in-sample. No fresh held-out audit exists; the held-out plan (reserve
  prefixes, 60–120-item human audit) is future work.
- **Provenance:** multi-role agent panel, author-overseen.
