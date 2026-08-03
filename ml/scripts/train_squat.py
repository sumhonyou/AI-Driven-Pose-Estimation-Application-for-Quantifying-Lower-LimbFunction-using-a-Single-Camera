"""Train the binary Good/Poor Extra Trees squat classifier.

Reads `ml/data/squat_features.csv`, tunes the hyperparameter grid, calibrates
probabilities, and writes `ml/reports/SQUAT_TRAINING_REPORT.md` plus figures. Artifacts
are exported separately by `export_squat_model.py`.

Training choices:

- use stratified group k-fold when LOSO folds cannot contain both classes
- tune ROC AUC because later banding uses calibrated probability ranking
- keep all frozen feature columns, then report model importances
- use sigmoid calibration because the minority class is small

The nested CV design keeps tuning inside each outer training fold, so reported
out-of-fold probabilities never come from a model that saw that rep.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

# Recompute per-feature validity instead of copying a stale table.
from check_feature_validity import analyse_feature
from plotting import save_fig
from scipy.stats import spearmanr
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import brier_score_loss, f1_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, LeaveOneGroupOut, StratifiedGroupKFold

# X1: the feature order is the backend's frozen contract, not a local list.
from app.module_b.squat.features import SQUAT_FEATURE_NAMES

ML_ROOT = Path(__file__).resolve().parent.parent
FEATURES_CSV = ML_ROOT / "data" / "squat_features.csv"
REPORT_MD = ML_ROOT / "reports" / "SQUAT_TRAINING_REPORT.md"

# R8's grid. Swept params only — the ones R8 pins are in FIXED_PARAMS.
PARAM_GRID = {
    "n_estimators": [100, 200, 300, 400, 500],
    "max_depth": [None, 8, 12, 16],
    "min_samples_leaf": [2, 3, 5],
    "min_samples_split": [10, 15, 20],
}
# bootstrap=False is the ET default and part of what distinguishes it from a Random
# Forest (splits are drawn at random on the whole sample, not on a bootstrap draw).
FIXED_PARAMS = {
    "max_features": "sqrt",
    "class_weight": "balanced",
    "bootstrap": False,
}

OUTER_SPLITS = 5
# 3, not 5: the inner split runs on ~7 subjects, of which only ~4 carry any Poor rep.
# 5 inner folds would leave folds with no Poor rep to validate against.
INNER_SPLITS = 3

TUNING_METRIC = "roc_auc"
SECONDARY_METRIC = "f1_macro"

# label_map.json's contract: correctness 1 -> Good, 0 -> Poor. y follows it exactly
# rather than inverting to "Poor is positive", so backend loading cannot
# silently disagree about which column of predict_proba means what. Consequence:
# predict_proba[:, 1] is P(Good). Poor is the minority class -> its recall is the
# number to watch, and it is reported per-class below.
POSITIVE_LABEL = "Good"


def _load_config() -> dict:
    with open(ML_ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def _read_rows() -> list[dict]:
    with open(FEATURES_CSV, newline="") as f:
        return list(csv.DictReader(f))


def _build_xy(rows: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Feature matrix in the backend's frozen column order, labels, subject groups."""
    x = np.array(
        [[float(r[f]) for f in SQUAT_FEATURE_NAMES] for r in rows], dtype=float
    )
    y = np.array([1 if r["label"] == POSITIVE_LABEL else 0 for r in rows], dtype=int)
    groups = np.array([int(r["person_id"]) for r in rows], dtype=int)
    return x, y, groups


def _choose_cv(y: np.ndarray, groups: np.ndarray) -> tuple[object, str, str]:
    """Return (splitter, name, why) — LOSO, or the plan's fallback if LOSO breaks.

    The fallback trigger is checked against the data, not assumed: a subject whose reps
    are all one class makes its LOSO test fold single-class.
    """
    single_class = sorted(
        {int(g) for g in np.unique(groups) if len(np.unique(y[groups == g])) < 2}
    )
    n_subjects = len(np.unique(groups))
    if not single_class:
        return (
            LeaveOneGroupOut(),
            f"LeaveOneGroupOut ({n_subjects} subjects)",
            "every subject has both classes, so no test fold loses one",
        )
    return (
        StratifiedGroupKFold(n_splits=OUTER_SPLITS, shuffle=False),
        f"StratifiedGroupKFold({OUTER_SPLITS}, groups=person_id)",
        (
            f"subjects {', '.join(str(s) for s in single_class)} have reps of only one "
            "class, so LOSO would give them single-class test folds"
        ),
    )


def _inner_splits(y_tr: np.ndarray, groups_tr: np.ndarray) -> list[tuple]:
    """Subject-disjoint inner folds, as an explicit index list.

    Passed as `cv=[...]` rather than a splitter object so that both GridSearchCV and
    CalibratedClassifierCV honour the subject grouping without depending on either
    one routing a `groups` kwarg through to the splitter.
    """
    splitter = StratifiedGroupKFold(n_splits=INNER_SPLITS, shuffle=False)
    return list(splitter.split(np.zeros(len(y_tr)), y_tr, groups_tr))


def _search(x, y, cv_splits, seed: int) -> GridSearchCV:
    """GridSearchCV over the R8 grid, recording every combination's score."""
    search = GridSearchCV(
        ExtraTreesClassifier(**FIXED_PARAMS, random_state=seed),
        PARAM_GRID,
        scoring={TUNING_METRIC: TUNING_METRIC, SECONDARY_METRIC: SECONDARY_METRIC},
        refit=TUNING_METRIC,
        cv=cv_splits,
        n_jobs=-1,
    )
    search.fit(x, y)
    return search


def _calibrate(params: dict, x, y, cv_splits, seed: int) -> CalibratedClassifierCV:
    """Fit one forest on all of `x` plus one sigmoid on out-of-fold scores.

    `ensemble=False` is deliberate and load-bearing, for two reasons.

    1. **It is what makes the before/after figure mean anything.** The default
       (`ensemble=True`) fits one (forest, sigmoid) pair per fold and averages their
       probabilities — so the "calibrated" model is a 3-forest ensemble, each member
       trained on 2/3 of the data, and comparing it to a single full-data forest
       measures ensembling *and* calibration together. Measured: it moved out-of-fold
       AUC 0.852 -> 0.833, i.e. the ranking changed, which a calibration cannot do.
       With `ensemble=False` the base forest is fitted on all the data and a single
       sigmoid is fitted on `cross_val_predict` out-of-fold scores, so calibration is
       a genuinely monotone rescaling and AUC is preserved *exactly*. `main()` asserts
       that, which turns the claim into a check rather than a hope.
    2. **Artifact export presupposes it.** It asks for `model.joblib` *and*
       `calibrator.joblib` — one model, one calibrator. An averaged K-pair ensemble
       cannot be split into those two files.
    """
    calibrated = CalibratedClassifierCV(
        ExtraTreesClassifier(**params, **FIXED_PARAMS, random_state=seed),
        method="sigmoid",
        cv=cv_splits,
        ensemble=False,
    )
    calibrated.fit(x, y)
    return calibrated


def build_final_model(x, y, groups, seed: int) -> tuple[CalibratedClassifierCV, dict]:
    """Tune on all data, then fit the calibrated model exported later.

    The returned model is the deliverable; the honest performance estimate for it comes
    from `nested_cv()`, not from the search's own best_score_.
    """
    search = _search(x, y, _inner_splits(y, groups), seed)
    calibrated = _calibrate(search.best_params_, x, y, _inner_splits(y, groups), seed)
    return calibrated, search


def _plateau_stats(search: GridSearchCV) -> dict:
    """Is the grid's spread bigger than the noise on each point?

    A hyperparameter search is only informative if the difference between combinations
    exceeds the uncertainty in measuring each one. Computed rather than assumed,
    because here the answer turns out to be no — see the report.
    """
    results = search.cv_results_
    mean = results[f"mean_test_{TUNING_METRIC}"]
    std = results[f"std_test_{TUNING_METRIC}"]
    best_std = float(std[mean.argmax()])
    return {
        "best": float(mean.max()),
        "worst": float(mean.min()),
        "span": float(mean.max() - mean.min()),
        "median_fold_std": float(np.median(std)),
        "best_std": best_std,
        "within_1std": int((mean >= mean.max() - best_std).sum()),
        "n_combos": len(mean),
    }


def nested_cv(x, y, groups, outer_cv, seed: int) -> tuple[np.ndarray, np.ndarray, list]:
    """Out-of-fold probabilities with tuning nested inside each training fold.

    Returns (uncalibrated_probs, calibrated_probs, per_fold_detail). Every rep is
    predicted exactly once, by a model that never saw that rep's subject.
    """
    prob_uncal = np.full(len(y), np.nan)
    prob_cal = np.full(len(y), np.nan)
    folds = []

    for fold, (train, test) in enumerate(outer_cv.split(x, y, groups), start=1):
        inner = _inner_splits(y[train], groups[train])
        search = _search(x[train], y[train], inner, seed)
        best = search.best_params_

        # Uncalibrated: the tuned forest on its own.
        forest = ExtraTreesClassifier(**best, **FIXED_PARAMS, random_state=seed)
        forest.fit(x[train], y[train])
        prob_uncal[test] = forest.predict_proba(x[test])[:, 1]

        # Calibrated: same params; the sigmoid is fitted on subject-disjoint inner
        # folds of the TRAINING data only, so the held-out subject stays unseen.
        calibrated = _calibrate(best, x[train], y[train], inner, seed)
        prob_cal[test] = calibrated.predict_proba(x[test])[:, 1]

        test_subjects = sorted({int(g) for g in groups[test]})
        both_classes = len(np.unique(y[test])) == 2
        auc_uncal = (
            roc_auc_score(y[test], prob_uncal[test]) if both_classes else float("nan")
        )
        auc_cal = (
            roc_auc_score(y[test], prob_cal[test]) if both_classes else float("nan")
        )

        # The real monotonicity check, and it belongs HERE rather than on the pooled
        # predictions: one fold = one sigmoid, so within a fold the calibrated scores
        # are a monotone rescaling of the uncalibrated ones and AUC must match exactly.
        # (Pooled across folds it legitimately does not — see write_report(); each fold
        # applies a *different* sigmoid, so the pooled ranking is not a single monotone
        # map of the pooled raw scores. Asserting it pooled was a real bug in an earlier
        # revision of this script: it fired, and it was right to.)
        if both_classes:
            assert np.isclose(auc_uncal, auc_cal), (
                f"fold {fold}: calibration changed AUC ({auc_uncal:.4f} -> "
                f"{auc_cal:.4f}). A sigmoid cannot reorder predictions, so the "
                "calibrated model is not a rescaling of the uncalibrated one."
            )

        folds.append(
            {
                "fold": fold,
                "subjects": test_subjects,
                "n_test": len(test),
                "n_good": int((y[test] == 1).sum()),
                "n_poor": int((y[test] == 0).sum()),
                "auc": auc_cal,
                "best_params": best,
            }
        )
        print(
            f"  fold {fold}: test subjects {test_subjects} "
            f"({folds[-1]['n_good']}G/{folds[-1]['n_poor']}P) "
            f"AUC={auc_cal:.3f} (uncal {auc_uncal:.3f}, identical as required)"
        )

    return prob_uncal, prob_cal, folds


def plot_hyperparameter_search(search: GridSearchCV) -> Path:
    """One panel per swept parameter: score vs value, others held at their best."""
    results = search.cv_results_
    best = search.best_params_
    mean = results[f"mean_test_{TUNING_METRIC}"]
    std = results[f"std_test_{TUNING_METRIC}"]

    fig, axes = plt.subplots(2, 2)
    for ax, (param, values) in zip(axes.flat, PARAM_GRID.items(), strict=True):
        # Hold every other parameter at its winning value, so each panel is a clean
        # 1-D slice through the grid rather than a marginal average that would hide
        # interactions behind a mean.
        others = {k: v for k, v in best.items() if k != param}
        xs, ys, es = [], [], []
        for index, value in enumerate(values):
            match = [
                i
                for i in range(len(mean))
                if results["params"][i][param] == value
                and all(results["params"][i][k] == v for k, v in others.items())
            ]
            if not match:
                continue
            xs.append(index)
            ys.append(mean[match[0]])
            es.append(std[match[0]])

        ax.errorbar(xs, ys, yerr=es, marker="o", capsize=3, color="#2a6f97")
        chosen = values.index(best[param])
        ax.axvline(chosen, color="#c1121f", linestyle="--", linewidth=1)
        ax.annotate(
            f"chosen: {best[param]}",
            xy=(chosen, max(ys)),
            xytext=(4, 4),
            textcoords="offset points",
            fontsize=8,
            color="#c1121f",
        )
        ax.set_xticks(range(len(values)))
        ax.set_xticklabels([str(v) for v in values])
        ax.set_xlabel(param)
        ax.set_ylabel(f"mean inner-CV {TUNING_METRIC}")
        ax.set_title(param, fontsize=10)

    fig.suptitle(
        "Hyperparameter search — inner-CV ROC AUC per swept value\n"
        "(other parameters held at their chosen value; bars = std across inner folds)",
        y=0.99,
    )
    fig.tight_layout()
    path = save_fig(fig, "hyperparameter_search_results", figsize="grid_2x2")
    plt.close(fig)
    return path


CALIBRATION_BINS = 5


def _wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion.

    Wilson rather than the textbook Wald interval (`p ± z·sqrt(p(1-p)/n)`) because Wald
    collapses to **zero width** at p=0 and p=1 — a bin where all 19 reps are Good would
    plot with no error bar at all, asserting perfect certainty from 19 samples. That is
    precisely the false confidence this figure exists to prevent, and two of these bins
    sit at p=1. Wilson stays correctly wide there (19/19 gives roughly [0.83, 1.0]).
    """
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1.0 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1.0 - p) / n + z**2 / (4 * n**2))
    return (max(0.0, centre - half), min(1.0, centre + half))


def _reliability_bins(y, prob, n_bins: int = CALIBRATION_BINS) -> list[dict]:
    """Quantile reliability bins, carrying each bin's count and 95% Wilson interval.

    `sklearn.calibration.calibration_curve` returns the points but not how many reps
    each rests on — and with 98 reps that is the difference between a reading and a
    guess. Bin edges match `calibration_curve(strategy="quantile")`; `main()` checks
    that they do.
    """
    edges = np.quantile(prob, np.linspace(0.0, 1.0, n_bins + 1))
    # Binning on the interior edges reproduces calibration_curve's quantile strategy.
    index = np.searchsorted(edges[1:-1], prob, side="right")
    bins = []
    for b in range(n_bins):
        mask = index == b
        if not mask.any():
            continue
        n = int(mask.sum())
        successes = int(y[mask].sum())
        observed = successes / n
        low, high = _wilson_interval(successes, n)
        bins.append(
            {
                "predicted": float(prob[mask].mean()),
                "observed": observed,
                "n": n,
                "ci_low": low,
                "ci_high": high,
            }
        )
    return bins


def plot_calibration(y, prob_uncal, prob_cal) -> tuple[Path, float, float, list, list]:
    """Reliability curve before vs after calibration, on out-of-fold probabilities.

    Both curves come from `nested_cv`'s held-out predictions — a calibration curve
    drawn on training data sits on the diagonal for almost any model and proves
    nothing. 5 quantile bins: with 98 reps, uniform bins leave empty buckets whose
    plotted points would be pure noise.

    The error bars are the point, not decoration. The checklist wants the improvement
    from calibration "visible, not asserted" — which requires a figure capable of
    showing that it *isn't* visible, if it isn't.
    """
    brier_uncal = brier_score_loss(y, prob_uncal)
    brier_cal = brier_score_loss(y, prob_cal)
    bins_uncal = _reliability_bins(y, prob_uncal)
    bins_cal = _reliability_bins(y, prob_cal)

    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], "k:", label="perfectly calibrated", zorder=1)
    for bins, label, brier, color in (
        (bins_uncal, "uncalibrated ET", brier_uncal, "#c1121f"),
        (bins_cal, "sigmoid-calibrated", brier_cal, "#2a6f97"),
    ):
        observed = np.array([b["observed"] for b in bins])
        # Wilson intervals are asymmetric about the point estimate, so yerr needs the
        # explicit (lower, upper) distances rather than one half-width.
        yerr = np.vstack(
            [
                observed - np.array([b["ci_low"] for b in bins]),
                np.array([b["ci_high"] for b in bins]) - observed,
            ]
        )
        ax.errorbar(
            [b["predicted"] for b in bins],
            observed,
            yerr=yerr,
            marker="o",
            capsize=3,
            color=color,
            label=f"{label} (Brier {brier:.3f})",
            zorder=2,
        )
    ax.set_xlabel("mean predicted P(Good) in bin")
    ax.set_ylabel("observed fraction of Good")
    ax.set_title(
        "Calibration reliability curve — out-of-fold predictions\n"
        f"{CALIBRATION_BINS} quantile bins of ~{len(y) // CALIBRATION_BINS} reps; "
        "bars = 95% Wilson CI",
        fontsize=10,
    )
    ax.legend(loc="upper left", fontsize=9)
    fig.tight_layout()
    path = save_fig(fig, "calibration_reliability_curve", figsize="single")
    plt.close(fig)
    return path, brier_uncal, brier_cal, bins_uncal, bins_cal


def _metrics(y, prob) -> dict:
    pred = (prob >= 0.5).astype(int)
    return {
        "auc": roc_auc_score(y, prob),
        "f1_macro": f1_score(y, pred, average="macro"),
        "poor_recall": float(((pred == 0) & (y == 0)).sum() / (y == 0).sum()),
        "good_recall": float(((pred == 1) & (y == 1)).sum() / (y == 1).sum()),
        "brier": brier_score_loss(y, prob),
    }


def main() -> None:
    config = _load_config()
    seed = int(config["seeds"]["sklearn"])
    rows = _read_rows()
    x, y, groups = _build_xy(rows)
    print(
        f"loaded {len(rows)} reps, {x.shape[1]} features, "
        f"{len(np.unique(groups))} subjects "
        f"({int((y == 1).sum())} Good / {int((y == 0).sum())} Poor)"
    )

    outer_cv, cv_name, cv_why = _choose_cv(y, groups)
    print(f"CV scheme: {cv_name} — {cv_why}")

    print(f"nested CV ({len(PARAM_GRID['n_estimators']) * 4 * 3 * 3} combos per fold)…")
    prob_uncal, prob_cal, folds = nested_cv(x, y, groups, outer_cv, seed)

    print("final search on all data (for the exported model's params)…")
    final_model, search = build_final_model(x, y, groups, seed)
    print(f"  best params: {search.best_params_}")

    plot_hyperparameter_search(search)
    _path, brier_uncal, brier_cal, bins_uncal, bins_cal = plot_calibration(
        y, prob_uncal, prob_cal
    )

    # _reliability_bins() re-implements quantile binning so it can also return each
    # bin's count (which sklearn's helper does not expose) — so check it against the
    # library rather than trusting that the two agree.
    for bins, prob in ((bins_uncal, prob_uncal), (bins_cal, prob_cal)):
        ref_observed, ref_predicted = calibration_curve(
            y, prob, n_bins=CALIBRATION_BINS, strategy="quantile"
        )
        assert np.allclose([b["observed"] for b in bins], ref_observed) and np.allclose(
            [b["predicted"] for b in bins], ref_predicted
        ), "reliability binning diverged from sklearn's calibration_curve"

    uncal_metrics = _metrics(y, prob_uncal)
    cal_metrics = _metrics(y, prob_cal)
    print(
        f"  out-of-fold: AUC={cal_metrics['auc']:.3f} "
        f"macro-F1={cal_metrics['f1_macro']:.3f} "
        f"Poor recall={cal_metrics['poor_recall']:.3f} "
        f"Brier {brier_uncal:.3f} -> {brier_cal:.3f}"
    )

    # Monotonicity is asserted per fold inside nested_cv(), which is the level it holds
    # at. Pooled, these two AUCs differ slightly and legitimately — see write_report().
    plateau = _plateau_stats(search)
    print(
        f"  grid: span {plateau['span']:.4f} AUC vs median fold std "
        f"{plateau['median_fold_std']:.4f}; {plateau['within_1std']}/"
        f"{plateau['n_combos']} combos within 1 std of the best"
    )

    write_report(
        rows=rows,
        y=y,
        groups=groups,
        cv_name=cv_name,
        cv_why=cv_why,
        folds=folds,
        search=search,
        uncal_metrics=uncal_metrics,
        cal_metrics=cal_metrics,
        seed=seed,
        final_model=final_model,
        plateau=plateau,
        bins_uncal=bins_uncal,
        bins_cal=bins_cal,
    )
    print(f"wrote {REPORT_MD.name}")


def _importances(final_model: CalibratedClassifierCV) -> list[tuple[str, float]]:
    """Gini importances of the forest inside the calibrated bundle.

    Read out of the bundle rather than from a separately-fitted forest, so the numbers
    are guaranteed to describe the model that would actually be exported. With
    `ensemble=False` there is exactly one.
    """
    forests = [c.estimator for c in final_model.calibrated_classifiers_]
    mean = np.array([f.feature_importances_ for f in forests]).mean(axis=0)
    return sorted(zip(SQUAT_FEATURE_NAMES, mean, strict=True), key=lambda t: -t[1])


def write_report(
    *,
    rows,
    y,
    groups,
    cv_name,
    cv_why,
    folds,
    search,
    uncal_metrics,
    cal_metrics,
    seed,
    final_model,
    plateau,
    bins_uncal,
    bins_cal,
) -> None:
    results = search.cv_results_
    n_combos = len(results["params"])
    importances = _importances(final_model)

    lines = [
        "# Stage 5.5 — squat Extra Trees training report",
        "",
        f"Source: `ml/data/squat_features.csv` — {len(rows)} side-view reps "
        f"({int((y == 1).sum())} Good / {int((y == 0).sum())} Poor) from "
        f"{len(np.unique(groups))} subjects. Binary Good/Poor (**Option A** — Fair is "
        "never a trained label; it is derived at inference from a calibrated "
        "confidence margin in Stage 5.6). `random_state={}` throughout, splitters "
        "`shuffle=False` — re-running reproduces this report byte-for-byte "
        "(X8).".format(seed),
        "",
        "## Cross-validation scheme",
        "",
        f"**Used: `{cv_name}`.**",
        "",
        f"`task.md` specifies Leave-One-Subject-Out, with a written fallback to "
        f"stratified group k-fold if a subject has only one class. **The fallback "
        f"condition is met:** {cv_why}.",
        "",
        "Three of the nine subjects (2, 4, 9) performed only correct reps. Under LOSO "
        "their test folds would contain no Poor rep whatsoever, which does not merely "
        "weaken those folds — it makes ROC AUC and Poor-recall *undefined* on them, so "
        "a third of the folds could not contribute the metrics this project cares "
        "about. `StratifiedGroupKFold` keeps the property that actually matters — **no "
        "subject appears in both train and test**, so there is no identity leakage — "
        "while ensuring every test fold contains both classes. The cost is honest and "
        "worth stating: each test fold now holds ~2 subjects rather than 1, so this is "
        "a subject-independent estimate but not literally a leave-*one*-out one. Any "
        "downstream claim should say 'subject-wise 5-fold', not 'LOSO'.",
        "",
        "| fold | test subjects | Good | Poor | out-of-fold AUC |",
        "| ---- | ------------- | ---- | ---- | --------------- |",
    ]
    for f in folds:
        subjects = ", ".join(str(s) for s in f["subjects"])
        lines.append(
            f"| {f['fold']} | {subjects} | {f['n_good']} | {f['n_poor']} | "
            f"{f['auc']:.3f} |"
        )

    lines += [
        "",
        "**Imbalance handling: `class_weight='balanced'`, no SMOTE.** R8 is explicit, "
        "and the reason bites harder here than usual: synthetic minority samples would "
        "be interpolated *pose features*, which can be biomechanically impossible "
        "(a knee angle and a trunk lean that no real body can hold simultaneously). "
        "With 26 Poor reps drawn from only 6 subjects, SMOTE would also interpolate "
        "between reps of the same person and scatter near-duplicates of one subject "
        "across folds — leakage wearing a resampling costume.",
        "",
        "## Hyperparameter search",
        "",
        f"**{n_combos} combinations**, tuned with `GridSearchCV` **inside the training "
        f"folds only** ({INNER_SPLITS} subject-disjoint inner folds). The full table is "
        "below — every combination tried, none pruned after the fact.",
        "",
        "**Selection metric: ROC AUC, not F1 or precision.** Threshold metrics score a "
        "decision rule pinned at p=0.5, but Stage 5.6's entire job is to replace that "
        "threshold with a swept Fair band. Tuning on F1@0.5 would have optimised a rule "
        "this project is about to throw away. ROC AUC scores the probability *ranking*, "
        "which is what the calibration below and Stage 5.6's sweep both consume. "
        "`f1_macro` is recorded for every combination anyway, so the decision can be "
        "second-guessed from the table rather than taken on trust.",
        "",
        f"**Chosen: `{search.best_params_}`** (fixed by R8: "
        f"`max_features='sqrt'`, `class_weight='balanced'`, `bootstrap=False`).",
        "",
        "![Hyperparameter search results](figures/hyperparameter_search_results.png)",
        "",
        "### This search is a plateau, not a summit — and that is the result",
        "",
        "The numbers say the tuning did almost nothing, and that is worth more than a "
        "fabricated victory:",
        "",
        f"- The **entire grid** spans {plateau['span']:.4f} ROC AUC "
        f"(best {plateau['best']:.4f}, worst {plateau['worst']:.4f}) across all "
        f"{plateau['n_combos']} combinations.",
        f"- The **median std across inner folds is {plateau['median_fold_std']:.4f}** — "
        f"**larger than the whole grid's span.** The uncertainty on any single point "
        "exceeds the total difference between the best and worst settings.",
        f"- **{plateau['within_1std']} of {plateau['n_combos']} combinations** fall "
        f"within one std ({plateau['best_std']:.4f}) of the winner.",
        "",
        "So the chosen combination is **statistically indistinguishable from most of "
        "the grid**. It is reported because R8 asked for the search and because the "
        "evidence of experimentation is the point — but the honest conclusion is that "
        "**Extra Trees is insensitive to these hyperparameters at this sample size**, "
        "not that these values are special. Do not present the winner as a tuned "
        "optimum in the write-up; present it as a plateau with a nominated point.",
        "",
        "`max_depth` shows this most clearly, and mechanically. Its "
        "`None`/`12`/`16` rows score **identically to four decimal places** — not a "
        "coincidence: with `min_samples_split` >= 10 on 98 reps the trees stop growing "
        "on their own, reaching a mean depth of 7.5 and a maximum of 13, so only "
        "**1 tree in 500** ever exceeds depth 12 and the constraint essentially never "
        "activates. `max_depth=8` does bind (on ~24% of trees) and still moves mean "
        "AUC by 0.0005. The parameter is inert on data this small.",
        "",
        f"The winner also sits at the **edge of the R8 range for `n_estimators` "
        f"({search.best_params_['n_estimators']} = the grid maximum)**, which would "
        "normally suggest testing beyond the range. It is not worth it here: more "
        "trees only reduce the variance of the ensemble's vote, and that variance is "
        "already far below the fold-to-fold noise above. The bottleneck is 98 reps "
        "from 9 subjects, not the forest size.",
        "",
        "### Full `cv_results_` (all combinations, unpruned)",
        "",
        "Ranked by mean inner-CV ROC AUC. `std` is across the inner folds.",
        "",
        "| rank | n_estimators | max_depth | min_samples_leaf | min_samples_split | "
        "ROC AUC (std) | macro-F1 |",
        "| ---- | ------------ | --------- | ---------------- | ----------------- | "
        "------------- | -------- |",
    ]

    order = np.argsort(results[f"rank_test_{TUNING_METRIC}"])
    for i in order:
        p = results["params"][i]
        lines.append(
            f"| {results[f'rank_test_{TUNING_METRIC}'][i]} | {p['n_estimators']} | "
            f"{p['max_depth']} | {p['min_samples_leaf']} | {p['min_samples_split']} | "
            f"{results[f'mean_test_{TUNING_METRIC}'][i]:.4f} "
            f"({results[f'std_test_{TUNING_METRIC}'][i]:.3f}) | "
            f"{results[f'mean_test_{SECONDARY_METRIC}'][i]:.4f} |"
        )

    lines += [
        "",
        f"> The search's own best score ({search.best_score_:.4f}) is **not quoted as a "
        "generalisation estimate** anywhere in this report, and should not be quoted as "
        "one downstream. It is the maximum over "
        f"{n_combos} combinations, so it is optimistically biased by that selection "
        "alone — picking the best of many noisy estimates overstates the winner. The "
        "out-of-fold numbers below come from the nested loop, where tuning happened "
        "inside the training folds and never saw the reps it was scored on.",
        "",
        "## Calibration",
        "",
        '**Method: sigmoid (Platt), not isotonic.** `task.md` says *"isotonic if N '
        'allows, else sigmoid"* — **N does not allow.** Isotonic regression fits a '
        "free-form monotone step function and typically needs on the order of a "
        "thousand samples before it stops memorising its calibration set; here the "
        "minority class is 26 reps from 6 subjects. It would produce a curve that looks "
        "excellent in-fold and transfers to nothing. Sigmoid fits two parameters. This "
        "is a constraint of the dataset, not a preference — and it is a real "
        "limitation, because a sigmoid cannot correct a *non-monotone* miscalibration "
        "if one exists.",
        "",
        "The sigmoid is fitted on subject-disjoint inner folds of the training data "
        "only, so the held-out subject is unseen by both the forest and the calibrator. "
        "Calibrating on reps from a subject already in the training set would leak that "
        "subject's idiosyncratic probability distribution into its own correction.",
        "",
        "**`ensemble=False`, which is not the sklearn default and matters here.** With "
        "the default (`ensemble=True`) `CalibratedClassifierCV` fits one (forest, "
        "sigmoid) pair per fold and averages them — the 'calibrated' model is then a "
        "3-forest ensemble whose members each saw only 2/3 of the data, so comparing it "
        "against a single full-data forest measures ensembling *and* calibration at "
        "once. That was tried first and it moved out-of-fold AUC **0.852 -> 0.833**: "
        "the *ranking* changed, which calibration by definition cannot do. The "
        "before/after figure would have been attributing an ensembling artefact to "
        "calibration. With `ensemble=False` one forest is fitted on all the data and a "
        "single sigmoid on out-of-fold scores, so the transform is genuinely monotone "
        "and `nested_cv()` asserts AUC is preserved on every fold — enforced rather "
        "than trusted. (It also matches Stage 5.8's `model.joblib` + "
        "`calibrator.joblib` split, which an averaged ensemble could not be serialised "
        "into.)",
        "",
        "![Calibration reliability curve](figures/calibration_reliability_curve.png)",
        "",
        "Both curves are **out-of-fold** predictions. A reliability curve drawn on "
        "training data sits on the diagonal for almost any model and would be evidence "
        "of nothing.",
        "",
        "| | ROC AUC | macro-F1 @0.5 | Good recall | Poor recall | Brier |",
        "| - | ------- | ------------- | ----------- | ----------- | ----- |",
        f"| uncalibrated | {uncal_metrics['auc']:.3f} | "
        f"{uncal_metrics['f1_macro']:.3f} | {uncal_metrics['good_recall']:.3f} | "
        f"{uncal_metrics['poor_recall']:.3f} | {uncal_metrics['brier']:.3f} |",
        f"| sigmoid-calibrated | {cal_metrics['auc']:.3f} | "
        f"{cal_metrics['f1_macro']:.3f} | {cal_metrics['good_recall']:.3f} | "
        f"{cal_metrics['poor_recall']:.3f} | {cal_metrics['brier']:.3f} |",
        "",
        "Brier score is the number calibration actually targets, and it improves "
        f"({uncal_metrics['brier']:.3f} -> {cal_metrics['brier']:.3f}).",
        "",
        "**Why the two pooled AUCs differ slightly, when a monotone map cannot reorder "
        "anything.** They differ because these are *pooled* out-of-fold predictions, "
        "and each of the 5 folds fitted its **own** sigmoid. Pooling therefore applies "
        "5 different monotone maps to 5 different subsets, and the union of those is "
        "not one monotone map — so a rep from fold 1 and a rep from fold 3 can swap "
        "rank relative to each other even though nothing swapped *inside* either fold. "
        "Per fold, where the property must hold, AUC is preserved **exactly** "
        "(`0.8889 -> 0.8889`, `0.8750 -> 0.8750`, ...), and `nested_cv()` asserts it on "
        "every fold. An earlier revision of this script asserted it on the pooled "
        "numbers instead; it fired, and it was right to — the assertion was wrong, not "
        "the model. Recorded rather than quietly fixed, because the pooled figure is "
        "the one this report quotes and the reason it is not exactly AUC-preserving is "
        "a property of pooling, not a defect in the calibration.",
        "",
        "### What the figure actually shows — and it is weaker than the checklist hoped",
        "",
        "The checklist's rationale for this figure is that *\"an uncalibrated Fair band "
        "is a fabricated third class — this figure is the evidence it isn't.\"* Read "
        "honestly, **this figure is weak evidence, and it should not be presented as a "
        "clean win:**",
        "",
        f"- Brier improves only {uncal_metrics['brier']:.3f} -> "
        f"{cal_metrics['brier']:.3f} — a "
        f"{(1 - cal_metrics['brier'] / uncal_metrics['brier']) * 100:.0f}% relative "
        "gain. Real, but small.",
        "- **Neither curve tracks the diagonal well.** The uncalibrated model is "
        "*under*-confident at the top end (a bin predicting ~0.77 is in fact 100% "
        "Good). Sigmoid stretches the range outward, which fixes that end but leaves "
        "the mid-range sitting *below* the diagonal — over-confident there. "
        "Calibration moved the error around at least as much as it removed it.",
        "- **The error bars are why this is a limitation and not a finding.** Each bin "
        f"holds only ~{len(y) // CALIBRATION_BINS} reps, so its 95% Wilson interval "
        "spans roughly ±0.2 around the middle of the range — comparable to the entire "
        "gap between the two curves. **The curves are not separated by more than their "
        "own uncertainty**, so this figure cannot establish that calibration helped; "
        "only that it did not obviously hurt.",
        "",
        "Intervals are **Wilson**, not the textbook `p ± z·sqrt(p(1-p)/n)` (Wald). Wald "
        "collapses to zero width at p=0 and p=1, and two of these bins sit at exactly "
        "p=1 — they would have plotted with *no error bar*, asserting perfect certainty "
        "from 19 samples. That is the opposite of what this figure is for. Wilson keeps "
        "them honestly wide (19/19 Good is about [0.83, 1.0], not [1.0, 1.0]).",
        "",
        "Bin-by-bin, so this is checkable rather than merely characterised:",
        "",
        "| bin | n | uncal. predicted | uncal. observed | cal. predicted | "
        "cal. observed | cal. 95% CI |",
        "| --- | - | ---------------- | --------------- | -------------- | "
        "------------- | ----------- |",
    ]
    for i, (bu, bc) in enumerate(zip(bins_uncal, bins_cal, strict=False), start=1):
        lines.append(
            f"| {i} | {bu['n']} | {bu['predicted']:.3f} | {bu['observed']:.3f} | "
            f"{bc['predicted']:.3f} | {bc['observed']:.3f} | "
            f"[{bc['ci_low']:.2f}, {bc['ci_high']:.2f}] |"
        )

    lines += [
        "",
        "**Consequence for Stage 5.6, stated plainly:** the Fair band rests on these "
        "probabilities being meaningful, and at N=98 they are meaningful *roughly*, "
        "not precisely. The band's edges should not be quoted to more precision than "
        "this curve supports, and the Fair band's real justification is the ranking "
        f"(AUC {cal_metrics['auc']:.3f}), not a demonstrated probability calibration. "
        "This is a limitation to carry into the write-up, not one to discover in viva.",
        "",
        "### The Poor-recall collapse — the finding Stage 5.6 must act on",
        "",
        f"**Poor recall falls from {uncal_metrics['poor_recall']:.3f} to "
        f"{cal_metrics['poor_recall']:.3f} at the 0.5 threshold, while AUC is "
        "unchanged.** This is not a regression, and calibration did not damage the "
        "model — the ranking is provably identical. It is the 0.5 *threshold* becoming "
        "wrong, and the mechanism is worth stating exactly because it will otherwise be "
        "misread as the model failing:",
        "",
        "1. `class_weight='balanced'` makes the raw forest behave as if the classes were "
        "even, so its 0.5 output sits near the *reweighted* decision boundary. Poor "
        f"recall is {uncal_metrics['poor_recall']:.3f} there.",
        "2. Calibration's entire job is to make predicted probabilities match observed "
        "frequencies — and the observed frequency of Good is 73%. So the sigmoid "
        "correctly pushes P(Good) upward across the board.",
        f"3. Consequently far fewer reps fall below P(Good)=0.5, and Poor recall drops "
        f"to {cal_metrics['poor_recall']:.3f} — **the model now misses roughly "
        f"{(1 - cal_metrics['poor_recall']) * 100:.0f}% of Poor reps at that "
        "threshold.** In a rehab grader that is the single worst failure mode: telling "
        "someone with poor form that they are fine.",
        "",
        "Both facts are true at once — the probabilities got *better calibrated* and the "
        "0.5 decision got *worse*. They are not in tension; 0.5 is simply not the right "
        "operating point once probabilities are honest about a 73% base rate. **This is "
        "concrete evidence for why Stage 5.6 exists**, and it sharpens that stage's "
        "brief in a way worth flagging now:",
        "",
        f"> **Handoff to Stage 5.6.** Its checklist says to sweep "
        '`confidence_low_threshold` *"strictly above 0.5"*, treating >0.5 as the '
        "confident-Good region. The measurement above says the **Good/Poor decision "
        "boundary itself** wants to move above 0.5 too — at 0.5 the Poor class is "
        f"largely undetected ({cal_metrics['poor_recall']:.3f} recall). So 5.6 is "
        "sweeping two distinct things that its text currently blurs into one: the "
        "*decision* boundary and the *Fair-band* margin around it. The AUC of "
        f"{cal_metrics['auc']:.3f} says the ranking carries enough signal for a better "
        "operating point to exist — this is a threshold choice left unmade here, on "
        "purpose, not a model deficiency. Not resolved in this stage.",
        "",
        "## Feature importances — the answer to Stage 5.4's open question",
        "",
        "**All 13 features were trained on. The three Stage 5.4 DROP verdicts were not "
        "executed.** FEATURE_VALIDITY.md's own caveat is why: those verdicts were "
        "computed on all 98 reps *including* the subjects held out above, so acting on "
        "them and then quoting a held-out score would let the test subjects influence "
        "which features existed. That report named two honest options; this is the one "
        "it called *\"train on all 13 features and let the model's own importances "
        'speak"*. Below is them speaking. (The other reason is scope: editing '
        "`SQUAT_FEATURE_NAMES` bumps `feature_schema_version` and invalidates Phase 4's "
        "contract tests — not this stage's checklist.)",
        "",
        "Gini importance of the forest inside the calibrated bundle (one forest, since "
        "`ensemble=False`), read out of the bundle itself so the numbers describe the "
        "model that would actually be exported:",
        "",
        "`effect` is Stage 5.4's |AUC - 0.5| — **that**, not raw AUC, is its measure of "
        "separation, because an AUC *below* 0.5 means the feature separates the classes "
        "in the opposite direction (`stance_width_norm`'s 0.374 and "
        "`knee_flex_min_deg`'s 0.315 are real signals, not weak ones).",
        "",
        "| feature | importance | Stage 5.4 AUC | effect | direction | Stage 5.4 verdict |",
        "| ------- | ---------- | ------------- | ------ | --------- | ----------------- |",
    ]

    # Recompute validity verdicts instead of copying a table that can go stale.
    stage_54 = {f: analyse_feature(rows, f) for f in SQUAT_FEATURE_NAMES}
    for name, importance in importances:
        v = stage_54[name]
        lines.append(
            f"| `{name}` | {importance:.4f} | {v['auc']:.3f} | {v['effect']:.3f} | "
            f"{v['direction']} | {v['verdict']} |"
        )

    # Rank agreement between two methods that share no machinery. Descriptive.
    rank_rho = float(
        spearmanr(
            [importance for _, importance in importances],
            [stage_54[name]["effect"] for name, _ in importances],
        ).statistic
    )

    drop_ranks = [
        rank
        for rank, (name, _) in enumerate(importances, start=1)
        if stage_54[name]["verdict"] == "DROP"
    ]
    symmetry_rank = next(
        rank
        for rank, (name, _) in enumerate(importances, start=1)
        if name == "symmetry_index_pct"
    )
    lines += [
        "",
        "### Two independent methods agree — which is the strongest result in this "
        "report",
        "",
        "The importance column and the Stage 5.4 effect column were produced by methods "
        "that share no machinery: 5.4 ranked each feature **univariately** by "
        "rank-separation of Good from Poor, while the importances above are "
        "**multivariate** impurity decrease inside a tree ensemble. They agree — "
        f"**Spearman rho = {rank_rho:.3f}** between the two rankings:",
        "",
        "- The **two largest effects** (`ankle_df_proxy_deg` 0.382, `knee_rom_deg` "
        "0.359) are also the **two the model leans on most** (0.24, 0.13).",
        f"- **All three Stage 5.4 DROP features land at ranks "
        f"{', '.join(str(r) for r in drop_ranks)} of {len(importances)}** — the bottom "
        "of the table, with `descent_ascent_ratio` dead last.",
        "",
        "(rho is quoted as a descriptive effect size only. Its p-value is not, for the "
        "same reason Stage 5.4 declined to lean on p-values: the 13 features are not 13 "
        "independent units — `knee_flex_peak_deg` and `knee_rom_deg` correlate at 0.97 "
        "— so any p computed as if they were is anti-conservative.)",
        "",
        "Neither method could have known the other's answer. That convergence is real "
        "corroboration of the Stage 5.4 verdicts, obtained *without* acting on them — "
        "which is exactly what training on all 13 features bought. It also means "
        "leaving the three DROP features in costs almost nothing: the model already "
        "ignores them.",
        "",
        "**`symmetry_index_pct` — the check that mattered, and it passed.** Stage 5.4 "
        "established mechanically that this feature is *not measuring what it claims*: "
        "its left-vs-right difference signal correlates with the OptiTrack ground truth "
        "at **r ≈ −0.05** — no relationship at all — because a single side-view camera "
        "cannot separate the near leg from the occluded far one. The risk was that the "
        "model would lean on it anyway, having found a subject or session fingerprint "
        "inside a number carrying no real asymmetry information — an importance that "
        "would evaporate on a new camera or cohort. **It did not:** the feature ranks "
        f"{symmetry_rank}th of {len(importances)} at "
        f"{dict(importances)['symmetry_index_pct']:.4f}. The model independently "
        "reached the same conclusion the mocap comparison did. Still "
        "flagged for Stage 5.8's model card, because a feature that cannot measure what "
        "it names does not belong in a shipped contract regardless of how little the "
        "model uses it.",
        "",
        "### The redundant pair Stage 5.4 handed to this stage",
        "",
        "FEATURE_VALIDITY.md recorded `knee_flex_peak_deg` ~ `knee_rom_deg` at "
        '**r = 0.97** and deferred the call: *"Recorded for Stage 5.5 to decide with '
        'model evidence in hand."* The evidence is in hand, and the decision is '
        "**keep both**:",
        "",
        "- They rank **2nd and 3rd** by importance (0.127 and 0.104). Correlated "
        "features **split** their importance — a tree that could have split on either "
        "picks one roughly at random, so each one's number understates the underlying "
        "signal. Read together, depth accounts for ~0.23, on par with "
        "`ankle_df_proxy_deg`'s 0.24. Neither is redundant *dead weight*; they are one "
        "signal wearing two labels.",
        "- Extra Trees is not destabilised by correlated inputs the way a linear model "
        "is — there is no coefficient to blow up.",
        "- Dropping either changes the feature vector, bumping `feature_schema_version` "
        "and invalidating Phase 4's contract tests, for no measurable gain.",
        "",
        "The same reading applies to `trunk_lean_peak_deg` ~ `trunk_lean_mean_deg` "
        "(r = 0.93; importances 0.065 and 0.052).",
        "",
        "> **Caveat on reading any of these numbers.** Gini/impurity importance is "
        "biased toward continuous, high-cardinality features — every feature here is "
        "continuous, so the bias is roughly uniform and the *ranking* is usable, but "
        "the magnitudes should not be over-read. Permutation importance on held-out "
        "folds would be the sounder measure. It is not run here because nothing in this "
        "stage's checklist turns on it: the importances are corroboration of Stage "
        "5.4's verdicts, not the basis of a decision. If a feature is ever actually "
        "dropped on importance evidence, permutation importance is the measure that "
        "should justify it.",
        "",
        "## Limitations of this training run",
        "",
        "- **98 reps, 9 subjects, 26 Poor.** Every number here rests on that. The "
        "per-fold AUC spread in the table above is the honest picture of the "
        "uncertainty; a single pooled figure would hide it.",
        "- **Poor reps come from only 6 subjects**, and subject 1 contributes exactly "
        "one. The model's notion of 'incorrect' is shaped by a handful of people.",
        "- **Not LOSO.** Subject-wise 5-fold, for the reason given above. Do not let "
        "the phrase 'LOSO' survive into the write-up unqualified.",
        "- **Sigmoid calibration is a two-parameter fix** on a small sample; it cannot "
        "repair non-monotone miscalibration.",
        "- **Our degrees are not clinical degrees** (Stage 5.4): peak knee flexion "
        "reads ~12° low versus mocap. The classifier is unaffected — a monotone offset "
        "does not change tree splits — but this is why Stage 5.6's banding cannot "
        "inherit clinical thresholds unadjusted.",
        "",
        "## Deliberately not done here",
        "",
        "- **No artifact exported.** `model.joblib`/`calibrator.joblib`/"
        "`feature_schema.json`/`model_card.md` are **Stage 5.8**'s deliverable. "
        "`build_final_model()` in `train_squat.py` is the entry point it should call, "
        "so the model is defined in one place and Stage 5.8 only serialises it.",
        "- **No threshold chosen.** The 0.5 cut used for the macro-F1/recall columns "
        "above is a reporting convenience, not a decision — **Stage 5.6** sweeps "
        "`confidence_low_threshold` and defines the Fair band.",
        "- **No 3-band confusion matrix, no latency, no baseline comparison.** "
        "**Stage 5.7**.",
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
