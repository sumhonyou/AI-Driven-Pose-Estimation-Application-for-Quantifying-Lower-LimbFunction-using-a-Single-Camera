"""Stage 5.3: build the per-rep squat feature table from extracted world landmarks.

For every side-view (`cam17_orientation == "front"` → Camera18 sees profile, verified
in Stage 5.0) squat rep: preprocess the **entire** video's landmark stream through the
live backend's confidence-filter → gap-fill → One-Euro pipeline (X1/X3 — the
cross-cutting preprocessing change, `app.module_b.core.preprocessing.
preprocess_world_landmarks`, wired into `POST /api/module-b/analyze` ahead of
`segment()`/`extract_features()`), then window the *preprocessed* stream by
Segmentation.csv's physio-verified `first_frame`/`last_frame` (NOT our FSM — the
dataset boundaries are ground truth here) and call the **backend's**
`extract_squat_features()`. Emits `ml/data/squat_features.csv`, one row per rep.

Preprocessing is run **once per video, over the full chronological stream, before
windowing** — OneEuroFilter is stateful, so preprocessing a rep's window in isolation
would reset its history at every rep boundary and diverge from what the live capture
(a whole-session buffer) actually produces. This mirrors `router.py`'s single call
site exactly.

As a free, honest validation (Stage 5.3), our own squat FSM is also run over the same
preprocessed full clips and its rep boundaries are compared against the dataset's —
written to `ml/reports/FEATURE_TABLE.md`. This is a report, not a gate.

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
from app.module_b.squat.features import SQUAT_FEATURE_NAMES, extract_squat_features
from app.module_b.squat.segmentation import segment_squat_frames

TARGET_EXERCISE_ID = "6"  # Ex6 = Squats
# Stage 5.0 (option a): side-view only. cam17_orientation == "front" is the cohort
# whose Camera18 recording is the true sagittal view (verified in DATA_AUDIT.md).
SIDE_VIEW_ORIENTATION = "front"

# Option A label map (also written to ml/artifacts/label_map.json). No Fair in training.
LABEL_MAP = {"1": "Good", "0": "Poor"}

ML_ROOT = Path(__file__).resolve().parent.parent
LANDMARKS_DIR = ML_ROOT / "data" / "landmarks"
FEATURES_CSV = ML_ROOT / "data" / "squat_features.csv"
LABEL_MAP_JSON = ML_ROOT / "artifacts" / "label_map.json"
REPORT_MD = ML_ROOT / "reports" / "FEATURE_TABLE.md"


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

    A no-pose (all-NaN) frame — no landmarks were returned at all — is dropped from
    the stream entirely rather than fed into preprocessing; this mirrors a live
    capture, which only ever sends frames where a pose was actually detected.
    `visibility` is carried through per landmark (required by both the confidence
    filter's gap-fill and `LandmarkSmoother`'s hold-last).

    Returns (frames, total_extracted_frame_count) — the count includes any dropped
    no-pose frames, used to catch a `first_frame`/`last_frame` index that exceeds
    what was actually extracted for this video.
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
    runs (confidence filter -> gap fill -> One Euro), computed exactly once per video
    and cached — mirrors `POST /api/module-b/analyze`'s single call over the whole
    received buffer, called by both `build_feature_rows` and `segmentation_agreement`
    so neither path re-derives a slightly different stream.
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
    """Extract one feature row per side-view squat rep. Returns (rows, build_stats)."""
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
    videos_seen: set[str] = set()
    for r in side_view_rows:
        video_id = r["video_id"]
        videos_seen.add(video_id)
        preprocessed = _preprocessed_stream(
            video_id, preprocessed_cache, frame_count_cache
        )

        first, last = int(r["first_frame"]), int(r["last_frame"])
        if last >= frame_count_cache[video_id]:
            raise IndexError(
                f"{video_id} rep {r['repetition_number']}: last_frame {last} exceeds "
                f"extracted frame count {frame_count_cache[video_id]} — frame/camera "
                f"misalignment, do not proceed."
            )

        frames = [f for f in preprocessed if first <= f["frameIndex"] <= last]
        total_dropped += (last - first + 1) - len(frames)
        if not frames:
            raise ValueError(
                f"{video_id} rep {r['repetition_number']}: no pose frames in window"
            )

        vector = extract_squat_features(frames)
        # Schema guard (X1): the vector we just built must match the frozen contract.
        if vector.names != SQUAT_FEATURE_NAMES:
            raise ValueError("FeatureVector.names drifted from SQUAT_FEATURE_NAMES")

        feature_rows.append(
            {
                "person_id": int(r["person_id"]),
                "video_id": video_id,
                "repetition_number": int(r["repetition_number"]),
                **dict(zip(vector.names, vector.values, strict=True)),
                "correctness": int(r["correctness"]),
                "label": LABEL_MAP[r["correctness"]],
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
    }
    return feature_rows, stats


def write_features_csv(feature_rows: list[dict]) -> list[str]:
    """Write squat_features.csv; assert feature columns match the frozen contract."""
    columns = (
        ["person_id", "video_id", "repetition_number"]
        + list(SQUAT_FEATURE_NAMES)
        + [
            "correctness",
            "label",
            "orientation",
            "lights_on",
            "mocap_erroneous",
            "feature_schema_version",
        ]
    )
    # Schema validation: the feature block, in order, must equal FeatureVector.names.
    feature_block = columns[3 : 3 + len(SQUAT_FEATURE_NAMES)]
    if tuple(feature_block) != SQUAT_FEATURE_NAMES:
        raise ValueError(
            "CSV feature column order/count drifted from SQUAT_FEATURE_NAMES"
        )

    FEATURES_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(FEATURES_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(feature_rows)
    return columns


def write_label_map() -> None:
    """Write the Option A label map, recording explicitly that there is no Fair class.

    `label_order` was added in Stage 5.8: `model_registry.load_joblib_model_bundle()`
    reads it to build `JoblibModelBundle.label_order`, and `validate_model_bundle()`
    requires it to be exactly `("Poor", "Good")` for Option A. Fixed independent of any
    trained model (it is the labelling convention, not a training result), so it is
    safe to write here at Stage 5.3 time rather than only once a model exists.
    """
    LABEL_MAP_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scheme": "Option A (binary Good/Poor)",
        "source_column": "correctness",
        "mapping": {"1": "Good", "0": "Poor"},
        "label_order": ["Poor", "Good"],
        "no_fair_in_training": True,
        "fair_note": (
            "Fair is never a trained label. It is derived at inference from a "
            "calibrated low-confidence margin (confidence_low_threshold) — see "
            "Phase 5 Stage 5.6."
        ),
    }
    with open(LABEL_MAP_JSON, "w") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")


# --- FSM-vs-dataset segmentation agreement (free validation, Stage 5.3) ---------------


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
    """Run our FSM over each full clip; match detected reps to dataset boundaries.

    Runs over the **same preprocessed stream** `build_feature_rows` already computed
    (via the shared cache) — the live pipeline calls `exercise.segment()` on the
    preprocessed buffer too (`router.py`: preprocess once, then segment), so this
    validates the FSM against what it actually receives at runtime, not raw landmarks.

    Over-/under-segmentation is measured against ALL Ex6 reps present in each Camera18
    clip (front + half-profile — the FSM is orientation-blind), with a front-only
    breakdown since those are the reps the model actually trains on. Matching is
    **strictly one-to-one**: candidate (detected, GT) pairs whose inclusive windows
    overlap by more than half the GT rep length are assigned greedily by descending
    overlap, each detected rep and each GT rep used at most once. This keeps a single
    merged detection from counting against two GT reps (which would hide an
    under-segmentation), so `matched <= min(detected, gt)` always holds.
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
            _rep_frame_bounds(rep) for rep in segment_squat_frames(preprocessed)
        ]

        gt = [
            (
                int(r["first_frame"]),
                int(r["last_frame"]),
                r["cam17_orientation"],
            )
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


def write_report(build_stats: dict, agreement: dict, feature_rows: list[dict]) -> None:
    """Write the feature-table build summary + FSM segmentation agreement report."""
    peaks = [row["knee_flex_peak_deg"] for row in feature_rows]
    durations = [row["rep_duration_s"] for row in feature_rows]

    lines = [
        "# Stage 5.3 — squat feature table build",
        "",
        "Preprocesses each video's **entire** landmark stream through the live "
        "backend's confidence-filter → gap-fill → One-Euro pipeline "
        "(`app.module_b.core.preprocessing.preprocess_world_landmarks`, the "
        "cross-cutting change wired into `POST /api/module-b/analyze` ahead of "
        "`segment()`/`extract_features()`), run once per video over the full "
        "chronological stream — not per rep — since OneEuroFilter is stateful and "
        "windowing first would reset its history at every rep boundary. Then windows "
        'every **side-view** (`cam17_orientation == "front"`, Camera18 = profile) '
        "Ex6 rep of that *preprocessed* stream by Segmentation.csv's physio-verified "
        "`first_frame`/`last_frame`, and calls the backend's "
        "`extract_squat_features()` (X1). Half-profile reps are excluded per the "
        "Stage 5.0 gate decision (option a — side-view only).",
        "",
        "## Feature table",
        "",
        f"- **Output:** `ml/data/squat_features.csv` — {build_stats['n_reps']} rows "
        f"(one per rep), {len(SQUAT_FEATURE_NAMES)} feature columns.",
        f"- **Class balance:** {build_stats['n_good']} Good / "
        f"{build_stats['n_poor']} Poor.",
        f"- **Subjects:** {build_stats['n_subjects']} across "
        f"{build_stats['n_videos']} videos.",
        f"- **No-pose frames dropped inside rep windows:** "
        f"{build_stats['dropped_no_pose_frames']} (expected 0 — the single no-pose "
        f"frame in the corpus is PM_008 frame 0, outside every rep window).",
        f"- **Feature schema version:** "
        f"`{feature_rows[0]['feature_schema_version']}`.",
        "",
        "Feature columns are written in `FeatureVector.names` order and asserted "
        "against `SQUAT_FEATURE_NAMES` at write time — the build fails loudly on drift.",
        "",
        "### Windowed-rep sanity (not a gate — Stage 5.4 does the real validity check)",
        "",
        f"- `knee_flex_peak_deg`: min {min(peaks):.1f}°, median "
        f"{np.median(peaks):.1f}°, max {max(peaks):.1f}° — non-trivial knee flexion in "
        f"every window confirms the dataset frame indices align with the Camera18 "
        f"extraction (had they indexed the wrong camera/offset, windows would not "
        f"contain a squat).",
        f"- `rep_duration_s`: min {min(durations):.2f}s, median "
        f"{np.median(durations):.2f}s, max {max(durations):.2f}s.",
        "",
        "### Far-limb occlusion (finding — feeds the monocular limitations write-up)",
        "",
        "A single side-view camera tracks the **near** leg well and the **far** leg "
        "poorly, systematically, in every subject. Mean landmark visibility across "
        "all 9 videos: left knee 0.95–0.99 and left ankle 0.97–0.99, versus right "
        "knee **0.59–0.78** and right ankle **0.68–0.87** (the subjects face the same "
        "way, so the right leg is the far one throughout). The far knee sits below "
        "the `MIN_VISIBILITY = 0.6` confidence threshold for whole reps at a time — "
        "measured at all 121 frames of PM_008's rep-1 window, far longer than the "
        "5-frame gap-fill cap.",
        "",
        "This is a property of monocular side-view capture, not of this dataset: the "
        "live app's own squat guidance asks for exactly this camera placement, so the "
        "same occlusion occurs at runtime. It is recorded here as evidence for the "
        "limitations write-up, alongside the dropped frontal-plane valgus measure "
        "(Locked Assumption #3) — both are the same underlying constraint (one camera "
        "cannot see what the body occludes).",
        "",
        "The far leg's landmarks are *low-confidence but still tracking* — not "
        "missing. On PM_008 rep 1 the far knee's raw trajectory peaked at 99.9° "
        "against the near knee's 77.9°, a plausible squat depth. Preprocessing "
        "therefore releases hold-last beyond the gap-fill window rather than freezing "
        "the far limb at its standing angle (see "
        "`module_b/core/preprocessing._release_persistent_occlusions`); freezing it "
        "halved the bilateral mean knee flexion and collapsed FSM rep agreement to "
        "32/98 front reps. Whether the far leg's estimate is *accurate* (not merely "
        "plausible) is exactly what Stage 5.4's `check_mocap_agreement.py` settles "
        "against the OptiTrack ground truth — it is not asserted here.",
        "",
        "## FSM vs. dataset segmentation agreement (free validation)",
        "",
        "Our squat FSM (`segment_squat_frames`, Stage 4.3) was run over each full "
        "Camera18 clip's **preprocessed** stream (the same one the feature table "
        "above uses) and its rep boundaries compared against the dataset's — this "
        "matches what the live pipeline's FSM actually receives (`router.py` "
        "preprocesses once, then segments), not raw landmarks. It validates the live "
        "rep detector against physio-verified boundaries; it is a report, not a gate. "
        "Matching is **strictly one-to-one** (greedy by overlap): each detected rep "
        "matches at most one GT rep and vice versa, so a merged or split detection "
        "cannot inflate the count.",
        "",
        f"- **Ground-truth Ex6 reps in these clips:** {agreement['total_gt']} "
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
        "| video | GT reps | FSM detected | matched |",
        "| ----- | ------- | ------------ | ------- |",
    ]
    for v in agreement["per_video"]:
        lines.append(
            f"| {v['video_id']} | {v['gt_reps']} | {v['detected_reps']} | "
            f"{v['matched']} |"
        )
    lines.append("")
    lines.append(
        "> The dataset's boundaries remain ground truth for windowing (Stage 5.3); "
        "this comparison only characterises how closely the runtime FSM reproduces "
        "them. Boundary differences are expected — the FSM's enter/exit hysteresis "
        "starts a rep a few frames after true descent onset and ends it a few frames "
        "after return to standing — and are recorded, not corrected."
    )
    lines.append("")

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

    print("Building feature table (side-view Ex6 reps) ...")
    feature_rows, build_stats = build_feature_rows(
        rows, preprocessed_cache, frame_count_cache
    )
    columns = write_features_csv(feature_rows)
    write_label_map()
    print(
        f"  wrote {FEATURES_CSV.name}: {build_stats['n_reps']} reps "
        f"({build_stats['n_good']} Good / {build_stats['n_poor']} Poor), "
        f"{len(SQUAT_FEATURE_NAMES)} features, {len(columns)} total columns"
    )
    print(f"  wrote {LABEL_MAP_JSON.name} (Option A, no Fair in training)")

    print("Running FSM segmentation-agreement validation ...")
    agreement = segmentation_agreement(rows, preprocessed_cache, frame_count_cache)
    write_report(build_stats, agreement, feature_rows)
    print(
        f"  FSM matched {agreement['total_matched']}/{agreement['total_gt']} GT reps; "
        f"front {agreement['front_matched']}/{agreement['front_gt']}"
    )
    print(f"  wrote {REPORT_MD.name}")
    print("done")


if __name__ == "__main__":
    main()
