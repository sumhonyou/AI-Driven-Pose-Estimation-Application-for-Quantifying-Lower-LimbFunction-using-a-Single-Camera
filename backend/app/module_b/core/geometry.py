"""Shared geometry helpers for Module B's world-landmark feature extractors."""

from __future__ import annotations

import math
from typing import Any

from app.module_a.core.geometry import calculate_angle
from app.module_a.core.geometry import trunk_lean_deg as _trunk_lean_deg


def landmark_value(landmark: Any, coordinate: str) -> float:
    """Read one coordinate from either a validated landmark or a plain dict."""
    if isinstance(landmark, dict):
        return float(landmark[coordinate])
    return float(getattr(landmark, coordinate))


def _point(landmark: Any) -> dict[str, float]:
    """Adapt validated Pydantic landmarks to Module A's dict geometry helpers."""
    return {
        coordinate: landmark_value(landmark, coordinate)
        for coordinate in ("x", "y", "z")
    }


def midpoint(left: Any, right: Any) -> dict[str, float]:
    """Return the metric midpoint of a bilateral landmark pair."""
    return {
        coordinate: (
            landmark_value(left, coordinate) + landmark_value(right, coordinate)
        )
        / 2.0
        for coordinate in ("x", "y", "z")
    }


def distance(a: Any, b: Any, *, in_plane: bool = False) -> float:
    """Return Euclidean landmark distance, optionally excluding camera depth."""
    coordinates = ("x", "y") if in_plane else ("x", "y", "z")
    return math.sqrt(
        sum(
            (landmark_value(a, coordinate) - landmark_value(b, coordinate)) ** 2
            for coordinate in coordinates
        )
    )


def knee_flexion_deg(hip: Any, knee: Any, ankle: Any) -> float:
    """Return flexion (0° straight, increasing as the knee bends)."""
    return 180.0 - calculate_angle(_point(hip), _point(knee), _point(ankle))


def hip_flexion_deg(shoulder: Any, hip: Any, knee: Any) -> float:
    """Return hip flexion (0° upright/extended, increasing while descending)."""
    return 180.0 - calculate_angle(_point(shoulder), _point(hip), _point(knee))


def trunk_lean_deg(shoulder: Any, hip: Any) -> float:
    """Return trunk lean while accepting validated landmarks as well as dicts."""
    return _trunk_lean_deg(_point(shoulder), _point(hip))


def shank_vs_vertical_deg(knee: Any, ankle: Any) -> float:
    """Return the shank's unsigned deviation from world vertical."""
    shank_length = distance(knee, ankle)
    if shank_length < 1e-9:
        return 0.0
    vertical_component = landmark_value(ankle, "y") - landmark_value(knee, "y")
    cosine = max(-1.0, min(1.0, vertical_component / shank_length))
    return math.degrees(math.acos(cosine))


__all__ = [
    "calculate_angle",
    "distance",
    "hip_flexion_deg",
    "knee_flexion_deg",
    "landmark_value",
    "midpoint",
    "shank_vs_vertical_deg",
    "trunk_lean_deg",
]
