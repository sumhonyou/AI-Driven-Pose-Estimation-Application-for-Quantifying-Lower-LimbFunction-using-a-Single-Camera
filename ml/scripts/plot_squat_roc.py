"""F4.6 — squat ROC curve, for the thesis (§4.2.2).

No ROC figure was ever generated for the squat model — the training report
(`SQUAT_TRAINING_REPORT.md`) quotes the AUC number but never plots the curve.
This script reuses `train_squat.py`'s own `nested_cv()` unchanged, so the curve is
drawn from the exact same out-of-fold calibrated probabilities that produced the
reported AUC = 0.832 (same seed, same CV scheme, same nested tuning) — not a
re-run that could drift from the quoted number.
"""

import matplotlib.pyplot as plt
from plotting import save_fig
from sklearn.metrics import roc_auc_score, roc_curve
from train_squat import _build_xy, _choose_cv, _load_config, _read_rows, nested_cv


def main() -> None:
    config = _load_config()
    seed = int(config["seeds"]["sklearn"])
    rows = _read_rows()
    x, y, groups = _build_xy(rows)

    outer_cv, cv_name, cv_why = _choose_cv(y, groups)
    print(f"CV scheme: {cv_name} — {cv_why}")

    print("nested CV (reproducing the out-of-fold probabilities)…")
    _prob_uncal, prob_cal, _folds = nested_cv(x, y, groups, outer_cv, seed)

    auc = roc_auc_score(y, prob_cal)
    print(f"out-of-fold AUC = {auc:.3f} (report quotes 0.832)")
    assert abs(auc - 0.832) < 0.001, (
        f"reproduced AUC {auc:.4f} does not match the reported 0.832 — "
        "the figure would contradict the text"
    )

    fpr, tpr, _thresholds = roc_curve(y, prob_cal)

    fig, ax = plt.subplots()
    ax.plot(
        fpr, tpr, color="#2b8cbe", lw=2, label=f"Squat classifier (AUC = {auc:.3f})"
    )
    ax.plot(
        [0, 1], [0, 1], color="gray", lw=1, linestyle="--", label="Chance (AUC = 0.500)"
    )
    ax.set_xlabel("False positive rate")
    ax.set_ylabel("True positive rate")
    ax.set_title(
        "ROC curve — squat classifier\nOut-of-fold predictions, subject-wise 5-fold CV"
    )
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.legend(loc="lower right")

    path = save_fig(fig, "roc_curve_squat", figsize="single")
    plt.close(fig)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
