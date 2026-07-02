"""Capture-quality checks: per-frame validity and session-level quality band."""

from app.module_a.config import MIN_VISIBILITY, QUALITY_GOOD_MIN, QUALITY_MODERATE_MIN

# Landmarks required for STS knee-angle + trunk-lean geometry (indices match MediaPipe Pose).
REQUIRED_LANDMARKS = {
    11: "left_shoulder",
    12: "right_shoulder",
    23: "left_hip",
    24: "right_hip",
    25: "left_knee",
    26: "right_knee",
    27: "left_ankle",
    28: "right_ankle",
}


def is_frame_valid(world_landmarks: list[dict]) -> bool:
    """A frame is valid if all required landmarks are visible above threshold."""
    if not world_landmarks or len(world_landmarks) < 33:
        return False
    return all(
        world_landmarks[idx].get("visibility", 0.0) >= MIN_VISIBILITY
        for idx in REQUIRED_LANDMARKS
    )


def average_visibility(world_landmarks: list[dict]) -> float:
    """Mean visibility across the required landmarks for one frame."""
    if not world_landmarks:
        return 0.0
    values = [
        (
            world_landmarks[idx].get("visibility", 0.0)
            if idx < len(world_landmarks)
            else 0.0
        )
        for idx in REQUIRED_LANDMARKS
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
