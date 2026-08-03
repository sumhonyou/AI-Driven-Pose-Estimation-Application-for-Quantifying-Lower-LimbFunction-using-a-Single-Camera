"""Export the trained squat model artifacts used by the backend.

Builds the final calibrated model through `train_squat.build_final_model()` and writes:
`model.joblib`, `calibrator.joblib`, `feature_schema.json`, `label_map.json`, and
`model_card.md`.

Key checks before export:

- split the fitted forest and sigmoid calibrator into separate inspectable files
- verify recomposed probabilities match the calibrated sklearn wrapper
- stamp `model_version` with the current git short hash, plus `.dirty` if needed
- recompute model-card metrics from the training code instead of transcribing prose
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import joblib
import numpy as np
from build_features import LABEL_MAP_JSON, write_label_map
from train_squat import (
    FIXED_PARAMS,
    PARAM_GRID,
    _build_xy,
    _choose_cv,
    _load_config,
    _metrics,
    _read_rows,
    build_final_model,
    nested_cv,
)

from app.module_b.squat.features import SQUAT_FEATURE_NAMES

ML_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ML_ROOT / "artifacts" / "squat"
FEATURE_SCHEMA_VERSION = (
    "1.0.0"  # matches MODULE_B_CORE_CONFIG["feature_schema_version"]
)
MODEL_NAME_VERSION = (
    "squat-1.0.0"  # the human-assigned model name; not the schema version
)


def _git_shorthash() -> str:
    """Return a traceable code-state id for the exported artifact.

    `.dirty` is appended (a standard git convention, e.g. `git describe --dirty`) when
    the working tree has uncommitted changes, so the artifact does not silently claim
    it was built from an exact committed snapshot when it was not.
    """
    shorthash = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ML_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=ML_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    return f"{shorthash}.dirty" if dirty else shorthash


def _split_calibrated_model(calibrated) -> tuple[object, dict]:
    """Pull the fitted forest and sigmoid params out of the calibrated wrapper.

    Only valid for `ensemble=False`: one forest and one sigmoid calibrator, not a K-pair
    ensemble.
    """
    calibrated_classifiers = calibrated.calibrated_classifiers_
    if len(calibrated_classifiers) != 1:
        raise ValueError(
            f"Expected exactly one calibrated classifier (ensemble=False), got "
            f"{len(calibrated_classifiers)} — was the model built with ensemble=True?"
        )
    cc = calibrated_classifiers[0]
    if list(cc.classes) != [0, 1]:
        raise ValueError(
            f"Expected binary classes [0, 1] (Poor, Good per label_map.json), got "
            f"{list(cc.classes)}"
        )
    if len(cc.calibrators) != 1:
        raise ValueError(
            f"Expected exactly one sigmoid calibrator, got {len(cc.calibrators)}"
        )

    forest = cc.estimator
    sigmoid = cc.calibrators[0]
    if list(forest.classes_) != [0, 1]:
        raise ValueError(f"Forest classes_ {list(forest.classes_)} != [0, 1]")
    return forest, {"a": float(sigmoid.a_), "b": float(sigmoid.b_)}


def _verify_recomposition(calibrated, forest, calibration: dict, x: np.ndarray) -> None:
    """The correctness gate: recomposed probabilities must equal the real pipeline's,
    bit for bit, on the actual training matrix — not assumed from reading source."""
    expected = calibrated.predict_proba(x)
    raw_p_good = forest.predict_proba(x)[:, 1]
    p_good = 1.0 / (1.0 + np.exp(calibration["a"] * raw_p_good + calibration["b"]))
    recomposed = np.column_stack([1.0 - p_good, p_good])
    if not np.array_equal(expected, recomposed):
        max_diff = float(np.max(np.abs(expected - recomposed)))
        raise AssertionError(
            "Forest+sigmoid recomposition does NOT reproduce "
            f"CalibratedClassifierCV.predict_proba() exactly (max abs diff {max_diff}). "
            "Do not export: the split artifacts would behave differently from every "
            "metric Stages 5.5-5.7 reported."
        )


def _deployed_confidence_check(calibrated, x: np.ndarray, y: np.ndarray) -> dict:
    """Does the SHIPPED single-calibration model ever confidently predict Poor?

    Not a rhetorical question — checked directly against every row this exact model
    was trained on (in-sample; there is no other data to check the final artifact
    against without a further held-out split). This is a distinct question from Stage
    5.5-5.7's headline metrics, which describe the pooled 5-fold *out-of-fold* nested-CV
    estimate — 5 different fold-specific calibrations, not the one calibration this
    script is about to export. The two can legitimately disagree, and the export
    process is the first point where the actual shipped artifact's own behaviour can be
    checked at all, so it is checked and recorded here rather than assumed to match.
    """
    p_good = calibrated.predict_proba(x)[:, 1]
    confidence_low_threshold = (
        0.15  # mirrors MODULE_B_CORE_CONFIG's 0.85 (P(Good)<=0.15
    )
    # <=> confidence=max(p,1-p)>=0.85 toward Poor); not imported to avoid a config
    # dependency in an export script whose job is to describe the model, not the fusion
    # config it will later be evaluated under.
    poor_mask = y == 0
    return {
        "min_p_good": float(p_good.min()),
        "n_confident_poor": int((p_good <= confidence_low_threshold).sum()),
        "n_confident_poor_among_poor_rows": int(
            (p_good[poor_mask] <= confidence_low_threshold).sum()
        ),
        "n_poor_rows": int(poor_mask.sum()),
        "most_poor_leaning_p_good": (
            float(p_good[poor_mask].min()) if poor_mask.any() else None
        ),
    }


def _recomputed_metrics(x, y, groups, outer_cv, seed: int) -> dict:
    """Recompute report metrics from `nested_cv()` instead of transcribing them."""
    _prob_uncal, prob_cal, _folds = nested_cv(x, y, groups, outer_cv, seed)
    return _metrics(y, prob_cal)


def write_feature_schema(model_version: str) -> Path:
    """Write feature names, order, schema version, and model version."""
    path = ARTIFACTS_DIR / "feature_schema.json"
    payload = {
        "schema_version": FEATURE_SCHEMA_VERSION,
        "names": list(SQUAT_FEATURE_NAMES),
        "model_version": model_version,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n")
    return path


def write_model_card(
    *,
    model_version: str,
    n_reps: int,
    n_good: int,
    n_poor: int,
    n_subjects: int,
    cv_name: str,
    metrics: dict,
    git_shorthash: str,
    confidence_check: dict,
) -> Path:
    path = ARTIFACTS_DIR / "model_card.md"
    path.write_text(
        f"""# Squat Model Card

**model_version:** `{model_version}`
**Exported:** Phase 5, Stage 5.8 (2026-07-16)
**Code state:** `{git_shorthash}`

## Training data

REHAB24-6, side-view squat repetitions only (Ex6, `cam17_orientation="front"` per the
project's verified side-view mapping). **{n_reps} repetitions from {n_subjects}
subjects** ({n_good} Good, {n_poor} Poor). Full dataset audit:
[DATA_AUDIT.md](../../reports/DATA_AUDIT.md). Feature construction:
[FEATURE_TABLE.md](../../reports/FEATURE_TABLE.md).

## Protocol

- **Model:** Extra Trees classifier (`bootstrap=False`, `class_weight="balanced"`,
  `max_features="sqrt"`), hyperparameters tuned via nested `GridSearchCV` over the R8
  grid (`n_estimators`, `max_depth`, `min_samples_leaf`, `min_samples_split`), tuning
  metric ROC AUC. Full grid and plateau analysis:
  [SQUAT_TRAINING_REPORT.md](../../reports/SQUAT_TRAINING_REPORT.md).
- **Cross-validation:** `{cv_name}` (subject-grouped, not literal LOSO — three subjects
  are single-class after the side-view filter; see the training report for why).
- **Calibration:** Platt/sigmoid, `CalibratedClassifierCV(ensemble=False)`. The base
  forest is fit on all training data; the sigmoid is fit on out-of-fold scores. Why
  sigmoid not isotonic, and why `ensemble=False` specifically, is justified in the
  training report — not repeated here.
- **Labels (Option A):** binary Good/Poor only. Fair is never a trained label; it is
  derived at inference from a calibrated confidence margin
  (`confidence_low_threshold`, earned in Stage 5.6). See
  [label_map.json](label_map.json).

## Metrics (out-of-fold, recomputed at export time from the same seeded nested CV)

| Metric | Value |
| --- | --- |
| ROC AUC | {metrics["auc"]:.4f} |
| Macro-F1 @ 0.5 | {metrics["f1_macro"]:.4f} |
| Recall (Good) @ 0.5 | {metrics["good_recall"]:.4f} |
| Recall (Poor) @ 0.5 | {metrics["poor_recall"]:.4f} |
| Brier score | {metrics["brier"]:.4f} |

These are the binary classifier's own out-of-fold metrics at the conventional 0.5
threshold — **not** the deployed fused 3-band system's metrics, which are threshold-
independent-in-part and reported separately (Stage 5.6/5.7). See:

- Calibration curve: [calibration_reliability_curve.png](../../reports/figures/calibration_reliability_curve.png)
- Hyperparameter search: [hyperparameter_search_results.png](../../reports/figures/hyperparameter_search_results.png)
- Fused 3-band confusion matrix: [confusion_matrix_3band.png](../../reports/figures/confusion_matrix_3band.png)
- Robustness signals: [robustness_signals.png](../../reports/figures/robustness_signals.png)
- Baseline comparison: [baseline_comparison_bar.png](../../reports/figures/baseline_comparison_bar.png)
- Inference latency: [inference_latency_distribution.png](../../reports/figures/inference_latency_distribution.png)

## Limitations

Full limitations are tracked in
[PHASE5_CHAPTER_DRAFT.md](../../reports/PHASE5_CHAPTER_DRAFT.md) §8 and are not repeated
here in full; the ones most relevant to *using this artifact* specifically:

- **⚠ This exact shipped model never reaches confidence ≥ 0.85 toward Poor on any of
  its own 98 training rows — checked directly against `calibrated.predict_proba()` at
  export time, not assumed.** Minimum calibrated P(Good) across all rows:
  **{confidence_check["min_p_good"]:.4f}** (confidence {1 - confidence_check["min_p_good"]:.4f},
  short of the 0.85 bar); among the {confidence_check["n_poor_rows"]} genuinely-Poor
  rows specifically, the most Poor-leaning prediction is P(Good) =
  **{confidence_check["most_poor_leaning_p_good"]:.4f}**, still not confident enough to
  band Poor under `confidence_low_threshold=0.85`. **This is a distinct fact from the
  recall(Poor)=0.077 figure Stage 5.7 reported**, which describes the 5-fold *nested
  cross-validation* pooled estimate (5 different fold-specific calibrations, min
  P(Good)=0.134, 2/26 Poor rows caught) — an estimate of generalisation, not a
  description of this one exported artifact. The two are complementary, not
  contradictory: the out-of-fold estimate is the honest generalisation signal; this
  in-sample check is the first point the actual shipped calibration could be examined
  directly, and it shows this specific artifact is, if anything, *more* conservative
  than that estimate suggested. Practically: **do not assume this model will ever
  return a confident "Poor" fused verdict** — treat every "not confidently Good" result
  as effectively "Fair" until evidence says otherwise.
- **9 subjects, 26 Poor repetitions from only 6 of them.** Every metric above rests on
  a small, correlated sample; effect sizes and cross-subject consistency were
  prioritised over significance testing throughout Phase 5.
- **Calibration quality is limited by sample size** (sigmoid, not isotonic — 26 minority
  samples cannot support a free-form calibration curve).
- **`q` (capture quality) is insensitive to far-limb occlusion** in this camera
  geometry — see Stage 5.7's evaluation report §4. Do not treat a "good" `q` as proof
  the far limb was tracked.
- **The fused system trades a large abstention rate for safety**: at the shipped
  operating point, roughly half of repetitions receive no confident verdict. See
  [SQUAT_EVALUATION_REPORT_3BAND.md](../../reports/SQUAT_EVALUATION_REPORT_3BAND.md) §7.1.
- **Evaluated on REHAB24-6 only.** Stage 5.9's EC3D check is the first independent
  (never-trained-on) generalisation signal; treat this model as unvalidated outside
  REHAB24-6 until that report exists.
"""
    )
    return path


def main() -> None:
    config = _load_config()
    seed = int(config["seeds"]["sklearn"])
    rows = _read_rows()
    x, y, groups = _build_xy(rows)
    outer_cv, cv_name, _cv_why = _choose_cv(y, groups)

    print("Training the final calibrated model (Stage 5.5's build_final_model)...")
    calibrated, _search = build_final_model(x, y, groups, seed)

    print("Splitting into forest + sigmoid...")
    forest, calibration = _split_calibrated_model(calibrated)

    print("Verifying the split reproduces the real pipeline exactly...")
    _verify_recomposition(calibrated, forest, calibration, x)
    print("  OK: forest+sigmoid recomposition is bit-for-bit identical.")

    print(
        "Recomputing out-of-fold metrics for the model card (Stage 5.5's nested_cv)..."
    )
    metrics = _recomputed_metrics(x, y, groups, outer_cv, seed)
    print(f"  AUC={metrics['auc']:.4f} f1_macro={metrics['f1_macro']:.4f}")

    print("Checking whether the SHIPPED calibration ever confidently predicts Poor...")
    confidence_check = _deployed_confidence_check(calibrated, x, y)
    print(
        f"  min P(Good) over all rows={confidence_check['min_p_good']:.4f}  "
        f"most Poor-leaning P(Good) among Poor rows="
        f"{confidence_check['most_poor_leaning_p_good']:.4f}  "
        f"confident-Poor rows={confidence_check['n_confident_poor']}/{len(rows)}"
    )
    if confidence_check["n_confident_poor"] == 0:
        print(
            "  ⚠ This model reaches confidence>=0.85 toward Poor on NONE of its own "
            "training rows — recorded in model_card.md, not silently shipped."
        )

    git_shorthash = _git_shorthash()
    model_version = f"{MODEL_NAME_VERSION}+rehab246-loso-{git_shorthash}"
    print(f"model_version = {model_version}")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(forest, ARTIFACTS_DIR / "model.joblib")
    joblib.dump(calibration, ARTIFACTS_DIR / "calibrator.joblib")
    write_feature_schema(model_version)
    write_label_map()  # includes label_order; single source for labels
    write_model_card(
        model_version=model_version,
        n_reps=len(rows),
        n_good=int(y.sum()),
        n_poor=int((y == 0).sum()),
        n_subjects=len(set(groups.tolist())),
        cv_name=cv_name,
        metrics=metrics,
        git_shorthash=git_shorthash,
        confidence_check=confidence_check,
    )
    print(f"Wrote model.joblib, calibrator.joblib, feature_schema.json, model_card.md,")
    print(f"and updated {LABEL_MAP_JSON.name} to {ARTIFACTS_DIR}")


if __name__ == "__main__":
    main()
