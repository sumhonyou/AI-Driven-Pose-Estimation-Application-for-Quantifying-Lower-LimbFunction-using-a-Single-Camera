"""Stage 5.12: interpretable fault gates for squat (depth / lean / heel-rise).

These gates are a **separate override layer**, deliberately NOT part of fusion or of
`RuleScores.score`. `RuleScores.score` is an equal-weight mean, which would let one
hard fault be diluted by good sub-scores — the wrong mechanism for "any single named
fault should force Needs Improvement". A gate instead makes a binary pass/fail
decision per rep; if any enabled gate fails on any rep, `router.py` overrides the
fused band to Poor and attaches a specific, human-readable reason.

Why gates at all, when Stage 5.11 already ships a committed Good/Poor ML verdict: the
ML's verdict is a single opaque number that cannot say *why* a rep was bad, and it
only ever scores the first detected rep of a set (a separate, deferred finding). These
gates run across **every** rep and name the fault. Each gate's threshold is justified
differently, and that difference is intentional (see ml/reports/
SQUAT_FAULT_GATE_ANALYSIS.md, Stage 5.12 Phase A):

- **lean** — data-driven. `trunk_lean_peak_deg` has a real KEEP verdict on REHAB24-6
  (AUC 0.762, Poor leans more); the threshold is that dataset's own Youden-J cut.
- **depth** — a fixed CLINICAL floor, NOT data-driven. This dataset's own labels run
  the opposite way (Poor reps are measurably *deeper*), so "too shallow" cannot be
  learned here; the threshold is the clinical parallel-squat norm adjusted for this
  pipeline's measured -12° under-read.
- **heel_rise** — data-driven, from a new measurement that passed a heel-visibility
  go/no-go census and the standard KEEP/DROP validity check (AUC 0.728, Poor higher).
  `heel_rise_peak_norm` is a rule-only signal — it is NOT in the frozen ML feature
  vector, so this gate needs no `feature_schema_version` bump and no retrain.

Depth and lean read the already-extracted `FeatureVector` (no schema change). Heel-rise
reads the rep's raw frames directly (landmarks 29–32), since heel/ankle position is not
part of the squat feature vector. Gates are computed on the same per-rep windows the
features use, so a gate's scale matches the thresholds derived in Phase A.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.module_b.core.features import FeatureVector
from app.module_b.core.geometry import distance, landmark_value, midpoint

# MediaPipe landmark indices used only by the heel-rise gate (rule-only; never enters
# the ML feature vector). Left/right heel and foot-index (toe).
_HEEL = {"left": 29, "right": 30}
_TOE = {"left": 31, "right": 32}
_MAX_HEEL_LANDMARK_INDEX = 32


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
    """Run every enabled gate against EVERY rep; collect all failures.

    Running across every rep (not just the first) is the concrete fix for the
    fault-detection blind spot: the ML only scores rep 0, but a set is "Needs
    Improvement" if *any* rep trips a gate. Iterated rep-then-gate in a fixed order so
    the resulting tag list is deterministic (X8).
    """
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
    """Peak bilateral heel lift from the rep's first frame, normalized by trunk length.

    Identical construction to the Phase A analysis script the threshold was derived
    from (X1 in spirit): bilateral (toe_y − heel_y) per frame, referenced to the first
    frame, peak over the rep, divided by mean trunk length. A positive value means the
    heel rose relative to the grounded toe.
    """
    if not frames:
        raise ValueError("Cannot evaluate heel rise on an empty rep")
    bilateral = [
        (_toe_heel_lift(frame, "left") + _toe_heel_lift(frame, "right")) / 2.0
        for frame in frames
    ]
    baseline = bilateral[0]
    peak_rise = max(value - baseline for value in bilateral)
    norm_ref = sum(_trunk_length(frame) for frame in frames) / len(frames)
    if norm_ref < 1e-9:
        raise ValueError("Cannot normalize heel rise with a zero trunk length")
    return peak_rise / norm_ref


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
