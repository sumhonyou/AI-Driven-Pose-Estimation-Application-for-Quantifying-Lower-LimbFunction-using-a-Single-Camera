# EC3D joint order and mapping (authoritative)

Resolves **open question Q3** ("EC3D's exact 25-joint index order"). Established
empirically against the pickle itself (2026-07-17, Stage 5.9), not guessed and not
taken on trust from a README.

**Verdict: EC3D's 25 joints are in OpenPose `BODY_25` order.**

Dataset: `data_3D.pickle`, from _3D Pose Based Feedback for Physical Exercises_
(Zhao, Kiciroglu, Wang, Salzmann, Fua — ACCV 2022);
repo [`Jacoo-Zhao/3D-Pose-Based-Feedback-For-Physical-Exercises`](https://github.com/Jacoo-Zhao/3D-Pose-Based-Feedback-For-Physical-Exercises).

## Why this needed proving

`task.md`'s Q3 asks for the order "from the repo's data-loader before trusting any
mapping", with "plot one frame's 25 points and label limbs" as the fallback. The repo's
README documents the pickle's _shape_ (`(29789, 3, 25)`) but **not its joint order**, and
names no skeleton format. So the order was recovered from the data, by a method stronger
than eyeballing a plot.

## File structure

| key      | type      | shape            | meaning                                                                                                |
| -------- | --------- | ---------------- | ------------------------------------------------------------------------------------------------------ |
| `poses`  | `float64` | `(29789, 3, 25)` | **(frame, xyz, joint)** — note the axis order; every consumer here transposes to `(frame, joint, xyz)` |
| `labels` | `<U6`     | `(29789, 5)`     | per-frame `[exercise, subject, instruction_label, episode, global_frame_id]`                           |

- `exercise` ∈ `SQUAT` (11,109 frames), `Lunges` (12,754), `Plank` (5,926).
- `subject` ∈ `Hugues`, `Isinsu`, `Sena`, `Vidit` — **4 subjects**, as the paper states.
- One `(subject, instruction_label, episode)` triple = **one repetition**
  (48–172 frames; 1.6–5.7 s at 30 fps).
- **30 fps**, per the paper. The pickle stores no timestamp, so this is the only source
  for the three temporal features.

## How the order was confirmed (four independent checks)

### 1. Bone rigidity — every published `BODY_25` edge is rigid

A real bone holds constant length across frames; a wrong pairing does not. Coefficient
of variation of the inter-joint distance over the 10,283 squat frames used by Stage 5.9:

| edge                 | indices | length | CV      |
| -------------------- | ------- | ------ | ------- |
| Neck–MidHip (torso)  | j01–j08 | 0.1954 | 0.00173 |
| Neck–RShoulder       | j01–j02 | 0.0607 | 0.00000 |
| Neck–LShoulder       | j01–j05 | 0.0552 | 0.00000 |
| RShoulder–RElbow     | j02–j03 | 0.1028 | 0.00154 |
| RElbow–RWrist        | j03–j04 | 0.0968 | 0.00135 |
| LShoulder–LElbow     | j05–j06 | 0.1080 | 0.00154 |
| LElbow–LWrist        | j06–j07 | 0.0947 | 0.00137 |
| MidHip–RHip          | j08–j09 | 0.0395 | 0.00014 |
| MidHip–LHip          | j08–j12 | 0.0440 | 0.00007 |
| RHip–RKnee (thigh)   | j09–j10 | 0.1403 | 0.00161 |
| RKnee–RAnkle (shank) | j10–j11 | 0.1357 | 0.00172 |
| LHip–LKnee (thigh)   | j12–j13 | 0.1413 | 0.00149 |
| LKnee–LAnkle (shank) | j13–j14 | 0.1471 | 0.00173 |
| Neck–Nose            | j01–j00 | 0.0926 | 0.00173 |

Every edge the `BODY_25` tree predicts is rigid, at an anatomically sensible length
(thigh ≈ shank ≈ 0.14; torso ≈ 0.20). A wrong joint order cannot produce that.

### 2. The foot triads — the decisive test

`BODY_25` attaches `{19,20,21} = L{BigToe, SmallToe, Heel}` to `14 = LAnkle`, and
`{22,23,24} = R{BigToe, SmallToe, Heel}` to `11 = RAnkle`. Which ankle each triad is
rigid against is unambiguous:

| joint | CV vs j11   | CV vs j14   | attaches to |
| ----- | ----------- | ----------- | ----------- |
| j19   | 0.21396     | **0.00166** | j14         |
| j20   | 0.20137     | **0.00136** | j14         |
| j21   | 0.22426     | **0.00153** | j14         |
| j22   | **0.00155** | 0.19116     | j11         |
| j23   | **0.00128** | 0.18346     | j11         |
| j24   | **0.00156** | 0.23974     | j11         |

A ~130× separation, splitting exactly along `BODY_25`'s published grouping. Within each
triad the heel is nearest its ankle (j14–j21 = 0.0244; j11–j24 = 0.0191) and the big toe
furthest (0.0667 / 0.0645) — the correct anatomy for a foot.

### 3. The root — j08 is the origin

`poses[:, :, 8]` is **exactly** `(0, 0, 0)` in every frame (max abs value `0.0`). Only
`BODY_25`'s `MidHip` is a plausible root, and root-centring is what pins it there.

### 4. The anatomical axes — two independent anterior checks agree

| axis | meaning                   | evidence                                                                                                                                 |
| ---- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 0    | medio-lateral             | the two ankles separate along it (j11 mean −0.076, j14 mean +0.085)                                                                      |
| 1    | **anterior** (forward)    | big-toe-minus-heel is +0.075 (j19−j21) and +0.067 (j22−j24) — the foot points this way; independently, nose-minus-ear-midpoint is +0.047 |
| 2    | **up** (see caveat below) | nose +0.276 vs ankles −0.200                                                                                                             |

The two anterior indicators (foot anatomy, face anatomy) are unrelated and agree.

## The 25 joints

| idx | joint             | idx | joint  | idx | joint     |
| --- | ----------------- | --- | ------ | --- | --------- |
| 0   | Nose              | 9   | RHip   | 18  | LEar      |
| 1   | Neck              | 10  | RKnee  | 19  | LBigToe   |
| 2   | RShoulder         | 11  | RAnkle | 20  | LSmallToe |
| 3   | RElbow            | 12  | LHip   | 21  | LHeel     |
| 4   | RWrist            | 13  | LKnee  | 22  | RBigToe   |
| 5   | LShoulder         | 14  | LAnkle | 23  | RSmallToe |
| 6   | LElbow            | 15  | REye   | 24  | RHeel     |
| 7   | LWrist            | 16  | LEye   |     |           |
| 8   | **MidHip (root)** | 17  | REar   |     |           |

## The mapping actually used (`validate_ec3d.py`)

Only the 8 landmarks `core/quality.REQUIRED_LANDMARKS` names are mapped — they are the
only ones squat feature extraction reads. The other 25 MediaPipe slots are filled with
`visibility: 0.0` placeholders and never touched.

| BODY_25     | → MediaPipe-33    |
| ----------- | ----------------- |
| 5 LShoulder | 11 left_shoulder  |
| 2 RShoulder | 12 right_shoulder |
| 12 LHip     | 23 left_hip       |
| 9 RHip      | 24 right_hip      |
| 13 LKnee    | 25 left_knee      |
| 10 RKnee    | 26 right_knee     |
| 14 LAnkle   | 27 left_ankle     |
| 11 RAnkle   | 28 right_ankle    |

**Axis conversion.** EC3D `(lateral, anterior, up)` → MediaPipe world `(x, y=DOWN, z=depth)`:

```
mp_x = -anterior      mp_y = -up      mp_z = lateral
```

`y` is negated because MediaPipe world landmarks put **+y downward** (confirmed against
`core/geometry.shank_vs_vertical_deg`, which reads `ankle.y - knee.y` as the downward
component). A side-view capture puts the sagittal plane in the image, so _anterior_
becomes the horizontal image axis and _medio-lateral_ becomes depth — which matters for
`hip_mid_jitter_norm`, the one feature computed `in_plane=True` (x/y only). Both mapped
axes are negated so `det(R) = +1`: a proper rotation, not a mirror that would silently
swap the skeleton's left and right.

**Left/right handedness is unresolved — and provably does not matter here.** Whether
`BODY_25`'s "R" joints are anatomically right depends on the capture's handedness
convention, which the pickle does not record. It is not load-bearing for squat: swapping
the L and R halves of the mapping above and re-extracting leaves **all 13 features
bit-identical** (max |delta| = `0.0` across all 132 reps, verified). Every squat feature
is a both-legs mean, an absolute difference, a midpoint, or an inter-ankle distance —
each invariant to the relabel. **This does not extend to Phase 5B**: a lunge's lead leg
is side-specific, so `knee_passes_toe` would need this resolved first.

## ⚠ The poses are canonicalised, not raw mocap

Anyone reusing this file must know this. Measured over the frames Stage 5.9 uses:

| property                     | measured                         | consequence                                                         |
| ---------------------------- | -------------------------------- | ------------------------------------------------------------------- |
| mid-hip (j08) max abs coord  | `0.0`                            | **root-centred** — global translation is gone                       |
| neck (j01) up-axis std       | `4.7e-17` (pinned at 0.19517662) | **orientation-normalised** — the torso never moves, under any label |
| neck (j01) anterior-axis std | `0.0`                            | the trunk cannot lean forward at all                                |
| per-subject thigh length     | 0.1403–0.1405                    | **template skeleton** — spread **0.160%** across 4 different people |

So:

- **3-point joint angles survive** (knee/hip flexion) — invariant to rigid transforms.
- **Gravity-referenced measures do not.** There is no world vertical left; axis 2 is the
  _torso_ axis. `trunk_lean_peak_deg` collapses to ~3–4° (vs ~35–44° in REHAB24-6) and
  the "Front bent" class shows no more lean than the Correct class.
- **Global-translation measures do not.** `hip_mid_jitter_norm` ≈ 0 for every rep.
- **Per-subject anatomy is gone.** All four subjects share one skeleton.

The angle-vs-non-angle split `task.md` assumed does not survive contact with this:
`ankle_df_proxy_deg` _is_ an angle and is the model's single most important feature, but
it is measured against gravity and so does not transfer. The distinction that matters is
**intrinsic (rigid-transform-invariant) vs world-referenced**. See
`../reports/EC3D_VALIDATION_REPORT.md`.

## Instruction labels

Label ids are **global across exercises** (label 4 = "Not low enough" appears in both
SQUAT and Lunges). Names are the paper's.

| id   | meaning          | exercise         | plane    |
| ---- | ---------------- | ---------------- | -------- |
| 1    | Correct          | all              | —        |
| 2    | Feet too wide    | SQUAT            | frontal  |
| 3    | Knees inward     | SQUAT            | frontal  |
| 4    | Not low enough   | SQUAT, Lunges    | sagittal |
| 5    | Front bent       | SQUAT            | sagittal |
| 6    | Knee passes toe  | Lunges           | sagittal |
| 7, 8 | (plank faults)   | Plank            | —        |
| 10   | **undocumented** | SQUAT, Sena only | —        |

SQUAT episode counts: label 1 = 41, 2 = 23, 3 = 23, 4 = 21, 5 = 24 → **132**, which is
exactly the paper's stated squat-sequence count. **Label 10 (Sena, 9 episodes, 826
frames) is excluded**: including it gives 141, contradicting the paper; no other subject
has it; and its meaning is undocumented, so guessing would be inventing ground truth.
`validate_ec3d.py` asserts the 132 count at load time so a changed pickle fails loudly.

Under Option A (Locked Assumption #1) the model is binary, so label 1 → **Good** and
labels 2–5 → **Poor**, the same collapse REHAB24-6's `correctness` column gets.

## Note for Phase 5B (recorded, not acted on)

`task.md` flags: _"`knee_passes_toe` needs a toe/foot-tip joint. If EC3D lacks one
(Stage 5.9's open question), approximate from ankle **or drop it** — and say which."_

**EC3D does not lack one.** `BODY_25` carries `LBigToe` (19) and `RBigToe` (22), both
confirmed rigid against their ankles above, so no approximation is needed _on EC3D_. Two
caveats before anyone builds on that: MediaPipe-33's nearest equivalent is
`foot_index` (31/32), which is what the **live** runtime would have to supply — the
constraint is the runtime's, not the dataset's; and the left/right ambiguity above must
be resolved first, since a lunge's lead leg is side-specific. Phase 5B's decision, not
this stage's.
