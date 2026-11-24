"""Figure contract tests: 600 DPI at final size, >=8 pt effective type.

Runs both figure generators in ``--verify-only`` mode as subprocesses. The
generators redraw deterministically from frozen analysis artifacts on import
(CPU-only, no GPU) and then assert the print contract: 600 DPI, a pixel width
consistent with the final printed width, and an effective (printed) minimum
type size of at least 8 pt for every figure.
"""

from __future__ import annotations

from _requires import requires_matplotlib
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PY = sys.executable

pytestmark = requires_matplotlib


def _run(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_PY, str(_REPO / "scripts" / "paper_figures" / script), "--verify-only"],
        capture_output=True,
        text=True,
        cwd=str(_REPO),
    )


def test_schematic_figures_verify() -> None:
    proc = _run("make_figures.py")
    assert proc.returncode == 0, proc.stderr[-2000:]
    for name in ("fig1.png", "fig2.png", "fig3.png", "fig4.png"):
        assert name in proc.stdout


def test_result_figures_verify() -> None:
    proc = _run("make_result_figures.py")
    assert proc.returncode == 0, proc.stderr[-2000:]
    for name in ("fig5.png", "fig6.png", "fig7.png", "fig8.png", "fig9.png", "fig10.png"):
        assert name in proc.stdout
