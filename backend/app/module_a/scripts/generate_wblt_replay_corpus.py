"""Generates the committed WBLT replay corpus: synthetic per-attempt landmark
sequences spanning the Poor/Fair/Good bands, both legs, plus one heel-lift
invalid case.

There is no real pilot/patient recording available for this prototype, so the
corpus is synthetic with a KNOWN ground-truth intended distance per sample --
unlike SLS's hold-time reliability question, WBLT's distance is
self-measured/self-reported (ruler/tape) rather than camera-derived, so the
question this corpus answers is: does the persisted `distance_cm` (gated on
the camera's heel-lift/touch validity check) faithfully preserve a distance
that agrees with an independent repeat tape measurement? Each sample also
gets a simulated "manual" (independent repeat tape) reading: the true intended
distance plus small Gaussian noise, modelling the imprecision of a second
tape measurement -- consistent with Powden et al. (2015)'s reported WBLT
distance MDC of ~1.0-1.5cm. The one invalid (heel-lift) sample models the
camera correctly rejecting a touch a naive tape-only method would have
accepted.

Deterministic: seeded RNG, so re-running this script reproduces byte-identical
output. The corpus is committed to the repo (backend/app/module_a/replay_corpus/wblt/)
so evaluation is reproducible from committed data without re-running this script.

Usage:
    python -m app.module_a.scripts.generate_wblt_replay_corpus
"""

import json
import random
from pathlib import Path

from app.module_a.wblt.config import CALIBRATION_SECONDS

CORPUS_DIR = Path(__file__).resolve().parents[1] / "replay_corpus" / "wblt"
SEED = 20260713  # fixed seed -> reproducible corpus
FRAME_STEP_MS = 33.0  # ~30fps, matches SLS/squat corpus convention
# Read live from wblt/config.py rather than a hardcoded mirror -- a prior version of
# this constant drifted out of sync with a CALIBRATION_SECONDS bump (1.0 -> 2.0) and
# silently invalidated the entire corpus: every frame fell inside the calibration
# window, so no frame ever reached theta computation and every sample returned
# distance_cm=None. Importing the real value makes that class of drift impossible.
CALIBRATION_SEC = CALIBRATION_SECONDS
N_CALIBRATION = int(CALIBRATION_SEC * 1000 / FRAME_STEP_MS) + 1  # +1 margin of safety
N_HOLD = 15
MANUAL_TAPE_NOISE_SD = 0.4  # cm; independent repeat tape measurement imprecision
AGEBAND_SEX = "30-39_male"  # fixed profile so every sample bands the same way
EXACT_AGE = 33
GENDER = "male"


def _r(v: float) -> float:
    """4dp is far more precision than these synthetic coordinates need; rounding
    keeps the committed corpus JSON compact (default float repr() bloats file size)."""
    return round(v, 4)


_LEG_INDICES = {
    "right": (26, 28, 30, 32),  # knee, ankle, heel, foot_index
    "left": (25, 27, 29, 31),
}


def _landmark(x: float, y: float, z: float = 0.0, visibility: float = 1.0) -> dict:
    return {"x": _r(x), "y": _r(y), "z": z, "visibility": visibility}


def _frame(
    t_ms: float, leg: str, knee: dict, ankle: dict, heel: dict, foot_index: dict
) -> dict:
    knee_idx, ankle_idx, heel_idx, foot_idx = _LEG_INDICES[leg]
    world = [_landmark(0.0, 0.0) for _ in range(33)]
    world[knee_idx] = knee
    world[ankle_idx] = ankle
    world[heel_idx] = heel
    world[foot_idx] = foot_index
    world[23] = _landmark(0.0, 0.3)  # hip left -- side-on camera (hip_x_sep=0)
    world[24] = _landmark(0.0, 0.3)  # hip right
    return {"timestampMs": round(t_ms, 1), "worldLandmarks": world}


def _make_frames(
    leg: str, knee_xy_offset: float, heel_rise: float, rng: random.Random
) -> list[dict]:
    """Foot-flat calibration window, then a lunge hold with `knee_xy_offset`
    forward lean (controls the dorsiflexion angle) and `heel_rise` heel lift
    (0 = flat; > heel_lift_tol_ratio * shank_len trips the heel-lift gate)."""
    ankle = _landmark(0.0, 0.5)
    heel_flat = _landmark(0.0, 0.5)
    foot_index = _landmark(0.15, 0.5)
    knee_flat = _landmark(0.0, 0.0)

    frames = []
    t = 0.0
    step_ms = 1000.0 * CALIBRATION_SEC / N_CALIBRATION
    for _ in range(N_CALIBRATION):
        jitter = rng.uniform(-0.002, 0.002)
        frames.append(
            _frame(
                t,
                leg,
                _landmark(knee_flat["x"] + jitter, knee_flat["y"]),
                ankle,
                heel_flat,
                foot_index,
            )
        )
        t += step_ms

    # Start the hold phase just past the calibration window boundary (t = last
    # calibration frame + one step), not a hardcoded offset -- otherwise a future
    # CALIBRATION_SECONDS increase silently swallows the hold frames into
    # calibration again, exactly as happened before this fix.
    t = CALIBRATION_SEC * 1000.0 + FRAME_STEP_MS
    knee_hold = _landmark(knee_xy_offset, 0.0)
    heel_hold = _landmark(0.0, 0.5 - heel_rise)
    for _ in range(N_HOLD):
        frames.append(_frame(t, leg, knee_hold, ankle, heel_hold, foot_index))
        t += FRAME_STEP_MS
    return frames


# (sample_id, leg, intended_distance_cm, knee_xy_offset, heel_rise, touched, band_hint)
# knee_xy_offset roughly correlates with intended distance (deeper lunge -> more
# dorsiflexion), same proxy relationship exercised in test_module_a_wblt.py.
SAMPLE_SPECS = [
    ("good_right_1", "right", 10.0, 0.35, 0.0, True, "Good"),
    ("good_left_1", "left", 9.5, 0.32, 0.0, True, "Good"),
    ("good_right_2", "right", 11.0, 0.38, 0.0, True, "Good"),
    ("fair_right_1", "right", 8.0, 0.22, 0.0, True, "Fair"),
    ("fair_left_1", "left", 7.8, 0.20, 0.0, True, "Fair"),
    ("fair_right_2", "right", 8.5, 0.24, 0.0, True, "Fair"),
    ("poor_right_1", "right", 6.0, 0.12, 0.0, True, "Poor"),
    ("poor_left_1", "left", 5.5, 0.10, 0.0, True, "Poor"),
    ("poor_left_2", "left", 4.0, 0.07, 0.0, True, "Poor"),
    # Heel lifts during the hold -> camera correctly rejects the touch even
    # though a naive tape-only method (no camera check) would have accepted
    # it -- this is the one deliberate system/manual disagreement in the corpus.
    ("invalid_heel_lift_right_1", "right", 9.0, 0.28, 0.225, True, "Invalid"),
]


def build_corpus() -> list[dict]:
    rng = random.Random(SEED)
    manifest = []
    for (
        sample_id,
        leg,
        intended_cm,
        knee_offset,
        heel_rise,
        touched,
        band_hint,
    ) in SAMPLE_SPECS:
        frames = _make_frames(leg, knee_offset, heel_rise, rng)
        manual_cm = max(0.0, intended_cm + rng.gauss(0.0, MANUAL_TAPE_NOISE_SD))
        frames_path = CORPUS_DIR / f"{sample_id}.json"
        frames_path.write_text(json.dumps(frames, separators=(",", ":")))
        manifest.append(
            {
                "sample_id": sample_id,
                "leg": leg,
                "frames_file": frames_path.name,
                "target_distance_cm": round(intended_cm, 3),
                "touched": touched,
                "manual_distance_cm": round(manual_cm, 3),
                "target_band_hint": band_hint,
                "exact_age": EXACT_AGE,
                "gender": GENDER,
            }
        )
    return manifest


def main() -> None:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_corpus()
    (CORPUS_DIR / "labels.json").write_text(json.dumps(manifest, indent=2))
    print(f"[corpus] Wrote {len(manifest)} samples + labels.json to {CORPUS_DIR}")


if __name__ == "__main__":
    main()
