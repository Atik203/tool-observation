# Runbook — ToolResult-800 pipeline

This runbook is the operator view. The protocol is authoritative for design; this file is for
execution, recovery, and troubleshooting.

> **Current state:** v0.1.0 is a scaffold. Pipeline stages `00`–`10` are honest stubs that exit
> with code 2 and print their plan. The commands below are the intended interface; they do not
> produce data yet. Do not report results from a stub.

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
python scripts/01_parse.py --upstream data/upstream --out data/interim/candidates.parquet
python scripts/02_scrub.py --in data/interim/candidates.parquet --out data/interim/scrubbed.parquet
python scripts/03_relevance.py --in data/interim/scrubbed.parquet --out data/interim/eligible.parquet
python scripts/04_replay.py --in data/interim/eligible.parquet --out data/interim/replay.parquet --threshold 0.98
python scripts/05_sample.py --in data/interim/replay.parquet --out data/manifests/sample_880.json --seed 20261108
python scripts/06_freeze.py --sample data/manifests/sample_880.json --out data/manifests/toolresult800_v1.json
python scripts/07_render.py --manifest data/manifests/toolresult800_v1.json --out data/manifests/perturbations.jsonl
python scripts/08_audit.py --manifest data/manifests/toolresult800_v1.json --out artifacts/audit/g0_audit.csv
```

Acceptance: ≥880 eligible, ≥440/domain pre-audit, ≥400/domain post-audit, replay ≥98%, audit
≥36/40. Freeze only after the audit. Record the manifest hash and the prereg hash.

**Stop:** if any check fails, do not proceed to G1. Fix and re-run, or invoke the 500/2 fallback.

---

## 3. Rental setup (24 GB GPU)

1. Book a 24 GB RTX 3090/4090 community instance at $0.30–0.50/h. Prefer a host with 60 GB disk.
2. Record the host, GPU, driver, CUDA, and hourly rate in `artifacts/env/rental_contract.txt`.
3. Install Python 3.12 and create the environment from `environment.yml`; install the GPU stack
   from `requirements-gpu.lock.txt` **generated on that host**.
4. Write `artifacts/env/rental_env.txt`:

```text
host=...
gpu=...
driver=...
cuda=...
vllm=...
torch=...
hourly_usd=...
```

5. Download the three pinned models once. Verify revision hashes against
   `data/manifests/model_pins.json`. Do not accept a floating `main`.
6. Run the 60-prefix calibration before the main run.

```powershell
python scripts/09_run.py --stage calibration --config configs/calibration.yaml
```

Acceptance: parse ≥95%, jitter ≤20%, s=3 switch 10–80%, refusal <5% per model. No main spend
before this passes.

---

## 4. Main run

```powershell
python scripts/09_run.py --stage main --config configs/main.yaml --resume
```

- 34,800-generation envelope; sharded by model and domain.
- Checkpoint every 40 prefixes; one ledger row per generation.
- Stop at $22 spend or 45 GPU-hours, whichever first.
- A parser-error rate >5% in a shard fails fast.

**Resume after interruption:** relaunch with `--resume`; the runner reads the ledger, skips
completed `(model, prefix, arm, step)` rows, and never overwrites a completed row. If the ledger
is corrupt, stop and restore from the last shard checkpoint; do not fabricate missing rows.

**Stop procedure:** flush the ledger, write `artifacts/cost/main_cost.json` with cumulative spend,
GPU-hours, completed prefixes, and reason. Analyze only completed cells and disclose the gap.

---

## 5. Analysis

```powershell
python scripts/10_release.py --runs data/runs/main --out artifacts/analysis
```

Intended outputs: parsed outcomes, slope table (pooled and per model), silent-propagation share,
s=3 vs s=1 McNemar, recovery curves, t½ with CI, Weibull shape test, κ/α report, figures. Every
table includes the manifest hash and ledger row count.

Check G3/G4 before writing any claim. If a gate fails, write the null/measurement report; do not
reframe exploratory analyses as confirmatory.

---

## 6. Release

Follow `release/README.md`. In short:

1. Scrub re-scan and PII audit on the release candidate.
2. Verify the upstream MIT notice and `DATA_LICENSE.md`.
3. Build ToolResult-800 with manifests, perturbations, labels, and traces.
4. Write checksums (`SHA256SUMS`), data card, and CITATION.
5. Deposit and mint a DOI; tag the repository.
6. Publish the paper preprint only after the analysis freeze.

---

## 7. Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `toolobs validate` missing PyYAML | Minimal environment | `pip install pyyaml`; CI intentionally does not need it |
| `pytest` import error | Package not installed | `pip install -e .` or use `python -m pytest` after editable install |
| Replay mismatch spike | Task DB version or tool schema drift | Check pin; rebuild harness; do not lower the 98% threshold |
| vLLM OOM at 8k context | Batch too large or KV cache | Lower `batch_size` to 8, `max_num_seqs` to 8, `gpu_memory_utilization` to 0.85 |
| AWQ load failure | Wheel/CUDA mismatch | Regenerate the GPU lock on the host; do not reuse a CPU lock |
| Refusal rate >5% | Prompt/format mismatch | Fix the prompt at G1; do not coerce at analysis time |
| Parser failures >5% | Model output drift | Stop the shard; inspect examples; fix parser and re-calibrate |
| Ledger write failure | Disk full or permissions | Stop; free space; resume from the last checkpoint; never re-generate completed rows silently |
| Budget approaching $22 | Rental clock or long generations | Stop at the limit; analyze completed shards; no second rental |
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
