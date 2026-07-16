"""Shared plotting helpers for every ml/ report figure.

Every script that produces a figure for ml/reports/*.md goes through save_fig()
here — one DPI, one style, set once. No script sets its own DPI/style ad hoc.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

FIGURES_DIR = Path(__file__).resolve().parent.parent / "reports" / "figures"
DPI = 150

# Fixed figure size per plot type (inches). Callers request one of these by name
# rather than hand-picking a size per script.
FIGSIZES = {
    "single": (6, 4.5),
    "wide": (10, 4.5),
    "grid_4x4": (14, 12),
    "grid_2x2": (11, 8),  # one panel per swept hyperparameter (Stage 5.5)
    "bland_altman": (7, 6),
    "heatmap": (9, 8),  # square-ish, for the Stage 5.4 feature correlation matrix
}

_style_applied = False


def _apply_style() -> None:
    global _style_applied
    if _style_applied:
        return
    sns.set_theme(style="whitegrid")
    _style_applied = True


def save_fig(fig: plt.Figure, name: str, figsize: str | None = None) -> Path:
    """Save fig to ml/reports/figures/{name}.png at fixed DPI, return the path."""
    _apply_style()
    if figsize is not None:
        fig.set_size_inches(*FIGSIZES[figsize])
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / f"{name}.png"
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    return out_path
