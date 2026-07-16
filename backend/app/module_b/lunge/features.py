"""Pure, side-view lunge feature extraction from one rep's world-landmark frames.

A lunge is asymmetric: the front (lead) leg and back leg do different jobs in one
rep, so features are defined in front_/back_ terms rather than squat's both-legs
means. The vector is lead-leg-invariant (a left-lead and right-lead rep of equal
quality produce the same values); the anatomical lead leg is recorded as
FeatureVector.lead_leg metadata, not as a numeric feature.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from app.module_b.core.config import MODULE_B_CORE_CONFIG
from app.module_b.core.features import FeatureVector
from app.module_b.core.geometry import (distance, hip_flexion_deg,
                                        knee_flexion_deg, landmark_value,
                                        midpoint, shank_vs_vertical_deg,
                                        trunk_lean_deg)
from app.module_b.lunge.config import LUNGE_CONFIG


class RepWithFrames(Protocol):
    """Minimal Stage 4.2 view of a rep; Stage 4.3's Rep will satisfy this."""

    frames: Sequence[Any]


LUNGE_FEATURE_NAMES = (
    "front_knee_flex_peak_deg",
    "front_knee_flex_min_deg",
    "front_knee_rom_deg",
    "back_knee_flex_peak_deg",
    "back_knee_flex_min_deg",
    "back_knee_rom_deg",
    "front_hip_flex_peak_deg",
    "back_hip_flex_peak_deg",
    "trunk_lean_peak_deg",
    "trunk_lean_mean_deg",
    "front_knee_ang_vel_max_dps",
    "rep_duration_s",
    "descent_ascent_ratio",
    "front_ankle_df_proxy_deg",
    "hip_mid_jitter_norm",
    "stance_length_norm",
    "knee_passes_toe_norm",
)

# `knee_valgus_proxy` is deliberately excluded: it is a frontal-plane measure a
# single monocular side view cannot support (task.md: Deliberately Not Built).
# Within-rep left-vs-right symmetry is also excluded on purpose: the two legs do
# different jobs in a lunge, so it is meaningless per rep. Cross-rep symmetry
# (leading-left vs leading-right) is computed at set level in Stage 4.4.


def extract_lunge_features(
    rep: RepWithFrames | Mapping[str, Any] | Sequence[Any],
    lead_leg: str | None = None,
) -> FeatureVector:
    """Extract the stable, ordered feature vector for one already-segmented rep.

    lead_leg: pass "left"/"right" to force the front leg (offline training uses the
    given `exercise_subtype`, Stage 5.3). Left None live, where the front leg is
    inferred from which foot is more forward (Stage 5.2).
    """
    frames = _frames_for_rep(rep)
    if not frames:
        raise ValueError("Cannot extract lunge features from an empty rep")

    samples = [_frame_sample(frame) for frame in frames]
    anterior_sign = _anterior_sign(samples)
    front = _resolve_front_leg(samples, anterior_sign, lead_leg)
    back = "right" if front == "left" else "left"

    timestamps_s = [sample["timestamp_s"] for sample in samples]
    trunk_leans = [sample["trunk_lean"] for sample in samples]
    norm_ref = _norm_ref(samples)

    front_knee = [sample[f"{front}_knee_flexion"] for sample in samples]
    back_knee = [sample[f"{back}_knee_flexion"] for sample in samples]
    front_knee_peak = max(front_knee)
    front_knee_min = min(front_knee)
    back_knee_peak = max(back_knee)
    back_knee_min = min(back_knee)

    values = (
        front_knee_peak,
        front_knee_min,
        front_knee_peak - front_knee_min,
        back_knee_peak,
        back_knee_min,
        back_knee_peak - back_knee_min,
        max(sample[f"{front}_hip_flexion"] for sample in samples),
        max(sample[f"{back}_hip_flexion"] for sample in samples),
        max(trunk_leans),
        sum(trunk_leans) / len(trunk_leans),
        _max_angular_velocity(front_knee, timestamps_s),
        timestamps_s[-1] - timestamps_s[0],
        _descent_ascent_ratio(front_knee, timestamps_s),
        max(sample[f"{front}_ankle_df_proxy"] for sample in samples),
        _hip_mid_jitter_norm(samples, norm_ref),
        sum(sample["stance_length"] for sample in samples) / len(samples) / norm_ref,
        _knee_passes_toe_norm(samples, front, anterior_sign, norm_ref),
    )
    return FeatureVector(
        schema_version=MODULE_B_CORE_CONFIG["feature_schema_version"],
        names=LUNGE_FEATURE_NAMES,
        values=tuple(float(value) for value in values),
        lead_leg=front,
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
    # Lunge needs the foot-tip joints (31/32) for knee_passes_toe, so it requires
    # the full MediaPipe-33 set, not just through the ankles like squat.
    if len(landmarks) <= 32:
        raise ValueError(
            "Lunge feature extraction requires MediaPipe landmarks through index 32"
        )
    left_shoulder, right_shoulder = landmarks[11], landmarks[12]
    left_hip, right_hip = landmarks[23], landmarks[24]
    left_knee, right_knee = landmarks[25], landmarks[26]
    left_ankle, right_ankle = landmarks[27], landmarks[28]
    left_toe, right_toe = landmarks[31], landmarks[32]
    shoulder_mid = midpoint(left_shoulder, right_shoulder)
    hip_mid = midpoint(left_hip, right_hip)
    return {
        "timestamp_s": float(_frame_value(frame, "timestampMs")) / 1000.0,
        "left_knee_flexion": knee_flexion_deg(left_hip, left_knee, left_ankle),
        "right_knee_flexion": knee_flexion_deg(right_hip, right_knee, right_ankle),
        "left_hip_flexion": hip_flexion_deg(left_shoulder, left_hip, left_knee),
        "right_hip_flexion": hip_flexion_deg(right_shoulder, right_hip, right_knee),
        "left_ankle_df_proxy": shank_vs_vertical_deg(left_knee, left_ankle),
        "right_ankle_df_proxy": shank_vs_vertical_deg(right_knee, right_ankle),
        "trunk_lean": trunk_lean_deg(shoulder_mid, hip_mid),
        "hip_mid": hip_mid,
        "trunk_length": distance(shoulder_mid, hip_mid),
        "thigh_length": (
            distance(left_hip, left_knee) + distance(right_hip, right_knee)
        )
        / 2.0,
        "stance_length": distance(left_ankle, right_ankle),
        "left_ankle_x": landmark_value(left_ankle, "x"),
        "right_ankle_x": landmark_value(right_ankle, "x"),
        "left_knee_x": landmark_value(left_knee, "x"),
        "right_knee_x": landmark_value(right_knee, "x"),
        "left_toe_x": landmark_value(left_toe, "x"),
        "right_toe_x": landmark_value(right_toe, "x"),
    }


def _frame_value(frame: Any, name: str) -> Any:
    if isinstance(frame, Mapping):
        return frame[name]
    return getattr(frame, name)


def _anterior_sign(samples: list[dict[str, Any]]) -> float:
    """Return +1/-1 for the world-x direction the toes point (forward)."""
    toe_ahead = sum(
        (sample["left_toe_x"] - sample["left_ankle_x"])
        + (sample["right_toe_x"] - sample["right_ankle_x"])
        for sample in samples
    )
    return 1.0 if toe_ahead >= 0.0 else -1.0


def _resolve_front_leg(
    samples: list[dict[str, Any]], anterior_sign: float, lead_leg: str | None
) -> str:
    """Force the front leg when given, else infer it from the more-forward foot."""
    if lead_leg is not None:
        if lead_leg not in {"left", "right"}:
            raise ValueError("lead_leg must be 'left', 'right', or None")
        return lead_leg
    left_forward = (
        sum(s["left_ankle_x"] for s in samples) / len(samples) * anterior_sign
    )
    right_forward = (
        sum(s["right_ankle_x"] for s in samples) / len(samples) * anterior_sign
    )
    return "left" if left_forward >= right_forward else "right"


def _norm_ref(samples: list[dict[str, Any]]) -> float:
    strategy = LUNGE_CONFIG["norm_ref_strategy"]
    if strategy not in {"thigh_length", "trunk_length"}:
        raise ValueError(f"Unsupported lunge norm_ref_strategy: {strategy}")
    reference = sum(sample[strategy] for sample in samples) / len(samples)
    if reference < 1e-9:
        raise ValueError(f"Cannot normalize lunge features with a zero {strategy}")
    return reference


def _max_angular_velocity(values: list[float], timestamps_s: list[float]) -> float:
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


def _knee_passes_toe_norm(
    samples: list[dict[str, Any]], front: str, anterior_sign: float, norm_ref: float
) -> float:
    """Max normalised anterior excursion of the front knee past the front toe.

    Positive means the knee travelled forward of the toe (the lunge fault); a value
    at or below zero means the knee stayed behind the toe throughout the rep.
    """
    excursions = [
        (sample[f"{front}_knee_x"] - sample[f"{front}_toe_x"]) * anterior_sign
        for sample in samples
    ]
    return max(excursions) / norm_ref
