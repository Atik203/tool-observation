#!/usr/bin/env python3
"""Generate the schematic figures for the ToolResult-800 paper.

The four figures are design schematics, not result plots:

* ``fig-design.png``   -- frozen prefix -> five paired arms -> target model.
* ``fig-pipeline.png`` -- harvest through G0 freeze, G1, G2, and analysis.
* ``fig-arms.png``     -- the V / s=0..3 severity ladder with a synthetic record.
* ``fig-analysis.png`` -- conceptual slope and recovery curves, explicitly
  labelled "illustrative, not data".

Every figure is written at 600 DPI with a base font of at least 14 pt.  No
number in these files is a study outcome.  The only counts that appear are
design constants recorded in ``README.md`` / ``docs/PROTOCOL.md`` (sample size,
arm count, generation envelope).

Run from the repository root::

    python scripts/paper_figures/make_figures.py

Use ``--verify-only`` to re-check DPI and pixel dimensions without redrawing.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

# ---------------------------------------------------------------------------
# Output and style contract
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTDIR = REPO_ROOT / "paper" / "figures"

DPI = 600
BASE_FONT = 16
TITLE_FONT = 22
FOOTNOTE_FONT = 14

# Okabe-Ito colour-blind-safe palette.
BLUE = "#0072B2"
ORANGE = "#E69F00"
GREEN = "#009E73"
VERMILLION = "#D55E00"
PURPLE = "#CC79A7"
SKY = "#56B4E9"
YELLOW = "#F0E442"
INK = "#111111"
MUTED = "#4D4D4D"
GRID = "#D9D9D9"
PAPER = "#FFFFFF"

TINT = {
    BLUE: "#E6F1F8",
    ORANGE: "#FDF2DC",
    GREEN: "#E4F4EF",
    VERMILLION: "#FAE8E1",
    PURPLE: "#F7E9F1",
    SKY: "#E7F5FB",
    YELLOW: "#FFF8D6",
}

MONO = "DejaVu Sans Mono"


def set_style() -> None:
    """Apply the paper-wide figure style."""
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": BASE_FONT,
            "axes.titlesize": TITLE_FONT,
            "axes.labelsize": 18,
            "xtick.labelsize": 15,
            "ytick.labelsize": 15,
            "legend.fontsize": 14,
            "figure.titlesize": 24,
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "savefig.dpi": DPI,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.12,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "lines.solid_capstyle": "round",
            "lines.dash_capstyle": "round",
        }
    )


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------


def canvas(figsize: tuple[float, float]):
    """Full-bleed axis in 0..100 coordinates for schematic layouts."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def card(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    facecolor: str = PAPER,
    edgecolor: str = INK,
    lw: float = 2.0,
    radius: float = 1.2,
    zorder: float = 2,
) -> FancyBboxPatch:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=lw,
        zorder=zorder,
    )
    ax.add_patch(patch)
    return patch


def band(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    color: str,
    *,
    zorder: float = 3,
) -> Rectangle:
    """Inset header strip, so a rounded card still shows its outline."""
    rect = Rectangle(
        (x + 0.18, y),
        w - 0.36,
        h,
        facecolor=color,
        edgecolor="none",
        zorder=zorder,
    )
    ax.add_patch(rect)
    return rect


def label(
    ax,
    x: float,
    y: float,
    text: str,
    *,
    size: float = BASE_FONT,
    color: str = INK,
    weight: str = "normal",
    ha: str = "center",
    va: str = "center",
    family: str | None = None,
    style: str = "normal",
    zorder: float = 6,
    **kwargs,
) -> None:
    ax.text(
        x,
        y,
        text,
        fontsize=size,
        color=color,
        fontweight=weight,
        ha=ha,
        va=va,
        family=family,
        fontstyle=style,
        zorder=zorder,
        **kwargs,
    )


def arrow(
    ax,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = MUTED,
    lw: float = 2.2,
    style: str = "-|>",
    scale: float = 18,
    rad: float = 0.0,
    linestyle: str = "-",
    zorder: float = 1,
) -> None:
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle=style,
        mutation_scale=scale,
        linewidth=lw,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
        linestyle=linestyle,
        shrinkA=0,
        shrinkB=0,
        zorder=zorder,
    )
    ax.add_patch(patch)


def paragraph(
    ax,
    x: float,
    y: float,
    lines: list[str],
    *,
    size: float = 14,
    color: str = INK,
    ha: str = "center",
    va: str = "top",
    family: str | None = None,
    weight: str = "normal",
    linespacing: float = 1.35,
    zorder: float = 6,
) -> None:
    ax.text(
        x,
        y,
        "\n".join(lines),
        fontsize=size,
        color=color,
        ha=ha,
        va=va,
        family=family,
        fontweight=weight,
        linespacing=linespacing,
        zorder=zorder,
    )


def save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, facecolor=PAPER)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Figure 1: design
# ---------------------------------------------------------------------------


def make_design(outdir: Path) -> Path:
    fig, ax = canvas((15.0, 9.2))

    # Frozen prefix ---------------------------------------------------------
    card(ax, 17.5, 78.0, 65.0, 17.0, facecolor=TINT[BLUE], edgecolor=BLUE, lw=2.4)
    label(ax, 50.0, 91.6, "Frozen τ-bench prefix", size=24, weight="bold", color=BLUE)
    label(
        ax,
        50.0,
        87.6,
        "real donor trajectory · cut after a tool observation · target models never generate it",
        size=14,
        color=MUTED,
    )

    chips = [
        ("system\npolicy", False),
        ("user\nturn", False),
        ("donor tool\ncall", False),
        ("real tool\nobservation", True),
    ]
    chip_w, chip_gap = 14.2, 1.4
    chip_x = 19.3
    for text, highlight in chips:
        card(
            ax,
            chip_x,
            79.4,
            chip_w,
            5.6,
            facecolor=PAPER,
            edgecolor=ORANGE if highlight else GRID,
            lw=2.2 if highlight else 1.4,
            radius=0.8,
            zorder=4,
        )
        label(
            ax,
            chip_x + chip_w / 2,
            82.2,
            text,
            size=14,
            color=INK,
            weight="bold" if highlight else "normal",
            linespacing=1.15,
            zorder=7,
        )
        chip_x += chip_w + chip_gap

    # Arms ------------------------------------------------------------------
    arms = [
        ("V", "verbatim JSON", "anchor · not in slope", BLUE, PAPER),
        ("s = 0", "faithful prose", "placebo", GREEN, TINT[GREEN]),
        ("s = 1", "non-critical field", "negative control", SKY, TINT[SKY]),
        ("s = 2", "critical wrong value", "dose", ORANGE, TINT[ORANGE]),
        ("s = 3", "critical + contradiction", "dose (compound)", VERMILLION, TINT[VERMILLION]),
    ]
    arm_w, arm_gap = 17.2, 1.6
    arm_y, arm_h = 50.0, 17.0
    arm_x = 4.2
    centers: list[float] = []
    for title, subtitle, role, color, tint in arms:
        centers.append(arm_x + arm_w / 2)
        card(ax, arm_x, arm_y, arm_w, arm_h, facecolor=tint, edgecolor=color, lw=2.4)
        band(ax, arm_x, arm_y + arm_h - 4.2, arm_w, 4.2, color)
        header_ink = PAPER if color in (BLUE, VERMILLION) else INK
        label(
            ax,
            arm_x + arm_w / 2,
            arm_y + arm_h - 2.1,
            title,
            size=22,
            weight="bold",
            color=header_ink,
        )
        label(
            ax,
            arm_x + arm_w / 2,
            arm_y + 9.4,
            subtitle,
            size=14,
            color=INK,
        )
        label(
            ax,
            arm_x + arm_w / 2,
            arm_y + 3.8,
            role,
            size=14,
            color=MUTED,
            style="italic",
        )
        arm_x += arm_w + arm_gap

    # Fan-out arrows from the prefix to each arm.
    for cx in centers:
        arrow(ax, (50.0, 78.0), (cx, arm_y + arm_h), color="#8A8A8A", lw=1.9, scale=16)

    # Target model ----------------------------------------------------------
    card(ax, 20.0, 31.0, 60.0, 12.0, facecolor=TINT[PURPLE], edgecolor=PURPLE, lw=2.4)
    label(
        ax,
        50.0,
        40.2,
        "Target models · greedy decoding (T = 0)",
        size=21,
        weight="bold",
        color=PURPLE,
    )
    model_names = [
        "Qwen3.5-9B-AWQ",
        "Ministral-3-8B",
        "Llama-3.1-8B",
    ]
    model_w, model_gap = 18.2, 1.0
    model_x = 21.4
    for name in model_names:
        card(
            ax,
            model_x,
            32.2,
            model_w,
            4.8,
            facecolor=PAPER,
            edgecolor=PURPLE,
            lw=1.4,
            radius=0.7,
            zorder=4,
        )
        label(ax, model_x + model_w / 2, 34.6, name, size=14, zorder=7)
        model_x += model_w + model_gap

    for cx in centers:
        arrow(ax, (cx, arm_y), (50.0, 43.0), color="#8A8A8A", lw=1.9, scale=16)

    # Decision and recovery -------------------------------------------------
    arrow(ax, (50.0, 31.0), (36.0, 23.0), color=INK, lw=2.4)

    card(ax, 9.0, 8.5, 54.0, 14.5, facecolor=PAPER, edgecolor=INK, lw=2.2)
    label(ax, 36.0, 19.4, "Next decision", size=21, weight="bold")
    label(ax, 36.0, 15.2, "JSON tool call or final answer", size=15)
    label(
        ax,
        36.0,
        11.7,
        "signature compared with the V continuation",
        size=14,
        color=MUTED,
    )

    card(ax, 67.0, 8.5, 25.0, 14.5, facecolor=TINT[ORANGE], edgecolor=ORANGE, lw=2.0)
    label(ax, 79.5, 19.4, "Recovery follow-up", size=18, weight="bold", color=INK)
    paragraph(
        ax,
        79.5,
        15.6,
        ["continue H = 4 steps", "transient primary; persistent 25%"],
        size=14,
        color=INK,
        linespacing=1.25,
    )
    arrow(
        ax,
        (63.0, 15.7),
        (67.0, 15.7),
        color=ORANGE,
        lw=2.2,
        linestyle=(0, (4, 3)),
    )

    # Footer ----------------------------------------------------------------
    label(
        ax,
        50.0,
        3.6,
        "800 primary prefixes (400 airline + 400 retail)  ·  paired within prefix  ·  5 arms × 3 models = 12,000 base generations",
        size=FOOTNOTE_FONT,
        color=MUTED,
    )
    label(
        ax,
        50.0,
        1.1,
        "recovery and jitter repeats bring the pre-specified envelope to 34,800 generations",
        size=FOOTNOTE_FONT,
        color=MUTED,
    )

    return save(fig, outdir / "fig-design.png")


# ---------------------------------------------------------------------------
# Figure 2: pipeline
# ---------------------------------------------------------------------------


def make_pipeline(outdir: Path) -> Path:
    fig, ax = canvas((17.0, 10.0))

    label(
        ax,
        3.0,
        95.0,
        "Study pipeline and gate sequence",
        size=26,
        weight="bold",
        ha="left",
    )
    label(
        ax,
        3.0,
        89.5,
        "G0 — CPU-only harvest and freeze",
        size=18,
        weight="bold",
        color=BLUE,
        ha="left",
    )

    stages = [
        (
            "1",
            "Harvest",
            ["Pin the τ-bench commit;", "parse real trajectories", "into post-tool", "decision points."],
            BLUE,
        ),
        (
            "2",
            "Scrub / relevance",
            ["Remove PII; exclude", "profile tools; keep", "observations whose", "values the donor used."],
            BLUE,
        ),
        (
            "3",
            "Replay",
            ["Re-execute tool calls", "against the task", "database; keep only", "normalized matches."],
            BLUE,
        ),
        (
            "4",
            "Sample",
            ["800 primary + 80", "reserve (400 airline /", "400 retail);", "cap 10 per task–domain."],
            BLUE,
        ),
        (
            "5",
            "Render / perturb",
            ["Five arms per prefix;", "fixed template; s=0", "value-set check; write", "perturbation records."],
            BLUE,
        ),
        (
            "6",
            "Freeze",
            ["Manifest, renderer,", "rubric, prereg; 40-item", "human audit, pass at", "≥ 36/40."],
            BLUE,
        ),
    ]

    stage_w, stage_gap = 15.2, 0.8
    stage_x = 1.8
    stage_y, stage_h = 61.0, 22.0
    stage_centers: list[float] = []
    for number, title, body, color in stages:
        stage_centers.append(stage_x + stage_w / 2)
        card(ax, stage_x, stage_y, stage_w, stage_h, facecolor=TINT[color], edgecolor=color, lw=2.2)
        band(ax, stage_x, stage_y + stage_h - 5.0, stage_w, 5.0, color)
        label(
            ax,
            stage_x + stage_w / 2,
            stage_y + stage_h - 2.5,
            f"{number}  {title}",
            size=14.5,
            weight="bold",
            color=PAPER,
        )
        paragraph(
            ax,
            stage_x + stage_w / 2,
            stage_y + stage_h - 7.6,
            body,
            size=14,
            linespacing=1.32,
        )
        stage_x += stage_w + stage_gap

    for left, right in zip(stage_centers[:-1], stage_centers[1:], strict=False):
        arrow(ax, (left + stage_w / 2, stage_y + 6.0), (right - stage_w / 2, stage_y + 6.0))

    # Wrap from stage 6 down and back to stage 7.
    last_x = stage_centers[-1]
    first_x = 21.5
    wrap_y = 55.0
    ax.plot([last_x, last_x], [stage_y, wrap_y], color=MUTED, lw=2.0, zorder=1)
    ax.plot([last_x, first_x], [wrap_y, wrap_y], color=MUTED, lw=2.0, zorder=1)
    arrow(ax, (first_x, wrap_y), (first_x, 46.0), color=MUTED, lw=2.0)
    label(
        ax,
        55.0,
        wrap_y + 1.8,
        "only after G0 freeze",
        size=14,
        color=MUTED,
        style="italic",
        ha="center",
    )

    bottom = [
        (
            "7",
            "G1 — Calibration",
            [
                "60 disjoint prefixes ×",
                "3 models. Parse ≥ 95%,",
                "placebo jitter ≤ 20%,",
                "s=3 switch 10–80%,",
                "format refusal < 5%.",
            ],
            ORANGE,
        ),
        (
            "8",
            "G2 — Main run",
            [
                "34,800-generation",
                "envelope on the H200",
                "slice; ledger every",
                "generation; hard stop at",
                "45 GPU-hours or 200 GB.",
            ],
            ORANGE,
        ),
        (
            "9",
            "G3 / G4 — Analysis",
            [
                "Pre-registered slope",
                "and recovery sequence;",
                "report gate outcomes",
                "and null results as",
                "measured.",
            ],
            GREEN,
        ),
    ]

    bottom_w, bottom_gap = 27.0, 3.0
    bottom_x = 8.0
    bottom_y, bottom_h = 23.0, 23.0
    bottom_centers: list[float] = []
    for number, title, body, color in bottom:
        bottom_centers.append(bottom_x + bottom_w / 2)
        card(
            ax,
            bottom_x,
            bottom_y,
            bottom_w,
            bottom_h,
            facecolor=TINT[color],
            edgecolor=color,
            lw=2.4,
        )
        band(ax, bottom_x, bottom_y + bottom_h - 5.4, bottom_w, 5.4, color)
        header_ink = INK if color in (ORANGE, GREEN) else PAPER
        label(
            ax,
            bottom_x + bottom_w / 2,
            bottom_y + bottom_h - 2.7,
            f"{number}  {title}",
            size=18,
            weight="bold",
            color=header_ink,
        )
        paragraph(
            ax,
            bottom_x + bottom_w / 2,
            bottom_y + bottom_h - 8.0,
            body,
            size=14,
            linespacing=1.38,
        )
        bottom_x += bottom_w + bottom_gap

    for left, right in zip(bottom_centers[:-1], bottom_centers[1:], strict=False):
        arrow(ax, (left + bottom_w / 2, bottom_y + 10.0), (right - bottom_w / 2, bottom_y + 10.0))

    label(
        ax,
        50.0,
        15.0,
        "Sequential gates: G1 cannot start before G0 freezes; G2 cannot start before G1 passes.",
        size=15,
        color=INK,
        weight="bold",
    )
    label(
        ax,
        50.0,
        9.5,
        "Stage descriptions are schematic; recorded counts and hashes live in the G0 report and manifests.",
        size=FOOTNOTE_FONT,
        color=MUTED,
    )

    return save(fig, outdir / "fig-pipeline.png")


# ---------------------------------------------------------------------------
# Figure 3: arms
# ---------------------------------------------------------------------------


def _observation_card(
    ax,
    x: float,
    y: float,
    w: float,
    h: float,
    lines: list[tuple[str, str | None]],
    *,
    mono: bool,
    size: float = 14,
) -> None:
    """Draw a small observation excerpt; highlight lines by tint colour."""
    card(ax, x, y, w, h, facecolor=PAPER, edgecolor=GRID, lw=1.4, radius=0.9)
    line_h = min(4.3, h / (len(lines) + 0.6))
    block_h = line_h * len(lines)
    top = y + h / 2 + block_h / 2 - line_h / 2
    for i, (text, tint) in enumerate(lines):
        yy = top - i * line_h
        bbox = None
        if tint is not None:
            bbox = {
                "boxstyle": "round,pad=0.18",
                "facecolor": tint,
                "edgecolor": "none",
            }
        ax.text(
            x + 0.9,
            yy,
            text,
            fontsize=size,
            family=MONO if mono else "DejaVu Sans",
            ha="left",
            va="center",
            color=INK,
            bbox=bbox,
            zorder=7,
        )


def make_arms(outdir: Path) -> Path:
    fig, ax = canvas((18.0, 10.0))

    label(
        ax,
        50.0,
        96.3,
        "Five arms: V format anchor + s = 0…3 severity ladder",
        size=22,
        weight="bold",
    )

    panels = [
        {
            "title": "V",
            "subtitle": "verbatim JSON",
            "role": "anchor · not in slope",
            "color": BLUE,
            "tint": PAPER,
            "mono": True,
            "obs": [
                ('{"flight": "TA100",', None),
                (' "date": "2027-03-14",', None),
                (' "fare_usd": 420,', None),
                (' "cabin": "economy",', None),
                (' "status": "confirmed"}', None),
            ],
            "change": [
                "Raw JSON, byte-for-byte",
                "real observation.",
                "Format / jitter anchor;",
                "not a severity level.",
            ],
        },
        {
            "title": "s = 0",
            "subtitle": "faithful prose",
            "role": "placebo · jitter absorbed by α",
            "color": GREEN,
            "tint": TINT[GREEN],
            "mono": False,
            "obs": [
                ("Flight TA100 departs", None),
                ("2027-03-14. Fare: \\$420.", None),
                ("Cabin: economy.", None),
                ("Status: confirmed.", None),
            ],
            "change": [
                "All values preserved in",
                "the fixed prose template.",
                "Value set must equal V;",
                "any loss excludes the prefix.",
            ],
        },
        {
            "title": "s = 1",
            "subtitle": "non-critical change",
            "role": "negative control",
            "color": SKY,
            "tint": TINT[SKY],
            "mono": False,
            "obs": [
                ("Flight TA100 departs", None),
                ("2027-03-14. Fare: \\$420.", None),
                ("Cabin: economy.", None),
                ("Aircraft: A321.", TINT[SKY]),
                ("Status: confirmed.", None),
            ],
            "change": [
                "Aircraft A320 → A321.",
                "Non-critical: must not",
                "appear in the donor's",
                "factual continuation.",
            ],
        },
        {
            "title": "s = 2",
            "subtitle": "critical wrong value",
            "role": "dose",
            "color": ORANGE,
            "tint": TINT[ORANGE],
            "mono": False,
            "obs": [
                ("Flight TA100 departs", None),
                ("2027-03-14. Fare: \\$520.", TINT[ORANGE]),
                ("Cabin: economy.", None),
                ("Status: confirmed.", None),
            ],
            "change": [
                "Fare \\$420 → \\$520.",
                "Decision-critical: plausible,",
                "and trusting it changes the",
                "correct next action.",
            ],
        },
        {
            "title": "s = 3",
            "subtitle": "critical + contradiction",
            "role": "dose · compound",
            "color": VERMILLION,
            "tint": TINT[VERMILLION],
            "mono": False,
            "obs": [
                ("Flight TA100 departs", None),
                ("2027-03-14. Fare: \\$520.", TINT[VERMILLION]),
                ("Cabin: economy.", None),
                ("Status: cancelled.", TINT[VERMILLION]),
                ("Seats available: 6.", TINT[YELLOW]),
            ],
            "change": [
                "Fare \\$420 → \\$520 plus",
                "status confirmed →",
                "cancelled while seats",
                "remain. Critical error +",
                "contradiction.",
            ],
        },
    ]

    panel_w, panel_gap = 18.0, 1.6
    panel_x, panel_y, panel_h = 1.8, 21.0, 71.0
    centers: list[float] = []
    for panel in panels:
        centers.append(panel_x + panel_w / 2)
        color = panel["color"]
        card(
            ax,
            panel_x,
            panel_y,
            panel_w,
            panel_h,
            facecolor=panel["tint"],
            edgecolor=color,
            lw=2.6,
        )
        band(ax, panel_x, panel_y + panel_h - 9.4, panel_w, 9.4, color)
        header_ink = PAPER if color in (BLUE, VERMILLION) else INK
        label(
            ax,
            panel_x + panel_w / 2,
            panel_y + panel_h - 4.2,
            panel["title"],
            size=24,
            weight="bold",
            color=header_ink,
        )
        label(
            ax,
            panel_x + panel_w / 2,
            panel_y + panel_h - 7.6,
            panel["subtitle"],
            size=14,
            color=header_ink,
        )

        _observation_card(
            ax,
            panel_x + 0.9,
            panel_y + 35.0,
            panel_w - 1.8,
            23.5,
            panel["obs"],
            mono=panel["mono"],
            size=14,
        )

        # Change description.
        card(
            ax,
            panel_x + 0.9,
            panel_y + 13.0,
            panel_w - 1.8,
            19.0,
            facecolor=PAPER,
            edgecolor=color,
            lw=1.4,
            radius=0.9,
        )
        label(
            ax,
            panel_x + panel_w / 2,
            panel_y + 29.4,
            "change",
            size=14,
            weight="bold",
            color=color,
        )
        paragraph(
            ax,
            panel_x + panel_w / 2,
            panel_y + 26.8,
            panel["change"],
            size=14,
            linespacing=1.3,
        )

        label(
            ax,
            panel_x + panel_w / 2,
            panel_y + 7.2,
            panel["role"],
            size=14,
            color=MUTED,
            style="italic",
        )
        panel_x += panel_w + panel_gap

    # Severity ladder covers s=0..s=3 only; V is a format anchor.
    ladder_y = 13.0
    arrow(ax, (centers[1] - 5.0, ladder_y), (centers[4] + 5.0, ladder_y), color=INK, lw=2.4)
    for cx in centers[1:]:
        ax.plot([cx, cx], [ladder_y - 1.0, ladder_y + 1.0], color=INK, lw=2.0, zorder=2)
    label(
        ax,
        58.0,
        7.2,
        "severity ladder: ordinal, not interval",
        size=15,
        color=INK,
        weight="bold",
    )
    label(
        ax,
        centers[0],
        13.0,
        "V is a format anchor,\nnot a severity level",
        size=14,
        color=MUTED,
        style="italic",
        linespacing=1.2,
    )

    label(
        ax,
        50.0,
        2.6,
        "Synthetic example (flight TA100). No real τ-bench record and no PII; values illustrate the manipulation, not study data.",
        size=FOOTNOTE_FONT,
        color=MUTED,
    )

    return save(fig, outdir / "fig-arms.png")


# ---------------------------------------------------------------------------
# Figure 4: analysis (explicitly illustrative)
# ---------------------------------------------------------------------------


def make_analysis(outdir: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(16.0, 8.8))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.80, bottom=0.20, wspace=0.26)
    ax_slope, ax_rec = axes

    # ---- Panel A: conceptual within-prefix slope --------------------------
    severities = [0, 1, 2, 3]
    # Prefix-specific intercepts with one common slope.  These are schematic
    # model-implied lines, not estimated probabilities.
    intercepts = [-1.0, 0.05, 1.1]
    slope = 0.55
    prefix_colors = [BLUE, GREEN, PURPLE]
    for i, (alpha, color) in enumerate(zip(intercepts, prefix_colors, strict=False), start=1):
        ys = [alpha + slope * s for s in severities]
        ax_slope.plot(
            severities,
            ys,
            color=color,
            lw=3.0,
            marker="o",
            ms=9,
            mfc=PAPER,
            mew=2.4,
            label=f"prefix $p_{i}$",
            zorder=4,
        )

    ax_slope.set_xlim(-0.35, 3.35)
    ax_slope.set_ylim(-1.8, 3.0)
    ax_slope.set_xticks(severities)
    ax_slope.set_xticklabels(
        ["s = 0\nplacebo", "s = 1\nnegative\ncontrol", "s = 2\ndose", "s = 3\ndose\n(compound)"],
        fontsize=15,
    )
    ax_slope.set_yticks([])
    ax_slope.set_xlabel("severity level (ordinal)", fontsize=17)
    ax_slope.set_ylabel("logit P(switch) — conceptual", fontsize=17)
    ax_slope.set_title("Within-prefix slope\n(illustrative, not data)", fontsize=20, pad=14)
    ax_slope.grid(axis="x", color=GRID, lw=1.0, alpha=0.7, zorder=0)
    ax_slope.spines["top"].set_visible(False)
    ax_slope.spines["right"].set_visible(False)
    ax_slope.legend(
        loc="upper left",
        frameon=True,
        facecolor=PAPER,
        edgecolor=GRID,
        framealpha=1.0,
        fontsize=14,
        handlelength=1.8,
    )
    ax_slope.text(
        0.5,
        0.035,
        "model: logit P(Y=1) = α$_p$ + β·s,  β > 0  ·  V excluded",
        transform=ax_slope.transAxes,
        fontsize=14,
        color=MUTED,
        ha="center",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.35", facecolor=PAPER, edgecolor=GRID),
    )

    # ---- Panel B: conceptual four-step recovery ---------------------------
    hours = [0, 1, 2, 3, 4]
    mu = 0.45
    survival = [1.0] + [math.exp(-mu * h) for h in hours[1:]]
    ax_rec.plot(
        hours,
        survival,
        color=VERMILLION,
        lw=3.2,
        marker="o",
        ms=10,
        mfc=PAPER,
        mew=2.6,
        zorder=4,
    )
    ax_rec.fill_between(hours, survival, 0, color=TINT[VERMILLION], alpha=0.75, zorder=1)
    ax_rec.axhline(0.5, color=MUTED, lw=1.6, linestyle=(0, (5, 4)), zorder=2)
    ax_rec.axvline(1.54, color=MUTED, lw=1.4, linestyle=(0, (2, 3)), zorder=2)
    ax_rec.annotate(
        "t½ = ln 2 / μ\n(reported only if identifiable)",
        xy=(1.54, 0.5),
        xytext=(2.25, 0.78),
        fontsize=14,
        color=MUTED,
        ha="left",
        va="center",
        arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.4),
        bbox=dict(boxstyle="round,pad=0.3", facecolor=PAPER, edgecolor=GRID),
    )
    ax_rec.annotate(
        "censor at H = 4",
        xy=(4.0, survival[-1]),
        xytext=(2.95, 0.44),
        fontsize=14,
        color=MUTED,
        ha="left",
        va="center",
        arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.6),
    )

    ax_rec.set_xlim(-0.3, 4.3)
    ax_rec.set_ylim(-0.04, 1.08)
    ax_rec.set_xticks(hours)
    ax_rec.set_xticklabels(["h = 0\ninjection", "h = 1", "h = 2", "h = 3", "h = 4\nhorizon"], fontsize=15)
    ax_rec.set_yticks([])
    ax_rec.set_xlabel("steps since injection", fontsize=17)
    ax_rec.set_ylabel("share not yet recovered — conceptual", fontsize=17)
    ax_rec.set_title("Four-step recovery\n(illustrative, not data)", fontsize=20, pad=14)
    ax_rec.grid(axis="x", color=GRID, lw=1.0, alpha=0.7, zorder=0)
    ax_rec.spines["top"].set_visible(False)
    ax_rec.spines["right"].set_visible(False)

    ax_rec.text(
        0.04,
        0.04,
        "risk set: prefixes that moved at injection\nand did not flag there\n"
        "R1 = signature matches V; R2 = explicit flag",
        transform=ax_rec.transAxes,
        fontsize=14,
        color=MUTED,
        ha="left",
        va="bottom",
        linespacing=1.35,
        bbox=dict(boxstyle="round,pad=0.35", facecolor=PAPER, edgecolor=GRID),
    )

    # ---- Shared labels ----------------------------------------------------
    fig.suptitle(
        "Analysis plan: slope and recovery are conceptual",
        fontsize=24,
        fontweight="bold",
        y=0.955,
    )
    fig.text(
        0.5,
        0.010,
        "ILLUSTRATIVE, NOT DATA — no study outcomes have been generated; axes are unnumbered by design.",
        ha="center",
        va="bottom",
        fontsize=16,
        fontweight="bold",
        color=VERMILLION,
        bbox=dict(boxstyle="round,pad=0.45", facecolor=TINT[VERMILLION], edgecolor=VERMILLION, lw=1.6),
    )
    for ax in (ax_slope, ax_rec):
        ax.text(
            0.5,
            0.55,
            "ILLUSTRATIVE\nNOT DATA",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=32,
            fontweight="bold",
            color=VERMILLION,
            alpha=0.06,
            zorder=0,
            linespacing=1.2,
        )

    return save(fig, outdir / "fig-analysis.png")


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def describe_png(path: Path) -> tuple[int, int, tuple[float, float]]:
    """Return (width, height, dpi) for a PNG, using Pillow."""
    from PIL import Image

    with Image.open(path) as image:
        width, height = image.size
        dpi = image.info.get("dpi", (0.0, 0.0))
    if isinstance(dpi, (int, float)):
        dpi = (float(dpi), float(dpi))
    return width, height, (float(dpi[0]), float(dpi[1]))


def verify(outdir: Path) -> list[Path]:
    expected = [
        "fig-design.png",
        "fig-pipeline.png",
        "fig-arms.png",
        "fig-analysis.png",
    ]
    print(f"{'file':22s} {'width':>7s} {'height':>7s} {'dpi':>12s}")
    paths = []
    for name in expected:
        path = outdir / name
        if not path.exists():
            raise FileNotFoundError(f"missing figure: {path}")
        width, height, dpi = describe_png(path)
        if min(dpi) < DPI - 0.5:
            raise ValueError(f"{path.name}: expected {DPI} DPI, got {dpi}")
        if width < 3000 or height < 3000:
            raise ValueError(f"{path.name}: unexpectedly small ({width}x{height})")
        print(f"{name:22s} {width:7d} {height:7d} {dpi[0]:6.0f} x {dpi[1]:<5.0f}")
        paths.append(path)
    return paths


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--outdir",
        type=Path,
        default=DEFAULT_OUTDIR,
        help=f"output directory (default: {DEFAULT_OUTDIR})",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="check existing PNGs without redrawing",
    )
    args = parser.parse_args()

    outdir = args.outdir.resolve()
    set_style()

    if not args.verify_only:
        outdir.mkdir(parents=True, exist_ok=True)
        for maker in (make_design, make_pipeline, make_arms, make_analysis):
            path = maker(outdir)
            try:
                shown = path.relative_to(REPO_ROOT)
            except ValueError:
                shown = path
            print(f"wrote {shown}")

    verify(outdir)


if __name__ == "__main__":
    main()
