"""Pure, side-view squat feature extraction from one rep's world-landmark frames."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.core.geometry import (
    distance,
    hip_flexion_deg,
    knee_flexion_deg,
    midpoint,
    shank_vs_vertical_deg,
    trunk_lean_deg,
)
from app.module_b.squat.config import SQUAT_CONFIG


class RepWithFrames(Protocol):
    """Minimal rep shape required by the squat feature extractor."""

    frames: Sequence[Any]


SQUAT_FEATURE_NAMES = (
    "knee_flex_peak_deg",
    "knee_flex_min_deg",
    "knee_rom_deg",
    "hip_flex_peak_deg",
    "trunk_lean_peak_deg",
    "trunk_lean_mean_deg",
    "knee_ang_vel_max_dps",
    "rep_duration_s",
    "descent_ascent_ratio",
    "symmetry_index_pct",
    "ankle_df_proxy_deg",
    "hip_mid_jitter_norm",
    "stance_width_norm",
)

# `knee_valgus_proxy` is deliberately excluded: it is a frontal-plane measure
# that a single monocular side view cannot support (task.md: Deliberately Not Built).


def extract_squat_features(
    rep: RepWithFrames | Mapping[str, Any] | Sequence[Any],
) -> FeatureVector:
    """Extract the stable, ordered feature vector for one already-segmented rep."""
    frames = _frames_for_rep(rep)
    if not frames:
        raise ValueError("Cannot extract squat features from an empty rep")

    samples = [_frame_sample(frame) for frame in frames]
    knee_flexions = [sample["knee_flexion"] for sample in samples]
    hip_flexions = [sample["hip_flexion"] for sample in samples]
    trunk_leans = [sample["trunk_lean"] for sample in samples]
    timestamps_s = [sample["timestamp_s"] for sample in samples]

    norm_ref = _norm_ref(samples)
    peak_knee_flexion = max(knee_flexions)
    min_knee_flexion = min(knee_flexions)
    values = (
        peak_knee_flexion,
        min_knee_flexion,
        peak_knee_flexion - min_knee_flexion,
        max(hip_flexions),
        max(trunk_leans),
        sum(trunk_leans) / len(trunk_leans),
        _max_knee_angular_velocity(knee_flexions, timestamps_s),
        timestamps_s[-1] - timestamps_s[0],
        _descent_ascent_ratio(knee_flexions, timestamps_s),
        sum(sample["symmetry_index"] for sample in samples) / len(samples),
        max(sample["ankle_df_proxy"] for sample in samples),
        _hip_mid_jitter_norm(samples, norm_ref),
        sum(sample["stance_width"] for sample in samples) / len(samples) / norm_ref,
    )
    return FeatureVector(
        schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
        names=SQUAT_FEATURE_NAMES,
        values=tuple(float(value) for value in values),
    )


def _frames_for_rep(
    rep: RepWithFrames | Mapping[str, Any] | Sequence[Any],
) -> list[Any]:
    if isinstance(rep, Mapping):
        frames = rep.get("frames")
    elif isinstance(rep, Sequence) and not isinstance(rep, (str, bytes)):
        frames = rep
    else:
        frames = getattr(rep, "frames", None)
    if frames is None:
        raise ValueError("Rep must provide its frames")
    return list(frames)


def _frame_sample(frame: Any) -> dict[str, Any]:
    landmarks = _frame_value(frame, "worldLandmarks")
    if len(landmarks) <= 28:
        raise ValueError(
            "Squat feature extraction requires MediaPipe landmarks through index 28"
        )
    left_shoulder, right_shoulder = landmarks[11], landmarks[12]
    left_hip, right_hip = landmarks[23], landmarks[24]
    left_knee, right_knee = landmarks[25], landmarks[26]
    left_ankle, right_ankle = landmarks[27], landmarks[28]
    shoulder_mid = midpoint(left_shoulder, right_shoulder)
    hip_mid = midpoint(left_hip, right_hip)
    left_knee_flexion = knee_flexion_deg(left_hip, left_knee, left_ankle)
    right_knee_flexion = knee_flexion_deg(right_hip, right_knee, right_ankle)
    mean_knee_flexion = (left_knee_flexion + right_knee_flexion) / 2.0
    knee_mean = max((left_knee_flexion + right_knee_flexion) / 2.0, 1e-9)
    return {
        "timestamp_s": float(_frame_value(frame, "timestampMs")) / 1000.0,
        "knee_flexion": mean_knee_flexion,
        "hip_flexion": (
            hip_flexion_deg(left_shoulder, left_hip, left_knee)
            + hip_flexion_deg(right_shoulder, right_hip, right_knee)
        )
        / 2.0,
        "trunk_lean": trunk_lean_deg(shoulder_mid, hip_mid),
        "symmetry_index": abs(left_knee_flexion - right_knee_flexion)
        / knee_mean
        * 100.0,
        "ankle_df_proxy": (
            shank_vs_vertical_deg(left_knee, left_ankle)
            + shank_vs_vertical_deg(right_knee, right_ankle)
        )
        / 2.0,
        "hip_mid": hip_mid,
        "trunk_length": distance(shoulder_mid, hip_mid),
        "thigh_length": (
            distance(left_hip, left_knee) + distance(right_hip, right_knee)
        )
        / 2.0,
        "stance_width": distance(left_ankle, right_ankle),
    }


def _frame_value(frame: Any, name: str) -> Any:
    if isinstance(frame, Mapping):
        return frame[name]
    return getattr(frame, name)


def _norm_ref(samples: list[dict[str, Any]]) -> float:
    strategy = SQUAT_CONFIG["norm_ref_strategy"]
    if strategy not in {"thigh_length", "trunk_length"}:
        raise ValueError(f"Unsupported squat norm_ref_strategy: {strategy}")
    reference = sum(sample[strategy] for sample in samples) / len(samples)
    if reference < 1e-9:
        raise ValueError(f"Cannot normalize squat features with a zero {strategy}")
    return reference


def _max_knee_angular_velocity(values: list[float], timestamps_s: list[float]) -> float:
    velocities = [
        abs(current - previous) / (current_time - previous_time)
        for previous, current, previous_time, current_time in zip(
            values[:-1], values[1:], timestamps_s[:-1], timestamps_s[1:], strict=True
        )
        if current_time > previous_time
    ]
    return max(velocities, default=0.0)


def _descent_ascent_ratio(values: list[float], timestamps_s: list[float]) -> float:
    peak_index = max(range(len(values)), key=values.__getitem__)
    descent_s = timestamps_s[peak_index] - timestamps_s[0]
    ascent_s = timestamps_s[-1] - timestamps_s[peak_index]
    if ascent_s <= 0.0:
        return 0.0
    return descent_s / ascent_s


def _hip_mid_jitter_norm(samples: list[dict[str, Any]], norm_ref: float) -> float:
    displacements = [
        distance(previous["hip_mid"], current["hip_mid"], in_plane=True)
        for previous, current in zip(samples[:-1], samples[1:], strict=True)
    ]
    return (
        (sum(displacements) / len(displacements) / norm_ref) if displacements else 0.0
    )
