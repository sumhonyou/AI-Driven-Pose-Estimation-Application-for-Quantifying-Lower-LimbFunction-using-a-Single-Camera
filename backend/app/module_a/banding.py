"""STS score/band computation (blueprint §6): start at 10, apply deductions.

Score is on a 0-10 scale (proposal Table 6: Poor 0-4, Fair 4-7, Good 7-10).
Poor capture quality overrides everything -> band is "invalid" (never a
misleading Good/Fair/Poor claim on unreliable data).
"""

from app.module_a import config


def score_to_band(score: float) -> str:
    if score < config.SCORE_POOR_MAX:
        return "poor"
    if score < config.SCORE_FAIR_MAX:
        return "fair"
    return "good"


def time_band(completion_time_sec: float | None) -> str | None:
    """Band from total time to complete 5 reps (only meaningful if all 5 reps done)."""
    if completion_time_sec is None:
        return None
    if completion_time_sec <= config.TIME_GOOD_MAX_SEC:
        return "good"
    if completion_time_sec <= config.TIME_FAIR_MAX_SEC:
        return "fair"
    return "poor"


def compute_band(metrics: dict, quality: dict) -> dict:
    """Returns {score, band, warning_tags} from session metrics + capture quality."""
    warning_tags: list[str] = []
    quality_band = quality["quality_band"]

    if quality_band == "poor":
        warning_tags.append("poor_capture_quality")
        return {"score": 0.0, "band": "invalid", "warning_tags": warning_tags}

    score = 10.0
    rep_count = metrics["rep_count"]
    target = metrics["target_rep_count"]

    if rep_count < target:
        warning_tags.append("incomplete_reps")
        score = min(score, 3.0)

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
    if avg_trunk_lean is not None and avg_trunk_lean > config.TRUNK_LEAN_EXCESSIVE_DEG:
        warning_tags.append("excessive_trunk_lean")
        score -= 1.0

    score = max(0.0, round(score, 2))
    band = score_to_band(score)

    return {
        "score": score,
        "band": band,
        "warning_tags": warning_tags,
        "time_band": t_band,
    }
