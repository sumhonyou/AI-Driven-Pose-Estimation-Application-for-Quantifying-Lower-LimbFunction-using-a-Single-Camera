"""Stage 5.2 landmark extraction: RGB video -> world landmarks (.npz per video).

Runs the *same* pose_landmarker_full.task the frontend self-hosts (X3), with the
exact same detection config as useMediaPipePose.ts: CPU delegate (GPU delegate is
Ubuntu-only, errors on macOS/Apple Silicon), VIDEO running mode, num_poses=1,
confidence thresholds 0.5. Extracts pose_world_landmarks only, never image
landmarks.

No confidence-filter / gap-fill / One-Euro preprocessing is applied here. Stage
5.2 decision (HY, 2026-07-16): the live squat pipeline (SquatExercise.segment /
extract_squat_features, called from POST /api/module-b/analyze) receives raw
MediaPipe world landmarks straight from the frontend with zero smoothing applied
anywhere — confirmed by reading useMediaPipePose.ts (worldLandmarks bypass the
2D-only landmark smoother) and squat/segmentation.py /squat/features.py (no
filtering before use). So offline extraction matches runtime *as it actually is*
(X1), not as X3's aspirational "confidence filter -> gap fill -> One Euro"
pipeline describes it — that pipeline exists for Module A, not Module B squat.
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

# Matches frontend/src/hooks/useMediaPipePose.ts exactly.
DETECTION_CONFIG = {
    "num_poses": 1,
    "min_pose_detection_confidence": 0.5,
    "min_pose_presence_confidence": 0.5,
    "min_tracking_confidence": 0.5,
}

TARGET_EXERCISE_ID = "6"  # Ex6 = Squats (Locked Assumption #2, squat-first)
# Verified visually in Stage 5.0 (DATA_AUDIT.md): cam17_orientation == "front" rows
# get their true sagittal/profile view from Camera18, the only usable side view.
SIDE_VIEW_CAMERA = "Camera18"


def _asset_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def _ex6_video_ids(segmentation_csv: Path) -> list[str]:
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

    data_dir = Path(__file__).resolve().parent.parent / "data" / "landmarks"
    data_dir.mkdir(parents=True, exist_ok=True)

    video_ids = _ex6_video_ids(segmentation_csv)
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
            videos_dir / "Ex6" / f"{video_id}-{SIDE_VIEW_CAMERA}-30fps-transposed.mp4"
        )
        if not video_path.exists():
            raise FileNotFoundError(f"Expected {video_path}")

        print(f"extracting {video_id} ...")
        # A fresh landmarker per video: VIDEO running mode tracks its own internal
        # "last timestamp" and rejects a reset-to-0 timestamp from the next video
        # as non-monotonic if the same instance is reused across videos.
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
