# Stage 5.5 — squat Extra Trees training report

Source: `ml/data/squat_features.csv` — 98 side-view reps (72 Good / 26 Poor) from 9 subjects. Binary Good/Poor (**Option A** — Fair is never a trained label; it is derived at inference from a calibrated confidence margin in Stage 5.6). `random_state=42` throughout, splitters `shuffle=False` — re-running reproduces this report byte-for-byte (X8).

---

## Table of Contents

- [Cross-validation scheme](#cross-validation-scheme)
- [Hyperparameter search](#hyperparameter-search)
  - [This search is a plateau, not a summit — and that is the result](#this-search-is-a-plateau-not-a-summit-and-that-is-the-result)
  - [Full cv_results_ (all combinations, unpruned)](#full-cvresults-all-combinations-unpruned)
- [Calibration](#calibration)
  - [What the figure actually shows — and it is weaker than the checklist hoped](#what-the-figure-actually-shows-and-it-is-weaker-than-the-checklist-hoped)
  - [The Poor-recall collapse — the finding Stage 5.6 must act on](#the-poor-recall-collapse-the-finding-stage-56-must-act-on)
- [Feature importances — the answer to Stage 5.4's open question](#feature-importances-the-answer-to-stage-54s-open-question)
  - [Two independent methods agree — which is the strongest result in this report](#two-independent-methods-agree-which-is-the-strongest-result-in-this-report)
  - [The redundant pair Stage 5.4 handed to this stage](#the-redundant-pair-stage-54-handed-to-this-stage)
- [Limitations of this training run](#limitations-of-this-training-run)
- [Deliberately not done here](#deliberately-not-done-here)

---

## Cross-validation scheme

**Used: `StratifiedGroupKFold(5, groups=person_id)`.**

`task.md` specifies Leave-One-Subject-Out, with a written fallback to stratified group k-fold if a subject has only one class. **The fallback condition is met:** subjects 2, 4, 9 have reps of only one class, so LOSO would give them single-class test folds.

Three of the nine subjects (2, 4, 9) performed only correct reps. Under LOSO their test folds would contain no Poor rep whatsoever, which does not merely weaken those folds — it makes ROC AUC and Poor-recall _undefined_ on them, so a third of the folds could not contribute the metrics this project cares about. `StratifiedGroupKFold` keeps the property that actually matters — **no subject appears in both train and test**, so there is no identity leakage — while ensuring every test fold contains both classes. The cost is honest and worth stating: each test fold now holds ~2 subjects rather than 1, so this is a subject-independent estimate but not literally a leave-_one_-out one. Any downstream claim should say 'subject-wise 5-fold', not 'LOSO'.

| fold | test subjects | Good | Poor | out-of-fold AUC |
| ---- | ------------- | ---- | ---- | --------------- |
| 1    | 1, 8          | 21   | 6    | 0.889           |
| 2    | 7, 9          | 16   | 5    | 0.887           |
| 3    | 2, 5          | 15   | 5    | 0.773           |
| 4    | 4, 6          | 15   | 5    | 0.893           |
| 5    | 3             | 5    | 5    | 1.000           |

**Imbalance handling: `class_weight='balanced'`, no SMOTE.** R8 is explicit, and the reason bites harder here than usual: synthetic minority samples would be interpolated _pose features_, which can be biomechanically impossible (a knee angle and a trunk lean that no real body can hold simultaneously). With 26 Poor reps drawn from only 6 subjects, SMOTE would also interpolate between reps of the same person and scatter near-duplicates of one subject across folds — leakage wearing a resampling costume.

## Hyperparameter search

**180 combinations**, tuned with `GridSearchCV` **inside the training folds only** (3 subject-disjoint inner folds). The full table is below — every combination tried, none pruned after the fact.

**Selection metric: ROC AUC, not F1 or precision.** Threshold metrics score a decision rule pinned at p=0.5, but Stage 5.6's entire job is to replace that threshold with a swept Fair band. Tuning on F1@0.5 would have optimised a rule this project is about to throw away. ROC AUC scores the probability _ranking_, which is what the calibration below and Stage 5.6's sweep both consume. `f1_macro` is recorded for every combination anyway, so the decision can be second-guessed from the table rather than taken on trust.

**Chosen: `{'max_depth': None, 'min_samples_leaf': 2, 'min_samples_split': 10, 'n_estimators': 500}`** (fixed by R8: `max_features='sqrt'`, `class_weight='balanced'`, `bootstrap=False`).

![Hyperparameter search results](figures/hyperparameter_search_results.png)

### This search is a plateau, not a summit — and that is the result

The numbers say the tuning did almost nothing, and that is worth more than a fabricated victory:

- The **entire grid** spans 0.0407 ROC AUC (best 0.9125, worst 0.8718) across all 180 combinations.
- The **median std across inner folds is 0.0455** — **larger than the whole grid's span.** The uncertainty on any single point exceeds the total difference between the best and worst settings.
- **163 of 180 combinations** fall within one std (0.0233) of the winner.

So the chosen combination is **statistically indistinguishable from most of the grid**. It is reported because R8 asked for the search and because the evidence of experimentation is the point — but the honest conclusion is that **Extra Trees is insensitive to these hyperparameters at this sample size**, not that these values are special. Do not present the winner as a tuned optimum in the write-up; present it as a plateau with a nominated point.

`max_depth` shows this most clearly, and mechanically. Its `None`/`12`/`16` rows score **identically to four decimal places** — not a coincidence: with `min_samples_split` >= 10 on 98 reps the trees stop growing on their own, reaching a mean depth of 7.5 and a maximum of 13, so only **1 tree in 500** ever exceeds depth 12 and the constraint essentially never activates. `max_depth=8` does bind (on ~24% of trees) and still moves mean AUC by 0.0005. The parameter is inert on data this small.

The winner also sits at the **edge of the R8 range for `n_estimators` (500 = the grid maximum)**, which would normally suggest testing beyond the range. It is not worth it here: more trees only reduce the variance of the ensemble's vote, and that variance is already far below the fold-to-fold noise above. The bottleneck is 98 reps from 9 subjects, not the forest size.

### Full `cv_results_` (all combinations, unpruned)

Ranked by mean inner-CV ROC AUC. `std` is across the inner folds.

| rank | n_estimators | max_depth | min_samples_leaf | min_samples_split | ROC AUC (std)  | macro-F1 |
| ---- | ------------ | --------- | ---------------- | ----------------- | -------------- | -------- |
| 1    | 500          | None      | 2                | 10                | 0.9125 (0.023) | 0.7293   |
| 1    | 500          | 12        | 2                | 10                | 0.9125 (0.023) | 0.7293   |
| 1    | 500          | 16        | 2                | 10                | 0.9125 (0.023) | 0.7293   |
| 4    | 400          | 8         | 2                | 20                | 0.9122 (0.035) | 0.7336   |
| 4    | 400          | None      | 2                | 20                | 0.9122 (0.035) | 0.7336   |
| 4    | 400          | 12        | 2                | 20                | 0.9122 (0.035) | 0.7336   |
| 4    | 400          | 16        | 2                | 20                | 0.9122 (0.035) | 0.7336   |
| 8    | 500          | 16        | 2                | 20                | 0.9110 (0.034) | 0.7336   |
| 8    | 500          | 8         | 2                | 20                | 0.9110 (0.034) | 0.7336   |
| 8    | 500          | None      | 2                | 20                | 0.9110 (0.034) | 0.7336   |
| 8    | 500          | 12        | 2                | 20                | 0.9110 (0.034) | 0.7336   |
| 12   | 300          | None      | 3                | 10                | 0.9107 (0.039) | 0.7447   |
| 12   | 300          | 16        | 3                | 10                | 0.9107 (0.039) | 0.7447   |
| 12   | 300          | 8         | 3                | 10                | 0.9107 (0.039) | 0.7447   |
| 12   | 300          | 12        | 3                | 10                | 0.9107 (0.039) | 0.7447   |
| 16   | 100          | 8         | 5                | 20                | 0.9102 (0.055) | 0.7447   |
| 16   | 100          | 12        | 5                | 20                | 0.9102 (0.055) | 0.7447   |
| 16   | 100          | None      | 5                | 20                | 0.9102 (0.055) | 0.7447   |
| 16   | 100          | 16        | 5                | 20                | 0.9102 (0.055) | 0.7447   |
| 20   | 300          | 8         | 5                | 20                | 0.9084 (0.051) | 0.7336   |
| 20   | 400          | None      | 5                | 20                | 0.9084 (0.051) | 0.7336   |
| 20   | 300          | None      | 5                | 20                | 0.9084 (0.051) | 0.7336   |
| 20   | 300          | 16        | 5                | 20                | 0.9084 (0.051) | 0.7336   |
| 20   | 300          | 12        | 5                | 20                | 0.9084 (0.051) | 0.7336   |
| 20   | 400          | 12        | 5                | 20                | 0.9084 (0.051) | 0.7336   |
| 20   | 400          | 16        | 5                | 20                | 0.9084 (0.051) | 0.7336   |
| 20   | 400          | 8         | 5                | 20                | 0.9084 (0.051) | 0.7336   |
| 28   | 400          | 8         | 3                | 10                | 0.9080 (0.038) | 0.7447   |
| 28   | 500          | 8         | 3                | 10                | 0.9080 (0.038) | 0.7332   |
| 28   | 500          | 16        | 3                | 10                | 0.9080 (0.038) | 0.7332   |
| 28   | 400          | None      | 3                | 10                | 0.9080 (0.038) | 0.7447   |
| 28   | 400          | 16        | 3                | 10                | 0.9080 (0.038) | 0.7447   |
| 28   | 400          | 12        | 3                | 10                | 0.9080 (0.038) | 0.7447   |
| 28   | 500          | 12        | 3                | 10                | 0.9080 (0.038) | 0.7332   |
| 28   | 500          | None      | 3                | 10                | 0.9080 (0.038) | 0.7332   |
| 36   | 200          | 12        | 5                | 20                | 0.9073 (0.050) | 0.7336   |
| 36   | 500          | 12        | 5                | 20                | 0.9073 (0.050) | 0.7336   |
| 36   | 200          | 16        | 5                | 20                | 0.9073 (0.050) | 0.7336   |
| 36   | 500          | None      | 5                | 20                | 0.9073 (0.050) | 0.7336   |
| 36   | 200          | 8         | 5                | 20                | 0.9073 (0.050) | 0.7336   |
| 36   | 500          | 8         | 5                | 20                | 0.9073 (0.050) | 0.7336   |
| 36   | 500          | 16        | 5                | 20                | 0.9073 (0.050) | 0.7336   |
| 36   | 200          | None      | 5                | 20                | 0.9073 (0.050) | 0.7336   |
| 44   | 300          | 12        | 3                | 20                | 0.9069 (0.042) | 0.7336   |
| 44   | 400          | 16        | 3                | 20                | 0.9069 (0.042) | 0.7336   |
| 44   | 400          | 8         | 3                | 20                | 0.9069 (0.042) | 0.7336   |
| 44   | 300          | 8         | 3                | 20                | 0.9069 (0.042) | 0.7336   |
| 44   | 300          | None      | 3                | 20                | 0.9069 (0.042) | 0.7336   |
| 44   | 400          | 12        | 3                | 20                | 0.9069 (0.042) | 0.7336   |
| 44   | 300          | 16        | 3                | 20                | 0.9069 (0.042) | 0.7336   |
| 44   | 400          | None      | 3                | 20                | 0.9069 (0.042) | 0.7336   |
| 52   | 100          | None      | 3                | 20                | 0.9066 (0.041) | 0.7447   |
| 52   | 100          | 16        | 3                | 20                | 0.9066 (0.041) | 0.7447   |
| 52   | 100          | 8         | 3                | 20                | 0.9066 (0.041) | 0.7447   |
| 52   | 100          | 12        | 3                | 20                | 0.9066 (0.041) | 0.7447   |
| 56   | 500          | 8         | 3                | 15                | 0.9065 (0.042) | 0.7336   |
| 56   | 500          | 16        | 3                | 15                | 0.9065 (0.042) | 0.7336   |
| 56   | 500          | None      | 3                | 15                | 0.9065 (0.042) | 0.7336   |
| 56   | 400          | None      | 3                | 15                | 0.9065 (0.042) | 0.7336   |
| 56   | 400          | 8         | 3                | 15                | 0.9065 (0.042) | 0.7336   |
| 56   | 400          | 12        | 3                | 15                | 0.9065 (0.042) | 0.7336   |
| 56   | 500          | 12        | 3                | 15                | 0.9065 (0.042) | 0.7336   |
| 56   | 400          | 16        | 3                | 15                | 0.9065 (0.042) | 0.7336   |
| 64   | 500          | 8         | 5                | 15                | 0.9060 (0.043) | 0.7336   |
| 64   | 500          | None      | 5                | 15                | 0.9060 (0.043) | 0.7336   |
| 64   | 500          | 12        | 5                | 15                | 0.9060 (0.043) | 0.7336   |
| 64   | 500          | 16        | 5                | 15                | 0.9060 (0.043) | 0.7336   |
| 68   | 300          | 16        | 5                | 15                | 0.9050 (0.047) | 0.7336   |
| 68   | 300          | 12        | 5                | 15                | 0.9050 (0.047) | 0.7336   |
| 68   | 300          | 8         | 5                | 15                | 0.9050 (0.047) | 0.7336   |
| 68   | 300          | None      | 5                | 15                | 0.9050 (0.047) | 0.7336   |
| 72   | 200          | 16        | 5                | 15                | 0.9045 (0.048) | 0.7336   |
| 72   | 400          | 8         | 5                | 15                | 0.9045 (0.048) | 0.7336   |
| 72   | 200          | 8         | 5                | 15                | 0.9045 (0.048) | 0.7336   |
| 72   | 400          | None      | 5                | 15                | 0.9045 (0.048) | 0.7336   |
| 72   | 200          | 12        | 5                | 15                | 0.9045 (0.048) | 0.7336   |
| 72   | 200          | None      | 5                | 15                | 0.9045 (0.048) | 0.7336   |
| 72   | 400          | 16        | 5                | 15                | 0.9045 (0.048) | 0.7336   |
| 72   | 400          | 12        | 5                | 15                | 0.9045 (0.048) | 0.7336   |
| 80   | 500          | 8         | 2                | 10                | 0.9045 (0.034) | 0.7293   |
| 81   | 400          | 16        | 2                | 10                | 0.9037 (0.041) | 0.7447   |
| 81   | 400          | None      | 2                | 10                | 0.9037 (0.041) | 0.7447   |
| 81   | 400          | 12        | 2                | 10                | 0.9037 (0.041) | 0.7447   |
| 84   | 200          | 16        | 3                | 15                | 0.9031 (0.050) | 0.7447   |
| 84   | 200          | 12        | 3                | 15                | 0.9031 (0.050) | 0.7447   |
| 84   | 200          | None      | 3                | 15                | 0.9031 (0.050) | 0.7447   |
| 87   | 200          | 12        | 3                | 10                | 0.9030 (0.045) | 0.7447   |
| 87   | 200          | None      | 3                | 10                | 0.9030 (0.045) | 0.7447   |
| 87   | 200          | 16        | 3                | 10                | 0.9030 (0.045) | 0.7447   |
| 90   | 400          | 8         | 5                | 10                | 0.9022 (0.045) | 0.7336   |
| 90   | 400          | 16        | 5                | 10                | 0.9022 (0.045) | 0.7336   |
| 90   | 500          | None      | 5                | 10                | 0.9022 (0.045) | 0.7336   |
| 90   | 500          | 16        | 5                | 10                | 0.9022 (0.045) | 0.7336   |
| 90   | 500          | 12        | 5                | 10                | 0.9022 (0.045) | 0.7336   |
| 90   | 400          | 12        | 5                | 10                | 0.9022 (0.045) | 0.7336   |
| 90   | 400          | None      | 5                | 10                | 0.9022 (0.045) | 0.7336   |
| 90   | 500          | 8         | 5                | 10                | 0.9022 (0.045) | 0.7336   |
| 98   | 200          | 8         | 3                | 15                | 0.9020 (0.050) | 0.7447   |
| 99   | 300          | 8         | 2                | 20                | 0.9019 (0.044) | 0.7447   |
| 99   | 200          | 8         | 3                | 10                | 0.9019 (0.044) | 0.7447   |
| 99   | 100          | None      | 3                | 10                | 0.9019 (0.044) | 0.7012   |
| 99   | 100          | 12        | 3                | 10                | 0.9019 (0.044) | 0.7012   |
| 99   | 100          | 8         | 3                | 10                | 0.9019 (0.044) | 0.7012   |
| 99   | 300          | None      | 2                | 20                | 0.9019 (0.044) | 0.7447   |
| 99   | 300          | 16        | 2                | 20                | 0.9019 (0.044) | 0.7447   |
| 99   | 100          | 16        | 3                | 10                | 0.9019 (0.044) | 0.7012   |
| 99   | 300          | 12        | 2                | 20                | 0.9019 (0.044) | 0.7447   |
| 108  | 200          | 8         | 3                | 20                | 0.9018 (0.038) | 0.7336   |
| 108  | 200          | 16        | 3                | 20                | 0.9018 (0.038) | 0.7336   |
| 108  | 200          | 12        | 3                | 20                | 0.9018 (0.038) | 0.7336   |
| 108  | 200          | None      | 3                | 20                | 0.9018 (0.038) | 0.7336   |
| 112  | 500          | None      | 3                | 20                | 0.9015 (0.044) | 0.7336   |
| 112  | 500          | 12        | 3                | 20                | 0.9015 (0.044) | 0.7336   |
| 112  | 500          | 8         | 3                | 20                | 0.9015 (0.044) | 0.7336   |
| 112  | 500          | 16        | 3                | 20                | 0.9015 (0.044) | 0.7336   |
| 112  | 400          | 8         | 2                | 10                | 0.9015 (0.044) | 0.7447   |
| 117  | 100          | 16        | 5                | 15                | 0.9012 (0.055) | 0.7211   |
| 117  | 100          | 12        | 5                | 15                | 0.9012 (0.055) | 0.7211   |
| 117  | 100          | None      | 5                | 15                | 0.9012 (0.055) | 0.7211   |
| 117  | 100          | 8         | 5                | 15                | 0.9012 (0.055) | 0.7211   |
| 121  | 300          | None      | 3                | 15                | 0.9011 (0.050) | 0.7447   |
| 121  | 300          | 12        | 3                | 15                | 0.9011 (0.050) | 0.7447   |
| 121  | 300          | 16        | 3                | 15                | 0.9011 (0.050) | 0.7447   |
| 121  | 300          | 8         | 3                | 15                | 0.9011 (0.050) | 0.7447   |
| 125  | 200          | 12        | 5                | 10                | 0.9010 (0.044) | 0.7336   |
| 125  | 200          | 8         | 5                | 10                | 0.9010 (0.044) | 0.7336   |
| 125  | 200          | 16        | 5                | 10                | 0.9010 (0.044) | 0.7336   |
| 125  | 200          | None      | 5                | 10                | 0.9010 (0.044) | 0.7336   |
| 129  | 100          | None      | 5                | 10                | 0.9007 (0.043) | 0.7332   |
| 129  | 100          | 12        | 5                | 10                | 0.9007 (0.043) | 0.7332   |
| 129  | 100          | 16        | 5                | 10                | 0.9007 (0.043) | 0.7332   |
| 129  | 100          | 8         | 5                | 10                | 0.9007 (0.043) | 0.7332   |
| 133  | 300          | 16        | 5                | 10                | 0.8999 (0.043) | 0.7336   |
| 133  | 300          | 12        | 5                | 10                | 0.8999 (0.043) | 0.7336   |
| 133  | 300          | None      | 5                | 10                | 0.8999 (0.043) | 0.7336   |
| 133  | 300          | 8         | 5                | 10                | 0.8999 (0.043) | 0.7336   |
| 137  | 500          | 8         | 2                | 15                | 0.8988 (0.048) | 0.7336   |
| 137  | 300          | 16        | 2                | 10                | 0.8988 (0.048) | 0.7293   |
| 137  | 500          | None      | 2                | 15                | 0.8988 (0.048) | 0.7336   |
| 137  | 300          | 12        | 2                | 10                | 0.8988 (0.048) | 0.7293   |
| 137  | 300          | None      | 2                | 10                | 0.8988 (0.048) | 0.7293   |
| 137  | 500          | 12        | 2                | 15                | 0.8988 (0.048) | 0.7336   |
| 137  | 500          | 16        | 2                | 15                | 0.8988 (0.048) | 0.7336   |
| 144  | 400          | 8         | 2                | 15                | 0.8985 (0.054) | 0.7447   |
| 145  | 400          | 16        | 2                | 15                | 0.8973 (0.052) | 0.7447   |
| 145  | 400          | None      | 2                | 15                | 0.8973 (0.052) | 0.7447   |
| 145  | 400          | 12        | 2                | 15                | 0.8973 (0.052) | 0.7447   |
| 148  | 100          | 16        | 2                | 20                | 0.8959 (0.057) | 0.7447   |
| 148  | 100          | 12        | 2                | 20                | 0.8959 (0.057) | 0.7447   |
| 148  | 100          | None      | 2                | 20                | 0.8959 (0.057) | 0.7447   |
| 148  | 100          | 8         | 2                | 20                | 0.8959 (0.057) | 0.7447   |
| 152  | 100          | 16        | 3                | 15                | 0.8954 (0.051) | 0.7332   |
| 152  | 100          | 12        | 3                | 15                | 0.8954 (0.051) | 0.7332   |
| 152  | 100          | None      | 3                | 15                | 0.8954 (0.051) | 0.7332   |
| 155  | 100          | 8         | 3                | 15                | 0.8942 (0.050) | 0.7332   |
| 156  | 300          | 8         | 2                | 10                | 0.8935 (0.055) | 0.7293   |
| 157  | 100          | 12        | 2                | 10                | 0.8922 (0.049) | 0.7273   |
| 157  | 100          | 16        | 2                | 10                | 0.8922 (0.049) | 0.7273   |
| 157  | 100          | None      | 2                | 10                | 0.8922 (0.049) | 0.7273   |
| 160  | 200          | 16        | 2                | 10                | 0.8915 (0.053) | 0.7389   |
| 160  | 200          | 12        | 2                | 10                | 0.8915 (0.053) | 0.7389   |
| 160  | 200          | None      | 2                | 10                | 0.8915 (0.053) | 0.7389   |
| 163  | 100          | 8         | 2                | 10                | 0.8896 (0.058) | 0.7273   |
| 164  | 200          | 8         | 2                | 10                | 0.8874 (0.062) | 0.7389   |
| 165  | 200          | None      | 2                | 20                | 0.8870 (0.062) | 0.7447   |
| 165  | 200          | 8         | 2                | 20                | 0.8870 (0.062) | 0.7447   |
| 165  | 200          | 12        | 2                | 20                | 0.8870 (0.062) | 0.7447   |
| 165  | 200          | 16        | 2                | 20                | 0.8870 (0.062) | 0.7447   |
| 169  | 300          | 12        | 2                | 15                | 0.8831 (0.065) | 0.7447   |
| 169  | 300          | 16        | 2                | 15                | 0.8831 (0.065) | 0.7447   |
| 169  | 300          | None      | 2                | 15                | 0.8831 (0.065) | 0.7447   |
| 169  | 300          | 8         | 2                | 15                | 0.8831 (0.065) | 0.7447   |
| 173  | 200          | None      | 2                | 15                | 0.8795 (0.079) | 0.7447   |
| 173  | 200          | 12        | 2                | 15                | 0.8795 (0.079) | 0.7447   |
| 173  | 200          | 16        | 2                | 15                | 0.8795 (0.079) | 0.7447   |
| 173  | 200          | 8         | 2                | 15                | 0.8795 (0.079) | 0.7447   |
| 177  | 100          | 8         | 2                | 15                | 0.8734 (0.086) | 0.7447   |
| 178  | 100          | 16        | 2                | 15                | 0.8718 (0.085) | 0.7447   |
| 178  | 100          | None      | 2                | 15                | 0.8718 (0.085) | 0.7447   |
| 178  | 100          | 12        | 2                | 15                | 0.8718 (0.085) | 0.7447   |

> The search's own best score (0.9125) is **not quoted as a generalisation estimate** anywhere in this report, and should not be quoted as one downstream. It is the maximum over 180 combinations, so it is optimistically biased by that selection alone — picking the best of many noisy estimates overstates the winner. The out-of-fold numbers below come from the nested loop, where tuning happened inside the training folds and never saw the reps it was scored on.

## Calibration

**Method: sigmoid (Platt), not isotonic.** `task.md` says _"isotonic if N allows, else sigmoid"_ — **N does not allow.** Isotonic regression fits a free-form monotone step function and typically needs on the order of a thousand samples before it stops memorising its calibration set; here the minority class is 26 reps from 6 subjects. It would produce a curve that looks excellent in-fold and transfers to nothing. Sigmoid fits two parameters. This is a constraint of the dataset, not a preference — and it is a real limitation, because a sigmoid cannot correct a _non-monotone_ miscalibration if one exists.

The sigmoid is fitted on subject-disjoint inner folds of the training data only, so the held-out subject is unseen by both the forest and the calibrator. Calibrating on reps from a subject already in the training set would leak that subject's idiosyncratic probability distribution into its own correction.

**`ensemble=False`, which is not the sklearn default and matters here.** With the default (`ensemble=True`) `CalibratedClassifierCV` fits one (forest, sigmoid) pair per fold and averages them — the 'calibrated' model is then a 3-forest ensemble whose members each saw only 2/3 of the data, so comparing it against a single full-data forest measures ensembling _and_ calibration at once. That was tried first and it moved out-of-fold AUC **0.852 -> 0.833**: the _ranking_ changed, which calibration by definition cannot do. The before/after figure would have been attributing an ensembling artefact to calibration. With `ensemble=False` one forest is fitted on all the data and a single sigmoid on out-of-fold scores, so the transform is genuinely monotone and `nested_cv()` asserts AUC is preserved on every fold — enforced rather than trusted. (It also matches Stage 5.8's `model.joblib` + `calibrator.joblib` split, which an averaged ensemble could not be serialised into.)

![Calibration reliability curve](figures/calibration_reliability_curve.png)

Both curves are **out-of-fold** predictions. A reliability curve drawn on training data sits on the diagonal for almost any model and would be evidence of nothing.

|                    | ROC AUC | macro-F1 @0.5 | Good recall | Poor recall | Brier |
| ------------------ | ------- | ------------- | ----------- | ----------- | ----- |
| uncalibrated       | 0.852   | 0.707         | 0.708       | 0.808       | 0.154 |
| sigmoid-calibrated | 0.832   | 0.631         | 0.861       | 0.385       | 0.149 |

Brier score is the number calibration actually targets, and it improves (0.154 -> 0.149).

**Why the two pooled AUCs differ slightly, when a monotone map cannot reorder anything.** They differ because these are _pooled_ out-of-fold predictions, and each of the 5 folds fitted its **own** sigmoid. Pooling therefore applies 5 different monotone maps to 5 different subsets, and the union of those is not one monotone map — so a rep from fold 1 and a rep from fold 3 can swap rank relative to each other even though nothing swapped _inside_ either fold. Per fold, where the property must hold, AUC is preserved **exactly** (`0.8889 -> 0.8889`, `0.8750 -> 0.8750`, ...), and `nested_cv()` asserts it on every fold. An earlier revision of this script asserted it on the pooled numbers instead; it fired, and it was right to — the assertion was wrong, not the model. Recorded rather than quietly fixed, because the pooled figure is the one this report quotes and the reason it is not exactly AUC-preserving is a property of pooling, not a defect in the calibration.

### What the figure actually shows — and it is weaker than the checklist hoped

The checklist's rationale for this figure is that _"an uncalibrated Fair band is a fabricated third class — this figure is the evidence it isn't."_ Read honestly, **this figure is weak evidence, and it should not be presented as a clean win:**

- Brier improves only 0.154 -> 0.149 — a 3% relative gain. Real, but small.
- **Neither curve tracks the diagonal well.** The uncalibrated model is _under_-confident at the top end (a bin predicting ~0.77 is in fact 100% Good). Sigmoid stretches the range outward, which fixes that end but leaves the mid-range sitting _below_ the diagonal — over-confident there. Calibration moved the error around at least as much as it removed it.
- **The error bars are why this is a limitation and not a finding.** Each bin holds only ~19 reps, so its 95% Wilson interval spans roughly ±0.2 around the middle of the range — comparable to the entire gap between the two curves. **The curves are not separated by more than their own uncertainty**, so this figure cannot establish that calibration helped; only that it did not obviously hurt.

Intervals are **Wilson**, not the textbook `p ± z·sqrt(p(1-p)/n)` (Wald). Wald collapses to zero width at p=0 and p=1, and two of these bins sit at exactly p=1 — they would have plotted with _no error bar_, asserting perfect certainty from 19 samples. That is the opposite of what this figure is for. Wilson keeps them honestly wide (19/19 Good is about [0.83, 1.0], not [1.0, 1.0]).

Bin-by-bin, so this is checkable rather than merely characterised:

| bin | n   | uncal. predicted | uncal. observed | cal. predicted | cal. observed | cal. 95% CI  |
| --- | --- | ---------------- | --------------- | -------------- | ------------- | ------------ |
| 1   | 20  | 0.287            | 0.450           | 0.314          | 0.500         | [0.30, 0.70] |
| 2   | 19  | 0.441            | 0.474           | 0.609          | 0.474         | [0.27, 0.68] |
| 3   | 20  | 0.622            | 0.750           | 0.832          | 0.700         | [0.48, 0.85] |
| 4   | 19  | 0.768            | 1.000           | 0.937          | 1.000         | [0.83, 1.00] |
| 5   | 20  | 0.863            | 1.000           | 0.970          | 1.000         | [0.84, 1.00] |

**Consequence for Stage 5.6, stated plainly:** the Fair band rests on these probabilities being meaningful, and at N=98 they are meaningful _roughly_, not precisely. The band's edges should not be quoted to more precision than this curve supports, and the Fair band's real justification is the ranking (AUC 0.832), not a demonstrated probability calibration. This is a limitation to carry into the write-up, not one to discover in viva.

### The Poor-recall collapse — the finding Stage 5.6 must act on

**Poor recall falls from 0.808 to 0.385 at the 0.5 threshold, while AUC is unchanged.** This is not a regression, and calibration did not damage the model — the ranking is provably identical. It is the 0.5 _threshold_ becoming wrong, and the mechanism is worth stating exactly because it will otherwise be misread as the model failing:

1. `class_weight='balanced'` makes the raw forest behave as if the classes were even, so its 0.5 output sits near the _reweighted_ decision boundary. Poor recall is 0.808 there.
2. Calibration's entire job is to make predicted probabilities match observed frequencies — and the observed frequency of Good is 73%. So the sigmoid correctly pushes P(Good) upward across the board.
3. Consequently far fewer reps fall below P(Good)=0.5, and Poor recall drops to 0.385 — **the model now misses roughly 62% of Poor reps at that threshold.** In a rehab grader that is the single worst failure mode: telling someone with poor form that they are fine.

Both facts are true at once — the probabilities got _better calibrated_ and the 0.5 decision got _worse_. They are not in tension; 0.5 is simply not the right operating point once probabilities are honest about a 73% base rate. **This is concrete evidence for why Stage 5.6 exists**, and it sharpens that stage's brief in a way worth flagging now:

> **Handoff to Stage 5.6.** Its checklist says to sweep `confidence_low_threshold` _"strictly above 0.5"_, treating >0.5 as the confident-Good region. The measurement above says the **Good/Poor decision boundary itself** wants to move above 0.5 too — at 0.5 the Poor class is largely undetected (0.385 recall). So 5.6 is sweeping two distinct things that its text currently blurs into one: the _decision_ boundary and the _Fair-band_ margin around it. The AUC of 0.832 says the ranking carries enough signal for a better operating point to exist — this is a threshold choice left unmade here, on purpose, not a model deficiency. Not resolved in this stage.

## Feature importances — the answer to Stage 5.4's open question

**All 13 features were trained on. The three Stage 5.4 DROP verdicts were not executed.** FEATURE_VALIDITY.md's own caveat is why: those verdicts were computed on all 98 reps _including_ the subjects held out above, so acting on them and then quoting a held-out score would let the test subjects influence which features existed. That report named two honest options; this is the one it called _"train on all 13 features and let the model's own importances speak"_. Below is them speaking. (The other reason is scope: editing `SQUAT_FEATURE_NAMES` bumps `feature_schema_version` and invalidates Phase 4's contract tests — not this stage's checklist.)

Gini importance of the forest inside the calibrated bundle (one forest, since `ensemble=False`), read out of the bundle itself so the numbers describe the model that would actually be exported:

`effect` is Stage 5.4's |AUC - 0.5| — **that**, not raw AUC, is its measure of separation, because an AUC _below_ 0.5 means the feature separates the classes in the opposite direction (`stance_width_norm`'s 0.374 and `knee_flex_min_deg`'s 0.315 are real signals, not weak ones).

| feature                | importance | Stage 5.4 AUC | effect | direction   | Stage 5.4 verdict |
| ---------------------- | ---------- | ------------- | ------ | ----------- | ----------------- |
| `ankle_df_proxy_deg`   | 0.2388     | 0.882         | 0.382  | Poor higher | KEEP              |
| `knee_rom_deg`         | 0.1270     | 0.859         | 0.359  | Poor higher | KEEP              |
| `knee_flex_peak_deg`   | 0.1043     | 0.837         | 0.337  | Poor higher | KEEP              |
| `stance_width_norm`    | 0.0777     | 0.374         | 0.126  | Poor lower  | KEEP (caveat)     |
| `knee_flex_min_deg`    | 0.0724     | 0.315         | 0.185  | Poor lower  | KEEP              |
| `trunk_lean_peak_deg`  | 0.0649     | 0.762         | 0.262  | Poor higher | KEEP              |
| `hip_flex_peak_deg`    | 0.0624     | 0.784         | 0.284  | Poor higher | KEEP              |
| `knee_ang_vel_max_dps` | 0.0608     | 0.750         | 0.250  | Poor higher | KEEP              |
| `trunk_lean_mean_deg`  | 0.0519     | 0.695         | 0.195  | Poor higher | KEEP              |
| `rep_duration_s`       | 0.0438     | 0.492         | 0.008  | Poor lower  | DROP              |
| `symmetry_index_pct`   | 0.0395     | 0.442         | 0.058  | Poor lower  | DROP              |
| `hip_mid_jitter_norm`  | 0.0375     | 0.650         | 0.150  | Poor higher | KEEP              |
| `descent_ascent_ratio` | 0.0191     | 0.467         | 0.033  | Poor lower  | DROP              |

### Two independent methods agree — which is the strongest result in this report

The importance column and the Stage 5.4 effect column were produced by methods that share no machinery: 5.4 ranked each feature **univariately** by rank-separation of Good from Poor, while the importances above are **multivariate** impurity decrease inside a tree ensemble. They agree — **Spearman rho = 0.775** between the two rankings:

- The **two largest effects** (`ankle_df_proxy_deg` 0.382, `knee_rom_deg` 0.359) are also the **two the model leans on most** (0.24, 0.13).
- **All three Stage 5.4 DROP features land at ranks 10, 11, 13 of 13** — the bottom of the table, with `descent_ascent_ratio` dead last.

(rho is quoted as a descriptive effect size only. Its p-value is not, for the same reason Stage 5.4 declined to lean on p-values: the 13 features are not 13 independent units — `knee_flex_peak_deg` and `knee_rom_deg` correlate at 0.97 — so any p computed as if they were is anti-conservative.)

Neither method could have known the other's answer. That convergence is real corroboration of the Stage 5.4 verdicts, obtained _without_ acting on them — which is exactly what training on all 13 features bought. It also means leaving the three DROP features in costs almost nothing: the model already ignores them.

**`symmetry_index_pct` — the check that mattered, and it passed.** Stage 5.4 established mechanically that this feature is _not measuring what it claims_: its left-vs-right difference signal correlates with the OptiTrack ground truth at **r ≈ −0.05** — no relationship at all — because a single side-view camera cannot separate the near leg from the occluded far one. The risk was that the model would lean on it anyway, having found a subject or session fingerprint inside a number carrying no real asymmetry information — an importance that would evaporate on a new camera or cohort. **It did not:** the feature ranks 11th of 13 at 0.0395. The model independently reached the same conclusion the mocap comparison did. Still flagged for Stage 5.8's model card, because a feature that cannot measure what it names does not belong in a shipped contract regardless of how little the model uses it.

### The redundant pair Stage 5.4 handed to this stage

FEATURE_VALIDITY.md recorded `knee_flex_peak_deg` ~ `knee_rom_deg` at **r = 0.97** and deferred the call: _"Recorded for Stage 5.5 to decide with model evidence in hand."_ The evidence is in hand, and the decision is **keep both**:

- They rank **2nd and 3rd** by importance (0.127 and 0.104). Correlated features **split** their importance — a tree that could have split on either picks one roughly at random, so each one's number understates the underlying signal. Read together, depth accounts for ~0.23, on par with `ankle_df_proxy_deg`'s 0.24. Neither is redundant _dead weight_; they are one signal wearing two labels.
- Extra Trees is not destabilised by correlated inputs the way a linear model is — there is no coefficient to blow up.
- Dropping either changes the feature vector, bumping `feature_schema_version` and invalidating Phase 4's contract tests, for no measurable gain.

The same reading applies to `trunk_lean_peak_deg` ~ `trunk_lean_mean_deg` (r = 0.93; importances 0.065 and 0.052).

> **Caveat on reading any of these numbers.** Gini/impurity importance is biased toward continuous, high-cardinality features — every feature here is continuous, so the bias is roughly uniform and the _ranking_ is usable, but the magnitudes should not be over-read. Permutation importance on held-out folds would be the sounder measure. It is not run here because nothing in this stage's checklist turns on it: the importances are corroboration of Stage 5.4's verdicts, not the basis of a decision. If a feature is ever actually dropped on importance evidence, permutation importance is the measure that should justify it.

## Limitations of this training run

- **98 reps, 9 subjects, 26 Poor.** Every number here rests on that. The per-fold AUC spread in the table above is the honest picture of the uncertainty; a single pooled figure would hide it.
- **Poor reps come from only 6 subjects**, and subject 1 contributes exactly one. The model's notion of 'incorrect' is shaped by a handful of people.
- **Not LOSO.** Subject-wise 5-fold, for the reason given above. Do not let the phrase 'LOSO' survive into the write-up unqualified.
- **Sigmoid calibration is a two-parameter fix** on a small sample; it cannot repair non-monotone miscalibration.
- **Our degrees are not clinical degrees** (Stage 5.4): peak knee flexion reads ~12° low versus mocap. The classifier is unaffected — a monotone offset does not change tree splits — but this is why Stage 5.6's banding cannot inherit clinical thresholds unadjusted.

## Deliberately not done here

- **No artifact exported.** `model.joblib`/`calibrator.joblib`/`feature_schema.json`/`model_card.md` are **Stage 5.8**'s deliverable. `build_final_model()` in `train_squat.py` is the entry point it should call, so the model is defined in one place and Stage 5.8 only serialises it.
- **No threshold chosen.** The 0.5 cut used for the macro-F1/recall columns above is a reporting convenience, not a decision — **Stage 5.6** sweeps `confidence_low_threshold` and defines the Fair band.
- **No 3-band confusion matrix, no latency, no baseline comparison.** **Stage 5.7**.
