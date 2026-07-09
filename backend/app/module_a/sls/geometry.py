"""SLS world-landmark geometry: lift-line, hip-midpoint, ball position, tolerance circle.

All measures use MediaPipe WORLD landmarks (metric, scale-invariant). Vertical axis
convention matches the rest of Module A: Y increases DOWNWARD, so "higher off the
ground" means a SMALLER y. A lifted foot therefore has a smaller y than when planted.
Scale invariance comes from normalising by stance-leg length (lift-line) and hip
width (ball position), never raw pixels.
"""

import math

# MediaPipe landmark indices, per side.
HIP = {"left": 23, "right": 24}
KNEE = {"left": 25, "right": 26}
ANKLE = {"left": 27, "right": 28}
FOOT_INDEX = {"left": 31, "right": 32}


def other_leg(leg: str) -> str:
    """The stance leg is whichever side is not being lifted."""
    return "left" if leg == "right" else "right"


def _dist(a: dict, b: dict) -> float:
    """3-D euclidean distance between two landmarks."""
    return math.sqrt(
        (a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2 + (a["z"] - b["z"]) ** 2
    )


def hip_width(world: list[dict]) -> float:
    """Distance between the two hips — the scale unit for lateral ball offset."""
    return _dist(world[HIP["left"]], world[HIP["right"]])


def hip_midpoint(world: list[dict]) -> dict:
    """Body-centre proxy: midpoint of the two hips."""
    left, right = world[HIP["left"]], world[HIP["right"]]
    return {
        "x": (left["x"] + right["x"]) / 2,
        "y": (left["y"] + right["y"]) / 2,
        "z": (left["z"] + right["z"]) / 2,
    }


def stance_leg_length(world: list[dict], stance_leg: str) -> float:
    """Hip->ankle distance of the stance leg — the scale unit for the lift-line."""
    return _dist(world[HIP[stance_leg]], world[ANKLE[stance_leg]])


def lifted_ankle_y(world: list[dict], lifted_leg: str) -> float:
    """Vertical position of the lifted leg's ankle (smaller = higher off the ground)."""
    return world[ANKLE[lifted_leg]]["y"]


def lift_line_y(
    baseline_ankle_y: float, leg_length: float, lift_line_norm: float
) -> float:
    """Y of the lift-line: a fraction of stance-leg length ABOVE the baseline foot.

    Up is -y, so "above baseline" subtracts. A foot is above the line when its
    ankle y is LESS than this value.
    """
    return baseline_ankle_y - lift_line_norm * leg_length


def is_above_line(ankle_y: float, line_y: float) -> bool:
    """True when the ankle has risen above the lift-line (y smaller than the line)."""
    return ankle_y < line_y


def ball_x_norm(world: list[dict], stance_leg: str) -> float:
    """Frontal-plane (left-right) offset of the hip-midpoint from the stance foot.

    Normalised by hip width for scale invariance. Only the x axis is used —
    monocular depth (z) is unreliable, so it is deliberately ignored for scoring.
    """
    width = hip_width(world)
    if width < 1e-9:
        return 0.0
    centre_x = hip_midpoint(world)["x"]
    stance_x = world[ANKLE[stance_leg]]["x"]
    return (centre_x - stance_x) / width


def is_inside_circle(ball_x: float, radius_norm: float) -> bool:
    """Ball is inside the tolerance circle when its |x offset| is within the radius."""
    return abs(ball_x) <= radius_norm
