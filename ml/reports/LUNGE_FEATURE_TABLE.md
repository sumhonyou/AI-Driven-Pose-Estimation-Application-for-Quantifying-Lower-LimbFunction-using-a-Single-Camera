# Stage 5.3 (Lunge) — lunge feature table build

Preprocesses each video's **entire** landmark stream through the live backend's confidence-filter → gap-fill → One-Euro pipeline (`app.module_b.core.preprocessing.preprocess_world_landmarks`, the same function `POST /api/module-b/analyze` runs ahead of `segment()`/`extract_features()`), once per video over the full chronological stream — not per rep — since OneEuroFilter is stateful and windowing first would reset its history at every rep boundary. Then windows every **side-view** (`cam17_orientation == "front"`, Camera18 = profile) Ex5 rep of that *preprocessed* stream by Segmentation.csv's physio-verified `first_frame`/`last_frame`, and calls the backend's `extract_lunge_features()` (X1). Half-profile reps are excluded per the Stage 5.0 (Lunge) gate decision (option a — side-view only, HY 2026-07-17).

## Feature table

- **Output:** `ml/data/lunge_features.csv` — 88 rows (one per rep), 17 feature columns.
- **Class balance:** 39 Good / 49 Poor.
- **Subjects:** 8 across 9 videos.
- **Lead-leg cohorts:** 42 left-lead / 46 right-lead.
- **No-pose frames dropped inside rep windows:** 0 (expected 0 — Stage 5.2 (Lunge) recorded a pose on every one of the 26,087 extracted frames).
- **Feature schema version:** `1.0.0`.

### One rep's annotation overshoots its video (found by this build's guard)

The dataset's `last_frame` for the rep(s) below runs past the final frame of the video file itself. This is an **annotation artifact, not a frame/camera misalignment** — verified before accepting it: both cameras report *and decode* the same frame count, every other rep in the same video sits well inside it, and no rep in the entire Ex5+Ex6 corpus overshoots by more than 5 frames. The window is clamped to the last real frame and the rep is kept; the build still fails loudly on any overshoot larger than the tolerance, or on a rep starting past the video's end.

| video | rep | annotated last_frame | clamped to | frames lost |
| ----- | --- | -------------------- | ---------- | ----------- |
| PM_117a | 9 | 1185 | 1183 | 2 |

The loss is at the **tail** of the rep (the return-to-standing phase, after peak flexion), so peak- and ROM-based features are unaffected; only `rep_duration_s` shortens, by the frames shown above (≈33 ms each at 30 fps). The rep is kept rather than dropped because HY's Stage 5.0 (Lunge) gate decision was explicitly to train on the **88** verified side-view reps — dropping one to avoid a sub-100 ms tail truncation would silently deviate from the approved cohort and cost a Poor-class rep from a small dataset.

Feature columns are written in `FeatureVector.names` order and asserted against `LUNGE_FEATURE_NAMES` at write time — the build fails loudly on drift.

### The two Stage 5.3 (Lunge) deltas, resolved

- **Lead-leg tag — used the dataset's given `exercise_subtype`.** Mapped `"front leg left"` → `left` / `"front leg right"` → `right` and passed to `extract_lunge_features(rep, lead_leg=...)`, overriding the live geometric inference. The build asserts the override actually took effect on every rep (`vector.lead_leg == lead_leg`) rather than trusting it.
- **`knee_passes_toe` — KEPT as a real measured feature, not approximated from the ankle and not dropped.** The plan allowed a fallback if no toe/foot-tip joint were available; Stage 5.2 (Lunge) verified against the real extraction that MediaPipe's foot-tip landmarks (31/32) are present in 100% of all 26,087 frames with mean visibility ≥0.826 per side, so no fallback is needed.

### `lead_leg` is metadata, never a model feature

`lead_leg` is written to the CSV for traceability and Stage 5.4's per-cohort analysis, but it is **outside the feature block** and **must not be trained on**. Stage 5.0 (Lunge) established that lead leg is perfectly confounded with subject in this dataset — every subject leads with exactly one leg, none performs both — so under LOSO it is perfectly collinear with the held-out subject and would act as a subject-identity proxy. This is enforced by construction rather than convention: Stage 4.2 designed the lunge vector to be *lead-leg-invariant* (front/back split, so a left-lead and an identical right-lead rep produce a bit-identical vector), and `lead_leg` lives on `FeatureVector.lead_leg` metadata, outside `names`/`values`.

### Windowed-rep sanity (not a gate — Stage 5.4 does the real validity check)

- `front_knee_flex_peak_deg`: min 49.7°, median 81.3°, max 110.9° — non-trivial front-knee flexion in every window confirms the dataset frame indices align with the Camera18 extraction.
- `back_knee_flex_peak_deg`: min 25.7°, median 84.3°, max 119.4°.
- `rep_duration_s`: min 1.33s, median 3.35s, max 5.50s.
- `knee_passes_toe_norm`: min -0.209, median 0.465, max 1.144 — a real spread rather than a constant, i.e. the foot-tip landmark is carrying signal, not a frozen default.

## FSM vs. dataset segmentation agreement (free validation)

Our lunge rep detector (`segment_lunge_frames` — cycle detection since Stage 5.3 (Lunge); see below) was run over each full Camera18 clip's **preprocessed** stream (the same one the feature table above uses) and its rep boundaries compared against the dataset's — this matches what the live pipeline's FSM actually receives, not raw landmarks. It validates the live rep detector against physio-verified boundaries; it is a report, not a gate. Matching is **strictly one-to-one** (greedy by overlap), so a merged or split detection cannot inflate the count.

- **Ground-truth Ex5 reps in these clips:** 174 (front + half-profile; the FSM is orientation-blind).
- **FSM-detected reps:** 174.
- **Matched (one-to-one):** 173.
- **Recall (GT reps matched):** 99.4% (1 GT reps missed).
- **Precision (detections matched):** 99.4% (1 spurious detections).
- **Front (side-view, trained) reps matched:** 88 / 88 (100.0% recall).
- **Boundary error on matched reps:** start median 7 frames (mean 36.3); end median 7 frames (mean 20.0). At 30 fps, 1 frame ≈ 33 ms.

### Why the detector was replaced (evidence, re-measured every run)

The agreement above is what **cycle detection** achieves. The detector that shipped through Stage 4.3 instead crossed absolute thresholds (`enter_descending_deg = 30°` / `exit_standing_deg = 20°`, borrowed from squat) and scored **50/88 = 56.8%** front-rep recall on this same data, against squat's own 93/98 = 94.9%. This section re-measures, on every run, the property of the movement that retired it, so the reasoning stays checkable rather than asserted from memory. The retired thresholds are hard-coded in this script for that purpose alone — they are gone from `lunge/config.py` and are not wired into anything.

**What the dataset's boundaries actually are.** Reps are annotated **back-to-back** — the median gap between consecutive reps is **1 frame**. A set is a *continuous* sequence of reps, so each boundary sits at the **top of a cycle**, not in a rest period. "Cycle-top flexion" below is the driving signal's minimum at that boundary: how far a subject straightens between two consecutive reps.

**The old model did not fail at the enter threshold.** The driving signal (the bilateral mean knee flexion) peaks above `30°` in **173 of 174** annotated reps — every descent was seen.

**It failed at the exit threshold.** The old FSM closed a rep only once the mean fell back under `20°`. A subject who fully extends at each cycle top sends it there and the rep closes; a subject who only **partially extends between consecutive reps** never does, so the rep never closes and consecutive reps merge into one long detection. That is why the old model's precision stayed high (94.1%) while its recall collapsed: it was not firing wrongly, it was firing too few times. **59 cycle tops never drop below 20°**, which is the same order as the 62 reps it lost.

**7 of 9 videos have at least one cycle top that never releases, and 3 have it in more than half their tops.**

| video | GT reps | median rep peak | median cycle-top flexion | tops never < retired exit |
| ----- | ------- | --------------- | ------------------------ | ------------------------- |
| PM_021 | 20 | 86.6° | 17.5° | 6 / 19 |
| PM_028 | 21 | 72.4° | 23.7° | 15 / 20 |
| PM_037 | 20 | 91.8° | 46.1° | 18 / 19 |
| PM_042 | 25 | 92.6° | 14.5° | 0 / 24 |
| PM_104 | 20 | 86.8° | 15.5° | 3 / 19 |
| PM_112 | 25 | 108.2° | 18.6° | 10 / 24 |
| PM_117a | 9 | 57.5° | 23.5° | 5 / 8 |
| PM_117b | 14 | 62.5° | 15.9° | 0 / 13 |
| PM_125 | 20 | 64.5° | 16.6° | 2 / 19 |

Read the last two columns together. `PM_042` and `PM_117b` extend fully at every cycle top and were the only two videos the old model handled well (24/25, 14/14). `PM_037` never extends far enough in 18 of 19 tops — its median cycle-top flexion is 46.1°, more than twice the retired exit threshold — and its 20 reps collapsed into 2 detections. The failure tracked a per-subject movement habit (how far they straighten between continuous reps), not noise.

**Why retuning could not rescue it, and cycle detection can.** A single global (enter, exit) pair would need `exit` above 60.0° (PM_037's worst cycle top) and `enter` below 14.8° (PM_042's weakest rep peak) simultaneously, with `exit < enter` — arithmetically impossible. Driving off the front knee only measured *worse* (subjects rest with the front knee more flexed than the bilateral mean), and a per-clip baseline-relative threshold also failed globally. Rest posture and rep depth **overlap across subjects** on any absolute scale, so no fixed angle separates them; cycle *shape* does. The replacement is measured above, in the same harness, on the same data.

The feature table was never affected either way — every rep is windowed by the dataset's physio-verified annotation, never by the detector.

> The dataset's boundaries remain ground truth for windowing (Stage 5.3); this comparison only characterises how closely the runtime FSM reproduces them. Boundary differences on matched reps are expected — the FSM's enter/exit hysteresis starts a rep a few frames after true descent onset and ends it a few frames after return to standing — and are recorded, not corrected.
