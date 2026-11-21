"""Result figures for the ToolResult-800 manuscript (from analysis artifacts)."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update(
    {
        "font.size": 11,
        "axes.labelsize": 12,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "legend.fontsize": 10,
        "figure.titlesize": 13,
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.06,
    }
)

ROOT = Path(__file__).resolve().parents[2]
AN = ROOT / "artifacts" / "analysis"
FIG = ROOT / "paper" / "figures"
FIG.mkdir(exist_ok=True)

COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00"]
MODELS = [
    "qwen3_5_9b_instruct_awq",
    "ministral_3_8b_instruct_2512_awq",
    "llama_3_1_8b_instruct_awq",
]
LABELS = ["Qwen3.5-9B", "Ministral-3-8B", "Llama-3.1-8B"]

g3 = json.loads((AN / "g3_analysis.json").read_text(encoding="utf-8"))
g4 = json.loads((AN / "g4_recovery.json").read_text(encoding="utf-8"))
ft = json.loads((AN / "field_taxonomy.json").read_text(encoding="utf-8"))
secondary = json.loads((AN / "prereg_secondary.json").read_text(encoding="utf-8"))


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
fig, ax = plt.subplots(figsize=(8.4, 4.0))
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
    ax.bar(
        xs,
        rates,
        width=width,
        color=COLORS[mi],
        label=label,
        yerr=[lows, highs],
        capsize=2,
        error_kw={"linewidth": 0.8},
    )
ax.set_xticks(range(4))
ax.set_xticklabels(
    ["s0\nprose placebo", "s1\nnon-critical", "s2\none critical", "s3\ncritical + second"]
)
ax.set_ylabel("Switch rate (Y)")
ax.set_ylim(0, 0.62)
ax.legend(frameon=False, ncol=3, fontsize=10, loc="upper left")
style(ax)
fig.tight_layout()
fig.savefig(FIG / "fig7.png", dpi=600)
plt.close(fig)

# --- Figure: forest plot
fig, ax = plt.subplots(figsize=(7.6, 3.3))
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
    ax.errorbar(
        beta,
        y,
        xerr=[[beta - lo], [hi - beta]],
        fmt="o",
        color=COLORS[0],
        capsize=3,
        markersize=5,
    )
    ax.text(hi + 0.02, y, f"{beta:.2f} [{lo:.2f}, {hi:.2f}]", va="center", fontsize=10)
ax.axvline(0, color="#555555", linewidth=0.8, linestyle="--")
ax.set_yticks(ys)
ax.set_yticklabels([label for _, label in rows])
ax.set_xlabel("Conditional-logit slope beta (per severity level)")
ax.set_xlim(-0.05, 1.45)
style(ax)
fig.tight_layout()
fig.savefig(FIG / "fig5.png", dpi=600)
plt.close(fig)

# --- Figure: field types at s=2
records = [r for r in ft["by_class_arm"] if r["arm"] == "s2"]
class_order = ["identifier", "money", "entity", "status"]
by_class = {r["class"]: r for r in records}
all_switch = {
    "k": sum(r["switch"]["k"] for r in records),
    "n": sum(r["switch"]["n"] for r in records),
}
all_silent_k = sum(r["silent"]["k"] for r in records)
all_switch_k = sum(r["switch"]["k"] for r in records)
fig, ax = plt.subplots(figsize=(8.0, 3.7))
xs = range(len(class_order) + 1)
switch_rates = [by_class[c]["switch"]["pct"] / 100 for c in class_order] + [
    all_switch["k"] / all_switch["n"]
]
silent_shares = []
for c in class_order:
    sil = by_class[c]["silent"]
    silent_shares.append(
        sil["k"] / sil["switch_denominator"] if sil["switch_denominator"] else 0.0
    )
silent_shares.append(all_silent_k / all_switch_k if all_switch_k else 0.0)
labels = [c.capitalize() for c in class_order] + ["All s=2"]
ax.bar(
    [x - 0.2 for x in xs],
    switch_rates,
    width=0.38,
    color=COLORS[0],
    label="Switch rate",
)
ax.bar(
    [x + 0.2 for x in xs],
    silent_shares,
    width=0.38,
    color=COLORS[3],
    label="Silent share of switches",
)
ax.set_xticks(list(xs))
ax.set_xticklabels(labels)
ax.set_ylabel("Rate")
ax.set_ylim(0, 0.62)
ax.legend(frameon=False, fontsize=10)
style(ax)
fig.tight_layout()
fig.savefig(FIG / "fig8.png", dpi=600)
plt.close(fig)

# --- Figure: tier odds ratios (s=1,2,3 vs s=0), log scale
tiers = ["s1", "s2", "s3"]
tier_titles = [
    "s = 1 (non-critical)",
    "s = 2 (one critical)",
    "s = 3 (critical + second)",
]
fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.6), sharey=True)
row_labels = list(LABELS) + ["Pooled"]
for ax, tier, title in zip(axes, tiers, tier_titles):
    ys = list(range(len(row_labels)))[::-1]
    for y, label, key in zip(ys, LABELS, MODELS):
        cell = secondary["tier_or"]["per_model"][key]
        i = int(tier[1]) - 1
        est = cell["categorical_fit"]["or"][i]
        lo = cell["bootstrap_or_ci_low"][i]
        hi = cell["bootstrap_or_ci_high"][i]
        ax.errorbar(
            est,
            y,
            xerr=[[est - lo], [hi - est]],
            fmt="o",
            color=COLORS[0],
            capsize=3,
            markersize=5,
        )
        ax.text(hi * 1.06, y, f"{est:.2f}", va="center", fontsize=9)
    pooled = secondary["tier_or"]["pooled"]
    i = int(tier[1]) - 1
    est = pooled["categorical_fit"]["or"][i]
    lo = pooled["bootstrap_or_ci_low"][i]
    hi = pooled["bootstrap_or_ci_high"][i]
    ax.errorbar(
        est,
        0,
        xerr=[[est - lo], [hi - est]],
        fmt="s",
        color=COLORS[3],
        capsize=3,
        markersize=5,
    )
    ax.text(hi * 1.06, 0, f"{est:.2f}", va="center", fontsize=9)
    ax.axvline(1, color="#555555", linewidth=0.8, linestyle="--")
    ax.set_xscale("log")
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("Odds ratio vs s=0 (log scale)")
    style(ax)
axes[0].set_yticks(list(range(len(row_labels)))[::-1])
axes[0].set_yticklabels(row_labels)
fig.tight_layout()
fig.savefig(FIG / "fig6.png", dpi=600)
plt.close(fig)

# --- Figure: sensitivity of the pooled slope
fig, axes = plt.subplots(1, 2, figsize=(12.0, 3.8))
panel_a = [
    (
        "Primary (s0-s3)",
        g3["pooled"]["beta"],
        g3["bootstrap"]["ci_low"],
        g3["bootstrap"]["ci_high"],
    ),
    (
        "Strict coding",
        secondary["strict_lenient"]["pooled"]["strict"]["beta"],
        secondary["strict_lenient"]["pooled"]["strict"]["bootstrap_ci_low"],
        secondary["strict_lenient"]["pooled"]["strict"]["bootstrap_ci_high"],
    ),
    (
        "Lenient coding",
        secondary["strict_lenient"]["pooled"]["lenient"]["beta"],
        secondary["strict_lenient"]["pooled"]["lenient"]["bootstrap_ci_low"],
        secondary["strict_lenient"]["pooled"]["lenient"]["bootstrap_ci_high"],
    ),
    (
        "Exclude s0",
        secondary["sensitivity_exclude_s0"]["pooled"]["beta"],
        secondary["sensitivity_exclude_s0"]["pooled"]["bootstrap_ci_low"],
        secondary["sensitivity_exclude_s0"]["pooled"]["bootstrap_ci_high"],
    ),
]
ys = list(range(len(panel_a)))[::-1]
for y, (label, est, lo, hi) in zip(ys, panel_a):
    axes[0].errorbar(
        est,
        y,
        xerr=[[est - lo], [hi - est]],
        fmt="o",
        color=COLORS[0],
        capsize=3,
        markersize=5,
    )
    axes[0].text(hi + 0.02, y, f"{est:.2f}", va="center", fontsize=9)
axes[0].axvline(0, color="#555555", linewidth=0.8, linestyle="--")
axes[0].set_yticks(ys)
axes[0].set_yticklabels([r[0] for r in panel_a])
axes[0].set_xlabel("Slope beta (per level)")
axes[0].set_title("Coding and placebo sensitivity", fontsize=11)
axes[0].set_xlim(-0.02, 1.35)
style(axes[0])

panel_b = [
    ("Airline", secondary["stratified"]["domain"]["airline"]["pooled"]),
    ("Retail", secondary["stratified"]["domain"]["retail"]["pooled"]),
    ("Claude donor", secondary["stratified"]["donor"]["claude35sonnet"]["pooled"]),
    ("GPT-4o donor", secondary["stratified"]["donor"]["gpt4o"]["pooled"]),
]
ys = list(range(len(panel_b)))[::-1]
for y, (label, cell) in zip(ys, panel_b):
    est = cell["beta"]
    lo = cell["bootstrap_ci_low"]
    hi = cell["bootstrap_ci_high"]
    axes[1].errorbar(
        est,
        y,
        xerr=[[est - lo], [hi - est]],
        fmt="o",
        color=COLORS[2],
        capsize=3,
        markersize=5,
    )
    axes[1].text(hi + 0.02, y, f"{est:.2f}", va="center", fontsize=9)
axes[1].axvline(0, color="#555555", linewidth=0.8, linestyle="--")
axes[1].set_yticks(ys)
axes[1].set_yticklabels([r[0] for r in panel_b])
axes[1].set_xlabel("Slope beta (per level)")
axes[1].set_title("Domain and donor strata", fontsize=11)
axes[1].set_xlim(-0.02, 1.4)
style(axes[1])
fig.tight_layout()
fig.savefig(FIG / "fig10.png", dpi=600)
plt.close(fig)

# --- Figure: recovery at s=2 and s=3 (transient)
fig, axes = plt.subplots(1, 2, figsize=(11.2, 3.8), sharey=True)
for ax, severity, title in zip(
    axes, (2, 3), ("s = 2 (one critical)", "s = 3 (critical + second)")
):
    for mi, (model, label) in enumerate(zip(MODELS, LABELS)):
        group = g4["groups"][f"{model}|transient_s{severity}"]
        steps = [0] + [row["step"] for row in group["kaplan_meier"]]
        surv = [1.0] + [row["survival"] for row in group["kaplan_meier"]]
        ax.step(
            steps,
            surv,
            where="post",
            color=COLORS[mi],
            label=f"{label} (n={group['n']})",
        )
    ax.set_xlabel("Step after corruption")
    ax.set_title(title, fontsize=11)
    ax.set_ylim(0.55, 1.0)
    ax.set_xticks(range(5))
    ax.legend(frameon=False, fontsize=9)
    style(ax)
axes[0].set_ylabel("Kaplan-Meier survival")
fig.tight_layout()
fig.savefig(FIG / "fig9.png", dpi=600)
plt.close(fig)

print("wrote result figures to", FIG)
