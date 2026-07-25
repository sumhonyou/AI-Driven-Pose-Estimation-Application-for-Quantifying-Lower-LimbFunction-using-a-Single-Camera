# Stage 5.3 — squat feature table build

Preprocesses each video's **entire** landmark stream through the live backend's confidence-filter → gap-fill → One-Euro pipeline (`app.module_b.core.preprocessing.preprocess_world_landmarks`, the cross-cutting change wired into `POST /api/module-b/analyze` ahead of `segment()`/`extract_features()`), run once per video over the full chronological stream — not per rep — since OneEuroFilter is stateful and windowing first would reset its history at every rep boundary. Then windows every **side-view** (`cam17_orientation == "front"`, Camera18 = profile) Ex6 rep of that _preprocessed_ stream by Segmentation.csv's physio-verified `first_frame`/`last_frame`, and calls the backend's `extract_squat_features()` (X1). Half-profile reps are excluded per the Stage 5.0 gate decision (option a — side-view only).

---

## Table of Contents

- [Feature table](#feature-table)
  - [Windowed-rep sanity (not a gate — Stage 5.4 does the real validity check)](#windowed-rep-sanity-not-a-gate-stage-54-does-the-real-validity-check)
  - [Far-limb occlusion (finding — feeds the monocular limitations write-up)](#far-limb-occlusion-finding-feeds-the-monocular-limitations-write-up)
- [FSM vs. dataset segmentation agreement (free validation)](#fsm-vs-dataset-segmentation-agreement-free-validation)

---

## Feature table

- **Output:** `ml/data/squat_features.csv` — 98 rows (one per rep), 13 feature columns.
- **Class balance:** 72 Good / 26 Poor.
- **Subjects:** 9 across 9 videos.
- **No-pose frames dropped inside rep windows:** 0 (expected 0 — the single no-pose frame in the corpus is PM_008 frame 0, outside every rep window).
- **Feature schema version:** `1.0.0`.

Feature columns are written in `FeatureVector.names` order and asserted against `SQUAT_FEATURE_NAMES` at write time — the build fails loudly on drift.

### Windowed-rep sanity (not a gate — Stage 5.4 does the real validity check)

- `knee_flex_peak_deg`: min 68.7°, median 98.3°, max 126.5° — non-trivial knee flexion in every window confirms the dataset frame indices align with the Camera18 extraction (had they indexed the wrong camera/offset, windows would not contain a squat).
- `rep_duration_s`: min 2.13s, median 3.13s, max 5.13s.

### Far-limb occlusion (finding — feeds the monocular limitations write-up)

A single side-view camera tracks the **near** leg well and the **far** leg poorly, systematically, in every subject. Mean landmark visibility across all 9 videos: left knee 0.95–0.99 and left ankle 0.97–0.99, versus right knee **0.59–0.78** and right ankle **0.68–0.87** (the subjects face the same way, so the right leg is the far one throughout). The far knee sits below the `MIN_VISIBILITY = 0.6` confidence threshold for whole reps at a time — measured at all 121 frames of PM_008's rep-1 window, far longer than the 5-frame gap-fill cap.

This is a property of monocular side-view capture, not of this dataset: the live app's own squat guidance asks for exactly this camera placement, so the same occlusion occurs at runtime. It is recorded here as evidence for the limitations write-up, alongside the dropped frontal-plane valgus measure (Locked Assumption #3) — both are the same underlying constraint (one camera cannot see what the body occludes).

The far leg's landmarks are _low-confidence but still tracking_ — not missing. On PM_008 rep 1 the far knee's raw trajectory peaked at 99.9° against the near knee's 77.9°, a plausible squat depth. Preprocessing therefore releases hold-last beyond the gap-fill window rather than freezing the far limb at its standing angle (see `module_b/core/preprocessing._release_persistent_occlusions`); freezing it halved the bilateral mean knee flexion and collapsed FSM rep agreement to 32/98 front reps. Whether the far leg's estimate is _accurate_ (not merely plausible) is exactly what Stage 5.4's `check_mocap_agreement.py` settles against the OptiTrack ground truth — it is not asserted here.

## FSM vs. dataset segmentation agreement (free validation)

Our squat FSM (`segment_squat_frames`, Stage 4.3) was run over each full Camera18 clip's **preprocessed** stream (the same one the feature table above uses) and its rep boundaries compared against the dataset's — this matches what the live pipeline's FSM actually receives (`router.py` preprocesses once, then segments), not raw landmarks. It validates the live rep detector against physio-verified boundaries; it is a report, not a gate. Matching is **strictly one-to-one** (greedy by overlap): each detected rep matches at most one GT rep and vice versa, so a merged or split detection cannot inflate the count.

- **Ground-truth Ex6 reps in these clips:** 195 (front + half-profile; the FSM is orientation-blind).
- **FSM-detected reps:** 192.
- **Matched (one-to-one):** 184.
- **Recall (GT reps matched):** 94.4% (11 GT reps missed).
- **Precision (detections matched):** 95.8% (8 spurious detections).
- **Front (side-view, trained) reps matched:** 93 / 98 (94.9% recall).
- **Boundary error on matched reps:** start median 20 frames (mean 21.2); end median 13 frames (mean 14.2). At 30 fps, 1 frame ≈ 33 ms.

| video  | GT reps | FSM detected | matched |
| ------ | ------- | ------------ | ------- |
| PM_008 | 27      | 28           | 27      |
| PM_022 | 22      | 23           | 22      |
| PM_029 | 20      | 20           | 20      |
| PM_038 | 20      | 17           | 17      |
| PM_043 | 20      | 20           | 16      |
| PM_105 | 21      | 21           | 20      |
| PM_113 | 22      | 22           | 22      |
| PM_118 | 23      | 22           | 21      |
| PM_126 | 20      | 19           | 19      |

> The dataset's boundaries remain ground truth for windowing (Stage 5.3); this comparison only characterises how closely the runtime FSM reproduces them. Boundary differences are expected — the FSM's enter/exit hysteresis starts a rep a few frames after true descent onset and ends it a few frames after return to standing — and are recorded, not corrected.
