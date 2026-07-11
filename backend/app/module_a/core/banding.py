"""Shared score/band primitives (blueprint §6) plus the exercise-type dispatcher.

Score is on a 0-10 scale (proposal Table 6: Poor 0-4, Fair 4-7, Good 7-10).
Poor capture quality overrides everything -> band is "invalid" (never a
misleading Good/Fair/Poor claim on unreliable data).
"""

from app.module_a.core import config


def score_to_band(score: float) -> str:
    if score < config.SCORE_POOR_MAX:
        return "poor"
    if score < config.SCORE_FAIR_MAX:
        return "fair"
    return "good"


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


def compute_band(
    metrics: dict, quality: dict, exercise_type: str = "sit_to_stand"
) -> dict:
    """Returns {score, band, warning_tags, session_status, is_partial_score}.

    STS is the only exercise left on this shared dispatcher -- SLS and WBLT
    each have their own dedicated banding, called from their own routers.
    Band/score computed from valid data only; session_status (complete/incomplete/
    low_confidence) tracks completeness/confidence separately from quality band.

    Imports the per-exercise banding module locally (not at module import time)
    since it imports `score_to_band`/`compute_session_status` back from this one
    -- a top-level import here would be circular.
    """
    warning_tags: list[str] = []
    quality_band = quality["quality_band"]

    if exercise_type == "sit_to_stand":
        from app.module_a.sts.banding import compute_sts_band

        return compute_sts_band(metrics, quality_band, warning_tags)
    else:
        raise ValueError(f"Unknown exercise_type: {exercise_type}")
