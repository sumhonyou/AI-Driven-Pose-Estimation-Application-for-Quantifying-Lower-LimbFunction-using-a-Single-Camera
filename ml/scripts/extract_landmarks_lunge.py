"""Stage 5.2 (Lunge) landmark extraction: RGB video -> world landmarks (.npz per video).

Structural mirror of `extract_landmarks.py` (squat's Stage 5.2), swapped to Ex5 / the
lunge exercise. Runs the *same* pose_landmarker_full.task the frontend self-hosts (X3),
with the exact same detection config as useMediaPipePose.ts: CPU delegate (GPU delegate
is Ubuntu-only, errors on macOS/Apple Silicon), VIDEO running mode, num_poses=1,
confidence thresholds 0.5. Extracts pose_world_landmarks only, never image landmarks.
Camera18 only (Stage 5.0 (Lunge)'s verified side-view source — re-verified visually for
Ex5 specifically, not carried over from squat, since a lunge is a directional movement).

No confidence-filter / gap-fill / One-Euro preprocessing is applied here, matching
squat's own extract_landmarks.py as it stands today: preprocessing
(`app.module_b.core.preprocessing.preprocess_world_landmarks`) is applied downstream, at
feature-table build time (Stage 5.3's `build_features.py`), not baked into the raw
landmark cache. This keeps the cache reusable across changes to the preprocessing logic
and matches the live router, which also preprocesses after capture, not during it.

Two Stage 5.2 (Lunge) deltas from task.md, both resolved by reading the code rather than
re-implementing anything here:

1. **Lead-leg tag, "infer from which foot is forward in world landmarks" at runtime.**
   This extractor does not compute lead leg — it dumps raw per-frame world landmarks,
   unsegmented into reps. Lead-leg inference is a rep-scoped operation
   (`app.module_b.lunge.features._anterior_sign` / `_resolve_front_leg`), applied once a
   stream has been windowed into reps: live inference at Stage 4.2/4.7 (already shipped),
   offline training at Stage 5.3 using the dataset's own `exercise_subtype` tag instead
   (it's given — Stage 5.3 (Lunge)'s own delta). Nothing to add here.
2. **Toe/foot-tip joint availability, for `knee_passes_toe`.** MediaPipe's 33-landmark
   pose output always includes `LEFT_FOOT_INDEX` (31) / `RIGHT_FOOT_INDEX` (32),
   regardless of exercise — this is a property of the pose model, not something that
   needs checking per exercise. Stage 4.2 already confirmed this is what the live stream
   provides. Verified for the extracted lunge data specifically (not just assumed from
   the live path) in `ml/reports/LUNGE_EXTRACTION_REPORT.md` — landmarks 31/32 are
   present and move plausibly across a rep, not NaN or frozen.

Parity check (WASM-vs-native delegate numeric divergence) is not re-run for lunge: it
tests the pose-landmarker pipeline itself (same model asset, same
`PoseLandmarkerOptions`, same delegate), a property of the shared infrastructure that
does not depend on which exercise the subject performs. Squat's own
`ml/reports/PARITY_CHECK.md` result is reused by reference. See the Stage 5.2 (Lunge)
task.md entry for the reasoning recorded at the time this decision was made.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import yaml
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

# Matches frontend/src/hooks/useMediaPipePose.ts exactly (identical to squat's own).
DETECTION_CONFIG = {
    "num_poses": 1,
    "min_pose_detection_confidence": 0.5,
    "min_pose_presence_confidence": 0.5,
    "min_tracking_confidence": 0.5,
}

TARGET_EXERCISE_ID = "5"  # Ex5 = Leg lunge
# Verified visually in Stage 5.0 (Lunge) (LUNGE_DATA_AUDIT.md): cam17_orientation ==
# "front" rows get their true sagittal/profile view from Camera18, re-checked on two
# subjects with opposite lead legs since a lunge travels along the facing axis.
SIDE_VIEW_CAMERA = "Camera18"


def _asset_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def _ex5_video_ids(segmentation_csv: Path) -> list[str]:
    with open(segmentation_csv, newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        ids = {r["video_id"] for r in reader if r["exercise_id"] == TARGET_EXERCISE_ID}
    return sorted(ids)


def _build_landmarker(model_path: Path) -> vision.PoseLandmarker:
    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=str(model_path), delegate=BaseOptions.Delegate.CPU
        ),
        running_mode=vision.RunningMode.VIDEO,
        **DETECTION_CONFIG,
    )
    return vision.PoseLandmarker.create_from_options(options)


def extract_video(
    video_path: Path, landmarker: vision.PoseLandmarker
) -> tuple[np.ndarray, np.ndarray, float]:
    """Return (timestamps_ms, world_landmarks[frame, landmark, xyz+vis+pres], fps).

    A frame with no detected pose is stored as NaN, never dropped — keeps frame
    indices aligned with Segmentation.csv's first_frame/last_frame for Stage 5.3.
    """
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_ms_step = 1000.0 / fps

    timestamps = []
    landmarks = []
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(round(frame_idx * frame_ms_step))
        result = landmarker.detect_for_video(mp_image, timestamp_ms)
        if result.pose_world_landmarks:
            frame_lms = np.array(
                [
                    [lm.x, lm.y, lm.z, lm.visibility, lm.presence]
                    for lm in result.pose_world_landmarks[0]
                ],
                dtype=np.float64,
            )
        else:
            frame_lms = np.full((33, 5), np.nan, dtype=np.float64)
        timestamps.append(timestamp_ms)
        landmarks.append(frame_lms)
        frame_idx += 1

    cap.release()
    return (
        np.array(timestamps, dtype=np.int64),
        np.array(landmarks, dtype=np.float64),
        fps,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "config.yaml",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Process at most N videos (debugging)."
    )
    args = parser.parse_args()

    config = _load_config(args.config)
    rehab_paths = config["dataset_paths"]["rehab246"]
    videos_dir = Path(rehab_paths["videos_dir"])
    segmentation_csv = Path(rehab_paths["segmentation_csv"])
    model_path = (args.config.resolve().parent / config["pose_model_asset"]).resolve()

    data_dir = Path(__file__).resolve().parent.parent / "data" / "landmarks_lunge"
    data_dir.mkdir(parents=True, exist_ok=True)

    video_ids = _ex5_video_ids(segmentation_csv)
    if args.limit:
        video_ids = video_ids[: args.limit]

    model_hash = _asset_hash(model_path)
    mp_version = mp.__version__
    for video_id in video_ids:
        out_path = data_dir / f"{video_id}.npz"
        if out_path.exists():
            print(f"skip {video_id} (cached)")
            continue

        video_path = (
            videos_dir / "Ex5" / f"{video_id}-{SIDE_VIEW_CAMERA}-30fps-transposed.mp4"
        )
        if not video_path.exists():
            raise FileNotFoundError(f"Expected {video_path}")

        print(f"extracting {video_id} ...")
        # A fresh landmarker per video: VIDEO running mode tracks its own internal
        # "last timestamp" and rejects a reset-to-0 timestamp from the next video
        # as non-monotonic if the same instance is reused across videos (the bug
        # squat's own Stage 5.2 hit and fixed the same way).
        landmarker = _build_landmarker(model_path)
        timestamps, landmarks, fps = extract_video(video_path, landmarker)
        landmarker.close()
        metadata = {
            "video_id": video_id,
            "camera": SIDE_VIEW_CAMERA,
            "source_path": str(video_path),
            "model_asset_sha256": model_hash,
            "mediapipe_version": mp_version,
            "delegate": "CPU",
            "fps": fps,
            "detection_config": DETECTION_CONFIG,
            "num_frames": int(len(timestamps)),
        }
        np.savez_compressed(
            out_path,
            timestamps_ms=timestamps,
            world_landmarks=landmarks,
            metadata_json=json.dumps(metadata),
        )
        print(f"  saved {out_path} ({len(timestamps)} frames)")

    print("done")


if __name__ == "__main__":
    main()
