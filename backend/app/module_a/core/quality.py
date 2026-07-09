"""Capture-quality checks: per-frame validity and session-level quality band."""

from app.module_a.core.config import (
    MIN_VISIBILITY,
    QUALITY_GOOD_MIN,
    QUALITY_MODERATE_MIN,
)

# STS knee-angle + trunk-lean geometry only ever needs ONE leg's kinematic chain
# (shoulder-hip-knee-ankle). A pure side-view camera structurally occludes the far
# leg behind the near leg, so requiring both legs' landmarks made captures fail
# even with a well-tracked near leg. SessionEngine picks whichever side MediaPipe
# tracks better for a given session (see _pick_tracked_leg) and quality is judged
# against that side only.
LANDMARKS_BY_LEG = {
    "left": {11: "left_shoulder", 23: "left_hip", 25: "left_knee", 27: "left_ankle"},
    "right": {
        12: "right_shoulder",
        24: "right_hip",
        26: "right_knee",
        28: "right_ankle",
    },
}


def is_frame_valid(world_landmarks: list[dict], leg: str = "left") -> bool:
    """A frame is valid if the tracked leg's chain is visible above threshold."""
    if not world_landmarks or len(world_landmarks) < 33:
        return False
    required = LANDMARKS_BY_LEG[leg]
    return all(
        world_landmarks[idx].get("visibility", 0.0) >= MIN_VISIBILITY
        for idx in required
    )


def average_visibility(world_landmarks: list[dict], leg: str = "left") -> float:
    """Mean visibility across the tracked leg's chain for one frame."""
    if not world_landmarks:
        return 0.0
    required = LANDMARKS_BY_LEG[leg]
    values = [
        (
            world_landmarks[idx].get("visibility", 0.0)
            if idx < len(world_landmarks)
            else 0.0
        )
        for idx in required
    ]
    return sum(values) / len(values)


def quality_band(valid_frame_ratio: float) -> str:
    """Maps a session-level valid-frame ratio to a capture-quality band."""
    if valid_frame_ratio >= QUALITY_GOOD_MIN:
        return "good"
    if valid_frame_ratio >= QUALITY_MODERATE_MIN:
        return "moderate"
    return "poor"


def session_quality(
    frame_validity: list[bool], frame_avg_visibility: list[float]
) -> dict:
    """Aggregates per-frame validity/visibility into session-level quality metrics."""
    total = len(frame_validity)
    valid_frame_ratio = (sum(frame_validity) / total) if total else 0.0
    avg_visibility = (sum(frame_avg_visibility) / total) if total else 0.0
    band = quality_band(valid_frame_ratio)
    return {
        "valid_frame_ratio": valid_frame_ratio,
        "average_visibility": avg_visibility,
        "quality_band": band,
    }
