/**
 * Pilot and planned-study facts for the site.
 *
 * Every value below is copied from the repository record, not estimated:
 * - README.md (pilot table, confirmatory design)
 * - prereg/PREREGISTRATION.md
 * - ROADMAP.md
 * - docs/PROTOCOL.md
 * - docs/IMPLEMENTATION_PLAN.md
 *
 * The pilot is a screening signal, not a dose-response estimate.
 */

export const pilot = {
  n: 60,
  model: "qwen3.5:4b",
  prefixType: "synthetic WebArena-lite / τ-style prefixes",
  decoding: "greedy",
  actionCodes: ["trust", "re-call", "flag"],
  consult: { count: 54, total: 60, pct: 90.0 },
  placeboJitter: { count: 0, total: 60, pct: 0 },
  errorSwitch: { count: 5, total: 60, pct: 8.3 },
  gap: { pp: 8.3, ci: [1.3, 15.3] as const },
  mcnemar: { b: 5, c: 0, p: 0.0625 },
  spotCheck: { agree: 12, total: 12 },
  source: "README.md · prereg/PREREGISTRATION.md · docs/IMPLEMENTATION_PLAN.md",
  caveats: [
    "N=60, one 4B model, synthetic prefixes, coarse action coding.",
    "No recovery data and no dose-response estimate.",
    "McNemar p=.0625 is marginal; the 95% interval includes a 1.3 pp effect.",
    "Letter coding missed some silent propagation, so 8.3 pp is an action-level lower bound.",
  ],
} as const;

export const planned = {
  prefixes: 800,
  reserve: 80,
  domains: { airline: 400, retail: 400 },
  models: [
    { name: "Qwen3.5-9B-AWQ", family: "Qwen", params: "9B" },
    { name: "Ministral-3-8B-Instruct-2512-AWQ", family: "Mistral", params: "8B" },
    { name: "Llama-3.1-8B-Instruct-AWQ-INT4", family: "Llama", params: "8B" },
  ],
  arms: [
    { id: "V", level: "anchor", change: "Exact real observation, raw JSON.", role: "Format/jitter anchor" },
    { id: "s=0", level: "0", change: "Faithful prose; all values preserved.", role: "Placebo" },
    { id: "s=1", level: "1", change: "One non-critical field changed or omitted.", role: "Negative control" },
    { id: "s=2", level: "2", change: "One critical field changed to a plausible wrong value.", role: "Dose" },
    { id: "s=3", level: "3", change: "Critical wrong value plus a second detectable contradiction.", role: "Dose (compound)" },
  ],
  generations: 34_800,
  baseGenerations: 12_000,
  transientGenerations: 19_200,
  persistentGenerations: 2_400,
  jitterGenerations: 1_200,
  recoverySteps: 4,
  persistentShare: 0.25,
  cashBudget: 0,
  gpuHoursCap: 45,
  storageCapGb: 200,
  gpuResource: "uiu-h200 H200 1g.18gb (18 GB VRAM)",
  seed: 20261108,
  source: "README.md · ROADMAP.md · docs/PROTOCOL.md",
} as const;

export const outcomes = [
  {
    id: "Y",
    label: "Any sensitivity",
    body: "The decision signature differs from the verbatim-observation continuation.",
  },
  {
    id: "Y^U",
    label: "Silent propagation",
    body: "The false critical value appears in the decision, with no flag. Not scored for s=1.",
  },
  {
    id: "Y^F",
    label: "Detection",
    body: "An explicit flag, doubt, “inconsistent”, “verify”, or “cannot trust”.",
  },
  {
    id: "Y^A",
    label: "Action switch",
    body: "The tool name or canonicalized arguments differ from the V continuation.",
  },
] as const;

export const gates = [
  {
    id: "G0",
    when: "End of week 2",
    criterion: "≥880 eligible; ≥440/domain pre-audit; ≥400/domain post-audit; replay ≥98%; 40-item audit ≥36/40.",
    fail: "500-prefix / 2-model fallback, or stop.",
  },
  {
    id: "G1",
    when: "Week 3",
    criterion: "Parse ≥95%; placebo jitter ≤20%; s=3 switch 10–80%; refusal <5% per model.",
    fail: "Fix prompt or parser; no main-run start.",
  },
  {
    id: "G2",
    when: "Weeks 4–7",
    criterion: "Stop at 45 GPU-hours or 200 GB storage; ledger complete.",
    fail: "Analyse completed shards; disclose.",
  },
  {
    id: "G3",
    when: "Weeks 8–10",
    criterion: "Pooled β>0; positive in ≥2/3 models; severity α≥.75; outcome κ≥.80 (or adjudicated ≥.70); recovery κ≥.75.",
    fail: "Null/measurement paper.",
  },
  {
    id: "G4",
    when: "Weeks 9–10",
    criterion: "≥50% of the s=3 risk set recovers by H=4; Weibull shape not rejected at p≥.01.",
    fail: "Report RMST/curve; t½ exploratory.",
  },
] as const;

export const phases = [
  { id: "P0", name: "Harvest and freeze", weeks: "1–2", gate: "G0" },
  { id: "P1", name: "Calibration", weeks: "3", gate: "G1" },
  { id: "P2", name: "Main run", weeks: "4–7", gate: "G2" },
  { id: "P3", name: "Labels and analysis", weeks: "6–10", gate: "G3/G4" },
  { id: "P4", name: "Paper", weeks: "9–14", gate: "Internal review" },
  { id: "P5", name: "Release", weeks: "15–18", gate: "Release checklist" },
] as const;

export const results = {
  status:
    "base matrix, recovery, and seed-repeat complete; label-free audits scored and checked by an agent verification panel (D-043); severity s2/s3 criterion fails",
  baseGenerations: 13_200,
  jitterGenerations: 1_200,
  recoveryGenerations: 7_211,
  totalGenerations: 21_611,
  primary: {
    pooledBeta: 0.877,
    pooledSe: 0.059,
    pooledP: 2.3e-49,
    bootstrapCi: [0.770, 0.998] as const,
    bootstrapP: 0.001,
    perModel: [
      { model: "Qwen3.5-9B", beta: 1.079, se: 0.114, p: 3.4e-21 },
      { model: "Ministral-3-8B", beta: 0.915, se: 0.090, p: 4.7e-24 },
      { model: "Llama-3.1-8B", beta: 0.649, se: 0.100, p: 1.0e-10 },
    ],
    silentShare: 0.213,
    silentN: 419,
    switchedN: 1_964,
    armRates: [
      { model: "Qwen3.5-9B", s0: 0.198, s1: 0.199, s2: 0.310, s3: 0.384 },
      { model: "Ministral-3-8B", s0: 0.319, s1: 0.336, s2: 0.444, s3: 0.519 },
      { model: "Llama-3.1-8B", s0: 0.381, s1: 0.397, s2: 0.448, s3: 0.490 },
    ],
    source: "artifacts/analysis/g3_analysis.json",
  },
  g1: {
    parse: { qwen: 0.983, ministral: 1.0, llama: 0.967 },
    negControlJitter: { qwen: 0.119, ministral: 0.133, llama: 0.105 },
    formatJitter: { qwen: 0.203, ministral: 0.367, llama: 0.456 },
    s3Switch: { qwen: 0.356, ministral: 0.55, llama: 0.561 },
    refusal: { qwen: 0.017, ministral: 0.0, llama: 0.0 },
    source: "artifacts/audit/g1_calibration_v3.json",
  },
  jitter: {
    stability: { qwen: 0.9894, ministral: 0.9895, llama: 1.0 },
    gate: 0.9,
    source: "artifacts/analysis/jitter_stability_*.json",
  },
  recovery: {
    passed: false,
    byModel: [
      { model: "Qwen3.5-9B", n: 264, recovered: 0.324, rmst: 2.97, halfLife: 6.39 },
      { model: "Ministral-3-8B", n: 406, recovered: 0.476, rmst: 2.71, halfLife: 4.29 },
      { model: "Llama-3.1-8B", n: 412, recovered: 0.282, rmst: 3.16, halfLife: 8.02 },
    ],
    source: "artifacts/analysis/g4_recovery.json",
  },
  source: "G3 analysis + G4 recovery reports, synced 2026-11-19",
} as const;

export const pilotTable = [
  { quantity: "Consult rate", value: "54/60 = 90.0%" },
  { quantity: "Placebo jitter", value: "0/60 = 0%" },
  { quantity: "Error switch", value: "5/60 = 8.3%" },
  { quantity: "Gap, 95% CI", value: "8.3 pp [1.3, 15.3]" },
  { quantity: "McNemar", value: "b=5, c=0; exact p=.0625" },
  { quantity: "Human spot-check", value: "12/12 labels agree" },
] as const;
