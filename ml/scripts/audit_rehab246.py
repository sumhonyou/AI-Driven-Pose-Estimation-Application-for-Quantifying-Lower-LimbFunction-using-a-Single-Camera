"""Stage 5.0 data audit for REHAB24-6.

Loads Segmentation.csv, filters to exercise_id == 6 (Squats), and reports every
number the Stage 5.0 hard gate requires. Never mutates the dataset; read-only.

Usage: python audit_rehab246.py [--config ../config.yaml]
"""

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

import yaml

EXERCISE_NAMES = {6: "Squats"}


def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def load_segmentation(csv_path: Path) -> list[dict]:
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        return list(reader)


def audit(rows: list[dict]) -> dict:
    """Compute every Stage 5.0 number. Returns a plain dict, printable and reusable."""
    report: dict = {}

    for ex_id in (6,):
        ex_rows = [r for r in rows if r["exercise_id"] == str(ex_id)]
        section: dict = {"total_reps": len(ex_rows)}

        # rep counts per exercise x correctness x person_id
        by_person_correctness: dict = defaultdict(lambda: Counter())
        for r in ex_rows:
            by_person_correctness[r["person_id"]][r["correctness"]] += 1
        section["reps_per_person_x_correctness"] = {
            pid: dict(counts)
            for pid, counts in sorted(
                by_person_correctness.items(), key=lambda kv: int(kv[0])
            )
        }

        # per-subject class presence (LOSO viability)
        single_class_subjects = [
            pid for pid, counts in by_person_correctness.items() if len(counts) < 2
        ]
        section["single_class_subjects"] = sorted(single_class_subjects, key=int)

        # cam17_orientation distribution
        section["cam17_orientation"] = dict(
            Counter(r["cam17_orientation"] for r in ex_rows)
        )

        # mocap_erroneous count
        section["mocap_erroneous_count"] = sum(
            1 for r in ex_rows if r["mocap_erroneous"] == "1"
        )

        # exercise_subtype values (only meaningful for Ex5)
        section["exercise_subtype"] = dict(
            Counter(r["exercise_subtype"] for r in ex_rows)
        )

        # lights_on distribution (task.md calls this "lighting distribution")
        section["lights_on"] = dict(Counter(r["lights_on"] for r in ex_rows))

        # correctness distribution
        section["correctness"] = dict(Counter(r["correctness"] for r in ex_rows))

        report[f"Ex{ex_id}_{EXERCISE_NAMES[ex_id]}"] = section

    # The view question: usable side-view rep count.
    # Verified hypothesis (see DATA_AUDIT.md / rehab24_6_schema.md): cam17_orientation
    # =='front' means camera18 sees a true profile/side view of the subject;
    # 'half-profile' is neither camera's true sagittal view; 'profile' never occurs
    # for Ex6 in this dataset.
    report.update(_side_view_report(rows, 6))

    return report


def _side_view_report(rows: list[dict], ex_id: int) -> dict:
    """Side-view (cam17_orientation=='front' -> Camera18) counts for one exercise."""
    prefix = f"ex{ex_id}"
    ex_rows = [r for r in rows if r["exercise_id"] == str(ex_id)]
    side_view_rows = [r for r in ex_rows if r["cam17_orientation"] == "front"]

    out: dict = {
        f"{prefix}_side_view_rep_count": len(side_view_rows),
        f"{prefix}_side_view_camera": "Camera18",
        f"{prefix}_side_view_by_person": dict(
            Counter(r["person_id"] for r in side_view_rows)
        ),
        f"{prefix}_side_view_by_correctness": dict(
            Counter(r["correctness"] for r in side_view_rows)
        ),
    }

    # LOSO viability specifically on the side-view-filtered subset
    by_person_correctness: dict = defaultdict(lambda: Counter())
    for r in side_view_rows:
        by_person_correctness[r["person_id"]][r["correctness"]] += 1
    out[f"{prefix}_side_view_reps_per_person_x_correctness"] = {
        pid: dict(counts)
        for pid, counts in sorted(
            by_person_correctness.items(), key=lambda kv: int(kv[0])
        )
    }
    out[f"{prefix}_side_view_single_class_subjects"] = sorted(
        [pid for pid, c in by_person_correctness.items() if len(c) < 2], key=int
    )
    out[f"{prefix}_side_view_subjects_missing_entirely"] = sorted(
        set(r["person_id"] for r in ex_rows)
        - set(r["person_id"] for r in side_view_rows),
        key=int,
    )

    return out


def print_report(report: dict) -> None:
    for key, value in report.items():
        print(f"\n=== {key} ===")
        if isinstance(value, dict):
            for k, v in value.items():
                print(f"  {k}: {v}")
        else:
            print(f"  {value}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "config.yaml",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    csv_path = Path(config["dataset_paths"]["rehab246"]["segmentation_csv"])
    rows = load_segmentation(csv_path)

    print(f"Loaded {len(rows)} rows from {csv_path}")
    report = audit(rows)
    print_report(report)


if __name__ == "__main__":
    main()
