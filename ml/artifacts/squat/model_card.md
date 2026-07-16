# Squat Model Card

**model_version:** `squat-1.0.0+rehab246-loso-3c441ac.dirty`
**Exported:** Phase 5, Stage 5.8 (2026-07-16)
**Code state:** `3c441ac.dirty`

## Training data

REHAB24-6, side-view squat repetitions only (Ex6, `cam17_orientation="front"` per the
project's verified side-view mapping). **98 repetitions from 9
subjects** (72 Good, 26 Poor). Full dataset audit:
[DATA_AUDIT.md](../../reports/DATA_AUDIT.md). Feature construction:
[FEATURE_TABLE.md](../../reports/FEATURE_TABLE.md).

## Protocol

- **Model:** Extra Trees classifier (`bootstrap=False`, `class_weight="balanced"`,
  `max_features="sqrt"`), hyperparameters tuned via nested `GridSearchCV` over the R8
  grid (`n_estimators`, `max_depth`, `min_samples_leaf`, `min_samples_split`), tuning
  metric ROC AUC. Full grid and plateau analysis:
  [SQUAT_TRAINING_REPORT.md](../../reports/SQUAT_TRAINING_REPORT.md).
- **Cross-validation:** `StratifiedGroupKFold(5, groups=person_id)` (subject-grouped, not literal LOSO — three subjects
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
| ROC AUC | 0.8317 |
| Macro-F1 @ 0.5 | 0.6307 |
| Recall (Good) @ 0.5 | 0.8611 |
| Recall (Poor) @ 0.5 | 0.3846 |
| Brier score | 0.1487 |

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
  **0.2438** (confidence 0.7562,
  short of the 0.85 bar); among the 26 genuinely-Poor
  rows specifically, the most Poor-leaning prediction is P(Good) =
  **0.2438**, still not confident enough to
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
  [SQUAT_EVALUATION_REPORT.md](../../reports/SQUAT_EVALUATION_REPORT.md) §7.1.
- **Evaluated on REHAB24-6 only.** Stage 5.9's EC3D check is the first independent
  (never-trained-on) generalisation signal; treat this model as unvalidated outside
  REHAB24-6 until that report exists.
