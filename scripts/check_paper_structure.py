"""Structural checks for the ToolResult-800 manuscript (P6.6 craft).

Run from the repository root:

    python scripts/check_paper_structure.py

The script is stdlib-only and checks the properties P6.6 owns: headed
Discussion/Limitations sections, a 10--12-table main text with the remaining
tables in a supplementary section, an abstract within 250 words, plain-text
keywords, no unresolved placeholders, one survival/recovery definition, and
the full-scale recovery figure.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "paper" / "toolresults.tex"
FIG9_SCRIPT = ROOT / "scripts" / "paper_figures" / "make_result_figures.py"

MAIN_TABLE_LABELS = {
    "tab:neighbors",
    "tab:notation",
    "tab:arms",
    "tab:models",
    "tab:gate-status",
    "tab:hypotheses",
    "tab:primary",
    "tab:tiers",
    "tab:audit",
    "tab:fieldtypes",
    "tab:recovery",
}
SUPPLEMENT_TABLE_LABELS = {
    "tab:supply",
    "tab:gates",
    "tab:envelope",
    "tab:pilot",
    "tab:g1",
    "tab:diagnostics",
    "tab:missing",
    "tab:typology",
    "tab:armrates",
    "tab:panel",
    "tab:wrongdir",
    "tab:utility",
    "tab:recovery_all",
    "tab:sensitivity",
}


def body(text: str) -> str:
    """Return the document body without the comment-only preamble."""
    return text[text.index("\\begin{document}") :]


def section_slice(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    stop = text.index(end, begin)
    return text[begin:stop]


def count_words(abstract: str) -> int:
    cleaned = re.sub(r"\\[A-Za-z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", " ", abstract)
    cleaned = cleaned.replace("$", " ").replace("~", " ")
    return len(cleaned.split())


def main() -> int:
    tex = TEX.read_text(encoding="utf-8")
    doc = body(tex)
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        print(("PASS " if condition else "FAIL ") + message)
        if not condition:
            failures.append(message)

    # 1. Headed Discussion and Limitations between Results and Conclusion.
    order = [
        doc.index("\\section{Results}"),
        doc.index("\\section{Discussion}"),
        doc.index("\\section{Limitations}"),
        doc.index("\\section{Conclusion}"),
    ]
    check(order == sorted(order), "Results -> Discussion -> Limitations -> Conclusion")

    # 2. Table split: 11 main, 14 supplementary, 25 total.
    supp_start = doc.index("\\section*{Supplementary tables}")
    decl_start = doc.index("\\section*{Declarations}")
    main_tex = doc[:supp_start]
    supp_tex = doc[supp_start:decl_start]
    main_labels = set(re.findall(r"\\label\{(tab:[^}]+)\}", main_tex))
    supp_labels = set(re.findall(r"\\label\{(tab:[^}]+)\}", supp_tex))
    check(main_labels == MAIN_TABLE_LABELS, f"main-text labels ({len(main_labels)})")
    check(
        supp_labels == SUPPLEMENT_TABLE_LABELS,
        f"supplementary labels ({len(supp_labels)})",
    )
    check(main_tex.count("\\begin{table}") == 11, "11 main-text table environments")
    check(
        supp_tex.count("\\begin{table}") == 14,
        "14 supplementary table environments",
    )
    check(doc.count("\\begin{table}") == 25, "25 table environments in total")
    check(
        "\\renewcommand{\\thetable}{S\\arabic{table}}" in tex,
        "supplementary tables use an S prefix",
    )

    # 3. Abstract <= 250 words, keywords plain text.
    abstract = section_slice(tex, "\\begin{abstract}", "\\end{abstract}")
    words = count_words(abstract)
    check(words <= 250, f"abstract {words} words (cap 250)")
    keywords = section_slice(tex, "\\begin{keywords}", "\\end{keywords}")
    check("tau-bench" in keywords, "keywords contain plain-text tau-bench")
    check("$" not in keywords, "keywords contain no math")

    # 4. No unresolved placeholder outside its definition/comment.
    placeholder = [
        line
        for line in tex.splitlines()
        if "\\pending{" in line
        and not line.lstrip().startswith("%")
        and "\\newcommand" not in line
    ]
    check(not placeholder, "no \\pending usages")

    # 5. Survival/recovery stated once, and the table column uses 1-S_KM(4).
    check(
        tex.count("recovery complement of the Kaplan--Meier") == 1,
        "one survival-vs-recovery definition",
    )
    check(
        "$1-S_{\\mathrm{KM}}(4)$" in tex,
        "table column uses 1-S_KM(4)",
    )

    # 6. Figure 9: full 0-1 scale and recovery complement.
    fig_src = FIG9_SCRIPT.read_text(encoding="utf-8")
    check("ax.set_ylim(0.0, 1.0)" in fig_src, "figure 9 y-axis spans 0-1")
    check("1.0 - value for value in surv" in fig_src, "figure 9 plots 1-S_KM")
    check((ROOT / "paper" / "figures" / "fig9.png").is_file(), "fig9.png exists")

    if failures:
        print(f"\n{len(failures)} check(s) failed")
        return 1
    print("\nall structural checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
