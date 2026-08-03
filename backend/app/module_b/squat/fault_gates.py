"""Interpretable squat fault gates: depth, trunk lean, and heel rise.

Fault gates are separate from ML fusion. They make named pass/fail decisions per rep so
the report can explain why a rep needs improvement.

Gate inputs:

- Depth and trunk lean use the extracted `FeatureVector`.
- Heel rise reads raw heel/toe landmarks because it is outside the frozen ML feature
  schema.

Heel-rise measurement uses the better-tracked camera-side leg, a short median baseline,
and a debounce window. If the chosen foot is not visible enough, the gate refuses to fire
instead of guessing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.module_a.core.config import MIN_VISIBILITY
from app.module_b.core.features import FeatureVector
from app.module_b.core.geometry import distance, landmark_value, midpoint

# MediaPipe landmark indices used only by the heel-rise gate (rule-only; never enters
# the ML feature vector). Left/right heel and foot-index (toe).
_HEEL = {"left": 29, "right": 30}
_TOE = {"left": 31, "right": 32}
_MAX_HEEL_LANDMARK_INDEX = 32

# Short start-of-rep window used for the heel baseline.
_SETTLE_WINDOW_FRAMES = 3
# A rise only counts once it holds for this many consecutive frames -- a single spiky
# frame (a landmark glitch) can no longer set the whole rep's peak. Same idiom as
# WBLT's `lift_debounce_frames`.
_DEBOUNCE_FRAMES = 3
# Below this mean visibility, even the camera-side foot isn't reliably tracked for the
# rep; the gate must not manufacture a verdict from a foot it effectively can't see.
_MIN_LEG_VISIBILITY = MIN_VISIBILITY
# Sentinel below any real normalized rise, guaranteeing the gate never fires when the
# near leg is unreliable.
_OCCLUDED_SENTINEL = float("-1.0")


@dataclass(frozen=True)
class GateCheck:
    """One failed fault gate on one rep, carrying the reason and the measured value."""

    tag: str
    message: str
    metric_value: float
    rep_index: int


@dataclass(frozen=True)
class FaultGateResult:
    """Aggregate gate outcome across a whole set. ``failed`` is empty iff all passed."""

    all_passed: bool
    failed: tuple[GateCheck, ...]


# --- Per-rep gate predicates ------------------------------------------------------


def depth_gate(
    features: FeatureVector, config: dict[str, Any], rep_index: int
) -> GateCheck | None:
    """Fail if the rep never reaches the clinical minimum knee-flexion depth.

    Clinical floor, not a learned cut — see the module docstring. Fires when
    ``knee_flex_peak_deg`` stays below ``min_knee_flex_peak_deg`` for the whole rep.
    """
    threshold = float(config["min_knee_flex_peak_deg"])
    peak = features.as_dict()["knee_flex_peak_deg"]
    if peak < threshold:
        return GateCheck(
            tag=config["tag"],
            message=config["message"],
            metric_value=float(peak),
            rep_index=rep_index,
        )
    return None


def lean_gate(
    features: FeatureVector, config: dict[str, Any], rep_index: int
) -> GateCheck | None:
    """Fail if peak trunk lean reaches the dataset-derived fault threshold."""
    threshold = float(config["fault_trunk_lean_peak_deg"])
    peak = features.as_dict()["trunk_lean_peak_deg"]
    if peak >= threshold:
        return GateCheck(
            tag=config["tag"],
            message=config["message"],
            metric_value=float(peak),
            rep_index=rep_index,
        )
    return None


def heel_rise_gate(
    rep: Any, config: dict[str, Any], rep_index: int
) -> GateCheck | None:
    """Fail if the heels lift off the floor past the dataset-derived threshold.

    Reads the rep's raw frames (landmarks 29–32) rather than the FeatureVector, since
    heel rise is a rule-only signal outside the frozen ML feature contract.
    """
    threshold = float(config["fault_heel_rise_peak_norm"])
    peak_norm = _heel_rise_peak_norm(_frames_for_rep(rep))
    if peak_norm >= threshold:
        return GateCheck(
            tag=config["tag"],
            message=config["message"],
            metric_value=float(peak_norm),
            rep_index=rep_index,
        )
    return None


# --- Set-level aggregator ---------------------------------------------------------


def evaluate_fault_gates(
    reps: Sequence[Any],
    feature_vectors: Sequence[FeatureVector],
    config: dict[str, Any],
) -> FaultGateResult:
    """Run every enabled gate against every rep and collect all failures."""
    if len(reps) != len(feature_vectors):
        raise ValueError("reps and feature_vectors must align one-to-one")

    depth_cfg = config.get("depth")
    lean_cfg = config.get("lean")
    heel_cfg = config.get("heel_rise")

    failed: list[GateCheck] = []
    for rep_index, (rep, features) in enumerate(zip(reps, feature_vectors)):
        if depth_cfg is not None and depth_cfg.get("enabled", False):
            check = depth_gate(features, depth_cfg, rep_index)
            if check is not None:
                failed.append(check)
        if lean_cfg is not None and lean_cfg.get("enabled", False):
            check = lean_gate(features, lean_cfg, rep_index)
            if check is not None:
                failed.append(check)
        if heel_cfg is not None and heel_cfg.get("enabled", False):
            check = heel_rise_gate(rep, heel_cfg, rep_index)
            if check is not None:
                failed.append(check)

    return FaultGateResult(all_passed=not failed, failed=tuple(failed))


# --- Heel-rise measurement (mirrors ml/scripts/analyze_fault_gate_thresholds.py) ---


def _heel_rise_peak_norm(frames: list[Any]) -> float:
    """Peak near-leg heel lift, debounced, normalized by trunk length."""
    if not frames:
        raise ValueError("Cannot evaluate heel rise on an empty rep")

    near_leg = _select_near_leg(frames)
    if _leg_visibility(frames, near_leg) < _MIN_LEG_VISIBILITY:
        return _OCCLUDED_SENTINEL

    lifts = [_toe_heel_lift(frame, near_leg) for frame in frames]
    settle = lifts[: min(_SETTLE_WINDOW_FRAMES, len(lifts))]
    baseline = sorted(settle)[len(settle) // 2]
    rises = [value - baseline for value in lifts]

    window = min(_DEBOUNCE_FRAMES, len(rises))
    sustained_peak = max(
        min(rises[i : i + window]) for i in range(len(rises) - window + 1)
    )

    norm_ref = sum(_trunk_length(frame) for frame in frames) / len(frames)
    if norm_ref < 1e-9:
        raise ValueError("Cannot normalize heel rise with a zero trunk length")
    return sustained_peak / norm_ref


def _select_near_leg(frames: list[Any]) -> str:
    """Pick the camera-side leg by whichever heel/toe pair is better tracked."""
    left_visibility = _leg_visibility(frames, "left")
    right_visibility = _leg_visibility(frames, "right")
    return "left" if left_visibility >= right_visibility else "right"


def _leg_visibility(frames: list[Any], side: str) -> float:
    """Mean heel+toe landmark visibility for one leg across the rep."""
    values = []
    for frame in frames:
        landmarks = _frame_landmarks(frame)
        values.append(landmark_value(landmarks[_HEEL[side]], "visibility"))
        values.append(landmark_value(landmarks[_TOE[side]], "visibility"))
    return sum(values) / len(values)


def _toe_heel_lift(frame: Any, side: str) -> float:
    landmarks = _frame_landmarks(frame)
    return landmark_value(landmarks[_TOE[side]], "y") - landmark_value(
        landmarks[_HEEL[side]], "y"
    )


def _trunk_length(frame: Any) -> float:
    landmarks = _frame_landmarks(frame)
    shoulder_mid = midpoint(landmarks[11], landmarks[12])
    hip_mid = midpoint(landmarks[23], landmarks[24])
    return distance(shoulder_mid, hip_mid)


def _frame_landmarks(frame: Any) -> Sequence[Any]:
    landmarks = _frame_value(frame, "worldLandmarks")
    if len(landmarks) <= _MAX_HEEL_LANDMARK_INDEX:
        raise ValueError(
            "Heel-rise gate requires MediaPipe landmarks through index "
            f"{_MAX_HEEL_LANDMARK_INDEX}"
        )
    return landmarks


def _frames_for_rep(rep: Any) -> list[Any]:
    if isinstance(rep, Mapping):
        frames = rep.get("frames")
    elif isinstance(rep, Sequence) and not isinstance(rep, (str, bytes)):
        frames = rep
    else:
        frames = getattr(rep, "frames", None)
    if frames is None:
        raise ValueError("Rep must provide its frames")
    return list(frames)


def _frame_value(frame: Any, name: str) -> Any:
    if isinstance(frame, Mapping):
        return frame[name]
    return getattr(frame, name)
