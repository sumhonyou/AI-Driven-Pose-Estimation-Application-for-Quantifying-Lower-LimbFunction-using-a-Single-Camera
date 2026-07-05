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


def compute_session_status(rep_count: int, target: int, quality_band: str) -> str:
    """Completeness/confidence status, kept independent of movement-quality band.

    A tracking problem (poor capture) or an early/incomplete stop must never be
    presented as if the movement itself was graded Poor -- that's a separate axis
    from `band`, which only ever describes movement quality.
    """
    if quality_band == "poor":
        return "low_confidence"
    if rep_count < target:
        return "incomplete"
    return "complete"


def compute_band(metrics: dict, quality: dict) -> dict:
    """Returns {score, band, warning_tags, session_status, is_partial_score} from
    session metrics + capture quality.

    `band`/`score` are computed only from the valid reps actually captured --
    never suppressed or force-capped because the set was incomplete or capture
    quality was poor. `session_status` carries that information instead.
    """
    warning_tags: list[str] = []
    quality_band = quality["quality_band"]
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
        "session_status": session_status,
        "is_partial_score": rep_count < target,
    }
