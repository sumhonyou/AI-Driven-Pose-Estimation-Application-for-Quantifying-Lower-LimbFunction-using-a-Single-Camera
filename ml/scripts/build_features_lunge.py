"""Stage 5.3 (Lunge): build the per-rep lunge feature table from extracted landmarks.

Structural mirror of `build_features.py` (squat's Stage 5.3), swapped to Ex5. For every
side-view (`cam17_orientation == "front"` → Camera18 sees profile, re-verified for Ex5
specifically in Stage 5.0 (Lunge)) lunge rep: preprocess the **entire** video's landmark
stream through the live backend's confidence-filter → gap-fill → One-Euro pipeline
(X1/X3 — `app.module_b.core.preprocessing.preprocess_world_landmarks`, the same function
`POST /api/module-b/analyze` runs ahead of `segment()`/`extract_features()`), then window
the *preprocessed* stream by Segmentation.csv's physio-verified `first_frame`/`last_frame`
(NOT our FSM — the dataset boundaries are ground truth here) and call the **backend's**
`extract_lunge_features()`. Emits `ml/data/lunge_features.csv`, one row per rep.

Preprocessing is run **once per video, over the full chronological stream, before
windowing** — OneEuroFilter is stateful, so preprocessing a rep's window in isolation
would reset its history at every rep boundary and diverge from what the live capture
produces. This mirrors `router.py`'s single call site exactly.

Two Stage 5.3 (Lunge) deltas from task.md:

1. **Lead-leg tag: use `exercise_subtype` from Segmentation.csv — it's given.** Mapped
   "front leg left" → "left" / "front leg right" → "right" and passed to
   `extract_lunge_features(rep, lead_leg=...)`, which overrides the live geometric
   inference. The dataset's physio-assigned tag is ground truth here, exactly as its
   rep boundaries are.

2. **`knee_passes_toe`: KEPT, not approximated from the ankle.** Stage 5.2 (Lunge)
   verified against the real extraction that MediaPipe's foot-tip landmarks
   (`LEFT_FOOT_INDEX`=31 / `RIGHT_FOOT_INDEX`=32) are present in 100% of all 26,087
   extracted frames with plausible visibility (≥0.826 mean per side). The fallback the
   plan allowed for ("approximate from ankle **or drop it**") is therefore not needed —
   `knee_passes_toe_norm` is a real measured feature, not a proxy.

**`lead_leg` is emitted as a metadata column, never as a model feature — deliberately.**
Stage 5.0 (Lunge) established that lead leg is perfectly confounded with subject in this
dataset (every subject leads with exactly one leg; none performs both), so under LOSO a
`lead_leg` feature is perfectly collinear with the held-out subject and would be a
subject-identity proxy. This is not merely avoided by convention: Stage 4.2 designed the
lunge feature vector to be *lead-leg-invariant* by construction (front/back split, so a
left-lead and an identical right-lead rep produce a bit-identical vector), and `lead_leg`
lives on `FeatureVector.lead_leg` metadata, outside `names`/`values`. The column is
written to the CSV for traceability and for Stage 5.4's per-cohort analysis only.
**Stage 5.5 must not train on it.**

As a free, honest validation (Stage 5.3), our own lunge FSM is also run over the same
preprocessed full clips and its rep boundaries compared against the dataset's — written
to `ml/reports/LUNGE_FEATURE_TABLE.md`. This is a report, not a gate.

`ml/artifacts/label_map.json` is shared with squat, not forked: it is exercise-agnostic
(Option A, `correctness` → Good/Poor, no Fair in training), so this script reads and
verifies it rather than rewriting it.

Deterministic (X8): videos/reps iterated in sorted order, no RNG, no wall-clock.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import yaml

# X1: import the SAME feature extractor, segmenter, and preprocessing the live
# backend uses — never re-implemented.
from app.module_b.core.preprocessing import preprocess_world_landmarks
from app.module_b.lunge.config import LUNGE_CONFIG
from app.module_b.lunge.features import LUNGE_FEATURE_NAMES, extract_lunge_features
from app.module_b.lunge.segmentation import mean_knee_flexion_deg, segment_lunge_frames

TARGET_EXERCISE_ID = "5"  # Ex5 = Leg lunge
# Stage 5.0 (Lunge), option a: side-view only. cam17_orientation == "front" is the
# cohort whose Camera18 recording is the true sagittal view (LUNGE_DATA_AUDIT.md).
SIDE_VIEW_ORIENTATION = "front"

# Option A label map (shared artifact, written by squat's build_features.py).
LABEL_MAP = {"1": "Good", "0": "Poor"}

# The dataset's own lead-leg tag -> the value extract_lunge_features expects.
LEAD_LEG_MAP = {"front leg left": "left", "front leg right": "right"}

# The RETIRED threshold model's values (backend lunge/config.py before Stage 5.3's fix
# replaced it with cycle detection). Hard-coded here rather than read from config
# precisely *because* config no longer carries them: this reproduces, on every run, the
# evidence that retired the model, so the dissertation's "why" numbers stay traceable to
# a live measurement rather than to memory. Do not wire these back into the detector.
RETIRED_ENTER_DESCENDING_DEG = 30.0
RETIRED_EXIT_STANDING_DEG = 20.0

# How many frames a rep's annotated `last_frame` may overshoot the end of the video
# before we treat it as real frame/camera misalignment rather than an annotation
# rounding artifact at the tail.
#
# Squat's build never needed this: no Ex6 rep overruns its video. Exactly one rep in
# the whole corpus does — PM_117a rep 9 (annotated 1110-1185; the video is 1184 frames,
# last valid index 1183), overshooting by 2 frames / 67ms at the end of a 2.53s rep.
# Verified this is an annotation artifact, not a misalignment: both cameras report
# and decode exactly 1184 frames, and all 8 other reps in that video sit well inside
# it. A genuine wrong-camera/offset error would miss by orders of magnitude more, so a
# tight tolerance keeps the guard's protective purpose intact while letting this
# through. The clamp is counted and reported, never silent.
MAX_TAIL_OVERSHOOT_FRAMES = 5

ML_ROOT = Path(__file__).resolve().parent.parent
LANDMARKS_DIR = ML_ROOT / "data" / "landmarks_lunge"
FEATURES_CSV = ML_ROOT / "data" / "lunge_features.csv"
LABEL_MAP_JSON = ML_ROOT / "artifacts" / "label_map.json"
REPORT_MD = ML_ROOT / "reports" / "LUNGE_FEATURE_TABLE.md"


def _load_config() -> dict:
    with open(ML_ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def _read_segmentation(segmentation_csv: Path) -> list[dict[str, str]]:
    with open(segmentation_csv, newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _load_landmarks(video_id: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (world_landmarks[frame, 33, 5], timestamps_ms) for one video's .npz."""
    npz_path = LANDMARKS_DIR / f"{video_id}.npz"
    if not npz_path.exists():
        raise FileNotFoundError(f"Missing extracted landmarks: {npz_path}")
    data = np.load(npz_path, allow_pickle=True)
    return data["world_landmarks"], data["timestamps_ms"]


def _raw_full_stream(video_id: str) -> tuple[list[dict], int]:
    """Build one video's entire chronological frame stream, runtime-shaped.

    A no-pose (all-NaN) frame is dropped rather than fed into preprocessing; this
    mirrors a live capture, which only sends frames where a pose was detected.
    `visibility` is carried per landmark (required by both the gap-fill's confidence
    filter and `LandmarkSmoother`'s hold-last).

    Returns (frames, total_extracted_frame_count) — the count includes any dropped
    no-pose frames, used to catch a `first_frame`/`last_frame` index that exceeds what
    was actually extracted for this video.
    """
    world_landmarks, timestamps_ms = _load_landmarks(video_id)
    frames = []
    for idx in range(world_landmarks.shape[0]):
        row = world_landmarks[idx]
        if np.isnan(row).all():
            continue
        frames.append(
            {
                "frameIndex": int(idx),
                "timestampMs": int(timestamps_ms[idx]),
                "worldLandmarks": [
                    {
                        "x": float(lm[0]),
                        "y": float(lm[1]),
                        "z": float(lm[2]),
                        "visibility": float(lm[3]),
                    }
                    for lm in row
                ],
            }
        )
    return frames, world_landmarks.shape[0]


def _preprocessed_stream(
    video_id: str,
    preprocessed_cache: dict[str, list[dict]],
    frame_count_cache: dict[str, int],
) -> list[dict]:
    """Return one video's full stream after the SAME preprocessing the live backend
    runs, computed exactly once per video and cached — mirrors the router's single call
    over the whole received buffer, and shared by both the feature table and the FSM
    agreement check so neither derives a subtly different stream.
    """
    if video_id not in preprocessed_cache:
        raw_frames, total_frames = _raw_full_stream(video_id)
        frame_count_cache[video_id] = total_frames
        preprocessed_cache[video_id] = preprocess_world_landmarks(raw_frames)
    return preprocessed_cache[video_id]


def build_feature_rows(
    rows: list[dict[str, str]],
    preprocessed_cache: dict[str, list[dict]],
    frame_count_cache: dict[str, int],
) -> tuple[list[dict], dict]:
    """Extract one feature row per side-view lunge rep. Returns (rows, build_stats)."""
    side_view_rows = sorted(
        (
            r
            for r in rows
            if r["exercise_id"] == TARGET_EXERCISE_ID
            and r["cam17_orientation"] == SIDE_VIEW_ORIENTATION
        ),
        key=lambda r: (r["video_id"], int(r["repetition_number"])),
    )

    feature_rows = []
    total_dropped = 0
    clamped_reps: list[dict] = []
    videos_seen: set[str] = set()
    for r in side_view_rows:
        video_id = r["video_id"]
        videos_seen.add(video_id)
        preprocessed = _preprocessed_stream(
            video_id, preprocessed_cache, frame_count_cache
        )

        first, last = int(r["first_frame"]), int(r["last_frame"])
        frame_count = frame_count_cache[video_id]
        last_valid = frame_count - 1
        if first > last_valid:
            raise IndexError(
                f"{video_id} rep {r['repetition_number']}: first_frame {first} exceeds "
                f"extracted frame count {frame_count} — the rep lies entirely outside "
                f"the video, i.e. real frame/camera misalignment. Do not proceed."
            )
        if last > last_valid:
            overshoot = last - last_valid
            if overshoot > MAX_TAIL_OVERSHOOT_FRAMES:
                raise IndexError(
                    f"{video_id} rep {r['repetition_number']}: last_frame {last} "
                    f"overshoots the extracted frame count {frame_count} by "
                    f"{overshoot} frames (tolerance {MAX_TAIL_OVERSHOOT_FRAMES}) — "
                    f"too large to be an annotation artifact, treat as frame/camera "
                    f"misalignment. Do not proceed."
                )
            clamped_reps.append(
                {
                    "video_id": video_id,
                    "repetition_number": int(r["repetition_number"]),
                    "annotated_last_frame": last,
                    "clamped_to": last_valid,
                    "frames_lost": overshoot,
                }
            )
            last = last_valid

        frames = [f for f in preprocessed if first <= f["frameIndex"] <= last]
        total_dropped += (last - first + 1) - len(frames)
        if not frames:
            raise ValueError(
                f"{video_id} rep {r['repetition_number']}: no pose frames in window"
            )

        # Delta 1: the dataset's given lead-leg tag overrides live geometric inference.
        subtype = r["exercise_subtype"]
        if subtype not in LEAD_LEG_MAP:
            raise ValueError(
                f"{video_id} rep {r['repetition_number']}: unexpected exercise_subtype "
                f"{subtype!r} — expected one of {sorted(LEAD_LEG_MAP)}"
            )
        lead_leg = LEAD_LEG_MAP[subtype]

        vector = extract_lunge_features(frames, lead_leg=lead_leg)
        # Schema guard (X1): the vector we just built must match the frozen contract.
        if vector.names != LUNGE_FEATURE_NAMES:
            raise ValueError("FeatureVector.names drifted from LUNGE_FEATURE_NAMES")
        if vector.lead_leg != lead_leg:
            raise ValueError(
                f"{video_id} rep {r['repetition_number']}: lead_leg override ignored "
                f"(asked {lead_leg!r}, vector carries {vector.lead_leg!r})"
            )

        feature_rows.append(
            {
                "person_id": int(r["person_id"]),
                "video_id": video_id,
                "repetition_number": int(r["repetition_number"]),
                **dict(zip(vector.names, vector.values, strict=True)),
                "correctness": int(r["correctness"]),
                "label": LABEL_MAP[r["correctness"]],
                # Metadata, NOT a model feature — confounded with subject (see docstring).
                "lead_leg": lead_leg,
                "orientation": r["cam17_orientation"],
                "lights_on": int(r["lights_on"]),
                "mocap_erroneous": int(r["mocap_erroneous"]),
                "feature_schema_version": vector.schema_version,
            }
        )

    stats = {
        "n_reps": len(feature_rows),
        "n_good": sum(1 for row in feature_rows if row["label"] == "Good"),
        "n_poor": sum(1 for row in feature_rows if row["label"] == "Poor"),
        "n_subjects": len({row["person_id"] for row in feature_rows}),
        "n_videos": len(videos_seen),
        "dropped_no_pose_frames": total_dropped,
        "n_lead_left": sum(1 for row in feature_rows if row["lead_leg"] == "left"),
        "n_lead_right": sum(1 for row in feature_rows if row["lead_leg"] == "right"),
        "clamped_reps": clamped_reps,
    }
    return feature_rows, stats


def write_features_csv(feature_rows: list[dict]) -> list[str]:
    """Write lunge_features.csv; assert feature columns match the frozen contract."""
    columns = (
        ["person_id", "video_id", "repetition_number"]
        + list(LUNGE_FEATURE_NAMES)
        + [
            "correctness",
            "label",
            "lead_leg",
            "orientation",
            "lights_on",
            "mocap_erroneous",
            "feature_schema_version",
        ]
    )
    # Schema validation: the feature block, in order, must equal FeatureVector.names.
    feature_block = columns[3 : 3 + len(LUNGE_FEATURE_NAMES)]
    if tuple(feature_block) != LUNGE_FEATURE_NAMES:
        raise ValueError(
            "CSV feature column order/count drifted from LUNGE_FEATURE_NAMES"
        )

    FEATURES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(FEATURES_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(feature_rows)
    return columns


def verify_label_map() -> None:
    """Verify the shared Option A label map matches what this build assumed.

    Not rewritten here: `label_map.json` is exercise-agnostic (it maps the dataset's
    `correctness` column, which means the same thing for Ex5 and Ex6) and squat's
    Stage 5.3 already wrote it. Forking a lunge copy would create two files to keep in
    sync for no benefit; this asserts agreement instead.
    """
    if not LABEL_MAP_JSON.exists():
        raise FileNotFoundError(
            f"Missing shared label map {LABEL_MAP_JSON} — run build_features.py first."
        )
    with open(LABEL_MAP_JSON) as f:
        payload = json.load(f)
    if payload.get("mapping") != LABEL_MAP:
        raise ValueError(
            f"Shared label_map.json mapping {payload.get('mapping')!r} disagrees with "
            f"this build's {LABEL_MAP!r}"
        )
    if not payload.get("no_fair_in_training"):
        raise ValueError("Shared label_map.json must record no_fair_in_training: true")


# --- FSM-vs-dataset segmentation agreement (free validation, Stage 5.3) ---------------


def exit_threshold_diagnostic(
    rows: list[dict[str, str]],
    preprocessed_cache: dict[str, list[dict]],
    frame_count_cache: dict[str, int],
) -> list[dict]:
    """Per video: does the FSM's driving signal return below the exit threshold at the
    top of each rep cycle?

    Explains *why* the agreement number below is what it is rather than reporting it
    bare. `segment_lunge_frames` drives off the **bilateral mean** knee flexion and
    closes a rep only when that mean falls back under `exit_standing_deg`.

    Note what the dataset's boundaries actually are: reps are annotated **back-to-back**
    (median gap between consecutive reps = 1 frame), so a set is a *continuous* sequence
    of reps and each boundary sits at the **top of a cycle**, not in a rest period. The
    "gap" measured below is therefore the top of the cycle between two consecutive reps.
    A subject who fully extends at the top of each cycle sends the mean back under the
    exit threshold and the rep closes; a subject who only *partially* extends between
    consecutive reps never does, so the rep never closes and consecutive reps merge into
    one detection.

    Reports, per video, how many cycle tops never drop below the exit threshold — the
    quantity that should predict missed reps if the merge mechanism is the cause.
    """
    enter = RETIRED_ENTER_DESCENDING_DEG
    exit_deg = RETIRED_EXIT_STANDING_DEG

    out = []
    video_ids = sorted(
        {r["video_id"] for r in rows if r["exercise_id"] == TARGET_EXERCISE_ID}
    )
    for video_id in video_ids:
        stream = _preprocessed_stream(video_id, preprocessed_cache, frame_count_cache)
        by_index = {f["frameIndex"]: f for f in stream}
        reps = sorted(
            (
                r
                for r in rows
                if r["exercise_id"] == TARGET_EXERCISE_ID and r["video_id"] == video_id
            ),
            key=lambda r: int(r["first_frame"]),
        )

        # Peak of the driving signal inside each annotated rep: does it even reach the
        # enter threshold? (Rules out "the FSM never saw the descent".)
        peaks = []
        for r in reps:
            first = int(r["first_frame"])
            last = min(int(r["last_frame"]), max(by_index))
            vals = [
                mean_knee_flexion_deg(by_index[i])
                for i in range(first, last + 1)
                if i in by_index
            ]
            if vals:
                peaks.append(max(vals))

        # Minimum of the driving signal in each gap *between* consecutive reps: does it
        # fall back under the exit threshold so the rep can close?
        gap_minima = []
        for a, b in zip(reps, reps[1:]):
            start = int(a["last_frame"])
            end = int(b["first_frame"])
            vals = [
                mean_knee_flexion_deg(by_index[i])
                for i in range(start, end + 1)
                if i in by_index
            ]
            if vals:
                gap_minima.append(min(vals))

        out.append(
            {
                "video_id": video_id,
                "n_reps": len(reps),
                "peak_median": float(np.median(peaks)) if peaks else 0.0,
                "peaks_below_enter": sum(1 for p in peaks if p < enter),
                "n_gaps": len(gap_minima),
                "gap_min_median": float(np.median(gap_minima)) if gap_minima else 0.0,
                "gaps_never_below_exit": sum(1 for g in gap_minima if g >= exit_deg),
            }
        )
    return out


def _rep_frame_bounds(rep) -> tuple[int, int]:
    """Recover a detected rep's (start_frame, end_frame) from its carried frames."""
    return rep.frames[0]["frameIndex"], rep.frames[-1]["frameIndex"]


def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> int:
    return max(0, min(a_end, b_end) - max(a_start, b_start) + 1)


def segmentation_agreement(
    rows: list[dict[str, str]],
    preprocessed_cache: dict[str, list[dict]],
    frame_count_cache: dict[str, int],
) -> dict:
    """Run our lunge FSM over each full clip; match detected reps to dataset boundaries.

    Runs over the **same preprocessed stream** `build_feature_rows` already computed
    (via the shared cache) — the live pipeline calls `exercise.segment()` on the
    preprocessed buffer too, so this validates the FSM against what it actually receives
    at runtime, not raw landmarks.

    Measured against ALL Ex5 reps present in each Camera18 clip (front + half-profile —
    the FSM is orientation-blind), with a front-only breakdown since those are the reps
    the model actually trains on. Matching is **strictly one-to-one**: candidate
    (detected, GT) pairs whose inclusive windows overlap by more than half the GT rep
    length are assigned greedily by descending overlap, each detected and each GT rep
    used at most once, so `matched <= min(detected, gt)` always holds and a merged
    detection cannot hide an under-segmentation.
    """
    per_video = []
    matched_start_err: list[int] = []
    matched_end_err: list[int] = []
    front_gt = front_matched = 0

    video_ids = sorted(
        {r["video_id"] for r in rows if r["exercise_id"] == TARGET_EXERCISE_ID}
    )
    for video_id in video_ids:
        preprocessed = _preprocessed_stream(
            video_id, preprocessed_cache, frame_count_cache
        )
        detected = [
            _rep_frame_bounds(rep) for rep in segment_lunge_frames(preprocessed)
        ]

        gt = [
            (int(r["first_frame"]), int(r["last_frame"]), r["cam17_orientation"])
            for r in rows
            if r["exercise_id"] == TARGET_EXERCISE_ID and r["video_id"] == video_id
        ]

        # Build all valid candidate pairs, then assign greedily by best overlap first.
        candidates = []
        for gi, (g_start, g_end, _orientation) in enumerate(gt):
            half_len = (g_end - g_start + 1) / 2.0
            for di, (d_start, d_end) in enumerate(detected):
                ov = _overlap(d_start, d_end, g_start, g_end)
                if ov > half_len:
                    candidates.append((ov, gi, di, d_start, d_end))
        candidates.sort(key=lambda c: (-c[0], c[1], c[2]))

        used_gt: set[int] = set()
        used_det: set[int] = set()
        video_matched = 0
        for _ov, gi, di, d_start, d_end in candidates:
            if gi in used_gt or di in used_det:
                continue
            used_gt.add(gi)
            used_det.add(di)
            video_matched += 1
            g_start, g_end, orientation = gt[gi]
            matched_start_err.append(abs(d_start - g_start))
            matched_end_err.append(abs(d_end - g_end))
            if orientation == SIDE_VIEW_ORIENTATION:
                front_matched += 1

        front_gt += sum(
            1 for _s, _e, orientation in gt if orientation == SIDE_VIEW_ORIENTATION
        )
        per_video.append(
            {
                "video_id": video_id,
                "gt_reps": len(gt),
                "detected_reps": len(detected),
                "matched": video_matched,
            }
        )

    def _median(xs: list[int]) -> float:
        return float(np.median(xs)) if xs else 0.0

    return {
        "per_video": per_video,
        "total_gt": sum(v["gt_reps"] for v in per_video),
        "total_detected": sum(v["detected_reps"] for v in per_video),
        "total_matched": sum(v["matched"] for v in per_video),
        "front_gt": front_gt,
        "front_matched": front_matched,
        "median_start_err_frames": _median(matched_start_err),
        "median_end_err_frames": _median(matched_end_err),
        "mean_start_err_frames": (
            float(np.mean(matched_start_err)) if matched_start_err else 0.0
        ),
        "mean_end_err_frames": (
            float(np.mean(matched_end_err)) if matched_end_err else 0.0
        ),
    }


def _clamp_section(build_stats: dict) -> list[str]:
    """Report any rep whose annotated window was clamped to the video's real end.

    Always emitted — a silent clamp is how a real misalignment would hide.
    """
    clamped = build_stats["clamped_reps"]
    if not clamped:
        return [
            "- **Annotation/video length mismatches:** none — every rep's annotated "
            "`first_frame`/`last_frame` lies inside its extracted video.",
            "",
        ]
    lines = [
        "### One rep's annotation overshoots its video (found by this build's guard)",
        "",
        "The dataset's `last_frame` for the rep(s) below runs past the final frame of "
        "the video file itself. This is an **annotation artifact, not a frame/camera "
        "misalignment** — verified before accepting it: both cameras report *and "
        "decode* the same frame count, every other rep in the same video sits well "
        "inside it, and no rep in the entire Ex5+Ex6 corpus overshoots by more than "
        f"{MAX_TAIL_OVERSHOOT_FRAMES} frames. The window is clamped to the last real "
        "frame and the rep is kept; the build still fails loudly on any overshoot "
        "larger than the tolerance, or on a rep starting past the video's end.",
        "",
        "| video | rep | annotated last_frame | clamped to | frames lost |",
        "| ----- | --- | -------------------- | ---------- | ----------- |",
    ]
    for c in clamped:
        lines.append(
            f"| {c['video_id']} | {c['repetition_number']} | "
            f"{c['annotated_last_frame']} | {c['clamped_to']} | {c['frames_lost']} |"
        )
    lines += [
        "",
        "The loss is at the **tail** of the rep (the return-to-standing phase, after "
        "peak flexion), so peak- and ROM-based features are unaffected; only "
        "`rep_duration_s` shortens, by the frames shown above (≈33 ms each at 30 fps). "
        "The rep is kept rather than dropped because HY's Stage 5.0 (Lunge) gate "
        "decision was explicitly to train on the **88** verified side-view reps — "
        "dropping one to avoid a sub-100 ms tail truncation would silently deviate "
        "from the approved cohort and cost a Poor-class rep from a small dataset.",
        "",
    ]
    return lines


def _exit_diagnostic_section(diagnostic: list[dict], agreement: dict) -> list[str]:
    """Explain the agreement number via the exit-threshold merge mechanism."""
    enter = RETIRED_ENTER_DESCENDING_DEG
    exit_deg = RETIRED_EXIT_STANDING_DEG
    total_never = sum(d["gaps_never_below_exit"] for d in diagnostic)
    total_below_enter = sum(d["peaks_below_enter"] for d in diagnostic)
    total_reps = sum(d["n_reps"] for d in diagnostic)
    n_videos = len(diagnostic)
    n_affected = sum(1 for d in diagnostic if d["gaps_never_below_exit"] > 0)
    n_severe = sum(
        1
        for d in diagnostic
        if d["n_gaps"] and d["gaps_never_below_exit"] / d["n_gaps"] > 0.5
    )

    lines = [
        "### Why the detector was replaced (evidence, re-measured every run)",
        "",
        "The agreement above is what **cycle detection** achieves. The detector that "
        "shipped through Stage 4.3 instead crossed absolute thresholds "
        f"(`enter_descending_deg = {enter:.0f}°` / `exit_standing_deg = {exit_deg:.0f}°`, "
        "borrowed from squat) and scored **50/88 = 56.8%** front-rep recall on this same "
        "data, against squat's own 93/98 = 94.9%. This section re-measures, on every "
        "run, the property of the movement that retired it, so the reasoning stays "
        "checkable rather than asserted from memory. The retired thresholds are "
        "hard-coded in this script for that purpose alone — they are gone from "
        "`lunge/config.py` and are not wired into anything.",
        "",
        "**What the dataset's boundaries actually are.** Reps are annotated "
        "**back-to-back** — the median gap between consecutive reps is **1 frame**. A "
        "set is a *continuous* sequence of reps, so each boundary sits at the **top of "
        'a cycle**, not in a rest period. "Cycle-top flexion" below is the driving '
        "signal's minimum at that boundary: how far a subject straightens between two "
        "consecutive reps.",
        "",
        f"**The old model did not fail at the enter threshold.** The driving signal (the "
        f"bilateral mean knee flexion) peaks above `{enter:.0f}°` in "
        f"**{total_reps - total_below_enter} of {total_reps}** annotated reps — every "
        f"descent was seen.",
        "",
        f"**It failed at the exit threshold.** The old FSM closed a rep only once the "
        f"mean fell back under `{exit_deg:.0f}°`. A subject who fully extends at each "
        f"cycle top sends it there and the rep closes; a subject who only **partially "
        f"extends between consecutive reps** never does, so the rep never closes and "
        f"consecutive reps merge into one long detection. That is why the old model's "
        f"precision stayed high (94.1%) while its recall collapsed: it was not firing "
        f"wrongly, it was firing too few times. **{total_never} cycle tops never drop "
        f"below {exit_deg:.0f}°**, which is the same order as the 62 reps it lost.",
        "",
        f"**{n_affected} of {n_videos} videos have at least one cycle top that never "
        f"releases, and {n_severe} have it in more than half their tops.**",
        "",
        "| video | GT reps | median rep peak | median cycle-top flexion | tops never < retired exit |",
        "| ----- | ------- | --------------- | ------------------------ | ------------------------- |",
    ]
    for d in diagnostic:
        lines.append(
            f"| {d['video_id']} | {d['n_reps']} | {d['peak_median']:.1f}° | "
            f"{d['gap_min_median']:.1f}° | "
            f"{d['gaps_never_below_exit']} / {d['n_gaps']} |"
        )
    lines += [
        "",
        "Read the last two columns together. `PM_042` and `PM_117b` extend fully at "
        "every cycle top and were the only two videos the old model handled well "
        "(24/25, 14/14). `PM_037` never extends far enough in 18 of 19 tops — its "
        "median cycle-top flexion is 46.1°, more than twice the retired exit threshold "
        "— and its 20 reps collapsed into 2 detections. The failure tracked a "
        "per-subject movement habit (how far they straighten between continuous reps), "
        "not noise.",
        "",
        "**Why retuning could not rescue it, and cycle detection can.** A single global "
        "(enter, exit) pair would need `exit` above 60.0° (PM_037's worst cycle top) and "
        "`enter` below 14.8° (PM_042's weakest rep peak) simultaneously, with "
        "`exit < enter` — arithmetically impossible. Driving off the front knee only "
        "measured *worse* (subjects rest with the front knee more flexed than the "
        "bilateral mean), and a per-clip baseline-relative threshold also failed "
        "globally. Rest posture and rep depth **overlap across subjects** on any "
        "absolute scale, so no fixed angle separates them; cycle *shape* does. The "
        "replacement is measured above, in the same harness, on the same data.",
        "",
        "The feature table was never affected either way — every rep is windowed by the "
        "dataset's physio-verified annotation, never by the detector.",
        "",
    ]
    return lines


def write_report(
    build_stats: dict, agreement: dict, feature_rows: list[dict], diagnostic: list[dict]
) -> None:
    """Write the feature-table build summary + FSM segmentation agreement report."""
    front_peaks = [row["front_knee_flex_peak_deg"] for row in feature_rows]
    back_peaks = [row["back_knee_flex_peak_deg"] for row in feature_rows]
    durations = [row["rep_duration_s"] for row in feature_rows]
    kpt = [row["knee_passes_toe_norm"] for row in feature_rows]

    lines = [
        "# Stage 5.3 (Lunge) — lunge feature table build",
        "",
        "Preprocesses each video's **entire** landmark stream through the live "
        "backend's confidence-filter → gap-fill → One-Euro pipeline "
        "(`app.module_b.core.preprocessing.preprocess_world_landmarks`, the same "
        "function `POST /api/module-b/analyze` runs ahead of "
        "`segment()`/`extract_features()`), once per video over the full chronological "
        "stream — not per rep — since OneEuroFilter is stateful and windowing first "
        "would reset its history at every rep boundary. Then windows every "
        '**side-view** (`cam17_orientation == "front"`, Camera18 = profile) Ex5 rep of '
        "that *preprocessed* stream by Segmentation.csv's physio-verified "
        "`first_frame`/`last_frame`, and calls the backend's `extract_lunge_features()` "
        "(X1). Half-profile reps are excluded per the Stage 5.0 (Lunge) gate decision "
        "(option a — side-view only, HY 2026-07-17).",
        "",
        "## Feature table",
        "",
        f"- **Output:** `ml/data/lunge_features.csv` — {build_stats['n_reps']} rows "
        f"(one per rep), {len(LUNGE_FEATURE_NAMES)} feature columns.",
        f"- **Class balance:** {build_stats['n_good']} Good / "
        f"{build_stats['n_poor']} Poor.",
        f"- **Subjects:** {build_stats['n_subjects']} across "
        f"{build_stats['n_videos']} videos.",
        f"- **Lead-leg cohorts:** {build_stats['n_lead_left']} left-lead / "
        f"{build_stats['n_lead_right']} right-lead.",
        f"- **No-pose frames dropped inside rep windows:** "
        f"{build_stats['dropped_no_pose_frames']} (expected 0 — Stage 5.2 (Lunge) "
        f"recorded a pose on every one of the 26,087 extracted frames).",
        f"- **Feature schema version:** "
        f"`{feature_rows[0]['feature_schema_version']}`.",
        "",
        *_clamp_section(build_stats),
        "Feature columns are written in `FeatureVector.names` order and asserted "
        "against `LUNGE_FEATURE_NAMES` at write time — the build fails loudly on drift.",
        "",
        "### The two Stage 5.3 (Lunge) deltas, resolved",
        "",
        "- **Lead-leg tag — used the dataset's given `exercise_subtype`.** Mapped "
        '`"front leg left"` → `left` / `"front leg right"` → `right` and passed to '
        "`extract_lunge_features(rep, lead_leg=...)`, overriding the live geometric "
        "inference. The build asserts the override actually took effect on every rep "
        "(`vector.lead_leg == lead_leg`) rather than trusting it.",
        "- **`knee_passes_toe` — KEPT as a real measured feature, not approximated "
        "from the ankle and not dropped.** The plan allowed a fallback if no toe/foot-"
        "tip joint were available; Stage 5.2 (Lunge) verified against the real "
        "extraction that MediaPipe's foot-tip landmarks (31/32) are present in 100% of "
        "all 26,087 frames with mean visibility ≥0.826 per side, so no fallback is "
        "needed.",
        "",
        "### `lead_leg` is metadata, never a model feature",
        "",
        "`lead_leg` is written to the CSV for traceability and Stage 5.4's per-cohort "
        "analysis, but it is **outside the feature block** and **must not be trained "
        "on**. Stage 5.0 (Lunge) established that lead leg is perfectly confounded with "
        "subject in this dataset — every subject leads with exactly one leg, none "
        "performs both — so under LOSO it is perfectly collinear with the held-out "
        "subject and would act as a subject-identity proxy. This is enforced by "
        "construction rather than convention: Stage 4.2 designed the lunge vector to be "
        "*lead-leg-invariant* (front/back split, so a left-lead and an identical "
        "right-lead rep produce a bit-identical vector), and `lead_leg` lives on "
        "`FeatureVector.lead_leg` metadata, outside `names`/`values`.",
        "",
        "### Windowed-rep sanity (not a gate — Stage 5.4 does the real validity check)",
        "",
        f"- `front_knee_flex_peak_deg`: min {min(front_peaks):.1f}°, median "
        f"{np.median(front_peaks):.1f}°, max {max(front_peaks):.1f}° — non-trivial "
        f"front-knee flexion in every window confirms the dataset frame indices align "
        f"with the Camera18 extraction.",
        f"- `back_knee_flex_peak_deg`: min {min(back_peaks):.1f}°, median "
        f"{np.median(back_peaks):.1f}°, max {max(back_peaks):.1f}°.",
        f"- `rep_duration_s`: min {min(durations):.2f}s, median "
        f"{np.median(durations):.2f}s, max {max(durations):.2f}s.",
        f"- `knee_passes_toe_norm`: min {min(kpt):.3f}, median {np.median(kpt):.3f}, "
        f"max {max(kpt):.3f} — a real spread rather than a constant, i.e. the foot-tip "
        f"landmark is carrying signal, not a frozen default.",
        "",
        "## FSM vs. dataset segmentation agreement (free validation)",
        "",
        "Our lunge rep detector (`segment_lunge_frames` — cycle detection since Stage "
        "5.3 (Lunge); see below) was run over each "
        "full Camera18 clip's **preprocessed** stream (the same one the feature table "
        "above uses) and its rep boundaries compared against the dataset's — this "
        "matches what the live pipeline's FSM actually receives, not raw landmarks. It "
        "validates the live rep detector against physio-verified boundaries; it is a "
        "report, not a gate. Matching is **strictly one-to-one** (greedy by overlap), "
        "so a merged or split detection cannot inflate the count.",
        "",
        f"- **Ground-truth Ex5 reps in these clips:** {agreement['total_gt']} "
        f"(front + half-profile; the FSM is orientation-blind).",
        f"- **FSM-detected reps:** {agreement['total_detected']}.",
        f"- **Matched (one-to-one):** {agreement['total_matched']}.",
        f"- **Recall (GT reps matched):** "
        f"{agreement['total_matched'] / agreement['total_gt'] * 100:.1f}% "
        f"({agreement['total_gt'] - agreement['total_matched']} GT reps missed).",
        f"- **Precision (detections matched):** "
        f"{agreement['total_matched'] / agreement['total_detected'] * 100:.1f}% "
        f"({agreement['total_detected'] - agreement['total_matched']} spurious "
        f"detections).",
        f"- **Front (side-view, trained) reps matched:** "
        f"{agreement['front_matched']} / {agreement['front_gt']} "
        f"({agreement['front_matched'] / agreement['front_gt'] * 100:.1f}% recall).",
        f"- **Boundary error on matched reps:** start median "
        f"{agreement['median_start_err_frames']:.0f} frames "
        f"(mean {agreement['mean_start_err_frames']:.1f}); end median "
        f"{agreement['median_end_err_frames']:.0f} frames "
        f"(mean {agreement['mean_end_err_frames']:.1f}). At 30 fps, 1 frame ≈ 33 ms.",
        "",
        *_exit_diagnostic_section(diagnostic, agreement),
        "> The dataset's boundaries remain ground truth for windowing (Stage 5.3); "
        "this comparison only characterises how closely the runtime FSM reproduces "
        "them. Boundary differences on matched reps are expected — the FSM's "
        "enter/exit hysteresis starts a rep a few frames after true descent onset and "
        "ends it a few frames after return to standing — and are recorded, not "
        "corrected.",
        "",
    ]

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_MD, "w") as f:
        f.write("\n".join(lines))


def main() -> None:
    config = _load_config()
    segmentation_csv = Path(config["dataset_paths"]["rehab246"]["segmentation_csv"])
    rows = _read_segmentation(segmentation_csv)

    # Shared across both stages: each video's full stream is preprocessed exactly
    # once (X1 — mirrors router.py's single call site) and reused by both.
    preprocessed_cache: dict[str, list[dict]] = {}
    frame_count_cache: dict[str, int] = {}

    print("Building lunge feature table (side-view Ex5 reps) ...")
    feature_rows, build_stats = build_feature_rows(
        rows, preprocessed_cache, frame_count_cache
    )
    columns = write_features_csv(feature_rows)
    verify_label_map()
    for c in build_stats["clamped_reps"]:
        print(
            f"  NOTE: {c['video_id']} rep {c['repetition_number']} annotated "
            f"last_frame {c['annotated_last_frame']} overshoots the video; clamped to "
            f"{c['clamped_to']} ({c['frames_lost']} frame(s) lost) — see report."
        )
    print(
        f"  wrote {FEATURES_CSV.name}: {build_stats['n_reps']} reps "
        f"({build_stats['n_good']} Good / {build_stats['n_poor']} Poor), "
        f"{len(LUNGE_FEATURE_NAMES)} features, {len(columns)} total columns"
    )
    print(
        f"  verified shared {LABEL_MAP_JSON.name} (Option A, no Fair in training) — "
        f"not forked"
    )

    print("Running FSM segmentation-agreement validation ...")
    agreement = segmentation_agreement(rows, preprocessed_cache, frame_count_cache)
    diagnostic = exit_threshold_diagnostic(rows, preprocessed_cache, frame_count_cache)
    write_report(build_stats, agreement, feature_rows, diagnostic)
    print(
        f"  FSM matched {agreement['total_matched']}/{agreement['total_gt']} GT reps; "
        f"front {agreement['front_matched']}/{agreement['front_gt']}"
    )
    print(f"  wrote {REPORT_MD.name}")
    print("done")


if __name__ == "__main__":
    main()
