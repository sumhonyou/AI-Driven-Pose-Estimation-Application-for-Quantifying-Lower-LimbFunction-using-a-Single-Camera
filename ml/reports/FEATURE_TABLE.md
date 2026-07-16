# Stage 5.3 — squat feature table build

Windows every **side-view** (`cam17_orientation == "front"`, Camera18 = profile) Ex6 rep by Segmentation.csv's physio-verified `first_frame`/`last_frame`, then calls the backend's `extract_squat_features()` (X1). Half-profile reps are excluded per the Stage 5.0 gate decision (option a — side-view only).

## Feature table

- **Output:** `ml/data/squat_features.csv` — 98 rows (one per rep), 13 feature columns.
- **Class balance:** 72 Good / 26 Poor.
- **Subjects:** 9 across 9 videos.
- **No-pose frames dropped inside rep windows:** 0 (expected 0 — the single no-pose frame in the corpus is PM_008 frame 0, outside every rep window).
- **Feature schema version:** `1.0.0`.

Feature columns are written in `FeatureVector.names` order and asserted against `SQUAT_FEATURE_NAMES` at write time — the build fails loudly on drift.

### Windowed-rep sanity (not a gate — Stage 5.4 does the real validity check)

- `knee_flex_peak_deg`: min 69.7°, median 99.8°, max 129.8° — non-trivial knee flexion in every window confirms the dataset frame indices align with the Camera18 extraction (had they indexed the wrong camera/offset, windows would not contain a squat).
- `rep_duration_s`: min 2.13s, median 3.13s, max 5.13s.

## FSM vs. dataset segmentation agreement (free validation)

Our squat FSM (`segment_squat_frames`, Stage 4.3) was run over each full Camera18 clip and its rep boundaries compared against the dataset's. This validates the live rep detector against physio-verified boundaries; it is a report, not a gate. Matching is **strictly one-to-one** (greedy by overlap): each detected rep matches at most one GT rep and vice versa, so a merged or split detection cannot inflate the count.

- **Ground-truth Ex6 reps in these clips:** 195 (front + half-profile; the FSM is orientation-blind).
- **FSM-detected reps:** 192.
- **Matched (one-to-one):** 182.
- **Recall (GT reps matched):** 93.3% (13 GT reps missed).
- **Precision (detections matched):** 94.8% (10 spurious detections).
- **Front (side-view, trained) reps matched:** 92 / 98 (93.9% recall).
- **Boundary error on matched reps:** start median 17 frames (mean 18.5); end median 15 frames (mean 17.0). At 30 fps, 1 frame ≈ 33 ms.

| video | GT reps | FSM detected | matched |
| ----- | ------- | ------------ | ------- |
| PM_008 | 27 | 28 | 27 |
| PM_022 | 22 | 23 | 22 |
| PM_029 | 20 | 20 | 20 |
| PM_038 | 20 | 17 | 17 |
| PM_043 | 20 | 20 | 15 |
| PM_105 | 21 | 21 | 20 |
| PM_113 | 22 | 22 | 22 |
| PM_118 | 23 | 22 | 20 |
| PM_126 | 20 | 19 | 19 |

> The dataset's boundaries remain ground truth for windowing (Stage 5.3); this comparison only characterises how closely the runtime FSM reproduces them. Boundary differences are expected — the FSM's enter/exit hysteresis starts a rep a few frames after true descent onset and ends it a few frames after return to standing — and are recorded, not corrected.
