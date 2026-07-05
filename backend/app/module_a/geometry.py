"""Joint-angle geometry from MediaPipe world landmarks.

Vertical axis convention (MediaPipe world landmarks, metric, hip-centered):
Y increases DOWNWARD, same as image-space landmarks.

Landmarks are re-centered on the hip midpoint every frame, so the hip's own Y
is always ~0 and cannot be used to measure how much the hip actually rose in
real space (confirmed against real recordings — see session_engine.py, which
no longer gates on hip displacement for exactly this reason). Knee angle, a
relative joint angle, is unaffected by this and is the reliable signal here.
"""

import math

# Vertical "up" unit vector in MediaPipe world-landmark space (see module docstring).
UP_VECTOR = (0.0, -1.0, 0.0)


def _vec(a: dict, b: dict) -> tuple[float, float, float]:
    """Vector from point b to point a (v = a - b)."""
    return (a["x"] - b["x"], a["y"] - b["y"], a["z"] - b["z"])


def _cross(v1: tuple, v2: tuple) -> tuple[float, float, float]:
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0],
    )


def _dot(v1: tuple, v2: tuple) -> float:
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]


def _norm(v: tuple) -> float:
    return math.sqrt(_dot(v, v))


def calculate_angle(a: dict, b: dict, c: dict) -> float:
    """Angle ABC in degrees, where b is the vertex.

    Uses atan2(|v1 x v2|, v1 . v2) instead of acos(dot/norms) because it stays
    numerically well-conditioned near 0deg/180deg — exactly the range the STS
    "standing" region and rep FSM operate in, where acos is most jitter-prone.
    """
    v1 = _vec(a, b)
    v2 = _vec(c, b)
    cross_mag = _norm(_cross(v1, v2))
    dot = _dot(v1, v2)
    angle_rad = math.atan2(cross_mag, dot)
    return math.degrees(angle_rad)


def knee_angle(hip: dict, knee: dict, ankle: dict) -> float:
    """Knee flexion angle: ~180 deg standing straight, smaller when bent/sitting."""
    return calculate_angle(hip, knee, ankle)


def trunk_lean_deg(shoulder: dict, hip: dict) -> float:
    """Trunk lean proxy: angle between the shoulder->hip segment and vertical."""
    v = _vec(shoulder, hip)
    v_norm = _norm(v)
    if v_norm < 1e-9:
        return 0.0
    cos_angle = _dot(v, UP_VECTOR) / v_norm
    cos_angle = max(-1.0, min(1.0, cos_angle))
    return math.degrees(math.acos(cos_angle))
