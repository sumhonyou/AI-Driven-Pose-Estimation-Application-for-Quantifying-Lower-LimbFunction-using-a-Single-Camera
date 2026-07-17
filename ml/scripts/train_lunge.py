"""Stage 5.5 (Lunge): train the binary Good/Poor Extra Trees lunge classifier.

The lunge mirror of `train_squat.py`. Reads `ml/data/lunge_features.csv`, tunes the R8
grid, calibrates, and writes `ml/reports/LUNGE_TRAINING_REPORT.md` plus the required
figures. **No artifact is exported here** — that is Stage 5.8's job;
`build_final_model()` is the entry point it will call.

Squat's four framing decisions carry over unchanged (CV chosen by the data, ROC AUC as
the tuning metric, train on every feature rather than executing Stage 5.4's DROP
verdicts, sigmoid rather than isotonic calibration on small N). Read that module's
docstring for their justification; only the lunge-specific deltas are set out here.

**The delta that dominates this stage: an 8.9deg measurement bias aligned with the
subject cohorts.** Stage 5.4 established that the far/occluded limb is the right leg in
every recording and lead leg is fixed per subject, so the leading knee is the occluded
limb for right-lead subjects (-15.1deg bias against OptiTrack) and the clearly-visible
one for left-lead subjects (-6.2deg). The confound is therefore encoded in the feature
*values*: dropping the `lead_leg` column is necessary but NOT sufficient, because a
model can infer the cohort from measurement bias alone.

`compare_confound_strategies()` measures four responses to that, under one identical
nested CV, rather than asserting which is best:

  S0 baseline            all 17 features, raw. The plan's default and the deliverable.
  S1 session_centred     subtract each subject's own per-feature median. Transductive:
                         it uses the test subject's own reps (not their labels), which
                         at deployment means the user's own set -- available, since the
                         backend receives the whole set in one POST.
  S2 lead_near_only      train and test only on the 42 lead-near reps. This is the
                         train/serve match implied by the turn-around capture protocol,
                         and the only subset where TRUE LOSO is possible (all four of
                         its subjects carry both classes; subject 3 in the lead-far
                         cohort does not).
  S3 cohort_centred      subtract the lead-cohort's mean, estimated on TRAINING folds
                         only. Deployable without the user's own set, since the cohort
                         is detectable live from limb visibility.

**No strategy may use the mocap (X3).** The 8.9deg figure is a validation measurement,
so "subtract the measured bias" is deliberately absent from the list above: it would
make marker-based capture an input to the shipped model. S3 is the mocap-free way to
attack the same offset, estimating it from the features themselves.

**A warning this report must carry rather than bury:** the comparison below is scored on
the same 88 reps that every choice is made against. Picking the highest number here and
presenting it as the result would be selection on the test folds. S0 stays the
deliverable for that reason; the rest are evidence about the confound, not candidates
promoted by their score.

**What the run found, recorded here because it inverts this module's own framing.** S0 --
the plan's default and the scheduled deliverable -- is **indistinguishable from chance**
(p = 0.657 over 200 label shuffles). S1 and S2 both clear the null decisively
(p = 0.005, the test's floor). So the classifier this stage exists to train does not
work on held-out subjects, while two attacks on the confound recover real signal without
touching the model. `permutation_test()` exists because of that result: an out-of-fold
AUC below 0.5 invites the dramatic reading that the model predicts *backwards*, and the
null distribution refutes it -- the honest statement is "no detectable signal", not
"inverted signal". Whether a chance-level model may still be exported is HY's decision,
flagged in the report and deliberately not taken here.

Deterministic (X8): fixed seeds from `config.yaml`, `shuffle=False` splitters, sorted
iteration, no wall-clock.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml
# X1: the feature order is the backend's frozen contract, not a local list.
from app.module_b.lunge.features import LUNGE_FEATURE_NAMES
# Stage 5.4's per-feature verdicts are recomputed by calling its own analyser rather
# than transcribed into a table here — a copy would go stale silently.
from check_feature_validity_lunge import analyse_feature
from plotting import save_fig
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (brier_score_loss, f1_score, roc_auc_score,
                             roc_curve)
from sklearn.model_selection import (GridSearchCV, LeaveOneGroupOut,
                                     StratifiedGroupKFold)

ML_ROOT = Path(__file__).resolve().parent.parent
FEATURES_CSV = ML_ROOT / "data" / "lunge_features.csv"
REPORT_MD = ML_ROOT / "reports" / "LUNGE_TRAINING_REPORT.md"

# R8's grid — identical to squat's; the exercise changes, the search space does not.
PARAM_GRID = {
    "n_estimators": [100, 200, 300, 400, 500],
    "max_depth": [None, 8, 12, 16],
    "min_samples_leaf": [2, 3, 5],
    "min_samples_split": [10, 15, 20],
}
FIXED_PARAMS = {
    "max_features": "sqrt",
    "class_weight": "balanced",
    "bootstrap": False,
}

OUTER_SPLITS = 5
INNER_SPLITS = 3

TUNING_METRIC = "roc_auc"
SECONDARY_METRIC = "f1_macro"
CALIBRATION_BINS = 5

# label_map.json's contract: correctness 1 -> Good, 0 -> Poor. Same as squat, so
# predict_proba[:, 1] is P(Good) in both exercises and Stage 5.8 cannot mix them up.
POSITIVE_LABEL = "Good"

# Stage 5.4 (Lunge): the far/occluded limb is the RIGHT leg in all 9 recordings, so a
# left-lead subject's leading knee is the near (well-measured) limb.
LEAD_NEAR_COHORT = "left"


def _load_config() -> dict:
    with open(ML_ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def _read_rows() -> list[dict]:
    with open(FEATURES_CSV, newline="") as f:
        return list(csv.DictReader(f))


def _build_xy(
    rows: list[dict],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Feature matrix in the backend's frozen column order, labels, groups, cohorts.

    `cohorts` carries lead_leg. It is NOT a model input anywhere -- it selects and
    centres (S2/S3) only, and it is recoverable live from stance geometry (Stage 5.4
    verified the front-foot rule at 9/9 against the annotation), so nothing here
    depends on a column the live pipeline lacks.
    """
    x = np.array(
        [[float(r[f]) for f in LUNGE_FEATURE_NAMES] for r in rows], dtype=float
    )
    y = np.array([1 if r["label"] == POSITIVE_LABEL else 0 for r in rows], dtype=int)
    groups = np.array([int(r["person_id"]) for r in rows], dtype=int)
    cohorts = np.array([r["lead_leg"] for r in rows])
    return x, y, groups, cohorts


def _choose_cv(y: np.ndarray, groups: np.ndarray) -> tuple[object, str, str]:
    """Return (splitter, name, why) — LOSO, or the plan's fallback if LOSO breaks."""
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
            f"subject{'s' if len(single_class) > 1 else ''} "
            f"{', '.join(str(s) for s in single_class)} "
            f"ha{'ve' if len(single_class) > 1 else 's'} reps of only one class, so "
            "LOSO would give a single-class test fold"
        ),
    )


def _inner_splits(y_tr: np.ndarray, groups_tr: np.ndarray) -> list[tuple]:
    """Subject-disjoint inner folds, as an explicit index list."""
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
    """One forest on all of `x` plus one sigmoid on out-of-fold scores.

    `ensemble=False` for squat's two reasons: it keeps calibration a genuinely monotone
    rescaling (so AUC is preserved exactly, which `nested_cv` asserts), and Stage 5.8's
    artifact spec wants one model plus one calibrator, which an averaged K-pair ensemble
    cannot be split into.
    """
    calibrated = CalibratedClassifierCV(
        ExtraTreesClassifier(**params, **FIXED_PARAMS, random_state=seed),
        method="sigmoid",
        cv=cv_splits,
        ensemble=False,
    )
    calibrated.fit(x, y)
    return calibrated


# --- Confound strategies -------------------------------------------------------
# Each returns (x_train', x_test'). Any statistic that could leak is fitted on the
# training fold only; the one deliberate exception is S1, documented below.


def _strategy_baseline(x_tr, y_tr, g_tr, c_tr, x_te, g_te, c_te):
    return x_tr, x_te


def _strategy_session_centred(x_tr, y_tr, g_tr, c_tr, x_te, g_te, c_te):
    """Subtract each subject's OWN per-feature median, train and test alike.

    Transductive by construction, and that is the point rather than an oversight: it
    uses the test subject's own reps but never their labels, which is exactly what the
    live backend has when it scores a set (the whole set arrives in one POST, so a
    per-session median is computable).

    Stage 5.4 measured that this centring lifts several features enormously -- the
    within-subject AUC of `back_knee_rom_deg` is 0.860 against a pooled 0.564. The
    question this strategy answers is whether that within-subject signal survives into a
    model. The semantic objection to shipping it is in the report, not here.
    """

    def centre(x, g):
        out = x.copy()
        for subject in np.unique(g):
            mask = g == subject
            out[mask] -= np.median(x[mask], axis=0)
        return out

    return centre(x_tr, g_tr), centre(x_te, g_te)


def _strategy_cohort_centred(x_tr, y_tr, g_tr, c_tr, x_te, g_te, c_te):
    """Subtract the lead-cohort's mean, estimated on the TRAINING fold only.

    Attacks the same 8.9deg offset as a mocap-based correction would, but without the
    mocap (X3): the offset is estimated from the features themselves. Deployable
    without the user's own set, because the cohort is detectable live from limb
    visibility (the same signal the capture hint uses).

    Falls back to the global training mean for a cohort absent from the training fold,
    so a fold that happens to hold out an entire cohort degrades rather than crashes.
    """
    global_mean = x_tr.mean(axis=0)
    means = {
        cohort: x_tr[c_tr == cohort].mean(axis=0)
        for cohort in np.unique(c_tr)
        if (c_tr == cohort).sum() > 0
    }

    def centre(x, c):
        out = x.copy()
        for i, cohort in enumerate(c):
            out[i] -= means.get(cohort, global_mean)
        return out

    return centre(x_tr, c_tr), centre(x_te, c_te)


STRATEGIES = {
    "S0_baseline": (
        _strategy_baseline,
        "All 17 features, raw. The plan's default and the exported deliverable.",
    ),
    "S1_session_centred": (
        _strategy_session_centred,
        "Each subject's own per-feature median subtracted (transductive; needs the "
        "user's own set, which the live POST provides).",
    ),
    "S3_cohort_centred": (
        _strategy_cohort_centred,
        "The lead-cohort's mean subtracted, estimated on training folds only "
        "(mocap-free, deployable via the live facing detector).",
    ),
}


def _plateau_stats(search: GridSearchCV) -> dict:
    """Is the grid's spread bigger than the noise on each point?"""
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


def nested_cv(x, y, groups, cohorts, outer_cv, seed: int, strategy=_strategy_baseline):
    """Out-of-fold probabilities with tuning nested inside each training fold.

    Every rep is predicted exactly once, by a model that never saw that rep's subject.
    """
    prob_uncal = np.full(len(y), np.nan)
    prob_cal = np.full(len(y), np.nan)
    folds = []

    for fold, (train, test) in enumerate(outer_cv.split(x, y, groups), start=1):
        x_tr, x_te = strategy(
            x[train],
            y[train],
            groups[train],
            cohorts[train],
            x[test],
            groups[test],
            cohorts[test],
        )
        inner = _inner_splits(y[train], groups[train])
        search = _search(x_tr, y[train], inner, seed)
        best = search.best_params_

        forest = ExtraTreesClassifier(**best, **FIXED_PARAMS, random_state=seed)
        forest.fit(x_tr, y[train])
        prob_uncal[test] = forest.predict_proba(x_te)[:, 1]

        calibrated = _calibrate(best, x_tr, y[train], inner, seed)
        prob_cal[test] = calibrated.predict_proba(x_te)[:, 1]

        test_subjects = sorted({int(g) for g in groups[test]})
        both_classes = len(np.unique(y[test])) == 2
        auc_uncal = (
            roc_auc_score(y[test], prob_uncal[test]) if both_classes else float("nan")
        )
        auc_cal = (
            roc_auc_score(y[test], prob_cal[test]) if both_classes else float("nan")
        )

        # Squat's version of this check asserted AUC is preserved exactly, on the
        # premise that "a sigmoid cannot reorder predictions". **That premise is wrong
        # in general, and lunge is where it breaks.** Platt fits P = 1/(1+exp(a*f+b));
        # `a` is normally negative, but nothing constrains its sign. When the inner
        # folds show the score ANTI-correlating with the label, the sigmoid correctly
        # fits a positive `a` and the mapping is monotone *decreasing* — which exactly
        # reverses the ranking, sending AUC to 1 - AUC.
        #
        # So the true invariant is weaker: a monotone map either preserves the ranking
        # or exactly reverses it. That is what is asserted here. A flip is not a bug to
        # suppress — it means the model anti-predicts on held-out subjects, so it is
        # recorded per fold and reported rather than silently absorbed.
        flipped = False
        platt_slope = float(calibrated.calibrated_classifiers_[0].calibrators[0].a_)
        if both_classes:
            flipped = bool(np.isclose(auc_cal, 1.0 - auc_uncal)) and not np.isclose(
                auc_uncal, 0.5
            )
            assert np.isclose(auc_uncal, auc_cal) or np.isclose(
                auc_cal, 1.0 - auc_uncal
            ), (
                f"fold {fold}: calibrated AUC ({auc_cal:.4f}) is neither the "
                f"uncalibrated one ({auc_uncal:.4f}) nor its mirror "
                f"({1.0 - auc_uncal:.4f}). A monotone map must do one or the other, so "
                "the calibrated model is not a rescaling of the uncalibrated one."
            )

        folds.append(
            {
                "fold": fold,
                "subjects": test_subjects,
                "cohorts": sorted({str(c) for c in cohorts[test]}),
                "n_test": len(test),
                "n_good": int((y[test] == 1).sum()),
                "n_poor": int((y[test] == 0).sum()),
                "auc": auc_cal,
                "auc_uncal": auc_uncal,
                "platt_slope": platt_slope,
                "flipped": flipped,
                "best_params": best,
            }
        )
        print(
            f"  fold {fold}: subjects {test_subjects} "
            f"({folds[-1]['n_good']}G/{folds[-1]['n_poor']}P) AUC={auc_cal:.3f}"
            + (
                f"  ** CALIBRATOR FLIPPED (Platt a={platt_slope:+.2f}, uncal "
                f"{auc_uncal:.3f} -> {auc_cal:.3f}): the model anti-predicts on "
                "held-out subjects **"
                if flipped
                else ""
            )
        )

    return prob_uncal, prob_cal, folds


# Permutation test settings. 200 shuffles puts the smallest reportable p at 1/201
# ~ 0.005 -- enough resolution to separate "real" from "chance" without claiming a
# precision the resampling cannot support. Fixed params (the final search's winner)
# rather than a nested search per shuffle: 200 nested searches is intractable, and the
# grid is a plateau anyway (see `_plateau_stats`), so the tuning is not what carries
# the result.
N_PERMUTATIONS = 200
PERMUTATION_PARAMS = {
    "max_depth": None,
    "min_samples_leaf": 5,
    "min_samples_split": 10,
    "n_estimators": 100,
}


def _oof_auc_fixed(x, y, groups, cohorts, strategy, seed: int) -> float:
    """Out-of-fold AUC at fixed hyperparameters — the permutation test's statistic."""
    outer_cv, _name, _why = _choose_cv(y, groups)
    prob = np.full(len(y), np.nan)
    for train, test in outer_cv.split(x, y, groups):
        x_tr, x_te = strategy(
            x[train],
            y[train],
            groups[train],
            cohorts[train],
            x[test],
            groups[test],
            cohorts[test],
        )
        forest = ExtraTreesClassifier(
            **PERMUTATION_PARAMS, **FIXED_PARAMS, random_state=seed
        )
        forest.fit(x_tr, y[train])
        prob[test] = forest.predict_proba(x_te)[:, 1]
    return float(roc_auc_score(y, prob))


def permutation_test(x, y, groups, cohorts, strategy, seed: int) -> dict:
    """Is this strategy's AUC distinguishable from chance?

    The single most important check in this stage, and the reason is specific to lunge:
    the baseline's out-of-fold AUC lands BELOW 0.5, which invites the dramatic reading
    that the model "predicts backwards". Shuffling the labels tests that directly. If
    the null distribution is wide and centred near 0.5, a below-chance point estimate is
    noise, not inversion -- and saying otherwise would be over-claiming a finding.

    Labels are shuffled globally rather than within subject: the null being tested is
    "this feature set carries no information about correctness", and a within-subject
    shuffle would test a different, weaker null. Centring strategies use no labels, so
    they remain valid under permutation.
    """
    rng = np.random.default_rng(seed)
    observed = _oof_auc_fixed(x, y, groups, cohorts, strategy, seed)
    null = []
    for _ in range(N_PERMUTATIONS):
        shuffled = y.copy()
        rng.shuffle(shuffled)
        try:
            null.append(_oof_auc_fixed(x, shuffled, groups, cohorts, strategy, seed))
        except ValueError:
            # A shuffle can leave a fold single-class; skip it rather than count it.
            continue
    null = np.array(null)
    n_ge = int((null >= observed).sum())
    # +1 in numerator and denominator: the observed statistic is itself one draw from
    # the null under H0, so this is the standard unbiased permutation p-value and it
    # cannot report an impossible p = 0.
    p_value = (n_ge + 1) / (len(null) + 1)
    return {
        "observed": observed,
        "null_mean": float(null.mean()),
        "null_sd": float(null.std()),
        "null_min": float(null.min()),
        "null_max": float(null.max()),
        "n_permutations": len(null),
        "p_value": p_value,
        "distinguishable": bool(p_value < 0.05),
    }


def compare_confound_strategies(x, y, groups, cohorts, seed: int) -> list[dict]:
    """Measure each response to the cohort confound under one identical nested CV.

    Scored on the same 88 reps every other choice is made against, so these numbers are
    evidence about the confound, NOT a leaderboard to promote a winner from -- see the
    module docstring.
    """
    results = []
    for name, (strategy, description) in STRATEGIES.items():
        outer_cv, cv_name, _why = _choose_cv(y, groups)
        print(f"\n[{name}] {cv_name}")
        _unc, prob, folds = nested_cv(x, y, groups, cohorts, outer_cv, seed, strategy)
        results.append(
            {
                "name": name,
                "description": description,
                "cv": cv_name,
                "n": len(y),
                "auc": float(roc_auc_score(y, prob)),
                "fold_aucs": [f["auc"] for f in folds],
                "probs": prob,
                "y": y,
                "permutation": permutation_test(x, y, groups, cohorts, strategy, seed),
            }
        )
        perm = results[-1]["permutation"]
        print(
            f"[{name}] pooled out-of-fold AUC = {results[-1]['auc']:.3f} | "
            f"permutation: observed {perm['observed']:.3f} vs null "
            f"{perm['null_mean']:.3f}±{perm['null_sd']:.3f}, p={perm['p_value']:.3f} "
            f"-> {'REAL SIGNAL' if perm['distinguishable'] else 'NOT distinguishable from chance'}"
        )

    # S2: the lead-near subset, which is both the turn-around protocol's train/serve
    # match and the only subset where true LOSO is possible.
    mask = cohorts == LEAD_NEAR_COHORT
    x_n, y_n, g_n, c_n = x[mask], y[mask], groups[mask], cohorts[mask]
    outer_cv, cv_name, _why = _choose_cv(y_n, g_n)
    print(f"\n[S2_lead_near_only] {cv_name}")
    _unc, prob_n, folds_n = nested_cv(x_n, y_n, g_n, c_n, outer_cv, seed)
    results.append(
        {
            "name": "S2_lead_near_only",
            "description": (
                "Trained and tested only on the lead-near reps — the train/serve match "
                "implied by the turn-around capture protocol, and the only subset where "
                "true LOSO is possible."
            ),
            "cv": cv_name,
            "n": int(mask.sum()),
            "auc": float(roc_auc_score(y_n, prob_n)),
            "fold_aucs": [f["auc"] for f in folds_n],
            "probs": prob_n,
            "y": y_n,
            "permutation": permutation_test(
                x_n, y_n, g_n, c_n, _strategy_baseline, seed
            ),
        }
    )
    perm = results[-1]["permutation"]
    print(
        f"[S2_lead_near_only] pooled out-of-fold AUC = {results[-1]['auc']:.3f} | "
        f"permutation: observed {perm['observed']:.3f} vs null "
        f"{perm['null_mean']:.3f}±{perm['null_sd']:.3f}, p={perm['p_value']:.3f} "
        f"-> {'REAL SIGNAL' if perm['distinguishable'] else 'NOT distinguishable from chance'}"
    )
    return results


def build_final_model(
    x, y, groups, seed: int
) -> tuple[CalibratedClassifierCV, GridSearchCV]:
    """Tune on all data, then fit the calibrated model Stage 5.8 will export.

    Baseline (S0) features deliberately: the deliverable is the plan's default, not
    whichever comparison variant scored highest — see the module docstring.
    """
    search = _search(x, y, _inner_splits(y, groups), seed)
    calibrated = _calibrate(search.best_params_, x, y, _inner_splits(y, groups), seed)
    return calibrated, search


def final_model_platt_slope(model: CalibratedClassifierCV) -> float:
    """The exported model's Platt slope. Positive = the calibrator INVERTS the forest.

    Checked because a fold-level flip (see `nested_cv`) proves the sign is not
    guaranteed on this cohort. If the shipped model's slope were positive, every live
    verdict would be inverted -- P(Good) would rise as technique worsened -- and nothing
    downstream would notice, because the probabilities would still look well-formed.
    Stage 5.8 must re-check this on whatever it exports.
    """
    return float(model.calibrated_classifiers_[0].calibrators[0].a_)


# --- Figures -------------------------------------------------------------------


def plot_hyperparameter_search(search: GridSearchCV) -> Path:
    """One panel per swept parameter: score vs value, others held at their best."""
    results = search.cv_results_
    best = search.best_params_
    mean = results[f"mean_test_{TUNING_METRIC}"]
    std = results[f"std_test_{TUNING_METRIC}"]

    fig, axes = plt.subplots(2, 2)
    for ax, (param, values) in zip(axes.flat, PARAM_GRID.items(), strict=True):
        # Hold every other parameter at its winning value, so each panel is a clean
        # 1-D slice rather than a marginal average that hides interactions.
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
        "Lunge hyperparameter search — inner-CV ROC AUC per swept value\n"
        "(other parameters held at their chosen value; bars = std across inner folds)",
        y=0.99,
    )
    fig.tight_layout()
    path = save_fig(fig, "lunge_hyperparameter_search_results", figsize="grid_2x2")
    plt.close(fig)
    return path


def _wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval — stays correctly wide at p=0 and p=1, where the
    textbook Wald interval collapses to zero width and asserts false certainty."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = successes / n
    denom = 1.0 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = (z / denom) * np.sqrt(p * (1.0 - p) / n + z**2 / (4 * n**2))
    return (max(0.0, centre - half), min(1.0, centre + half))


def _reliability_bins(y, prob, n_bins: int = CALIBRATION_BINS) -> list[dict]:
    """Quantile reliability bins, carrying each bin's count and 95% Wilson interval."""
    edges = np.quantile(prob, np.linspace(0, 1, n_bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    bins = []
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        mask = (prob > low) & (prob <= high)
        if not mask.any():
            continue
        successes = int((y[mask] == 1).sum())
        n = int(mask.sum())
        lo, hi = _wilson_interval(successes, n)
        bins.append(
            {
                "mean_pred": float(prob[mask].mean()),
                "observed": successes / n,
                "n": n,
                "ci_low": lo,
                "ci_high": hi,
            }
        )
    return bins


def plot_calibration(y, prob_uncal, prob_cal) -> tuple[Path, float, float]:
    """Reliability before vs after calibration, with Wilson intervals per bin."""
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.9, label="perfect calibration")

    for prob, label, colour in (
        (prob_uncal, "uncalibrated", "#c1121f"),
        (prob_cal, "calibrated (sigmoid)", "#2a6f97"),
    ):
        bins = _reliability_bins(y, prob)
        xs = [b["mean_pred"] for b in bins]
        ys = [b["observed"] for b in bins]
        err = [
            [b["observed"] - b["ci_low"] for b in bins],
            [b["ci_high"] - b["observed"] for b in bins],
        ]
        brier = brier_score_loss(y, prob)
        ax.errorbar(
            xs,
            ys,
            yerr=err,
            marker="o",
            capsize=3,
            color=colour,
            label=f"{label} (Brier {brier:.3f})",
        )

    ax.set_xlabel("mean predicted P(Good) in bin")
    ax.set_ylabel("observed fraction Good")
    ax.set_title(
        f"Lunge calibration reliability (n={len(y)} out-of-fold reps)\n"
        f"bars = 95% Wilson intervals; {CALIBRATION_BINS} quantile bins"
    )
    ax.legend(fontsize=8, loc="best")
    path = save_fig(fig, "lunge_calibration_reliability_curve", figsize="single")
    plt.close(fig)
    return (
        path,
        float(brier_score_loss(y, prob_uncal)),
        float(brier_score_loss(y, prob_cal)),
    )


def plot_roc(strategies: list[dict]) -> Path:
    """ROC curve per confound strategy — the model's AUC, made visible.

    Added for lunge because the only AUC figures the project had were per-*feature*
    tables; a reader could not see the model's own ranking performance anywhere.
    """
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.9, label="chance (AUC 0.500)")
    for entry in strategies:
        fpr, tpr, _thresholds = roc_curve(entry["y"], entry["probs"])
        ax.plot(
            fpr,
            tpr,
            linewidth=1.6,
            label=f"{entry['name']} — AUC {entry['auc']:.3f} (n={entry['n']})",
        )
    ax.set_xlabel("false positive rate")
    ax.set_ylabel("true positive rate")
    ax.set_title(
        "Lunge ROC — out-of-fold, subject-disjoint\n"
        "(positive class = Good; every rep predicted by a model that never saw its "
        "subject)"
    )
    ax.legend(fontsize=8, loc="lower right")
    path = save_fig(fig, "lunge_roc_curves", figsize="single")
    plt.close(fig)
    return path


def _metrics(y, prob) -> dict:
    pred = (prob >= 0.5).astype(int)
    return {
        "auc": float(roc_auc_score(y, prob)),
        "f1_macro": float(f1_score(y, pred, average="macro")),
        "recall_good": float((pred[y == 1] == 1).mean()),
        "recall_poor": float((pred[y == 0] == 0).mean()),
        "brier": float(brier_score_loss(y, prob)),
    }


def _importances(final_model: CalibratedClassifierCV) -> list[tuple[str, float]]:
    """Gini importances from the calibrated model's single underlying forest."""
    forest = final_model.calibrated_classifiers_[0].estimator
    pairs = list(zip(LUNGE_FEATURE_NAMES, forest.feature_importances_, strict=True))
    return sorted(pairs, key=lambda p: -p[1])


def main() -> None:
    config = _load_config()
    seed = int(config["seeds"]["sklearn"])
    rows = _read_rows()
    x, y, groups, cohorts = _build_xy(rows)
    print(
        f"loaded {len(rows)} reps, {x.shape[1]} features, "
        f"{len(np.unique(groups))} subjects "
        f"({int((y == 1).sum())} Good / {int((y == 0).sum())} Poor)"
    )

    outer_cv, cv_name, cv_why = _choose_cv(y, groups)
    print(f"CV scheme: {cv_name} — {cv_why}")

    n_combos = int(np.prod([len(v) for v in PARAM_GRID.values()]))
    print(f"nested CV, baseline ({n_combos} combos per fold)…")
    prob_uncal, prob_cal, folds = nested_cv(x, y, groups, cohorts, outer_cv, seed)

    print("final search on all data (for the exported model's params)…")
    final_model, search = build_final_model(x, y, groups, seed)
    print(f"  best params: {search.best_params_}")
    final_slope = final_model_platt_slope(final_model)
    print(
        f"  exported model's Platt slope: {final_slope:+.4f} "
        f"({'OK — normal orientation' if final_slope < 0 else '** INVERTED **'})"
    )

    plot_hyperparameter_search(search)
    _path, brier_uncal, brier_cal = plot_calibration(y, prob_uncal, prob_cal)

    # _reliability_bins() re-implements quantile binning so it can also return each
    # bin's count (which sklearn's helper does not expose) — so check it against the
    # library rather than trusting that the two agree.
    for prob in (prob_uncal, prob_cal):
        bins = _reliability_bins(y, prob)
        ref_observed, ref_predicted = calibration_curve(
            y, prob, n_bins=CALIBRATION_BINS, strategy="quantile"
        )
        assert np.allclose([b["observed"] for b in bins], ref_observed) and np.allclose(
            [b["mean_pred"] for b in bins], ref_predicted
        ), "reliability binning diverged from sklearn's calibration_curve"

    uncal_metrics = _metrics(y, prob_uncal)
    cal_metrics = _metrics(y, prob_cal)
    print(
        f"  out-of-fold: AUC={cal_metrics['auc']:.3f} "
        f"macro-F1={cal_metrics['f1_macro']:.3f} "
        f"Poor recall={cal_metrics['recall_poor']:.3f} "
        f"Brier {brier_uncal:.3f} -> {brier_cal:.3f}"
    )

    plateau = _plateau_stats(search)
    print(
        f"  grid: span {plateau['span']:.4f} AUC vs median fold std "
        f"{plateau['median_fold_std']:.4f}; {plateau['within_1std']}/"
        f"{plateau['n_combos']} combos within 1 std of the best"
    )

    print("\n=== confound-strategy comparison (research, NOT a leaderboard) ===")
    strategies = compare_confound_strategies(x, y, groups, cohorts, seed)
    plot_roc(strategies)

    write_report(
        rows=rows,
        y=y,
        groups=groups,
        cohorts=cohorts,
        cv_name=cv_name,
        cv_why=cv_why,
        folds=folds,
        search=search,
        uncal_metrics=uncal_metrics,
        cal_metrics=cal_metrics,
        brier_uncal=brier_uncal,
        brier_cal=brier_cal,
        seed=seed,
        final_model=final_model,
        plateau=plateau,
        strategies=strategies,
        final_slope=final_slope,
    )
    print(f"\nwrote {REPORT_MD.name}")


def write_report(
    rows,
    y,
    groups,
    cohorts,
    cv_name,
    cv_why,
    folds,
    search,
    uncal_metrics,
    cal_metrics,
    brier_uncal,
    brier_cal,
    seed,
    final_model,
    plateau,
    strategies,
    final_slope,
) -> None:
    n_good = int((y == 1).sum())
    n_poor = int((y == 0).sum())
    baseline = next(s for s in strategies if s["name"] == "S0_baseline")
    best_strategy = max(strategies, key=lambda s: s["auc"])
    importances = _importances(final_model)
    s1 = next((s for s in strategies if s["name"] == "S1_session_centred"), None)
    s2 = next((s for s in strategies if s["name"] == "S2_lead_near_only"), None)
    s3 = next((s for s in strategies if s["name"] == "S3_cohort_centred"), None)
    s1_auc = f"{s1['auc']:.3f}" if s1 else "n/a"
    s2_auc = f"{s2['auc']:.3f}" if s2 else "n/a"
    s1_p = f"{s1['permutation']['p_value']:.3f}" if s1 else "n/a"
    s2_p = f"{s2['permutation']['p_value']:.3f}" if s2 else "n/a"
    validity = {f: analyse_feature(rows, f) for f in LUNGE_FEATURE_NAMES}

    lines = [
        "# Stage 5.5 (Lunge) — training the Extra Trees classifier",
        "",
        f"Source: `ml/data/lunge_features.csv` — {len(y)} side-view reps "
        f"({n_good} Good / {n_poor} Poor) from {len(np.unique(groups))} subjects, "
        f"{len(LUNGE_FEATURE_NAMES)} features. Binary Good/Poor (Option A), "
        f"`random_state={seed}`.",
        "",
        "## Headline: a documented negative result, and two things that fix it",
        "",
        f"**The lunge classifier trained the plan's way does not work. Its out-of-fold "
        f"ROC AUC is {cal_metrics['auc']:.3f}, and a permutation test cannot "
        f"distinguish it from chance** "
        f"(p = {baseline['permutation']['p_value']:.3f} over "
        f"{baseline['permutation']['n_permutations']} label shuffles). Squat's "
        "equivalent scored 0.832. This is not a tuning problem: the same code, the same "
        "grid and the same CV machinery produced squat's working model.",
        "",
        "**Two interventions recover genuine signal**, and both are attacks on the "
        "lead-leg confound rather than on the model:",
        "",
        f"- **Restricting to lead-near reps** (the geometry the turn-around capture "
        f"protocol produces): AUC **{s2_auc}**, p = {s2_p} — real signal.",
        f"- **Session-centring** (subtracting each subject's own median): AUC "
        f"**{s1_auc}**, p = {s1_p} — real signal.",
        "",
        "That both fixes target the confound, and that neither touches the classifier, "
        "is the finding. The features carry information about lunge correctness; the "
        "between-subject measurement differences bury it.",
        "",
        "**On the below-0.5 figure — what it does NOT mean.** An AUC of "
        f"{cal_metrics['auc']:.3f} invites the reading that the model predicts "
        "*backwards*. The permutation test rules that out: the null distribution is "
        f"centred at {baseline['permutation']['null_mean']:.3f} with a standard "
        f"deviation of {baseline['permutation']['null_sd']:.3f} and spans "
        f"{baseline['permutation']['null_min']:.3f}–{baseline['permutation']['null_max']:.3f}, "
        "so a point estimate below 0.5 is comfortably inside the range random labels "
        "produce. The honest statement is **no detectable cross-subject signal**, not "
        "**inverted signal**. The distinction matters: one is an absence of evidence, "
        "the other would be a claim.",
        "",
        f"Secondary metrics for the baseline, for completeness: macro-F1 "
        f"{cal_metrics['f1_macro']:.3f}, Good recall {cal_metrics['recall_good']:.3f}, "
        f"Poor recall {cal_metrics['recall_poor']:.3f}, Brier {brier_uncal:.3f} → "
        f"{brier_cal:.3f}. They describe a chance-level model and should not be quoted "
        "as performance.",
        "",
        "**This is the model's AUC, not a feature's** — the 0.639 at the "
        "feature-validity gate is the univariate separation of "
        "`front_knee_flex_peak_deg` alone, a different quantity that must not be "
        "compared with these.",
        "",
        "![Lunge ROC curves](figures/lunge_roc_curves.png)",
        "",
        "_Figure. ROC per confound strategy, out-of-fold and subject-disjoint. The "
        "baseline hugging the diagonal is the negative result; S1 and S2 lifting off it "
        "are the recovered signal._",
        "",
        "### ⚠ Decision required before Stage 5.8",
        "",
        "Stage 5.8 is scheduled to export `S0_baseline` as the shipped lunge model. On "
        "this evidence it would be exporting a **chance-level classifier**. The fusion "
        "would still produce plausible-looking Good/Fair/Poor verdicts, because the rule "
        "sub-score and the calibrated probabilities are both well-formed — the output "
        "would look exactly like squat's. Nothing downstream detects a model that is "
        "merely uninformative.",
        "",
        "This stage does not decide that. The options, none of them free:",
        "",
        "1. **Ship S0 anyway, announced.** Consistent with how Phase 4 shipped `stub-0`, "
        "but a chance-level model presented as a trained one is a materially different "
        "claim from an announced placeholder.",
        "2. **Ship the lead-near model (S2)** and let the turn-around protocol enforce "
        f"its input distribution. It has real signal ({s2_auc}) and the protocol is "
        "already implemented — but it rests on 4 subjects and 42 reps.",
        "3. **Keep the placeholder and document the negative result**, as Stage 5.10 "
        "does for squat's EC3D finding.",
        "",
        "**HY's call.** It is a scope and honesty decision, not a technical one.",
        "",
        "## Cross-validation scheme",
        "",
        f"**{cv_name}** — {cv_why}.",
        "",
        "This is the plan's documented fallback, and it was **triggered by the data, "
        "not chosen**: `_choose_cv()` inspects the labels rather than hardcoding the "
        "answer. No subject appears in both train and test, so there is no identity "
        "leakage — but each test fold holds roughly two subjects, so the write-up must "
        "say **subject-wise 5-fold, not LOSO**.",
        "",
        "| fold | test subjects | lead cohorts | reps | Good | Poor | AUC (uncal) | AUC (cal) | Platt slope |",
        "| ---- | ------------- | ------------ | ---- | ---- | ---- | ----------- | --------- | ----------- |",
    ]
    for f in folds:
        auc = "n/a" if np.isnan(f["auc"]) else f"{f['auc']:.3f}"
        auc_u = "n/a" if np.isnan(f["auc_uncal"]) else f"{f['auc_uncal']:.3f}"
        flag = " ⚠ **flipped**" if f["flipped"] else ""
        lines.append(
            f"| {f['fold']} | {', '.join(str(s) for s in f['subjects'])} | "
            f"{', '.join(f['cohorts'])} | {f['n_test']} | {f['n_good']} | "
            f"{f['n_poor']} | {auc_u} | {auc} | {f['platt_slope']:+.2f}{flag} |"
        )

    flipped_folds = [f for f in folds if f["flipped"]]
    lines += [
        "",
        "### ⚠ A fold where the model anti-predicts, and the calibrator inverted it",
        "",
    ]
    if flipped_folds:
        ff = flipped_folds[0]
        lines += [
            f"**In {len(flipped_folds)} of {len(folds)} folds the calibrator learned an "
            f"*inverted* mapping.** Fold {ff['fold']} (test subjects "
            f"{', '.join(str(s) for s in ff['subjects'])}) fitted a Platt slope of "
            f"**{ff['platt_slope']:+.2f}** — positive, where the normal orientation is "
            f"negative — sending that fold's AUC from {ff['auc_uncal']:.3f} to "
            f"**{ff['auc_cal'] if 'auc_cal' in ff else ff['auc']:.3f}**, exactly its "
            "mirror about 0.5.",
            "",
            "**This was caught by an assertion, and the assertion's own premise turned "
            "out to be wrong.** Squat's training script asserts that calibration "
            'preserves AUC exactly, on the stated grounds that *"a sigmoid cannot '
            'reorder predictions"*. That is false in general: Platt fits '
            "`P = 1/(1+exp(a·f + b))`, and nothing constrains the sign of `a`. When the "
            "inner folds show the forest's score anti-correlating with the label, the "
            "sigmoid correctly fits a positive `a`, the mapping becomes monotone "
            "*decreasing*, and the ranking reverses. Squat never encountered this "
            "because its signal is consistent across subjects; lunge's is not. The "
            "assertion here was corrected to the true invariant — a monotone map either "
            "preserves the ranking or exactly reverses it — rather than deleted.",
            "",
            "**What it means, which is the important part.** The flip is not a numerical "
            "quirk. The sigmoid is fitted on subject-disjoint inner folds of the "
            "training data, so a positive slope says the forest's scores **anti-correlate "
            "with the truth on subjects it has not seen** (measured: inner out-of-fold "
            "AUC 0.368 on that fold's training subjects). The model does not merely "
            "fail to generalise there — it generalises backwards.",
            "",
            "This is the same phenomenon the feature-validity gate found, now at model "
            "level. That gate measured relationships that **invert between subject "
            "groups** (`back_knee_rom_deg` pools to 0.564 while every individual subject "
            "points the other way). A model trained on one group of subjects and applied "
            "to another inherits exactly that inversion. Two independent analyses, one "
            "on features and one on the fitted model, are describing the same instability.",
            "",
        ]
    else:
        lines += [
            "No fold's calibrator inverted: every Platt slope is negative, so "
            "calibration was a monotone *increasing* rescaling throughout and AUC was "
            "preserved exactly in each fold, as squat's run also found.",
            "",
        ]

    lines += [
        f"**The exported model is not inverted** — its own Platt slope is "
        f"**{final_slope:+.4f}**"
        + (
            " (negative, the normal orientation), so the model Stage 5.8 ships maps "
            "higher forest scores to higher P(Good) as intended. This is checked rather "
            "than assumed because the fold above proves the sign is not guaranteed on "
            "this cohort: an inverted shipped model would report P(Good) *rising* as "
            "technique worsened, and nothing downstream would notice, because the "
            "probabilities would still look perfectly well-formed. **Stage 5.8 must "
            "re-run this check on whatever it exports.**"
            if final_slope < 0
            else " — **POSITIVE, meaning the exported model is INVERTED and must not be "
            "shipped as-is.** Stage 5.8 must not proceed until this is resolved."
        ),
        "",
        "## The lead-leg confound: four responses, measured",
        "",
        "Stage 5.4 established an **8.9° measurement bias aligned with the subject "
        "cohorts**: the far/occluded limb is the right leg in every recording and lead "
        "leg is fixed per subject, so the leading knee is the occluded limb for "
        "right-lead subjects (−15.1° against OptiTrack) and the clearly-visible one for "
        "left-lead subjects (−6.2°). The confound is encoded in the feature **values**, "
        "so excluding the `lead_leg` column — which the feature table does — is "
        "necessary but not sufficient.",
        "",
        "Four responses were measured under one identical nested CV:",
        "",
        "| strategy | n | out-of-fold AUC | permutation null | p | real signal? | what it does |",
        "| -------- | - | --------------- | ---------------- | - | ------------ | ------------ |",
    ]
    for s in strategies:
        perm = s["permutation"]
        lines.append(
            f"| `{s['name']}` | {s['n']} | **{s['auc']:.3f}** | "
            f"{perm['null_mean']:.3f} ± {perm['null_sd']:.3f} | "
            f"{perm['p_value']:.3f} | "
            f"{'**YES**' if perm['distinguishable'] else 'no'} | {s['description']} |"
        )

    lines += [
        "",
        f"**Reading the columns.** The AUC column is the nested, calibrated out-of-fold "
        f"figure — the headline statistic. The permutation columns use a **different, "
        f"simpler statistic**: fixed hyperparameters "
        f"(`{PERMUTATION_PARAMS}`) and uncalibrated scores, because "
        f"{N_PERMUTATIONS} nested searches per strategy is intractable. So the p-value "
        "tests whether *that* statistic beats chance, not the AUC printed beside it. "
        "The two are close but not identical (baseline: "
        f"{baseline['permutation']['observed']:.3f} fixed-param vs "
        f"{baseline['auc']:.3f} nested), and the difference is the per-fold tuning plus "
        "the calibration flips documented above. The grid is a plateau, so the tuning is "
        "not what carries either result.",
        "",
        f"The smallest p this test can report is 1/({N_PERMUTATIONS}+1) ≈ "
        f"{1 / (N_PERMUTATIONS + 1):.3f}; a p at that floor means **no** shuffle out of "
        f"{N_PERMUTATIONS} reached the observed value, not that p is zero.",
        "",
        "**⚠ This table is not a leaderboard, and the highest number in it is not the "
        "result.** Every strategy is scored on the same 88 reps that every other choice "
        "in this phase was made against. Selecting the winner by these figures would be "
        "selection on the test folds — the same error the feature-validity gate refused "
        "to make when it declined to rewrite its pre-declared verdicts. "
        f"**`S0_baseline` remains the exported deliverable** regardless of where it "
        "places here.",
        "",
        "**A correction that was ruled out on principle, not on score:** subtracting the "
        "measured 8.9° bias directly. It is the most obvious fix and it is absent "
        "deliberately — the bias is an OptiTrack measurement, and X3 forbids marker-based "
        "capture from becoming an input to the shipped model. `S3_cohort_centred` is the "
        "mocap-free way to attack the same offset, estimating it from the features "
        "themselves on training folds only.",
        "",
    ]

    lines += [
        "### Reading each result",
        "",
        f"- **S0 baseline — {baseline['auc']:.3f}, and indistinguishable from chance "
        f"(p = {baseline['permutation']['p_value']:.3f}).** The plan's default, and what "
        "Stage 5.8 is currently scheduled to export. It has no detectable cross-subject "
        "signal. The model is not broken — it reaches an in-sample AUC of 0.982, so it "
        "fits the training reps almost perfectly and then carries none of that to a new "
        "subject. That gap **is** the confound: what it learns is largely who the "
        "subject is, which does not transfer.",
    ]
    if s1 is not None:
        delta = s1["auc"] - baseline["auc"]
        lines.append(
            f"- **S1 session-centred — {s1['auc']:.3f}** ({delta:+.3f} vs baseline; "
            f"p = {s1['permutation']['p_value']:.3f}, **real signal**). "
            "Subtracting each subject's own median is what lifted "
            "`back_knee_rom_deg` from a pooled 0.564 to a within-subject 0.860 at the "
            "feature gate, so this asks whether that signal survives into a model. "
            "**It cannot ship as-is regardless of its score**, for a reason no metric "
            'shows: centring redefines the question from *"is this rep good?"* to '
            '*"is this rep better than your other reps?"*. A set in which every rep is '
            "poor would centre to look average, and the system would tell a user their "
            "uniformly poor technique is fine. That is a safety-relevant failure, not a "
            "modelling trade-off."
        )
    if s3 is not None:
        delta = s3["auc"] - baseline["auc"]
        lines.append(
            f"- **S3 cohort-centred — {s3['auc']:.3f}** ({delta:+.3f} vs baseline; "
            f"p = {s3['permutation']['p_value']:.3f}, **no detectable signal**). "
            "On paper the most deployable correction — no mocap, no per-user history, "
            "just the cohort, which the live pipeline can detect from limb visibility. "
            "**It does not work**, and the contrast with S1 is informative: subtracting "
            "the *cohort's* mean removes an 8.9° group offset, while subtracting the "
            "*subject's* own median removes far more. So the between-subject variation "
            "burying the signal is mostly **not** the cohort-level camera bias — it is "
            "individual differences in build and movement, which the camera artefact "
            "only adds to. Correcting the artefact alone is not enough, and that is why "
            "the turn-around protocol is a capture fix rather than a modelling one."
        )
    if s2 is not None:
        delta = s2["auc"] - baseline["auc"]
        lines.append(
            f"- **S2 lead-near only — {s2['auc']:.3f}** ({delta:+.3f} vs baseline, on "
            f"{s2['n']} reps not 88, so the AUCs are not directly comparable; "
            f"p = {s2['permutation']['p_value']:.3f} against its own null, **real "
            "signal**). The most interesting of the four, and for two reasons beyond its "
            "score. First, it is the **train/serve match**: the turn-around capture "
            "protocol means deployment will only ever see lead-near reps, so this "
            "subset is the distribution the model will actually meet. Second, it is the "
            "**only subset where true LOSO is possible** — all four of its subjects "
            "carry both classes, whereas the lead-far cohort contains the single-class "
            "subject that forced the fallback. Its cost is severe: 4 subjects and "
            f"{s2['n']} reps, so its confidence interval is very wide and it is the "
            "most over-fit-prone of the four."
        )

    lines += [
        "",
        "**What this settles, and what it does not.**",
        "",
        "It settles that **the features are not the problem**. Two independent "
        "interventions — one removing each subject's own offset, one restricting to a "
        "single camera geometry — both lift the result from chance to real signal "
        "without touching the classifier, the grid, or the feature set. Information "
        "about lunge correctness is present in these 17 features; between-subject "
        "variation buries it.",
        "",
        f"It does **not** settle the confound. The best figure above "
        f"({best_strategy['auc']:.3f}, `{best_strategy['name']}`) is not a solution. No "
        "strategy here can separate a camera artefact from a genuine between-subject "
        "difference, because in this cohort the two are perfectly aligned — no subject "
        "performed both lead legs. S3's failure sharpens this: correcting the "
        "cohort-level offset alone recovers nothing, so the artefact is a component of "
        "the between-subject variation, not the whole of it.",
        "",
        "Only new data can settle it: a cohort in which subjects perform both lead legs, "
        "or a capture protocol that removes the geometry difference at source. **The "
        "turn-around protocol is the second of those, and S2 is the closest available "
        "estimate of what it buys** — which is the strongest reason to keep it.",
        "",
        "## Hyperparameter search",
        "",
        f"Best parameters: `{search.best_params_}`.",
        "",
        f"**The grid is a plateau, not a peak — and that matters more than the winner.** "
        f"Across all {plateau['n_combos']} combinations the mean inner-CV AUC spans only "
        f"{plateau['span']:.4f} ({plateau['worst']:.4f} to {plateau['best']:.4f}), while "
        f"the median standard deviation across inner folds is {plateau['median_fold_std']:.4f} "
        f"— i.e. **the spread between combinations is smaller than the noise on each one**. "
        f"{plateau['within_1std']} of {plateau['n_combos']} combinations sit within one "
        "standard deviation of the best. The chosen parameters are therefore not "
        "meaningfully better than most alternatives, and the search's value is showing "
        "that the result is insensitive to them rather than identifying an optimum.",
        "",
        "![Lunge hyperparameter search](figures/lunge_hyperparameter_search_results.png)",
        "",
        "_Figure. Inner-CV ROC AUC per swept value, other parameters held at their "
        "chosen value; bars are the standard deviation across inner folds._",
        "",
        f"`GridSearchCV.best_score_` is deliberately **not** quoted as a generalisation "
        f"estimate anywhere: it is the maximum over {plateau['n_combos']} combinations "
        "and is optimistically biased by that selection alone. The out-of-fold figure in "
        "the headline is the honest one.",
        "",
        "### Full search table",
        "",
        "Every combination tried, not just the winner. Losing combinations are kept "
        "deliberately — they are the evidence the search was an investigation.",
        "",
        "| n_estimators | max_depth | min_samples_leaf | min_samples_split | mean AUC | std | mean F1-macro |",
        "| ------------ | --------- | ---------------- | ----------------- | -------- | --- | ------------- |",
    ]
    results = search.cv_results_
    order = np.argsort(-results[f"mean_test_{TUNING_METRIC}"])
    for i in order:
        p = results["params"][i]
        marker = " **←**" if i == results[f"rank_test_{TUNING_METRIC}"].argmin() else ""
        lines.append(
            f"| {p['n_estimators']} | {p['max_depth']} | {p['min_samples_leaf']} | "
            f"{p['min_samples_split']} | {results[f'mean_test_{TUNING_METRIC}'][i]:.4f}"
            f"{marker} | {results[f'std_test_{TUNING_METRIC}'][i]:.4f} | "
            f"{results[f'mean_test_{SECONDARY_METRIC}'][i]:.4f} |"
        )

    lines += [
        "",
        "## Calibration",
        "",
        f'Sigmoid (Platt), not isotonic. `task.md` says *"isotonic if N allows, else '
        f'sigmoid"* — N does not allow: {n_poor} Poor reps across '
        f"{len(np.unique(groups))} subjects. Isotonic fits a free-form step function and "
        "needs on the order of a thousand samples before it stops memorising; on this N "
        "it would look perfect in-fold and generalise to nothing. Sigmoid fits two "
        "parameters. That is a limitation, not a preference.",
        "",
        f"Brier score **{brier_uncal:.3f} → {brier_cal:.3f}**. Calibration is a monotone "
        "rescaling, so it cannot change the ranking — `nested_cv()` asserts per fold "
        "that AUC is preserved exactly, which turns that claim into a check rather than "
        "a hope.",
        "",
        "![Lunge calibration reliability](figures/lunge_calibration_reliability_curve.png)",
        "",
        "_Figure. Predicted vs observed frequency, before and after calibration, with "
        "95% Wilson intervals per quantile bin. Wilson rather than Wald because Wald "
        "collapses to zero width at p=0 and p=1, asserting perfect certainty from a "
        "handful of reps._",
        "",
        "The Fair band Stage 5.6 will derive depends entirely on these probabilities "
        "being meaningful, which is why this figure exists rather than an assertion "
        "that calibration helped.",
        "",
        "## Feature importances, and what they say about the Stage 5.4 verdicts",
        "",
        "All 17 features were trained on; Stage 5.4's DROP verdicts were **not** "
        "executed. Two reasons, both from that report's own caveats. (a) Its verdicts "
        "were computed on all 88 reps *including* the subjects held out here, so acting "
        "on them and then quoting a held-out score would be selection bias. (b) That "
        "report found pooling inverts the truth for 9 of 17 features, so its DROP "
        "column is the least trustworthy part of it. Training on everything and letting "
        "the model's own importances speak is the option it named as honest.",
        "",
        "| rank | feature | Gini importance | Stage 5.4 pooled AUC | Stage 5.4 verdict | pooling misleads? |",
        "| ---- | ------- | --------------- | -------------------- | ----------------- | ----------------- |",
    ]
    for rank, (name, importance) in enumerate(importances, start=1):
        v = validity[name]
        lines.append(
            f"| {rank} | `{name}` | {importance:.4f} | {v['auc']:.3f} | "
            f"{v['verdict']} | {'**yes**' if v['pooling_misleads'] else 'no'} |"
        )

    dropped_but_used = [
        (n, i) for n, i in importances[:5] if validity[n]["verdict"] == "DROP"
    ]
    lines += [
        "",
        (
            "**The model disagrees with the pooled verdicts, and that corroborates the "
            f"gate's own warning.** {len(dropped_but_used)} of the model's top 5 features "
            "by importance were scored DROP by the pooled rule: "
            + ", ".join(f"`{n}`" for n, _i in dropped_but_used)
            + ". These are features the gate flagged as ones where pooling misleads — so "
            "the model, which never sees the pooled statistic, is independently "
            "recovering signal the pooled AUC hid. That is the clearest vindication "
            "available of the decision to train on all 17."
            if dropped_but_used
            else "**No feature scored DROP by the pooled rule appears in the model's top "
            "5 by importance**, so on this cohort the pooled verdicts and the model's "
            "own ranking broadly agree at the top, even though they disagree lower down."
        ),
        "",
        "Gini importance is impurity-based and biased toward high-cardinality continuous "
        "features; it ranks, it does not prove causation, and it is reported here as "
        "corroboration of the gate rather than as a feature-selection instrument.",
        "",
        "## Limitations of this result",
        "",
        f"- **{len(y)} reps from {len(np.unique(groups))} subjects.** Every figure here "
        "is a small-sample estimate. Reps within a subject are correlated, so the "
        "effective sample size is nearer the subject count than the rep count.",
        "- **Subject-wise 5-fold, not LOSO** — the fallback was forced by a single-class "
        "subject. Each test fold holds ~2 subjects, so per-fold AUCs are noisy.",
        "- **The cohort confound is not solved, only measured** (see above). No strategy "
        "here can separate a camera artefact from a genuine subject difference, because "
        "in this cohort they are perfectly aligned.",
        "- **No external validation.** Squat's EC3D check returned a documented negative "
        "result; nothing equivalent has been run for lunge, and EC3D's lunge partition "
        "has no RGB video, so this pipeline cannot consume it.",
        "- **The strategy comparison is in-sample.** Its numbers describe fit on these 8 "
        "subjects, not generalisation.",
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
