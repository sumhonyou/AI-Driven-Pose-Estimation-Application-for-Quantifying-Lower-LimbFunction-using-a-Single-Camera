"""STS score/band computation (blueprint §6): start at 10, apply deductions."""

from app.module_a.core.banding import compute_session_status, score_to_band
from app.module_a.core.config import TRUNK_LEAN_EXCESSIVE_DEG
from app.module_a.sts import config


def time_band(completion_time_sec: float | None) -> str | None:
    """Band from total time to complete 5 reps (only meaningful if all 5 reps done)."""
    if completion_time_sec is None:
        return None
    if completion_time_sec <= config.TIME_GOOD_MAX_SEC:
        return "good"
    if completion_time_sec <= config.TIME_FAIR_MAX_SEC:
        return "fair"
    return "poor"


def compute_sts_band(metrics: dict, quality_band: str, warning_tags: list[str]) -> dict:
    """STS-specific banding: based on rep count, timing, and stability."""
    rep_count = metrics["rep_count"]
    target = metrics["target_rep_count"]

    session_status = compute_session_status(rep_count, target, quality_band)
    if quality_band == "poor":
        warning_tags.append("poor_capture_quality")
    if rep_count < target:
        warning_tags.append("incomplete_reps")

    if rep_count == 0:
        return {
            "score": 0.0,
            "band": "invalid",
            "warning_tags": warning_tags,
            "time_band": None,
            "session_status": session_status,
            "is_partial_score": False,
        }

    score = 10.0

    if quality_band == "moderate":
        warning_tags.append("moderate_capture_quality")
        score -= 1.0

    completion_time = metrics["completion_time_sec"]
    t_band = time_band(completion_time) if rep_count >= target else None
    if t_band == "poor":
        warning_tags.append("very_slow_completion")
        score -= 2.0

    if metrics.get("wobble_count", 0) > 0:
        warning_tags.append("unstable_reps")
        score -= 1.0

    avg_trunk_lean = metrics.get("avg_trunk_lean_deg")
    if avg_trunk_lean is not None and avg_trunk_lean > TRUNK_LEAN_EXCESSIVE_DEG:
        warning_tags.append("excessive_trunk_lean")
        score -= 1.0

    score = max(0.0, round(score, 2))
    band = score_to_band(score)

    return {
        "score": score,
        "band": band,
        "warning_tags": warning_tags,
        "time_band": t_band,
        "session_status": session_status,
        "is_partial_score": rep_count < target,
    }
