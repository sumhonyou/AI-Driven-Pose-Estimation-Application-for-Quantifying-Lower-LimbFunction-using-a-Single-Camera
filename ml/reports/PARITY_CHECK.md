# Stage 5.2 — Python vs. browser world-landmark parity check

**Blocking gate for Stage 5.2.** Compares `ml/scripts/extract_landmarks.py`'s output
against the actual in-browser MediaPipe runtime (the exact code path
`useMediaPipePose.ts` uses in production) on the identical clip and frame range.

## Method

- **Clip:** `PM_008-Camera18-30fps-transposed.mp4`, frames 100–219 (120 frames,
  ~4s) — the same rep-1 range visually verified in Stage 5.0's `DATA_AUDIT.md`.
- **Python side:** `ml/scripts/extract_landmarks.py`'s already-cached
  `ml/data/landmarks/PM_008.npz`, sliced to the same frame range.
- **Browser side:** a temporary dev-only harness
  (`frontend/parity-check.html` + `frontend/src/devPages/parityCheck.ts`, both
  removed after this check — see "Cleanup" below) that:
  - Uses the **exact same production code path**: `@mediapipe/tasks-vision`
    (the frontend's installed npm package, not a re-implementation), the same
    self-hosted WASM at `/mediapipe/wasm`, and the same
    `/models/pose_landmarker_full.task` asset.
  - Uses the **identical `PoseLandmarkerOptions`** as `useMediaPipePose.ts`:
    `delegate: "CPU"`, `runningMode: "VIDEO"`, `numPoses: 1`,
    `minPoseDetectionConfidence/minPosePresenceConfidence/minTrackingConfidence: 0.5`.
  - Feeds the clip via an `HTMLVideoElement` (seeking to each frame's exact
    timestamp) instead of a live webcam — MediaPipe's `VIDEO` running mode
    accepts any video source, so this exercises the real detection pipeline,
    not a mock.
  - Calls `detectForVideo(video, timestampMs)` with the same
    `frame_idx * 1000 / fps` timestamp convention the Python script uses, so
    frame `N` in both pipelines refers to the same instant.
  - Ran in an actual Chrome tab against the project's own Vite dev server
    (`localhost:5180/parity-check.html`), not headless/simulated.
- Compared all 33 world landmarks' `(x, y, z, visibility)` for all 120 frames.

## Results

- **0 frames missing a detected pose** in either pipeline (120/120 compared).
- **Overall Pearson correlation (all x/y/z values, both pipelines): 0.9996.**
- **XYZ absolute difference (metres):** mean 5.5mm, median 3.1mm, p95 18.2mm, max
  68.5mm (worst case, one frame, one landmark).
- **Visibility absolute difference:** mean 0.004, max 0.12.
- **Worst-agreement landmarks** (by mean XYZ diff) are left-hand fingertips
  (17–20) and the right heel (30) — small, fast-moving extremities where
  sub-pixel detection noise between the native TFLite delegate (Python) and
  the browser's WASM/XNNPACK build (Chrome) is expected to be largest. None of
  these landmarks are used by squat's feature extraction.
- **The landmarks squat actually uses** (shoulders, hips, knees, ankles —
  `extract_squat_features`'s inputs): mean diff 0.8mm (hips) to 7.3mm (right
  ankle), all well under a centimetre.
- **Knee flexion angle** (the primary squat ROM signal, computed identically
  in both pipelines via `knee_flexion_deg`-equivalent geometry): **mean
  difference 0.90°, max 4.6°** across the 120 frames.

![Knee flexion angle: Python extraction vs. browser runtime, same clip](figures/parity_check_knee_flexion.png)

## Verdict

**Small numeric differences, no structural difference — parity confirmed.**
The two curves track each other closely throughout the full rep (descent,
bottom, ascent); the ~1° average and ~5° worst-case knee-flexion divergence is
consistent with expected delegate/backend floating-point differences (native
TFLite vs. browser WASM/XNNPACK), not a pipeline bug. This matches the "small
numeric differences are expected... a structural difference means the
pipeline is wrong" criterion from `task.md`'s Stage 5.2. Landmark extraction
is cleared to proceed.

## Cleanup

The browser-side harness was temporary dev tooling, not part of the shipped
app — removed after this check ran:

- `frontend/parity-check.html`
- `frontend/src/devPages/parityCheck.ts`
- `frontend/public/parity-clip.mp4` (a copy of the dataset clip, needed only
  so the dev server could serve it to the `<video>` element)

This report and the comparison figure are the permanent record of the check;
re-running it requires recreating the harness from the method described above
(the exact `PoseLandmarkerOptions` and frame range are documented here so it's
reproducible).
