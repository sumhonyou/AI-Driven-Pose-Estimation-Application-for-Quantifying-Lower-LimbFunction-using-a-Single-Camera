# EC3D external validation — Phase 5, Stage 5.9

**Verdict: the external validation could not be performed as a generalisation check,
and this report explains why with measurements rather than reporting a number that
would not mean what it appears to mean.** The confusion matrix the checklist requires
is included, and it is captioned as what it actually is.

Model under test: `squat-1.0.0+rehab246-loso-3c441ac.dirty` — the exported artifact in
`ml/artifacts/squat/`, loaded through the backend's own `get_model_bundle("squat")`,
scored at the shipped fusion config (`w_rule=0.2`, `w_ml=0.8`,
`confidence_low_threshold=0.85`). Nothing was re-tuned for this report.

Cohort: **132 EC3D squat repetitions** — 41 Correct, 91 faulty —
from **4 subjects** (Hugues, Isinsu, Sena, Vidit).

## The headline caveat, stated before any metric

EC3D has **4 subjects**. Nothing computed from it can be a generalisation
claim about a population; at this size a single subject moves every number materially.
The checklist called this an external *check*, never a headline, and that framing is
kept here. The findings below make the caveat stronger, not weaker.

## Result

| metric | value |
| ------ | ----- |
| `accuracy_strict` (Fair counted wrong) | **0.053** |
| `accuracy_confident` (Fair excluded) | **0.184** |
| `macro_f1` | 0.089 |
| `fair_rate` (abstention) | 0.712 |
| `recall_good` | 0.171 |
| `recall_poor` | 0.000 |
| n | 132 |

![Fused 3-band output on EC3D. Rows are EC3D ground truth (Correct/faulty, collapsed to Good/Poor by Option A); columns are the band the user would be shown. Cells show counts with row-normalised percentages. Drawn by the same plotting function as `confusion_matrix_3band.png` (not a copy of it), so the two matrices are directly comparable side by side.](figures/ec3d_confusion_matrix.png)

**The matrix above is n=132 repetitions from 4 subjects only,
and it is not a generalisation estimate.** It is the response of the shipped model to
input that is simultaneously out-of-distribution and inversely labelled, for the three
independent reasons measured below. Read beside `confusion_matrix_3band.png`
(REHAB24-6) it shows what changed between the two cohorts, not how well the model
travels.

P(Good) over the 132 EC3D reps ranged **0.618 –
0.942** (mean 0.819).

### Two cells carry the whole result

**`recall_poor` is exactly 0.000: the model did not return a
confident Poor for a single one of the 91 faulty repetitions.** This independently
corroborates the Stage 5.8 finding — which was measured in-sample, on the model's own
98 training rows — on **4 subjects it has never seen, from a different
dataset, captured on different hardware**. The mechanism is visible in the
probabilities: P(Good) never fell below 0.618 here, so
confidence toward Poor never exceeded 0.382, against a
`confidence_low_threshold` of 0.85. The Poor column of the matrix above is empty,
and it is empty for a reason that has now been observed twice by unrelated means.

**`accuracy_confident` = 0.184 is below chance, and that
is the signature of inversion rather than noise.** A model reading uninformative
features would land near 0.5 on the repetitions it commits to, or abstain. This one
commits to 38 repetitions and is wrong on
0.816 of them — it is not confused, it is
confidently backwards. Finding 2 is why.

## Finding 1 — EC3D's poses are canonicalised, not raw mocap

Measured over the 10283 frames used here:

| property | measured | what it means |
| -------- | -------- | ------------- |
| mid-hip (BODY_25 j8) max abs coordinate | `0.0e+00` | every frame is **root-centred**: the hip is pinned to the origin |
| neck (j1) up-axis std | `4.7e-17` (value 0.19517662) | the torso is **orientation-normalised**: the neck never moves, in any frame, under any label |
| neck (j1) anterior-axis std | `1.5e-17` | the trunk is pinned to y=0 — it cannot lean forward at all |
| per-subject thigh length | Hugues 0.140393, Isinsu 0.140341, Sena 0.140252, Vidit 0.140477 | spread **0.160%** — four different people share one **template skeleton** |

Three-point joint angles (knee, hip flexion) are invariant to rigid transforms, so they
survive this intact and are physiologically plausible. Two classes of feature do not:

- **Gravity-referenced features.** `trunk_lean_peak_deg`, `trunk_lean_mean_deg` and
  `ankle_df_proxy_deg` are angles against **world vertical**. After orientation
  normalisation there is no world vertical left — the canonical up-axis *is* the torso
  axis. `trunk_lean_peak_deg` collapses from a REHAB24-6 mean of ~35-44° to ~3-4°
  here, and the "Front bent" class shows **no more** trunk lean than the Correct class.
  The one fault trunk lean exists to detect is erased by the normalisation.
- **Global-translation features.** `hip_mid_jitter_norm` measures how much the hip
  midpoint moves. The hip is pinned at the origin, so it is ~0 for every rep.

The checklist anticipated this in part, asking for "the angle-based features only". The
data shows that heuristic does not survive contact: `ankle_df_proxy_deg` **is**
angle-based and is the model's single most important feature
(0.2388), yet it is measured against
gravity and so does not transfer either. The distinction that matters is not
angle-vs-non-angle but **intrinsic (rigid-transform-invariant) vs world-referenced**.

Recovering the lost orientation was considered and rejected: it would mean inventing an
estimator (fitting a ground plane from the feet, then un-rotating each frame), feeding
its unquantified error into the model's most important feature, and it still could not
restore `hip_mid_jitter_norm` or per-subject anatomy, both of which are gone rather than
rotated. That is the invented-methodology trap this project has already been caught by
once.

## Finding 2 — the two datasets disagree about what "incorrect" means

This is the decisive one. REHAB24-6's incorrect squats are **deeper** than its correct
ones — established independently in Stage 5.4/5.5/5.6 and the reason the ROM rule had to
be down-weighted. EC3D's fault taxonomy contains **"Not low enough"**, so its incorrect
squats are **shallower**. The model's learned relationship is therefore not merely
uninformative on EC3D, it is **backwards**.

AUC below 0.5 means the feature separates the classes in the opposite direction. Means
are Good/Poor.

| feature | Gini imp. | REHAB24-6 mean | EC3D mean | REHAB AUC | EC3D AUC | direction |
| ------- | --------- | -------------- | --------- | --------- | -------- | --------- |
| `ankle_df_proxy_deg` | 0.2388 | 31.07 / 41.05 | 14.09 / 21.77 | 0.882 | 0.775 | same |
| `knee_rom_deg` | 0.1270 | 78.03 / 96.95 | 113.28 / 106.84 | 0.859 | 0.425 | **INVERTED** |
| `knee_flex_peak_deg` | 0.1043 | 91.64 / 107.96 | 119.58 / 113.32 | 0.837 | 0.418 | **INVERTED** |
| `stance_width_norm` | 0.0777 | 0.77 / 0.71 | 0.73 / 0.87 | 0.374 | 0.657 | **INVERTED** |
| `knee_flex_min_deg` | 0.0724 | 13.61 / 11.01 | 6.30 / 6.47 | 0.315 | 0.542 | **INVERTED** |
| `trunk_lean_peak_deg` | 0.0649 | 34.74 / 44.12 | 3.70 / 3.84 | 0.762 | 0.536 | same |
| `hip_flex_peak_deg` | 0.0624 | 97.69 / 114.65 | 121.90 / 105.04 | 0.784 | 0.244 | **INVERTED** |
| `knee_ang_vel_max_dps` | 0.0608 | 144.57 / 178.31 | 187.24 / 184.11 | 0.750 | 0.480 | **INVERTED** |
| `trunk_lean_mean_deg` | 0.0519 | 19.74 / 23.96 | 2.03 / 2.04 | 0.695 | 0.550 | same |
| `rep_duration_s` | 0.0438 | 3.35 / 3.18 | 2.59 / 2.55 | 0.494 | 0.500 | **INVERTED** |
| `symmetry_index_pct` | 0.0395 | 32.13 / 28.93 | 20.10 / 20.78 | 0.442 | 0.486 | same |
| `hip_mid_jitter_norm` | 0.0375 | 0.00 / 0.00 | 0.00 / 0.00 | 0.650 | 0.568 | same |
| `descent_ascent_ratio` | 0.0191 | 1.24 / 1.22 | 1.37 / 1.40 | 0.467 | 0.501 | **INVERTED** |

**0.5674 of the forest's Gini importance mass
(56.7%) sits on features whose Good/Poor
direction inverts between the two datasets.** An inverted feature is worse than a
missing one: the model does not abstain on it, it reads the evidence confidently the
wrong way round.

### The inversion in one comparison

The clearest evidence is not in the table above but in the outcome. Of EC3D's
**21** *"Not low enough"* repetitions — the shallowest, most unambiguously
faulty squats in the cohort — the system called **17
(81.0%) Good**. Of its **41** genuinely
**Correct** repetitions it called only **7
(17.1%) Good**.

**The model is 4.7× more likely to approve
a "not low enough" fault than an actually-correct squat.** That is the learned
"incorrect reps are deeper" relationship applied to a cohort where the fault is being
too shallow. It is exactly backwards, it is not subtle, and no threshold change fixes
it — the ordering itself is wrong for this population.

This is not a bug in either dataset. It is evidence that the model learned a
**population-specific** notion of squat correctness rather than a universal one — which
is a genuine and reportable limitation of the trained artifact, and arguably the most
useful thing this stage produced.

## Finding 3 — half of EC3D's fault class is invisible to this system by design

Per EC3D instruction label, with the band the system would have shown:

| EC3D label | plane | n | Good | Fair | Poor |
| ---------- | ----- | - | --- | --- | --- |
| 1 — Correct | n/a (correct class) | 41 | 7 | 34 | 0 |
| 2 — Feet too wide | frontal | 23 | 5 | 18 | 0 |
| 3 — Knees inward | frontal | 23 | 8 | 15 | 0 |
| 4 — Not low enough | sagittal | 21 | 17 | 4 | 0 |
| 5 — Front bent | sagittal | 24 | 1 | 23 | 0 |

**"Feet too wide" and "Knees inward" are frontal-plane faults.** Locked Assumption #3
drops frontal valgus from the taxonomy as monocular-infeasible: there is no valgus
feature, no valgus tag and no valgus rule anywhere in this system, deliberately. Those
reps are still labelled incorrect in EC3D's ground truth, so the system is being marked
wrong for failing a test it was explicitly designed never to sit. They are
46 of the 91 faulty
repetitions.

The checklist's instruction — *"do not evaluate frontal-plane features here"* — was
aimed at not crediting the model for a valgus feature it does not have. The sharper
problem is the other direction: EC3D's fault **class**, not just its features, is
substantially frontal, so the Poor row of the matrix above cannot be read as a
measurement of this system.

## What this stage does and does not establish

**Does:**

- The validation firewall held. EC3D never touched training, and this is the first time
  the artifact met it.
- EC3D's joint order is resolved: OpenPose BODY_25, confirmed empirically
  ([`ec3d_joint_mapping.md`](../docs/ec3d_joint_mapping.md)). Open question Q3 is closed.
- The mapped features are physiologically plausible, so the mapping itself is sound —
  the failure is in comparability, not in the plumbing.
- The model's Good/Poor construct is **population-specific** and inverts on a cohort
  whose fault taxonomy includes "not low enough". That is a real, measured limitation.

**Does not:**

- Produce a generalisation estimate. The numbers in the Result table are reported for
  completeness and should not be quoted as one, in either direction. A good score would
  have been as meaningless as a poor one.
- Rescue the 91-rep Poor class from containing
  46 frontal-plane faults this
  system cannot see.

**What would make a real external check possible**, in rough order of cost: a cohort
whose "incorrect" class is defined by the same faults REHAB24-6's is; or raw
(non-canonicalised) EC3D mocap, which would restore the gravity-referenced features and
leave only the label-construct mismatch; or a model trained only on the intrinsic,
rigid-transform-invariant features, which could be scored on EC3D honestly but would be
a different artifact from the one that ships, and would still face Finding 2.

## Reproduce

```bash
ml/.venv/bin/python ml/scripts/validate_ec3d.py
```

Deterministic (X8): no RNG, no wall-clock. The label filter is asserted against the
paper's own 132-sequence count at load time, so a changed
pickle fails loudly rather than quietly reporting different numbers.
