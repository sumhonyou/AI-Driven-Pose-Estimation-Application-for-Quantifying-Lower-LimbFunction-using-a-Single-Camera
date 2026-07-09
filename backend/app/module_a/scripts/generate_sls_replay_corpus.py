"""Generates the committed SLS replay corpus: synthetic per-leg landmark
sequences spanning the Poor/Fair/Good bands, steady and swaying variants, plus
an "invalid" (never-lifted) case.

There is no real pilot/patient recording available for this prototype, so the
corpus is synthetic with a KNOWN ground-truth intended hold time per sample.
Each sample also gets a simulated "manual" (human stopwatch) label: the true
intended hold time plus small Gaussian timing noise, modelling the reaction-time
/ video-scrubbing imprecision of a human labeller -- this is what the evaluation
harness (run_sls_evaluation.py) treats as the reference to agree against.

Deterministic: seeded RNG, so re-running this script reproduces byte-identical
output. The corpus is committed to the repo (backend/app/module_a/replay_corpus/sls/)
so evaluation is reproducible from committed data without re-running this script.

Usage:
    python -m app.module_a.scripts.generate_sls_replay_corpus
"""

import json
import math
import random
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parents[1] / "replay_corpus" / "sls"
SEED = 20260707  # fixed seed -> reproducible corpus
FRAME_DT = 0.1  # 10 Hz synthetic sampling
CALIBRATION_SEC = 2.0
MANUAL_TIMING_NOISE_SD = 0.35  # seconds; models human stopwatch/video-scrub imprecision


def _r(v: float) -> float:
    """4dp is far more precision than these synthetic coordinates need; rounding
    keeps the committed corpus JSON compact (default float repr() bloats file size)."""
    return round(v, 4)


def _make_world(hip_mid_x: float, lifted_ankle_y: float, lifted_idx: int) -> list[dict]:
    """A minimal 33-landmark world pose; `lifted_idx` is 27 (left ankle) or 28 (right)."""
    zero = {"x": 0.0, "y": 0.0, "z": 0.0, "visibility": 1.0}
    world = [zero for _ in range(33)]
    world[23] = {"x": _r(hip_mid_x - 0.1), "y": 0.0, "z": 0.0, "visibility": 1.0}
    world[24] = {"x": _r(hip_mid_x + 0.1), "y": 0.0, "z": 0.0, "visibility": 1.0}
    world[25] = {"x": -0.1, "y": 0.4, "z": 0.0, "visibility": 1.0}
    world[26] = {"x": 0.1, "y": 0.4, "z": 0.0, "visibility": 1.0}
    world[27] = {"x": -0.1, "y": 0.8, "z": 0.0, "visibility": 1.0}
    world[28] = {"x": 0.1, "y": 0.8, "z": 0.0, "visibility": 1.0}
    world[lifted_idx] = dict(world[lifted_idx], y=_r(lifted_ankle_y))
    return world


def _make_frames(
    leg: str,
    intended_hold_sec: float,
    sway_amplitude: float,
    rng: random.Random,
) -> list[dict]:
    """Both feet planted for CALIBRATION_SEC, then the prompted leg lifts and holds
    for exactly `intended_hold_sec` before dropping back down."""
    lifted_idx = 28 if leg == "right" else 27
    total_sec = CALIBRATION_SEC + intended_hold_sec + 2.0
    frames = []
    t = 0.0
    while t <= total_sec + 1e-9:
        in_hold = CALIBRATION_SEC < t <= CALIBRATION_SEC + intended_hold_sec
        ankle_y = 0.45 if in_hold else 0.8
        hip_x = sway_amplitude * math.sin(t * 6.0) if in_hold else 0.0
        # Tiny per-frame jitter so frames aren't bit-identical -- deterministic via seeded rng.
        jitter = rng.uniform(-0.002, 0.002)
        frames.append(
            {
                "timestampMs": round(t * 1000.0, 1),
                "worldLandmarks": _make_world(hip_x + jitter, ankle_y, lifted_idx),
            }
        )
        t += FRAME_DT
    return frames


# (sample_id, leg, intended_hold_sec, sway_amplitude, target band for readability)
SAMPLE_SPECS = [
    ("good_steady_right_1", "right", 40.0, 0.0, "good"),
    ("good_steady_left_1", "left", 44.0, 0.05, "good"),
    ("good_capped_right_1", "right", 50.0, 0.0, "good"),  # exceeds 45s cap
    ("fair_steady_left_1", "left", 18.0, 0.1, "fair"),
    ("fair_swaying_right_1", "right", 20.0, 0.35, "fair"),
    ("fair_steady_right_2", "right", 12.0, 0.1, "fair"),
    ("poor_swaying_left_1", "left", 6.0, 0.4, "poor"),
    ("poor_short_right_1", "right", 3.0, 0.15, "poor"),
    ("poor_swaying_right_2", "right", 8.0, 0.5, "poor"),
    ("invalid_never_lifted_left_1", "left", 0.0, 0.0, "invalid"),
]


def build_corpus() -> list[dict]:
    rng = random.Random(SEED)
    manifest = []
    for sample_id, leg, intended_hold, sway, target_band in SAMPLE_SPECS:
        frames = _make_frames(leg, intended_hold, sway, rng)
        manual_hold = max(0.0, intended_hold + rng.gauss(0.0, MANUAL_TIMING_NOISE_SD))
        frames_path = CORPUS_DIR / f"{sample_id}.json"
        frames_path.write_text(json.dumps(frames, separators=(",", ":")))
        manifest.append(
            {
                "sample_id": sample_id,
                "leg": leg,
                "frames_file": frames_path.name,
                "intended_hold_sec": round(intended_hold, 3),
                "manual_hold_sec": round(manual_hold, 3),
                "target_band_hint": target_band,
                "sway_amplitude": sway,
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
