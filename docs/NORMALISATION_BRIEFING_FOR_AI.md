# Segment-Length Normalisation — Full Technical Briefing

Self-contained briefing for an AI agent (or a person) who needs to understand exactly
what "landmark normalisation" means in this codebase, why it exists, and how it differs
from what the Capstone 1 proposal originally described. Every fact below was verified
directly against the source code and the project's own ML evaluation reports — none of
it is inferred or assumed.

---

## 1. What the proposal originally said (verbatim)

> "This project will normalize landmarks because the user's height and camera distance
> will cause the MediaPipe to gather different data. For example, coordinate-based
> features, like hip-to-knee segment length, can be scaled relative to body segment
> length, ensuring more consistent comparisons. To avoid the system obtaining an exact
> degree as clinical measurements, it will use banding and relative features that remain
> stable under viewpoint changes."

Three separate claims are packed into this paragraph:

1. Normalisation exists because of **two** problems: user height AND camera distance.
2. The worked example given is **hip-to-knee segment length** (i.e. thigh length).
3. The system will show **bands only, never exact degrees**, and will be stable "under
   viewpoint changes."

All three need updating — see §4.

---

## 2. The architectural fact that changes everything: which landmark type is used

MediaPipe Pose produces **two** outputs per frame from the same single camera image:

| Output                                     | What it is                                                                                                                        | Used in this project for                                                                                  |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `landmarks` (normalised image coordinates) | `(x, y)` in `[0, 1]`, relative to image width/height — pixel-space, no real-world units                                           | Capture-quality checks, visibility gating, on-screen rendering                                            |
| `worldLandmarks`                           | Metric-scale (**metres**), hip-centred 3D estimate — MediaPipe's own learned body-model reconstruction from the same single frame | **All angle and length computation** — fault gates, feature extraction, rep segmentation, live estimators |

Confirmed by direct code search — `worldLandmarks` (not `landmarks`) is the input to:

- `backend/app/module_b/squat/features.py` (feature extraction)
- `backend/app/module_b/squat/fault_gates.py` (depth/lean/heel-rise gates)
- `backend/app/module_b/squat/segmentation.py` (rep boundary detection)
- The frontend live estimators (`squatLiveEstimate.ts`, `stsLiveEstimate.ts`, etc.)

**Why this matters for normalisation specifically:** `worldLandmarks` are already in real
metres. Standing closer to or further from the camera no longer inflates or shrinks the
coordinates the way it would with plain normalised `(x, y)` image coordinates. **This
removes camera-distance as a reason normalisation is needed at all** — that job is now
done at the source, by MediaPipe itself, before any of this project's own code runs.

This is still fully single-camera / monocular. World landmarks are not a second camera
or a depth sensor — they are MediaPipe's own inference from the same one RGB frame the
2D landmarks come from.

---

## 3. What normalisation actually does now, precisely

### 3.1 The mechanism

`backend/app/module_b/squat/features.py`:

```python
def _norm_ref(samples: list[dict[str, Any]]) -> float:
    strategy = SQUAT_CONFIG["norm_ref_strategy"]  # currently "trunk_length"
    if strategy not in {"thigh_length", "trunk_length"}:
        raise ValueError(f"Unsupported squat norm_ref_strategy: {strategy}")
    reference = sum(sample[strategy] for sample in samples) / len(samples)
    if reference < 1e-9:
        raise ValueError(f"Cannot normalize squat features with a zero {strategy}")
    return reference
```

`trunk_length` is computed per frame as `distance(shoulder_mid, hip_mid)` — a real
metric length in metres, from `worldLandmarks`, averaged across the rep. It is the
**denominator** two features are divided by.

### 3.2 Exactly which of the 13 shipped ML features use it

From `ml/artifacts/squat/feature_schema.json` (the frozen 13-dimension feature vector):

| #   | Feature                   | Uses `norm_ref`? | Why / why not                                                                                 |
| --- | ------------------------- | ---------------- | --------------------------------------------------------------------------------------------- |
| 1   | `knee_flex_peak_deg`      | No               | Angle (degrees) — already scale-invariant                                                     |
| 2   | `knee_flex_min_deg`       | No               | Angle                                                                                         |
| 3   | `knee_rom_deg`            | No               | Angle (range)                                                                                 |
| 4   | `hip_flex_peak_deg`       | No               | Angle                                                                                         |
| 5   | `trunk_lean_peak_deg`     | No               | Angle                                                                                         |
| 6   | `trunk_lean_mean_deg`     | No               | Angle                                                                                         |
| 7   | `knee_ang_vel_max_dps`    | No               | Angular velocity (deg/s) — scale-invariant                                                    |
| 8   | `rep_duration_s`          | No               | Time                                                                                          |
| 9   | `descent_ascent_ratio`    | No               | A ratio of two durations — self-normalising                                                   |
| 10  | `symmetry_index_pct`      | No               | Already a percentage of a within-rep mean                                                     |
| 11  | `ankle_df_proxy_deg`      | No               | Angle                                                                                         |
| 12  | **`hip_mid_jitter_norm`** | **Yes**          | A real **displacement** (metres) — needs a body-size reference to be comparable across people |
| 13  | **`stance_width_norm`**   | **Yes**          | A real **length** (ankle-to-ankle distance, metres) — same reason                             |

**Only the two features that are themselves a length or a displacement get normalised.**
The other 11 are angles, times, ratios, or percentages, which carry no absolute-scale
information to begin with — they were never candidates for normalisation under either
the old (2D) or new (world-landmark) representation.

A third, **non-ML** signal also uses the same reference: the heel-rise fault gate
(`fault_heel_rise_peak_norm`, rule-only, not one of the 13 frozen ML features) computes
peak heel lift normalised by trunk length — see
`backend/app/module_b/squat/fault_gates.py::_heel_rise_peak_norm`.

### 3.3 Which reference length won, and why (the "bake-off")

`ml/reports/NORM_REF_BAKEOFF.md` (Stage 5.4) compared two candidate references —
`trunk_length` vs `thigh_length` — using **cross-subject coefficient of variation (CV)**,
not raw variance (raw variance is scale-confounded: a longer reference shrinks the
feature and its variance together, which would make the _longer_ reference look better
for a trivial reason, not because it actually normalises anything).

| Feature               | Candidate    | Cross-subject CV | Winner |
| --------------------- | ------------ | ---------------- | ------ |
| `hip_mid_jitter_norm` | trunk_length | **0.1938**       | ✅     |
| `hip_mid_jitter_norm` | thigh_length | 0.2130           |        |
| `stance_width_norm`   | trunk_length | **0.1654**       | ✅     |
| `stance_width_norm`   | thigh_length | 0.1881           |        |

`trunk_length` won on **both** features, and on **both** CV and raw variance (so the
scale-confound described above did not decide the outcome). It is the shipped
`norm_ref_strategy` in `backend/app/module_b/squat/config.py`.

**Important: `thigh_length` (hip-to-knee) — the proposal's original worked example — is
computed in the code (`features.py`, used only as the losing bake-off candidate) but is
NOT one of the 13 shipped features and is NOT the reference actually used.** The
proposal's example needs updating to `stance_width_norm` / `hip_mid_jitter_norm`,
normalised by `trunk_length`.

### 3.4 What normalisation is for now (the corrected justification)

Cancelling **genuine body-size differences between people** — a taller person really
does have a longer trunk and a naturally wider stance, in real metres, independent of
camera distance. This is the only job left once world landmarks removed the
camera-distance problem at the source (§2).

The bake-off's own evidence supports exactly this framing: it measures **cross-subject**
spread (different people, same movement), not camera-distance spread. The evidence you
already have in the repo supports the body-size justification, not the old
camera-distance one.

### 3.5 The one honest caveat to keep

MediaPipe's world landmarks are themselves an **estimate** from a learned body model
(not measured 3D, e.g. not mocap) — the metric scale it assigns to a given person is
approximate, partly regressed toward a canonical body shape. Normalising by a trunk
length measured on **that same person, in that same session's frames**, cancels
whatever per-person scale MediaPipe itself assigned, which is why the step still
measurably helps (per the bake-off's CV numbers) even though the input is already
metric.

One small supporting detail: `hip_mid_jitter_norm`'s displacement is computed with
`in_plane=True` (`_hip_mid_jitter_norm` in `features.py`), deliberately dropping the
z-axis — consistent with treating the depth axis as the least reliable one, even under
the metric world-landmark representation.

---

## 4. Summary table: proposal claim → current reality

| Proposal claim                               | Still true?                                                                                                                                                                                              | Current reality                                                                                                                                                                                                                                                                                                     |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "Because of user height AND camera distance" | **Half.**                                                                                                                                                                                                | Height: yes, still the reason. Camera distance: **no longer the operative reason** — world landmarks solve it at the source.                                                                                                                                                                                        |
| "Hip-to-knee segment length" example         | **No.**                                                                                                                                                                                                  | `thigh_length` (hip-to-knee) lost the bake-off; the shipped normalised features are `stance_width_norm` and `hip_mid_jitter_norm`, both normalised by `trunk_length`.                                                                                                                                               |
| "Banding only, never exact degrees"          | **Contradicted by the shipped UI** — see the separate deviations-table entry on this; `Report.tsx` displays exact degree values (`knee_rom_deg`, `avg_trunk_lean_deg`, `leg_angle_deg`) alongside bands. |                                                                                                                                                                                                                                                                                                                     |
| "Stable under viewpoint changes"             | **Different mechanism, same goal.**                                                                                                                                                                      | The system does not achieve invariance _across_ viewpoints — it **requires one fixed viewpoint** (`required_view: "side_view"` for squat) and gates out frames where the camera isn't correctly positioned (e.g. WBLT's `lateral_alignment_max_hip_x_norm`). Constraining the view, not being robust to it varying. |

---

## 5. MediaPipe capture data flow — proposed understanding vs. verified code

This section checks a 6-step description of the capture pipeline (as understood by the
project author) against the actual source code, line by line. Every claim below was
checked directly — none of it is inferred.

### 5.0 The proposed understanding (as given)

> 1. Image-space landmarks are smoothed over four frames for skeleton display and used
>    for capture-quality/in-frame checks.
> 2. Raw world landmarks are captured from MediaPipe.
> 3. Module B sends only timestamps and world landmarks to the backend.
> 4. The backend treats visibility below 0.6 as uncertain, fills gaps of at most five
>    frames, releases long occlusions and applies One Euro smoothing.
> 5. The preprocessed world stream is segmented into repetitions.
> 6. The 13 features and three fault gates are calculated.

### 5.1 Verdict: correct in substance, on every step. Below is the precise mechanics for each.

**Step 1 — confirmed exactly, including the number "four."**
`frontend/src/hooks/useMediaPipePose.ts:78` calls `createLandmarkSmoother(4)`. The
implementation (`frontend/src/utils/poseLandmarks.ts::createLandmarkSmoother`) keeps a
rolling history of up to `windowSize` (4) past frames and returns, per landmark, the
plain mean of `x`, `y`, `z`, and `visibility` across whatever is currently in that
history (1 up to 4 frames — it does not wait to fill the window before smoothing). This
is applied **only** to `landmarks` (image-space), never to `worldLandmarks`. Confirmed
consumers of the smoothed `landmarks`:

- Skeleton/pose overlay rendering (drawn from the same `landmarks` state).
- Capture-quality functions in `frontend/src/utils/captureQuality.ts`
  (`computeFrameQuality`, `computeFullBodyQuality`, `areHeadAndFeetVisible`,
  `computeWbltLegQuality`) — confirmed called with `landmarks` (not `worldLandmarks`) at
  their call sites, e.g. `CameraSetup.tsx:60/62` and
  `SquatLiveSessionPage.tsx:136`.

**Step 2 — confirmed.** `useMediaPipePose.ts` sets `worldLandmarks` directly from
`result.worldLandmarks[0]` with only a field-mapping (`x`, `y`, `z`,
`visibility`) — no smoothing function is applied client-side. This is genuinely the raw
per-frame MediaPipe output.

**Step 3 — confirmed exactly.** `frontend/src/services/moduleBService.ts::analyze()`
constructs the request body as:

```ts
frames: frames.map((f) => ({
  timestampMs: f.timestampMs,
  worldLandmarks: f.worldLandmarks,
})),
```

No `landmarks` (image-space) field is included in the Module B payload — only
`timestampMs` and `worldLandmarks`, exactly as proposed. (Module A's recorder buffers the
same richer `PoseFrame` type internally, per `useSessionRecorder.ts`'s own comment, but
Module B's own service call narrows the wire payload to these two fields specifically.)

**Step 4 — confirmed, with the precise order and mechanics.**
`backend/app/module_b/core/preprocessing.py::preprocess_world_landmarks()` — its own
docstring states the order plainly: **"Confidence filter -> gap fill -> One Euro, in
that order."** The two numeric thresholds:

- `MIN_VISIBILITY = 0.6` (`backend/app/module_a/core/config.py:9`, reused by Module B —
  "landmark ignored (hold-last) below this visibility") — this is the "uncertain below
  0.6" gate, and it is what identifies which frames/landmarks need gap-filling or
  release in the first place.
- `MODULE_B_CORE_CONFIG["interpolation_max_gap_frames"] = 5` — the exact "at most five
  frames" cap.

The actual function body, in order:

1. `_fill_gaps(frames, max_gap_frames=5)` — short runs of low-visibility frames (≤5)
   are linearly interpolated between the last good anchor and the next one.
2. `_release_persistent_occlusions(filled, max_gap_frames)` — for a run **longer** than
   5 frames, instead of freezing the landmark at its last known value (which the
   downstream smoother would otherwise do), this raises that run's visibility to
   _exactly_ `MIN_VISIBILITY`. This is a deliberate mechanism, not a separate
   independent "release" step: it exists specifically so the next stage (the smoother)
   treats the landmark as barely-valid and smooths its own raw, uncertain trajectory
   rather than hold-lasting a stale position for the rest of a squat rep. The
   docstring's own justification: a persistently-occluded landmark (documented
   elsewhere in this project as the far leg in a side-view squat, visibility
   0.59–0.78) "still tracks a plausible trajectory... it is low-confidence, not wrong,"
   so releasing it is better than freezing it.
3. `LandmarkSmoother.smooth_frame()` (reused from `app.module_a.core.smoothing`, **not
   forked** — the same module both Module A and Module B call, to keep the two
   pipelines from silently drifting apart) — this is the One Euro filter pass. By the
   time it runs, nothing is still below `MIN_VISIBILITY` (step 2 already released any
   long run up to exactly that value), so its own internal hold-last branch never
   triggers here — it purely smooths.

So "releases long occlusions" is not a 4th sequential stage after One Euro as a literal
reading of the proposed order might suggest — it is a preparatory step that runs
**between** gap-fill and One Euro, specifically so that One Euro's own smoothing (not a
separate freeze) is what happens to long-occluded landmarks. The proposed description's
ordering is functionally correct; this is the added precision.

**Step 5 — confirmed.** The preprocessed world-landmark stream (the return value of
`preprocess_world_landmarks()`) is what `backend/app/module_b/squat/segmentation.py`
consumes to detect rep boundaries (`worldLandmarks` accessed via `_frame_value(frame,
"worldLandmarks")`).

**Step 6 — confirmed.** `backend/app/module_b/squat/features.py::extract_squat_features()`
computes the 13 shipped features (§3.2 above) from the same preprocessed stream, and
`backend/app/module_b/squat/fault_gates.py::evaluate_fault_gates()` computes the three
fault gates (depth, lean, heel-rise) from it independently.

### 5.2 One thing to add to the proposal's description, not in the original 6 steps

The proposed flow doesn't mention that the **raw** (pre-preprocessing) frames are
_also_ used separately — `router.py` computes the session's raw capture-quality score
(`valid_frame_ratio`, using `MODULE_B_CORE_CONFIG["confidence_threshold"] = 0.6`,
the same numeric value as `MIN_VISIBILITY` but a logically separate configuration
constant) directly on the raw stream, **before** any gap-fill/release/smoothing runs.
This is deliberate — `_release_persistent_occlusions`'s own docstring notes "the
capture-quality metric is computed on the raw frames upstream... so raising \[the
visibility] here cannot flatter a quality score." Worth stating explicitly: the
capture-quality number a user's report shows is never inflated by the preprocessing
pipeline's own occlusion-handling.

---

## 6. Code reference index (for direct lookup)

- `backend/app/module_b/squat/config.py` — `norm_ref_strategy: "trunk_length"`, `fault_gates` thresholds
- `backend/app/module_b/squat/features.py` — `_norm_ref()`, `_hip_mid_jitter_norm()`, `trunk_length`/`thigh_length` computation
- `backend/app/module_b/squat/fault_gates.py` — `_heel_rise_peak_norm()` (rule-only, also trunk-length-normalised)
- `ml/artifacts/squat/feature_schema.json` — the frozen 13-feature list
- `ml/reports/NORM_REF_BAKEOFF.md` — the trunk_length vs thigh_length decision and CV numbers
- `ml/reports/MOCAP_AGREEMENT.md` — the -11.96° bias finding (relevant to the separate exact-degree deviation, not to normalisation directly, but from the same measurement lineage)
- `frontend/src/hooks/useMediaPipePose.ts` — confirms both `landmarks` and `worldLandmarks` are captured per frame; `worldLandmarks` comment reads "metric, hip-centered — used for Module A joint-angle geometry"
- `frontend/src/utils/poseLandmarks.ts` — `createLandmarkSmoother()`, the 4-frame image-space smoother
- `frontend/src/utils/captureQuality.ts` — capture-quality functions, all operating on image-space `landmarks`
- `frontend/src/services/moduleBService.ts` — the exact `{timestampMs, worldLandmarks}` payload sent for analysis
- `backend/app/module_b/core/preprocessing.py` — `preprocess_world_landmarks()`, `_fill_gaps()`, `_release_persistent_occlusions()`
- `backend/app/module_b/core/config.py` — `confidence_threshold: 0.6`, `interpolation_max_gap_frames: 5`
- `backend/app/module_a/core/config.py` — `MIN_VISIBILITY = 0.6`
- `backend/app/module_a/core/smoothing.py` — `LandmarkSmoother` (the shared One Euro implementation, reused by both modules)
- `backend/app/module_b/squat/segmentation.py` — rep-boundary detection on the preprocessed world stream
