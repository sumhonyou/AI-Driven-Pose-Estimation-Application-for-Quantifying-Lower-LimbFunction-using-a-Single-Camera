"""Stage 5.0: the view question — extract real frames to verify which camera is sagittal.

Answers "which camera actually sees a true side view?" by pulling real frames out of
both cameras for one `front`-orientation rep and one `half-profile`-orientation rep,
and laying them out for comparison. Verified by looking, never assumed from the
schema's mapping table.

Squat's own Stage 5.0 check was done ad hoc and left no script behind; this exists so
the Ex5 (lunge) answer is reproducible. A lunge is a *directional* movement — the
subject steps along their facing axis — so Ex6's answer does not transfer to Ex5 on
its own and has to be re-verified per exercise.

Read-only: never writes to the dataset.

Usage: python make_view_figure.py --exercise 5 --video PM_021
"""

import argparse
import csv
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import yaml
from plotting import save_fig

CAMERAS = {
    17: "PM_{vid}-Camera17-30fps.mp4",
    18: "PM_{vid}-Camera18-30fps-transposed.mp4",
}


def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def pick_reps(csv_path: Path, exercise_id: int, video_id: str) -> dict:
    """Pick one rep per orientation from the given video. Returns {orientation: row}."""
    with open(csv_path, newline="") as f:
        rows = [
            r
            for r in csv.DictReader(f, delimiter=";")
            if r["exercise_id"] == str(exercise_id) and r["video_id"] == video_id
        ]
    picked: dict = {}
    for r in rows:
        picked.setdefault(r["cam17_orientation"], r)
    return picked


def grab_frame(video_path: Path, frame_index: int):
    """Grab a single frame by index. Returns RGB array."""
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"Could not read frame {frame_index} from {video_path}")
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exercise", type=int, default=5)
    parser.add_argument("--video", type=str, default="PM_021")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "config.yaml",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    paths = config["dataset_paths"]["rehab246"]
    videos_dir = Path(paths["videos_dir"]) / f"Ex{args.exercise}"

    picked = pick_reps(Path(paths["segmentation_csv"]), args.exercise, args.video)
    orientations = [o for o in ("front", "half-profile") if o in picked]
    print(f"Ex{args.exercise} {args.video}: orientations found -> {orientations}")

    fig, axes = plt.subplots(len(orientations), 2, figsize=(9, 4.5 * len(orientations)))
    if len(orientations) == 1:
        axes = [axes]

    for row_i, orientation in enumerate(orientations):
        rep = picked[orientation]
        # Mid-rep frame: the deepest point of the movement, where view matters most.
        mid = (int(rep["first_frame"]) + int(rep["last_frame"])) // 2
        for col_i, cam in enumerate((17, 18)):
            suffix = args.video.replace("PM_", "")
            video_path = videos_dir / CAMERAS[cam].format(vid=suffix)
            frame = grab_frame(video_path, mid)
            ax = axes[row_i][col_i]
            ax.imshow(frame)
            ax.set_title(
                f"Camera{cam} — cam17_orientation='{orientation}'\n"
                f"{args.video} rep {rep['repetition_number']}, frame {mid}",
                fontsize=9,
            )
            ax.axis("off")
            print(
                f"  {orientation:13s} Camera{cam}: frame {mid} from {video_path.name}"
            )

    fig.suptitle(
        f"Ex{args.exercise} view verification — which camera sees a true sagittal view?",
        fontsize=11,
    )
    fig.tight_layout()
    out = save_fig(fig, f"view_verification_ex{args.exercise}")
    print(f"Saved -> {out}")


if __name__ == "__main__":
    main()
