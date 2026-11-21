# VOICE_PROFILE.md — Calibrated Author Style & Structural Guide

- **Confidence:** High (empirically extracted from a complete 10,149-word journal manuscript scoring 0% on Turnitin).
- **Source Sample:** `G:\HaluRISC\Journal_Paper\halurisc.tex` (Title: *Calibrated Hallucination Risk for Large Language Models Under Domain and Task Shift with Evidence-Consistent XGBoost*).
- **Samples excluded and why:** None. Complete `.tex` source and associated high-resolution figures in `G:\HaluRISC\Journal_Paper\figures/` analyzed.

---

## 1. Quantitative Stylistic Fingerprint

| Metric | Measured Value in Author Sample | Target Standard for Future Writing |
| :--- | :--- | :--- |
| **Total Analyzed Body Words** | 10,149 words | Standard journal length |
| **Total Substantive Paragraphs** | 45 paragraphs | Comprehensive blocks |
| **Paragraph Word Count** | **Mean = 225.5 words**, Median = 207 words (Min = 91, Max = 447) | **8–18 lines / 120–250+ words per paragraph** (strictly ban 3–6 line stub micro-paragraphs) |
| **Sentence Length & Burstiness** | **Mean = 20.4 words, StDev = 10.8 words** (Min = 3, Max = 73) | **High Burstiness**: Pair 6–10 word definitive statements alongside 25–35 word compound sentences |
| **Top-Level Sections** | **Exactly 6 main numbered sections** | **Locked Standard: 6 Sections** (ask author before adding more) |
| **Subsections** | **Core only**: Sec 2 (2), Sec 3 (5), Sec 4 (4), Sec 5 (6) | **Max 3–5 core subsections per section** (never sprawl into 4.1–4.8 or 5.1–5.10) |
| **Conclusion Length** | **Exactly 1 paragraph (138 words, 7 sentences)** | **Strictly ONE single cohesive paragraph** (~120–160 words) |
| **Figure Resolution** | **600+ DPI PNG / Vector** | **600+ DPI minimum**, large legible fonts on axes/legends |
| **Figure Captions** | **Concise (1–2 lines max)** | Narrative explanation belongs in body text, not inside `\caption{}` |

---

## 2. Qualitative Stylistic & Grammatical Profile

| Feature | Observed in the Author's Writing | Author Directive for Future Writing |
| :--- | :--- | :--- |
| **Person and Voice** | Balanced academic voice. Uses first-person plural (`"We evaluated EC-XGB..."`, `"We tested only..."`) for methodological decisions and experimental setups. Combines with natural passive voice for mathematical procedures and data handling (`"Trees are added one at a time..."`, `"A logistic link maps..."`, `"Source calibration is fitted..."`). | Keep passive voice for objective data/math processes and `"we"` for author research decisions. |
| **Tense Habits** | **Past tense** for what was executed, measured, and observed in experiments (`"The m0 model reached 82.2%..."`, `"HaluAgent showed..."`, `"Target Platt lowered ECE..."`). **Present tense** for mathematical formulations, invariant algorithmic operations, and figure/table references (`"The model sums K trees..."`, `"Figure 3 shows..."`, `"Table 2 summarizes..."`). | Strictly maintain past tense for procedures/results and present tense for definitions and visuals. |
| **Sentence Rhythm & Cadence** | Alternates between direct, punchy technical facts (*"HaluEval is saturated as well."*, *"The baseline method uses 26 features."*) and multi-clause explanatory sentences detailing constraints and mechanisms. | Keep the standard deviation of sentence lengths high (~10+ words) to preserve authentic human burstiness. |
| **Paragraph Architecture** | Single-topic exhaustive paragraphs. The author does not split a continuous argument into 3–4 micro-paragraphs. Each paragraph introduces the claim/mechanism, presents the technical derivation or data evidence, notes the operational constraint, and concludes on the substantive takeaway. | Always write consolidated, substantial main paragraphs. Never leave fragmented 3–5 line stubs. |
| **Connectors & Transitions** | Heavy use of subordinating conjunctions: `While` (20x), `Although` (11x), `Since` (7x), `Because` (4x). Controlled logical adverbs: `Therefore` (16x), `However` (12x), `Thus` (8x), `First`, `Second`, `Third`, `Finally`. `Moreover` is used only once (1x). `Furthermore` and `In conclusion` are NEVER used (0x). | Do NOT inject AI transition clichés (*"Furthermore"*, *"Moreover"*, *"In conclusion"*). Use real logical connectors (`While`, `Although`, `Therefore`, `However`, `Since`). |
| **Mathematical Equations** | Mathematical formulations are presented in full detail. Displayed equations (`\begin{equation}`) are **immediately continued in the sentence using lowercase `where...`**: `where $\phi = \{f_k\}_{k=1}^K$ collects the trees...`. | **Strict rule:** Always use `where $a$ denotes...`, `$b$ represents...`. **Never use informal syntax** like `"here a = answers"` or `"here x is..."`. |
| **Evaluation Metrics Section** | Dedicated, mandatory subsection in Experiments (Section 4.4 / 4.X) containing explicit mathematical formulations for all metrics (ECE, Brier Score, AUROC, F1, Pair Accuracy) with variables defined formally using `where...`. | Mandatory in all manuscripts. Include formal algorithmic pseudocode for custom procedures. |
| **Statistical Analysis** | Rigorous statistical validation in Results: reports exact values, 95% confidence intervals (`[0.0348, 0.0554]`), Holm corrections, p-values, and per-seed stability. | Always pair quantitative comparison tables with statistical significance annotations and variance across runs. |
| **Figures & Captions** | Figures use high-contrast, large-font typography on axis labels and legends. Captions are concise 1–2 line descriptions (e.g. `\caption{End-to-end pipeline, deployment path, and evaluation corpora of EC-XGB.}`). | Keep `\caption{}` short; explain trends, curves, and takeaways in the accompanying body paragraphs. |

---

## 3. Structural Rules Derived from HaluRISC

1. **Section Architecture:** Standard **6 Sections** (1. Introduction, 2. Conventional Method, 3. Proposed Method, 4. Experiments, 5. Results, 6. Conclusion). Ask if more are needed.
2. **Subsections:** Core only (2 to 5 per section max). Subsume smaller points into substantial paragraphs under existing core subsections rather than creating 4.1–4.8 or 5.1–5.10.
3. **Paragraphs:** 120–250+ words per paragraph. No fragmented 3–6 line micro-paragraphs.
4. **Equations:** Rigorous formulations followed by `where $a$ denotes...` (never informal `here a = ...`).
5. **Conclusion:** Strictly **ONE single cohesive paragraph** (~120–160 words). No bullets, no multiple paragraphs.
6. **Visuals:** 600+ DPI, large legible fonts, concise 1–2 line captions.
