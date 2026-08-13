"""ROC curves for the two data-driven squat fault gates (lean, heel-rise), marking
each gate's deployed Youden's-J-optimal threshold.

`analyze_fault_gate_thresholds.py` already computes `roc_curve()` for both gates to
pick the deployed cut -- it just never plotted it. This script reuses that exact same
data-building and threshold logic (`derive_gate_threshold`, `build_heel_rise_rows`,
`cfv._read_rows`) rather than recomputing anything independently, so the plotted
curves and marked points are guaranteed consistent with the thresholds actually
shipped in `SQUAT_CONFIG["fault_gates"]`.
"""

from pathlib import Path

import check_feature_validity as cfv
import matplotlib.pyplot as plt
import numpy as np
from analyze_fault_gate_thresholds import build_heel_rise_rows, derive_gate_threshold
from build_features import _load_config, _read_segmentation
from plotting import save_fig
from sklearn.metrics import roc_auc_score, roc_curve

from app.module_b.squat.config import SQUAT_CONFIG


def _roc_panel(ax, rows: list[dict], feature: str, deployed_threshold: float, unit: str, label: str) -> None:
    y = np.array([1 if r["label"] == "Poor" else 0 for r in rows])
    x = np.array([float(r[feature]) for r in rows])
    fpr, tpr, thresholds = roc_curve(y, x)
    j = tpr - fpr
    best = int(np.argmax(j))
    auc = roc_auc_score(y, x)

    ax.plot(fpr, tpr, color="#2b8cbe", lw=2, label=f"{label} (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], color="gray", lw=1, linestyle="--")
    ax.scatter(
        [fpr[best]],
        [tpr[best]],
        color="#e6550d",
        s=90,
        zorder=5,
        label=f"Youden's J optimum\ncut = {thresholds[best]:.3f}{unit}",
    )
    # Sanity check: the marked point must be the same threshold the deployed gate
    # actually uses -- if these ever disagree, the figure would be lying about the
    # shipped config, so fail loudly rather than plot silently wrong numbers.
    assert abs(thresholds[best] - deployed_threshold) < 1e-2, (
        f"{feature}: recomputed Youden threshold {thresholds[best]:.4f} does not "
        f"match deployed SQUAT_CONFIG threshold {deployed_threshold:.4f}"
    )
    ax.set_xlabel("False positive rate\n(clean reps wrongly flagged)")
    ax.set_ylabel("True positive rate\n(real faults caught)")
    ax.set_title(f"{label} fault gate")
    ax.legend(loc="lower right", fontsize=8)


def main() -> None:
    gates = SQUAT_CONFIG["fault_gates"]
    lean_threshold = gates["lean"]["fault_trunk_lean_peak_deg"]
    heel_threshold = gates["heel_rise"]["fault_heel_rise_peak_norm"]

    feature_rows = cfv._read_rows()

    config = _load_config()
    seg_rows = _read_segmentation(
        Path(config["dataset_paths"]["rehab246"]["segmentation_csv"])
    )
    print("Building heel-rise feature from raw landmarks (reads all 9 cached .npz)...")
    heel_rise_rows = build_heel_rise_rows(seg_rows, {}, {})

    fig, (ax1, ax2) = plt.subplots(1, 2)
    _roc_panel(ax1, feature_rows, "trunk_lean_peak_deg", lean_threshold, "°", "Lean")
    _roc_panel(ax2, heel_rise_rows, "heel_rise_peak_norm", heel_threshold, "", "Heel-rise")
    fig.suptitle(
        "Fault-gate thresholds: Youden's J on pooled REHAB24-6 labels\n"
        "(orange point = deployed SQUAT_CONFIG cut)",
        y=1.08,
    )
    fig.tight_layout()
    path = save_fig(fig, "fault_gate_roc_lean_heelrise", figsize="wide")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
