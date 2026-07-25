# Stage 5.12 Phase A — squat fault-gate measurement (depth / lean / heel-rise)

Measurement stage for the approved fault-gates plan (`agile-roaming-kurzweil.md`): adds interpretable rule checks for the faults HY observed directly in the REHAB24-6 videos (forward lean, heel rise) alongside a clinically-derived depth floor, so a rep can be told "Needs Improvement" **with a specific reason** instead of a single opaque ML number. This is a measurement report, not a code change — Phase B wires whatever is decided here into the backend.

---

## Table of Contents

- [1. Heel visibility census (go/no-go)](#1-heel-visibility-census-gono-go)
- [Verdict: GO](#verdict-go)
- [2. Heel-rise feature validity check](#2-heel-rise-feature-validity-check)
- [3. Threshold derivation](#3-threshold-derivation)
  - [Lean gate (data-driven)](#lean-gate-data-driven)
  - [Depth gate (clinical norm, NOT data-driven)](#depth-gate-clinical-norm-not-data-driven)
  - [Heel-rise gate (data-driven, since census was GO and validity was KEEP)](#heel-rise-gate-data-driven-since-census-was-go-and-validity-was-keep)
- [Summary](#summary)

---

## 1. Heel visibility census (go/no-go)

`MIN_VISIBILITY = 0.6` is the actual switch controlling whether `preprocess_world_landmarks` treats a landmark as missing and reconstructs it (gap-fill or hold-last-release) rather than measuring it -- so this census asks the question that actually matters for trusting a new heel-based feature, not an arbitrary bar. Measured on the **raw** stream: asking the preprocessed stream would ask the filter to grade its own homework. Depth is located via **bilateral knee flexion**, a quantity independent of heel position, so the at-depth window is not circular with anything heel-based.

**Pre-declared rule (fixed before the numbers were seen): GO requires the far heel's (landmark 30) reps-weighted mean visibility >= 0.6 AND at least 80% of reps keep the far heel's at-depth minimum visibility above that same line.**

| video  | far heel mean | near heel mean | far heel min | median at-depth min | reps below at depth |
| ------ | ------------- | -------------- | ------------ | ------------------- | ------------------- |
| PM_008 | 0.747         | 0.899          | 0.094        | 0.709               | 0/17                |
| PM_022 | 0.818         | 0.925          | 0.501        | 0.690               | 0/10                |
| PM_029 | 0.807         | 0.940          | 0.508        | 0.716               | 0/10                |
| PM_038 | 0.850         | 0.959          | 0.566        | 0.731               | 0/10                |
| PM_043 | 0.729         | 0.906          | 0.418        | 0.646               | 0/10                |
| PM_105 | 0.764         | 0.870          | 0.375        | 0.557               | 7/10                |
| PM_113 | 0.818         | 0.951          | 0.537        | 0.578               | 8/10                |
| PM_118 | 0.753         | 0.911          | 0.408        | 0.639               | 0/11                |
| PM_126 | 0.796         | 0.905          | 0.444        | 0.661               | 2/10                |

**Reps-weighted far-heel mean visibility: 0.784.** 17/98 reps (17.3%) drop the far heel below `MIN_VISIBILITY` at depth; 55/98 dip below it somewhere in the rep window.

## Verdict: **GO**

The far heel behaves like squat's far ankle (mostly above the line), not like the far knee (which sits below it for whole reps at a time). Heel-rise is measured below.

## 2. Heel-rise feature validity check

`heel_rise_peak_norm`: peak bilateral (toe_y - heel_y) rise from the rep's first frame, normalized by mean trunk_length over the rep (X1: squat's own `norm_ref_strategy`). Computed on the **preprocessed** stream, matching how every shipped feature is built (`build_features.py`). Run through `check_feature_validity.analyse_feature()` (X1) -- the identical KEEP/DROP method used for all 13 shipped features, same pre-declared thresholds (`AUC_KEEP_MARGIN=0.1`, `DIRECTION_CONSISTENCY_MIN=0.6`).

| feature               | Good median | Poor median | AUC   | direction   | subjects agreeing | p       | verdict  |
| --------------------- | ----------- | ----------- | ----- | ----------- | ----------------- | ------- | -------- |
| `heel_rise_peak_norm` | 0.0593      | 0.0866      | 0.714 | Poor higher | 3/5               | 0.00127 | **KEEP** |

**KEEP** -- separates (AUC 0.714, poor higher) and the direction holds in 3/5 subjects. Proceeding to threshold derivation below.

## 3. Threshold derivation

### Lean gate (data-driven)

`trunk_lean_peak_deg` already has a real KEEP verdict (AUC 0.762, "Poor higher", 3/5 subjects, `FEATURE_VALIDITY.md`) -- exactly the fault HY observed directly in the videos. Threshold: pooled Youden's-J-optimal cut (positive class = Poor), honesty-checked with a subject-grouped out-of-fold pass reusing `train_squat._choose_cv()` (X1) -- the same CV-selection logic (LOSO unless a subject is single-class) the real classifier is evaluated with.

- **Deployed threshold (pooled, all 98 reps): 41.424 deg.** In-sample sensitivity 0.731, specificity 0.736.
- **Out-of-fold honesty check** (StratifiedGroupKFold(5, groups=person_id); subjects 2, 4, 9 have reps of only one class, so LOSO would give them single-class test folds): per-fold thresholds [46.02, 41.74, 41.42, 41.42, 44.75], pooled out-of-fold sensitivity 0.538, specificity 0.750 (TP=14, FN=12, FP=18, TN=54).
- As with the model's own out-of-fold vs in-sample numbers (`model_card.md`), the in-sample threshold is what gets deployed; the out-of-fold figures are the honest generalisation estimate, not the same claim.

### Depth gate (clinical norm, NOT data-driven)

**REHAB24-6's own labels run the opposite direction for depth** -- Poor reps are measurably _deeper_ (`FEATURE_VALIDITY.md`: `knee_flex_peak_deg` AUC 0.837, Poor median 107.7 deg vs Good median 92.8 deg, 5/5 subjects agree). A "too-shallow" rule therefore cannot be learned from this dataset's own Good/Poor separation. It is instead derived from a fixed clinical minimum -- `SQUAT_CONFIG["rules"]["rom"]["parallel_start_deg"]` = 90.0 deg (a true-angle norm, tagged `[clinical norm, S1]`) -- adjusted for this pipeline's own measurement bias: `MOCAP_AGREEMENT.md` found the pipeline under-reads peak knee flexion by 11.96 deg vs OptiTrack (ICC 0.726, n=98). A true 90.0 deg parallel squat therefore reads as approximately **78.04 deg on this pipeline's own scale**.

- **Deployed threshold: 78.04 deg** -- gate fires if `knee_flex_peak_deg` never reaches this value during the rep ("insufficient depth").
- **Transparency check against REHAB24-6's own labels** (reported, not used to choose the threshold): applying this cut here would flag 0/26 Poor reps and 17/72 Good reps as insufficiently deep -- exactly the mismatch the inverted-depth finding predicts, since this dataset's Poor reps skew deeper, not shallower. This is expected and does not undermine the gate: REHAB24-6's "incorrect" reps are a mix of deliberate faults (this dataset does not include a "too-shallow" fault condition), not evidence about real-world shallow squats.

### Heel-rise gate (data-driven, since census was GO and validity was KEEP)

- **Deployed threshold (pooled): 0.0710 (normalized units).** In-sample sensitivity 0.846, specificity 0.625.
- **Out-of-fold honesty check** (StratifiedGroupKFold(5, groups=person_id)): pooled out-of-fold sensitivity 0.808, specificity 0.597.

## Summary

| gate      | provenance                    | deployed threshold               |
| --------- | ----------------------------- | -------------------------------- |
| lean      | [dataset-derived, Stage 5.12] | trunk_lean_peak_deg >= 41.42 deg |
| depth     | [clinical norm, Stage 5.12]   | knee_flex_peak_deg < 78.04 deg   |
| heel-rise | [dataset-derived, Stage 5.12] | heel_rise_peak_norm >= 0.0710    |

Next: Phase B wires these into `backend/app/module_b/squat/fault_gates.py` and `SQUAT_CONFIG["fault_gates"]`, per the approved plan.
