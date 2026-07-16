# REHAB24-6 `Segmentation.csv` schema (authoritative)

Transcribed and verified directly against `Segmentation.txt` and a live read of
`Segmentation.csv` (2026-07-16) — not guessed from a screenshot, per Stage 5.0.

- **Delimiter:** `;` (semicolon), not comma.
- **Rows:** 1072 (data rows, excluding header).
- **One row = one repetition** (not one video).

## Columns

| Column                       | Type                  | Meaning                                                                                                                                                                                                                                                                                                   |
| ---------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `video_id`                   | string, e.g. `PM_008` | Id of the video file. Matches the `PM_###` prefix of every file in `videos/Ex{n}/`.                                                                                                                                                                                                                       |
| `repetition_number`          | int                   | Rep number within the given video (1-indexed).                                                                                                                                                                                                                                                            |
| `exercise_id`                | int, 1-6              | Exercise id. Per the Zenodo dataset page (cited in `task.md`'s Locked Assumptions, HY 2026-07-15): **Ex5 = Leg lunge, Ex6 = Squats** — the only two this project trains on.                                                                                                                               |
| `person_id`                  | int                   | Id of the exercising person (subject). Used as the LOSO grouping key.                                                                                                                                                                                                                                     |
| `first_frame` / `last_frame` | int                   | Frame range (inclusive) of this repetition within the video, at the video's native fps. These are the dataset's physio-verified rep boundaries — **ground truth for Stage 5.3 windowing**, not our FSM's output.                                                                                          |
| `cam17_orientation`          | enum                  | Orientation of the exercising person **towards camera17**. Observed literal values in the CSV: `front`, `half-profile`, `profile`. See "Known documentation inconsistency" below — camera18 is placed orthogonally to camera17, so this column also implies camera18's orientation via the mapping table. |
| `mocap_erroneous`            | int, 0/1              | 1 = some mocap markers were not correctly detected for this rep (candidate for exclusion from the Stage 5.4 mocap-agreement check).                                                                                                                                                                       |
| `exercise_subtype`           | string, may be empty  | For exercises with a right/left-sided distinction (e.g. Ex5 leg lunge: `front leg right` / `front leg left` — the lead-leg tag). **Empty for Ex6 (squats)** — squats have no side variant.                                                                                                                |
| `lights_on`                  | int, 0/1              | Whether the recording lights were switched on. (Note: `task.md`'s Stage 5.0 checklist calls this "lighting distribution" — the actual column name is `lights_on`, a boolean, not a categorical lighting variable.)                                                                                        |
| `extra_person_in_cam17`      | int, 0-3              | 0 = no extra person visible; 1 = negligible part visible briefly; 2 = noticeable part visible (e.g. whole arm) for more than a few frames; 3 = large part of an extra person visible.                                                                                                                     |
| `extra_person_in_cam18`      | int, 0-3              | Same semantics as `extra_person_in_cam17`, for camera18.                                                                                                                                                                                                                                                  |
| `correctness`                | int, 0/1              | 1 = repetition performed correctly, 0 = incorrectly. This is the Option A training label (`correctness=1 → Good`, `correctness=0 → Poor`, per Stage 5.3).                                                                                                                                                 |

## Known documentation inconsistency (flagged, not silently resolved)

`Segmentation.txt`'s own orientation-mapping table reads:

```
cam17 orientation -> cam18 orientation
  front -> side
  half-profile -> half-profile
  side -> front
```

but the line immediately above it states the **possible `cam17_orientation` values** are
`'front'`, `'half-profile'` and `'profile'` — i.e. the mapping table uses the word `side`
where the actual column enumerates `profile`. Treated here as the same concept
(`side` == `profile`) since `side` never appears as a literal CSV value (confirmed by
reading all 1072 rows — see `audit_rehab246.py` output). This textual inconsistency is
the file's own, not introduced by this project.

Reading the corrected table with that substitution:

| `cam17_orientation` | camera17 sees  | camera18 sees  |
| ------------------- | -------------- | -------------- |
| `front`             | front          | profile (side) |
| `half-profile`      | half-profile   | half-profile   |
| `profile`           | profile (side) | front          |

This is the basis for the Stage 5.0 view-camera decision below — **verified visually**,
not assumed, in `DATA_AUDIT.md`.

## Joints (`joints_names.txt`)

26 joints, indices 0-25 (OptiTrack mocap skeleton, used only for the Stage 5.4 mocap
agreement check, never for training — X3):

```
 0 Hips             7 LeftArm            14 RightHand          21 RightUpLeg
 1 Spine            8 LeftForeArm        15 RightHand_end      22 RightLeg
 2 Spine1           9 LeftHand           16 LeftUpLeg          23 RightFoot
 3 Neck             10 LeftHand_end      17 LeftLeg            24 RightToeBase
 4 Head             11 RightShoulder     18 LeftFoot           25 RightToeBase_end
 5 Head_end         12 RightArm          19 LeftToeBase
 6 LeftShoulder     13 RightForeArm      20 LeftToeBase_end
```

## Video files

`videos/Ex{n}/PM_###-Camera{17|18}-30fps[-transposed].mp4` — one file per
`(video_id, camera)` pair. Camera18 files carry a `-transposed` suffix (their sensor
orientation differs from camera17's; already corrected in the filename/encode, not
something this project needs to handle).
