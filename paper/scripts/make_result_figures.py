"""Result figures for the ToolResult-800 manuscript (from analysis artifacts)."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
AN = ROOT / "artifacts" / "analysis"
FIG = ROOT / "paper" / "figures"
FIG.mkdir(exist_ok=True)

COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00"]
MODELS = ["qwen3_5_9b_instruct_awq", "ministral_3_8b_instruct_2512_awq", "llama_3_1_8b_instruct_awq"]
LABELS = ["Qwen3.5-9B", "Ministral-3-8B", "Llama-3.1-8B"]

g3 = json.loads((AN / "g3_analysis.json").read_text(encoding="utf-8"))
g4 = json.loads((AN / "g4_recovery.json").read_text(encoding="utf-8"))
ft = json.loads((AN / "field_taxonomy.json").read_text(encoding="utf-8"))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color="#cccccc", linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)


# --- Figure: dose-response by arm and model
fig, ax = plt.subplots(figsize=(7.2, 3.4))
arms = ["s0", "s1", "s2", "s3"]
width = 0.26
for mi, (model, label) in enumerate(zip(MODELS, LABELS)):
    rates, lows, highs = [], [], []
    for arm in arms:
        cell = g3["arm_table"][f"{model}|{arm}"]
        lo, hi = wilson(cell["any"], cell["n"])
        rates.append(cell["switch_rate"])
        lows.append(cell["switch_rate"] - lo)
        highs.append(hi - cell["switch_rate"])
    xs = [i + (mi - 1) * width for i in range(4)]
    ax.bar(xs, rates, width=width, color=COLORS[mi], label=label, yerr=[lows, highs],
           capsize=2, error_kw={"linewidth": 0.8})
ax.set_xticks(range(4))
ax.set_xticklabels(["s0\nprose placebo", "s1\nnon-critical", "s2\none critical", "s3\ncritical + second"])
ax.set_ylabel("Switch rate (Y)")
ax.set_ylim(0, 0.62)
ax.legend(frameon=False, ncol=3, fontsize=8, loc="upper left")
style(ax)
fig.tight_layout()
fig.savefig(FIG / "result-dose.png", dpi=300)
plt.close(fig)

# --- Figure: forest plot
fig, ax = plt.subplots(figsize=(6.4, 2.8))
rows = [(m, LABELS[i]) for i, m in enumerate(MODELS)] + [("pooled", "Pooled")]
ys = list(range(len(rows)))[::-1]
for y, (key, label) in zip(ys, rows):
    if key == "pooled":
        beta = g3["pooled"]["beta"]
        se = g3["pooled"]["se_cluster"]
    else:
        beta = g3["per_model"][key]["beta"]
        se = g3["per_model"][key]["se_cluster"]
    lo, hi = beta - 1.96 * se, beta + 1.96 * se
    ax.errorbar(beta, y, xerr=[[beta - lo], [hi - beta]], fmt="o", color=COLORS[0],
                capsize=3, markersize=5)
    ax.text(hi + 0.02, y, f"{beta:.2f} [{lo:.2f}, {hi:.2f}]", va="center", fontsize=8)
ax.axvline(0, color="#555555", linewidth=0.8, linestyle="--")
ax.set_yticks(ys)
ax.set_yticklabels([label for _, label in rows])
ax.set_xlabel("Conditional-logit slope beta (per severity level)")
ax.set_xlim(-0.05, 1.45)
style(ax)
fig.tight_layout()
fig.savefig(FIG / "result-forest.png", dpi=300)
plt.close(fig)

# --- Figure: recovery curves (transient s3)
fig, ax = plt.subplots(figsize=(6.6, 3.2))
for mi, (model, label) in enumerate(zip(MODELS, LABELS)):
    group = g4["groups"][f"{model}|transient_s3"]
    steps = [0] + [row["step"] for row in group["kaplan_meier"]]
    surv = [1.0] + [row["survival"] for row in group["kaplan_meier"]]
    ax.step(steps, surv, where="post", color=COLORS[mi], label=f"{label} (n={group['n']})")
ax.set_xlabel("Step after corruption")
ax.set_ylabel("Kaplan-Meier survival")
ax.set_ylim(0.6, 1.0)
ax.set_xticks(range(5))
ax.legend(frameon=False, fontsize=8)
style(ax)
fig.tight_layout()
fig.savefig(FIG / "result-recovery.png", dpi=300)
plt.close(fig)

# --- Figure: field types at s=2
records = [r for r in ft["by_class_arm"] if r["arm"] == "s2"]
class_order = ["identifier", "money", "entity", "status"]
by_class = {r["class"]: r for r in records}
all_switch = {"k": sum(r["switch"]["k"] for r in records), "n": sum(r["switch"]["n"] for r in records)}
all_silent_k = sum(r["silent"]["k"] for r in records)
all_switch_k = sum(r["switch"]["k"] for r in records)
fig, ax = plt.subplots(figsize=(6.8, 3.2))
xs = range(len(class_order) + 1)
switch_rates = [by_class[c]["switch"]["pct"] / 100 for c in class_order] + [all_switch["k"] / all_switch["n"]]
silent_shares = []
for c in class_order:
    sil = by_class[c]["silent"]
    silent_shares.append(sil["k"] / sil["switch_denominator"] if sil["switch_denominator"] else 0.0)
silent_shares.append(all_silent_k / all_switch_k if all_switch_k else 0.0)
labels = [c.capitalize() for c in class_order] + ["All s=2"]
ax.bar([x - 0.2 for x in xs], switch_rates, width=0.38, color=COLORS[0], label="Switch rate")
ax.bar([x + 0.2 for x in xs], silent_shares, width=0.38, color=COLORS[3], label="Silent share of switches")
ax.set_xticks(list(xs))
ax.set_xticklabels(labels)
ax.set_ylabel("Rate")
ax.set_ylim(0, 0.62)
ax.legend(frameon=False, fontsize=8)
style(ax)
fig.tight_layout()
fig.savefig(FIG / "result-fields.png", dpi=300)
plt.close(fig)

print("wrote result figures to", FIG)
