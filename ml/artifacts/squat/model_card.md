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
- **Labels (Option A):** binary Good/Poor only. Fair is never a trained label. See
  [label_map.json](label_map.json).
- **Deployed banding (revised 2026-07-19):** squat now ships a **committed binary
  Good/Poor** decision — the Fair abstention was removed for this exercise. The band is a
  single cut on the fused score (`decision_threshold=8.447974`, `w_rule=0` — the
  calibrated classifier alone), chosen for maximum macro-F1 on the out-of-fold
  predictions. This makes "Poor" reachable (out-of-fold recall 0.077 → 1.000) at the cost
  of flagging ~31% of correct repetitions; the zero-severe-error guarantee is
  deliberately relinquished. The model artifact is unchanged — this is a decision-policy
  change only. See
  [SQUAT_EVALUATION_REPORT_2BAND.md](../../reports/SQUAT_EVALUATION_REPORT_2BAND.md) and
  PHASE5_CHAPTER_DRAFT.md §8.5. "Poor" is displayed as "Needs Improvement" in the UI.
- **Interpretable fault gates (added Stage 5.12, 2026-07-19):** the model artifact is
  **unchanged**; three rule gates (insufficient depth / excessive forward lean / heel
  lift) run alongside it as a separate override layer. Any gate failing on any rep forces
  the band to Poor with a specific reason; only when all gates pass does the model's
  verdict decide. The gates are rule-only (none enters the feature vector), so no schema
  bump or retrain. Provenance and thresholds:
  [SQUAT_FAULT_GATE_ANALYSIS.md](../../reports/SQUAT_FAULT_GATE_ANALYSIS.md); the depth
  gate is a clinical floor, not learned, because this dataset's depth signal is inverted
  (see the limitations below and PHASE5_CHAPTER_DRAFT.md).

## Metrics (out-of-fold, recomputed at export time from the same seeded nested CV)

| Metric              | Value  |
| ------------------- | ------ |
| ROC AUC             | 0.8317 |
| Macro-F1 @ 0.5      | 0.6307 |
| Recall (Good) @ 0.5 | 0.8611 |
| Recall (Poor) @ 0.5 | 0.3846 |
| Brier score         | 0.1487 |

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
here in full; the ones most relevant to _using this artifact_ specifically:

- **⚠ This exact shipped model never reaches confidence ≥ 0.85 toward Poor on any of
  its own 98 training rows — checked directly against `calibrated.predict_proba()` at
  export time, not assumed.** Minimum calibrated P(Good) across all rows:
  **0.2438** (confidence 0.7562,
  short of the 0.85 bar); among the 26 genuinely-Poor
  rows specifically, the most Poor-leaning prediction is P(Good) =
  **0.2438**, still not confident enough to
  band Poor under `confidence_low_threshold=0.85`. **This is a distinct fact from the
  recall(Poor)=0.077 figure Stage 5.7 reported**, which describes the 5-fold _nested
  cross-validation_ pooled estimate (5 different fold-specific calibrations, min
  P(Good)=0.134, 2/26 Poor rows caught) — an estimate of generalisation, not a
  description of this one exported artifact. The two are complementary, not
  contradictory: the out-of-fold estimate is the honest generalisation signal; this
  in-sample check is the first point the actual shipped calibration could be examined
  directly, and it shows this specific artifact is, if anything, _more_ conservative
  than that estimate suggested. Practically: **do not assume this model will ever
  return a confident "Poor" fused verdict** under the old 0.85-confidence gate. (The
  committed binary deployment policy no longer uses that gate: it reaches the incorrect
  verdict via a score threshold instead — see the deployed-banding note above — which is
  precisely how "Poor" was made reachable.)
- **9 subjects, 26 Poor repetitions from only 6 of them.** Every metric above rests on
  a small, correlated sample; effect sizes and cross-subject consistency were
  prioritised over significance testing throughout Phase 5.
- **Calibration quality is limited by sample size** (sigmoid, not isotonic — 26 minority
  samples cannot support a free-form calibration curve).
- **`q` (capture quality) is insensitive to far-limb occlusion** in this camera
  geometry — see Stage 5.7's evaluation report §4. Do not treat a "good" `q` as proof
  the far limb was tracked.
- **The deployed squat verdict now commits rather than abstains** (see the
  deployed-banding note above): it trades the three-band system's zero-severe-error
  guarantee for coverage of the incorrect class. The historical 3-band abstention — still
  used by Module A and lunge — is documented in
  [SQUAT_EVALUATION_REPORT_3BAND.md](../../reports/SQUAT_EVALUATION_REPORT_3BAND.md) §7.1;
  the committed binary behaviour in
  [SQUAT_EVALUATION_REPORT_2BAND.md](../../reports/SQUAT_EVALUATION_REPORT_2BAND.md).
- **Evaluated on REHAB24-6 only.** Stage 5.9's EC3D check is the first independent
  (never-trained-on) generalisation signal; treat this model as unvalidated outside
  REHAB24-6 until that report exists.
