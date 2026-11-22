#!/usr/bin/env python3
"""Generate the schematic figures for the ToolResult-800 paper.

The four figures are design schematics, not result plots:

* ``fig1.png`` -- frozen prefix -> five paired arms -> target model.
* ``fig3.png`` -- harvest through G0 freeze, G1, G2, and analysis.
* ``fig2.png`` -- the V / s=0..3 severity ladder with a synthetic record.
* ``fig4.png`` -- conceptual slope and recovery curves, explicitly labelled
  "conceptual schematic" (no study outcomes are plotted).

Every figure is drawn at (or just above) its final printed width -- the CAS
text block is 6.18 in wide and the manuscript includes figures at
0.95 \\linewidth -- with nominal fonts of at least 14 pt, so the effective
printed size stays well above 8 pt. No
number in these files is a study outcome. The only counts that appear are
design constants recorded in ``README.md`` / ``docs/PROTOCOL.md`` (sample size,
arm count, generation envelope).

Run from the repository root::

    python scripts/paper_figures/make_figures.py

Use ``--verify-only`` to re-check DPI, pixel dimensions, and effective type
size without redrawing.
"""

from __future__ import annotations

import argparse
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
    card(ax, 17.5, 78.0, 65.0, 17.0, facecolor=TINT[BLUE], edgecolor=BLUE, lw=3.2)
    label(ax, 50.0, 91.6, "Frozen τ-bench prefix", size=24, weight="bold", color=BLUE)
    label(
        ax,
        50.0,
        87.6,
        "real donor trajectory · cut after a tool observation",
        size=21,
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
            lw=3.0 if highlight else 2.0,
            radius=0.8,
            zorder=4,
        )
        label(
            ax,
            chip_x + chip_w / 2,
            82.2,
            text,
            size=21,
            color=INK,
            weight="bold" if highlight else "normal",
            linespacing=1.15,
            zorder=7,
        )
        chip_x += chip_w + chip_gap

    # Arms ------------------------------------------------------------------
    arms = [
        ("V", "verbatim JSON", "anchor", BLUE, PAPER),
        ("s = 0", "faithful prose", "placebo", GREEN, TINT[GREEN]),
        ("s = 1", "non-critical edit", "neg. control", SKY, TINT[SKY]),
        ("s = 2", "critical error", "dose", ORANGE, TINT[ORANGE]),
        ("s = 3", "error + conflict", "compound dose", VERMILLION, TINT[VERMILLION]),
    ]
    arm_w, arm_gap = 17.2, 1.6
    arm_y, arm_h = 50.0, 17.0
    arm_x = 4.2
    centers: list[float] = []
    for title, subtitle, role, color, tint in arms:
        centers.append(arm_x + arm_w / 2)
        card(ax, arm_x, arm_y, arm_w, arm_h, facecolor=tint, edgecolor=color, lw=3.2)
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
            size=21,
            color=INK,
        )
        label(
            ax,
            arm_x + arm_w / 2,
            arm_y + 3.8,
            role,
            size=21,
            color=MUTED,
            style="italic",
        )
        arm_x += arm_w + arm_gap

    # Fan-out arrows from the prefix to each arm.
    for cx in centers:
        arrow(ax, (50.0, 78.0), (cx, arm_y + arm_h), color="#8A8A8A", lw=2.4, scale=20)

    # Target model ----------------------------------------------------------
    card(ax, 20.0, 31.0, 60.0, 12.0, facecolor=TINT[PURPLE], edgecolor=PURPLE, lw=3.2)
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
            lw=2.0,
            radius=0.7,
            zorder=4,
        )
        label(ax, model_x + model_w / 2, 34.6, name, size=21, zorder=7)
        model_x += model_w + model_gap

    for cx in centers:
        arrow(ax, (cx, arm_y), (50.0, 43.0), color="#8A8A8A", lw=2.4, scale=20)

    # Decision and recovery -------------------------------------------------
    arrow(ax, (50.0, 31.0), (36.0, 23.0), color=INK, lw=3.0)

    card(ax, 9.0, 8.5, 54.0, 14.5, facecolor=PAPER, edgecolor=INK, lw=3.0)
    label(ax, 36.0, 19.4, "Next decision", size=21, weight="bold")
    label(ax, 36.0, 15.2, "JSON tool call or final answer", size=21)
    label(
        ax,
        36.0,
        11.7,
        "signature compared with the V continuation",
        size=21,
        color=MUTED,
    )

    card(ax, 67.0, 8.5, 25.0, 14.5, facecolor=TINT[ORANGE], edgecolor=ORANGE, lw=3.0)
    label(ax, 79.5, 19.4, "Recovery follow-up", size=21, weight="bold", color=INK)
    paragraph(
        ax,
        79.5,
        15.6,
        ["continue H = 4 steps", "persistent on 25%"],
        size=21,
        color=INK,
        linespacing=1.25,
    )
    arrow(
        ax,
        (63.0, 15.7),
        (67.0, 15.7),
        color=ORANGE,
        lw=3.0,
        linestyle=(0, (4, 3)),
    )

    # Footer ----------------------------------------------------------------
    label(
        ax,
        50.0,
        2.5,
        "800 primary (400 + 400) · 5 arms × 3 models · planned 34,800, executed 21,611 (see text)",
        size=21,
        color=MUTED,
    )

    return save(fig, outdir / "fig1.png")


# ---------------------------------------------------------------------------
# Figure 2: pipeline
# ---------------------------------------------------------------------------


def make_pipeline(outdir: Path) -> Path:
    fig, ax = canvas((6.3, 7.4))

    label(
        ax,
        50.0,
        95.5,
        "Study pipeline and gate sequence",
        size=15,
        weight="bold",
        ha="center",
    )

    stages = [
        ("1", "Harvest", "pin τ-bench commit; parse 13,605 post-tool points", BLUE),
        ("2", "Scrub + replay", "PII tools excluded; 99.91% replay on eligible pool", BLUE),
        ("3", "Sample + render", "800 primary + 80 reserve; five arms; s=0 check", BLUE),
        ("4", "Freeze (G0)", "manifest + renderer + prereg hashes; AI audit 40/40", BLUE),
        ("5", "Calibrate (G1)", "60 prefixes × 3 models; s0-vs-s1 ≤20% (A-004)", ORANGE),
        ("6", "Main run (G2)", "executed 21,611 rows; hard stop 45 GPU-h / 200 GB", ORANGE),
        ("7", "Analyse (G3/G4)", "slope + silent split; KM/RMST; gates as measured", GREEN),
    ]

    y = 89.0
    for number, title, desc, color in stages:
        card(ax, 2.0, y - 8.4, 96.0, 8.8, facecolor=TINT[color], edgecolor=color, lw=2.0)
        label(ax, 7.5, y - 4.0, number, size=14, weight="bold", color=color)
        label(ax, 13.0, y - 2.9, title, size=12.5, weight="bold", color=color, ha="left")
        label(ax, 13.0, y - 6.2, desc, size=11, color=INK, ha="left")
        if y > 30.0:
            arrow(ax, (50.0, y - 8.4), (50.0, y - 9.6), color=MUTED, lw=2.0)
        y -= 10.2

    label(
        ax,
        50.0,
        14.0,
        "Sequential gates: G1 starts only after G0 freezes; G2 only after G1 passes.",
        size=11,
        color=INK,
        weight="bold",
    )
    label(
        ax,
        50.0,
        7.0,
        "Schematic; counts and hashes live in the G0 report and manifests.",
        size=11,
        color=MUTED,
    )

    return save(fig, outdir / "fig3.png")
# ---------------------------------------------------------------------------
# Figure 3: arms
# ---------------------------------------------------------------------------


def make_arms(outdir: Path) -> Path:
    fig, ax = canvas((6.4, 5.6))

    label(
        ax,
        50.0,
        95.5,
        "Five arms: V format anchor + s = 0…3 severity ladder",
        size=15,
        weight="bold",
        ha="center",
    )

    panels = [
        ("V", '{"fare": 420, "status": "ok"}', "verbatim JSON · anchor, not in slope", BLUE),
        ("s = 0", "Fare: $420. Status: ok.", "faithful prose · placebo", GREEN),
        ("s = 1", "Fare: $420. Aircraft: A321.", "non-critical edit · neg. control", SKY),
        ("s = 2", "Fare: $520. Status: ok.", "critical error · dose", ORANGE),
        (
            "s = 3",
            "Fare: $520. Status: cancelled; seats open.",
            "error + conflict · compound dose",
            VERMILLION,
        ),
    ]

    y = 87.0
    for title, example, role, color in panels:
        card(ax, 2.0, y - 11.4, 96.0, 11.8, facecolor=TINT[color], edgecolor=color, lw=2.0)
        label(ax, 7.5, y - 5.5, title, size=13, weight="bold", color=color)
        label(ax, 22.0, y - 3.8, example, size=11, color=INK, ha="left", family=MONO)
        label(ax, 22.0, y - 8.4, role, size=11, color=MUTED, ha="left", style="italic")
        y -= 13.0

    label(
        ax,
        50.0,
        18.0,
        "severity ladder: ordinal, not interval · V is a format anchor, not a level",
        size=11,
        color=INK,
        weight="bold",
    )
    label(
        ax,
        50.0,
        10.0,
        "Synthetic example (flight TA100). No real record, no PII; values show the manipulation.",
        size=11,
        color=MUTED,
    )

    return save(fig, outdir / "fig2.png")
# ---------------------------------------------------------------------------
# Figure 4: analysis (explicitly a conceptual schematic, not results)
# ---------------------------------------------------------------------------


def make_analysis(outdir: Path) -> Path:
    fig, ax = canvas((6.3, 3.3))

    label(
        ax,
        50.0,
        94.0,
        "Analysis path: from switch indicator to recovery",
        size=22,
        weight="bold",
        ha="center",
    )

    boxes = [
        (
            "1  Switch",
            ["Y = 1 vs V ref", "flag alone counts"],
            BLUE,
        ),
        (
            "2  Slope",
            ["cond. logit;", "mover estimand"],
            GREEN,
        ),
        (
            "3  Split",
            ["action / flag /", "silent / other"],
            ORANGE,
        ),
        (
            "4  Recovery",
            ["KM + RMST;", "R1 ref match;", "R2 = flag"],
            VERMILLION,
        ),
    ]
    box_w, box_gap = 23.2, 1.0
    box_x = 1.8
    box_y, box_h = 30.0, 48.0
    centers: list[float] = []
    for title, body, color in boxes:
        centers.append(box_x + box_w / 2)
        card(ax, box_x, box_y, box_w, box_h, facecolor=TINT[color], edgecolor=color, lw=2.2)
        band(ax, box_x, box_y + box_h - 9.0, box_w, 9.0, color)
        header_ink = PAPER if color in (BLUE, VERMILLION) else INK
        label(
            ax,
            box_x + box_w / 2,
            box_y + box_h - 4.5,
            title,
            size=13,
            weight="bold",
            color=header_ink,
        )
        paragraph(
            ax,
            box_x + box_w / 2,
            box_y + box_h - 13.0,
            body,
            size=12,
            linespacing=1.3,
        )
        box_x += box_w + box_gap

    for left, right in zip(centers[:-1], centers[1:], strict=False):
        arrow(ax, (left + box_w / 2, box_y + box_h / 2), (right - box_w / 2, box_y + box_h / 2))

    label(
        ax,
        50.0,
        18.0,
        "Conceptual schematic: estimation order for slope, decomposition, and recovery. Not study data.",
        size=FOOTNOTE_FONT,
        color=MUTED,
    )
    label(
        ax,
        50.0,
        8.0,
        "V is the verbatim-observation reference; slope uses the prose arms s = 0…3 only.",
        size=FOOTNOTE_FONT,
        color=MUTED,
    )

    return save(fig, outdir / "fig4.png")


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
    # Maps figure file -> (canvas width in, printed fraction of the 6.18 in
    # text block, smallest nominal font in pt). The effective size is the
    # nominal size scaled by printed/canvas width; every entry must stay at
    # or above 8 pt.
    contract = {
        "fig1.png": (15.0, 0.95, 21),
        "fig3.png": (6.3, 0.95, 11),
        "fig2.png": (6.4, 0.95, 11),
        "fig4.png": (6.3, 0.95, 12),
    }
    print(f"{'file':22s} {'width':>7s} {'height':>7s} {'dpi':>12s} {'eff.pt':>7s}")
    paths = []
    for name, (canvas_in, fraction, min_font) in contract.items():
        path = outdir / name
        if not path.exists():
            raise FileNotFoundError(f"missing figure: {path}")
        width, height, dpi = describe_png(path)
        if min(dpi) < DPI - 0.5:
            raise ValueError(f"{path.name}: expected {DPI} DPI, got {dpi}")
        if width < 3300:
            raise ValueError(f"{path.name}: unexpectedly narrow ({width}px)")
        effective = min_font * (fraction * 6.18 / canvas_in)
        if effective < 8.0 - 1e-9:
            raise ValueError(
                f"{path.name}: effective font {effective:.2f} pt below 8 pt"
            )
        print(
            f"{name:22s} {width:7d} {height:7d}"
            f" {dpi[0]:6.0f} x {dpi[1]:<5.0f} {effective:7.2f}"
        )
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
