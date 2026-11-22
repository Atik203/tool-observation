# Cover letter — ToolResult-800 measurement study

[Journal: TBD — author to fill. Editor: TBD. Corresponding author: Md. Atikur Rahaman
<mrahaman2310298@bscse.uiu.ac.bd>, Computer Science and Engineering,
United International University, Dhaka 1212, Bangladesh.]

Dear Editor,

We submit our manuscript **"Tool-Result Errors in Language-Model Agents: A Fixed-Prefix
Measurement Study of Switches, Silent Propagation, and Recovery"** for consideration as a
research article.

**What the paper is.** A frozen fixed-prefix measurement study (preregistered, gated) of the
moment a tool-using agent reads a tool output: 800 real τ-bench prefixes (400 airline, 400
retail), each observed under five arms (verbatim JSON, faithful prose, one non-critical change,
one critical wrong value, critical-plus-contradiction), answered greedily by three open-weight
8–9B models at \$0 cash. The contribution is a reusable
stimulus set with full provenance, a within-prefix design with a silent-propagation
decomposition, and a four-step recovery curve — reported with failures stated, not hidden.

**Claim boundary (no overclaim).** The pre-registered content-sensitivity claim is *not* made:
three gate criteria failed and are reported as failures — protocol parser-failure rate 1.55%
against 1%, severity-audit s2/s3 decision share 88.3% against 90%, and crude recovery on the
semantic risk set 24.4/32.9/21.3% by model (Qwen/Ministral/Llama) against 50% (Kaplan–Meier 28.2/44.6/22.0% secondary). The G1 placebo
criterion was amended post-freeze (A-004, not blind) and is reported as a failed original
criterion. Within that bound we report a measured shift among movers (pooled slope 0.877
[0.770, 0.998]), at least 21.3% silent propagation of critical-arm switches (recall-adjusted
≈28.5%), semantic-risk-set recovery (v2) as the primary estimand, a row-level realized-severity
refit whose intervals overlap the assigned effects, cluster-robust inference checks, and an
exploratory blinded task-utility endpoint.

**Reproducibility.** The v1.0 release is staged with a DOI deposit record: scrubbed prefixes,
perturbation records, ledger extracts, audit packets/sheets, all analysis JSONs, preregistration
+ amendments, upstream MIT notice, and model-output license verification — with a
table-to-artifact map and a one-command validator (`make validate-release`, including producer
reruns that rebuild the T2–T6 analysis JSONs bit-identical). The G0
harvest audit is an AI pre-audit with human verification deferred; all ratings are AI-agent
produced, author-overseen — both stated in the paper, with a held-out human audit as future work.

**Fit.** The manuscript includes 2025–26 neighbors (all arXiv IDs verified 2026-11-22).
Highlights and keywords are within limits. Suggested handling: reviewers familiar with agent evaluation, measurement
methodology, and preregistered ML experimentation.

The work is original and not under consideration elsewhere; submission follows author
sign-off on the byline/ORCID/CRediT freeze (`docs/submission/authorship.md`; O.T. e-mail
still TBD). No competing interests; no external funding (university H200 slice in kind).

Sincerely,
Md. Atikur Rahaman (corresponding author), Ohidujjaman Tuhin
