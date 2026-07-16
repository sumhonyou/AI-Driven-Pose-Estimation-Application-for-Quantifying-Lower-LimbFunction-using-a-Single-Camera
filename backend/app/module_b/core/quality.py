"""Module B capture quality using the shared Module A quality-band convention."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.module_a.core.quality import quality_band
from app.module_b.core.config import MODULE_B_CORE_CONFIG

REQUIRED_LANDMARKS = (11, 12, 23, 24, 25, 26, 27, 28)


def assess_capture_quality(frames: list[dict[str, Any]]) -> dict[str, float | str]:
    """Return bilateral-feature capture Q without retaining browser video or frames."""
    if not frames:
        return {"q": 0.0, "valid_frame_ratio": 0.0, "capture_quality_band": "poor"}
    frame_visibilities = [_frame_visibility(frame) for frame in frames]
    q = sum(sum(values) / len(values) for values in frame_visibilities) / len(frames)
    confidence_threshold = MODULE_B_CORE_CONFIG["confidence_threshold"]
    valid_frame_ratio = sum(
        all(visibility >= confidence_threshold for visibility in values)
        for values in frame_visibilities
    ) / len(frames)
    # Module A's helper uses the same frozen good/moderate/poor boundaries as
    # MODULE_B_CORE_CONFIG, avoiding a fork of shared quality-band behavior.
    return {
        "q": q,
        "valid_frame_ratio": valid_frame_ratio,
        "capture_quality_band": quality_band(q),
    }


def _frame_visibility(frame: Any) -> list[float]:
    landmarks = _frame_value(frame, "worldLandmarks")
    values = []
    for index in REQUIRED_LANDMARKS:
        if index >= len(landmarks):
            values.append(0.0)
            continue
        landmark = landmarks[index]
        values.append(float(_landmark_value(landmark, "visibility", 0.0)))
    return values


def _frame_value(frame: Any, name: str) -> Any:
    if isinstance(frame, Mapping):
        return frame[name]
    return getattr(frame, name)


def _landmark_value(landmark: Any, name: str, default: float) -> float:
    if isinstance(landmark, Mapping):
        return landmark.get(name, default)
    return getattr(landmark, name, default)
