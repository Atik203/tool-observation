# Runbook — ToolResult-800 pipeline

This runbook is the operator view. The protocol is authoritative for design; this file is for
execution, recovery, and troubleshooting.

> **Current state (2026-11-15):** the CPU-only G0 pipeline is implemented through render, the
> 60-prefix calibration selection, the freeze dry-run, and the release packager. The 40-item
> human audit and the frozen `toolresult800_v1` manifest are pending. No study GPU run has
> started; the Qwen AWQ fit check is an environment check only. Stages are real, not stubs; do
> not report results from the dry-run or from the fake backend.

---

## 1. Local setup

```powershell
Set-Location G:\PROJECT\tool-observation
conda env create -f environment.yml
conda activate tool-observation
pip install -e ".[dev]"
python -m toolobs.cli validate
pytest -q
```

If `python` is not the conda interpreter:

```powershell
C:\ProgramData\anaconda3\python.exe -m toolobs.cli validate
C:\ProgramData\anaconda3\python.exe -m pytest -q
```

Expected validate output: all 8 configs present and valid YAML. If PyYAML is missing, validate
reports an existence-only check and exits 0 unless `--strict` is passed.

---

## 2. G0 harvest (CPU, $0)

Run in order. Each stage must pass its acceptance check before the next starts.

```powershell
python scripts/00_pin_source.py --config configs/harvest.yaml
python scripts/01_parse.py --upstream data/upstream/tau-bench --out data/interim/candidates.jsonl
python scripts/02_scrub.py --in data/interim/candidates.jsonl --out data/interim/scrubbed.jsonl
python scripts/03_relevance.py --in data/interim/scrubbed.jsonl --out data/interim/eligible.jsonl
python scripts/04_replay.py --in data/interim/eligible.jsonl --out data/interim/replayed.jsonl
python scripts/05_sample.py --in data/interim/replay_matched.jsonl --out data/interim/sample.jsonl
python scripts/07_render.py --sample data/interim/sample.jsonl --out data/interim/rendered.jsonl --perturbations-out data/interim/perturbations.jsonl
python scripts/08_audit.py --sample data/interim/sample.jsonl
# Fill artifacts/audit/g0_audit_sheet.csv, then:
python scripts/08_audit.py --score artifacts/audit/g0_audit_sheet.csv
python scripts/06_freeze.py --dry-run
python scripts/06_freeze.py   # only after the audit passes
```

The numeric prefixes are stage names, not execution order: render (07) and audit (08) run before
freeze (06). The freeze script also selects the 60 calibration prefixes and writes the scrubbed
`data/frozen/prefixes.jsonl` payload.

Acceptance: ≥880 eligible, ≥440/domain pre-audit, ≥400/domain post-audit, replay ≥98%, audit
≥36/40. Freeze only after the audit. Record the manifest hash and the prereg hash.

**Stop:** if any check fails, do not proceed to G1. Fix and re-run, or invoke the 500/2 fallback.

---

## 3. University GPU setup — `uiu-h200`

1. Connect only via the `uiu-h200` SSH alias. Do not expose ports or create another connection
   method.
2. Check `df -h` and `du -sh`; stay inside the project space. The hard cap is 200 GB.
3. Create a project-local venv or conda environment. Install from `environment.yml` and the GPU
   stack from `requirements-gpu.lock.txt` **generated on that host**. Do not change driver
   580.178.04, CUDA 13.5, system libraries, MIG settings, clocks, or power limits.
4. Use `tmux` or `screen`; stop idle GPU jobs.
5. Record the GPU, driver, CUDA, vLLM, torch, and storage in `artifacts/env/h200_env.txt`:

```text
gpu=H200 1g.18gb
driver=580.178.04
cuda=13.5
vllm=...
torch=...
storage_gb=...
```

6. Download the three pinned models once. Verify revision hashes against
   `data/manifests/model_pins.json`. Do not accept a floating `main`.
7. **Fit check:** the slice has 18 GB VRAM. Verify the pinned AWQ model, 24k context, and batch
   fit. All three pinned models pass at `gpu_memory_utilization=0.85`, 24k context, batch 4, and
   `max_num_seqs=8`. Qwen3.5 needs the cap because its Mamba cache cannot serve the default 256
   sequences; it also runs with thinking disabled. On the H200 host, export the project-local
   headers first (`PYTHONPATH=.deps/pyheaders`, `CPATH=.deps/pyheaders/include`,
   `C_INCLUDE_PATH=.deps/pyheaders/include`).

```powershell
python scripts/11_fit_check.py --model-id qwen3_5_9b_instruct_awq --batch-size 4 `
  --gpu-memory-utilization 0.85 --max-num-seqs 8
```

The fit check uses a generic non-study prompt and writes
`artifacts/env/<model>_fit_check.json`; it is environment evidence, not a study result.
8. Run the 60-prefix calibration before the main run.

```powershell
python scripts/09_run.py --stage calibration --all-models --backend vllm
```

Acceptance: parse ≥95%, negative-control jitter (s0 vs s1) ≤20%, s=3 switch 10–80%, refusal <5%
per model. V-vs-s0 format jitter is reported, not gated (D-026). No main-run start before this
passes.

`09_run.py --all-models` refuses with the vLLM backend (D-022): vLLM cannot unload a model inside
one process. Use the orchestrator, which starts one process per model:

```powershell
python scripts/09a_run_all.py --stage calibration --backend vllm
```

Re-score an existing ledger after a parser change without regenerating outputs:

```powershell
python scripts/09c_rescore.py --input data/runs/calibration/<model>/ledger.jsonl `
  --output data/runs/calibration_v3/<model>/ledger.jsonl --force
python scripts/09a_run_all.py --stage calibration --score-only `
  --ledger-root data/runs/calibration_v3 --report artifacts/audit/g1_calibration_v3.json
```

---

## 4. Main run

```powershell
python scripts/09a_run_all.py --stage main --backend vllm --resume
```

**Status:** the base matrix (4,400 rendered arms × 3 models = 13,200 generations) is implemented.
`scripts/09b_recovery.py` implements the transient and persistent H=4 recovery shards and
`scripts/09d_jitter.py` the 1,200 seed-repeat generations; both are CPU-tested. Full envelope:
34,800 generations.

Run the two extra shards after the base matrix finishes (they read the base ledger):

```powershell
python scripts/09d_jitter.py --model-id <model> --backend vllm
python scripts/09b_recovery.py --model-id <model> --regime both
```

- 34,800-generation envelope; sharded by model and domain.
- Checkpoint every 40 prefixes; one ledger row per generation.
- Stop at 45 GPU-hours or 200 GB storage, whichever first.
- A parser-error rate >5% in a shard fails fast.

**Resume after interruption:** relaunch with `--resume`; the runner reads the ledger, skips
completed `(model, prefix, arm, step)` rows, and never overwrites a completed row. If the ledger
is corrupt, stop and restore from the last shard checkpoint; do not fabricate missing rows.

**Stop procedure:** flush the ledger, write `artifacts/cost/main_cost.json` with cumulative
GPU-hours, storage, completed prefixes, and reason. Analyze only completed cells and disclose the
gap.

### Paused state — 2026-11-15 (resume here)

The GPU is idle and no tmux session is running. Everything below was copied to the local
checkout and verified by SHA-256.

| Item | State |
|---|---|
| G0 freeze | complete; manifest SHA-256 `d6e034d7…`, frozen prefixes present |
| G1 calibration | **pass**, all three models; report `artifacts/audit/g1_calibration_v3.json` |
| G1 ledgers | `data/runs/calibration/<model>/ledger.jsonl` (300 rows each, parser v2 raw) |
| G1 rescored | `data/runs/calibration_v3/<model>/ledger.jsonl` (300 rows each, parser v3) |
| G2 base | **partial**: Qwen 2,704 / 4,400 rows; Ministral and Llama not started |
| G2 recovery | runner written and CPU-tested; **not run** |
| G2 jitter | **not implemented** |

Resume the base matrix on the H200:

```bash
cd /home/mnh/tool-observation
export PYTHONPATH=/home/mnh/tool-observation/.deps/pyheaders \
       CPATH=/home/mnh/tool-observation/.deps/pyheaders/include \
       C_INCLUDE_PATH=/home/mnh/tool-observation/.deps/pyheaders/include
tmux new -s g2base -d \
  '.venv/bin/python scripts/09a_run_all.py --stage main --backend vllm --resume \
   > artifacts/audit/g2_base.log 2>&1'
```

`--resume` keeps the 2,704 existing Qwen rows and starts Ministral and Llama from row 0.

---

## 5. Analysis

The analysis core is implemented in `src/toolobs/analysis/`:

- `outcomes.py`: automatic `Y`, `Y^A`, `Y^F`, `Y^U` labels from ledger rows and perturbation records.
- `slope.py`: pure-Python conditional-logit slope, prefix-cluster SE, percentile bootstrap, Holm.
- `recovery.py`: discrete exponential, Kaplan–Meier, RMST, Weibull shape LRT.

There is no standalone analysis CLI yet; call these from a notebook or a small script and write
outputs under `artifacts/analysis/`. Every table must include the manifest hash and ledger row
count. Check G3/G4 before writing any claim. If a gate fails, write the null/measurement report;
do not reframe exploratory analyses as confirmatory.

---

## 6. Release

Follow `release/README.md`. In short:

1. Scrub re-scan and PII audit on the release candidate.
2. Verify the upstream MIT notice and `DATA_LICENSE.md`.
3. Build ToolResult-800 with manifests, perturbations, labels, and traces.
4. Write checksums (`SHA256SUMS`), data card, and CITATION.
5. Deposit and mint a DOI; tag the repository.
6. Publish the paper preprint only after the analysis freeze.

The packager is `python scripts/10_release.py`; it verifies the frozen manifest, payload hashes,
renderer hash, prereg hash, and a PII rescan before copying anything. It refuses without a passed
G0 audit and a frozen manifest.

---

## 7. Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `toolobs validate` missing PyYAML | Minimal environment | `pip install pyyaml`; CI intentionally does not need it |
| `pytest` import error | Package not installed | `pip install -e .` or use `python -m pytest` after editable install |
| Replay mismatch spike | Task DB version or tool schema drift | Check pin; rebuild harness; do not lower the 98% threshold |
| vLLM OOM at 24k context on 18 GB | Batch too large, context too long, or KV cache | Lower `batch_size` to 8, `max_num_seqs` to 8, `gpu_memory_utilization` to 0.85; lower context if needed; log the reduction |
| AWQ load failure | Wheel/CUDA mismatch | Regenerate the GPU lock on the host; do not reuse a CPU lock; do not reinstall the driver or CUDA |
| Refusal rate >5% | Prompt/format mismatch | Fix the prompt at G1; do not coerce at analysis time |
| Parser failures >5% | Model output drift | Stop the shard; inspect examples; fix parser and re-calibrate |
| Ledger write failure | Disk full or permissions | Stop; free space; resume from the last checkpoint; never re-generate completed rows silently |
| GPU-hour or storage cap approaching | Long generations or large traces | Stop at 45 GPU-hours or 200 GB; analyze completed shards; no second GPU |
| Suspected PII | Scrub miss or new field | Stop the release; report privately per `SECURITY.md`; re-scan |

---

## 8. What not to do

- Do not commit `data/raw/`, `data/upstream/`, `data/interim/`, `data/frozen/`, `data/runs/`,
  model weights, `.env`, tokens, or PII.
- Do not edit a frozen manifest to make a test pass.
- Do not run the main run on the local 3060.
- Do not add a paid API or a second GPU.
- Do not report a number without a ledger or manifest row.
- Do not call the pilot a dose-response law.
