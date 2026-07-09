"""SLS sub-scores, combined 0-10 score, and Table-6 banding.

All thresholds/weights come from config — prototype starting values, conservative,
tunable after pilot testing. Hold time is the PRIMARY measure; the stability
sub-score is a supporting indicator bounded by single-camera limitations.
"""

from app.module_a.sls import config


def hold_score(hold_seconds: float) -> float:
    """Piecewise hold sub-score (0-10), band-aligned to Table 6, capped at the max hold.

    <10s      -> Poor range 0-4
    10-25s    -> Fair range 4-7
    25-45s    -> Good range 7-10
    >=45s     -> 10
    """
    t = hold_seconds
    poor_max = config.SLS_HOLD_POOR_MAX_SEC  # 10
    fair_max = config.SLS_HOLD_FAIR_MAX_SEC  # 25
    cap = config.SLS_MAX_HOLD_SEC  # 45

    if t <= 0:
        return 0.0
    if t < poor_max:
        return 4.0 * (t / poor_max)
    if t < fair_max:
        return 4.0 + 3.0 * ((t - poor_max) / (fair_max - poor_max))
    if t < cap:
        return 7.0 + 3.0 * ((t - fair_max) / (cap - fair_max))
    return 10.0


def hold_time_band(hold_seconds: float) -> str:
    """Band from raw hold time alone (Table 6 breakpoints), independent of stability.

    Used by the evaluation harness: a human reviewer timing hold duration from
    video can reproduce this band, but can't independently judge the ball-in-circle
    stability sub-score the way the system does -- so band *agreement* is evaluated
    on this hold-time dimension, not the full stability-blended `combinedScore` band.
    """
    if hold_seconds <= 0:
        return "invalid"
    if hold_seconds < config.SLS_HOLD_POOR_MAX_SEC:
        return "poor"
    if hold_seconds < config.SLS_HOLD_FAIR_MAX_SEC:
        return "fair"
    return "good"


def stability_score(percent_frames_inside: float) -> float:
    """Time-in-circle stability sub-score (0-10): 10 x share of hold spent inside.

    Normalising by hold duration keeps this about *steadiness*, so it is not
    double-counted with hold time (which the hold sub-score already covers).
    """
    pct = max(0.0, min(1.0, percent_frames_inside))
    return 10.0 * pct


def score_to_band(score: float) -> str:
    """Table 6: Poor 0-4, Fair 4-7, Good 7-10."""
    if score < config.SCORE_POOR_MAX:
        return "poor"
    if score < config.SCORE_FAIR_MAX:
        return "fair"
    return "good"


def combined_score(hold_sub: float, stability_sub: float) -> float:
    """Weighted blend of the two sub-scores (default 50/50, config-driven)."""
    return (
        config.SLS_HOLD_WEIGHT * hold_sub + config.SLS_STABILITY_WEIGHT * stability_sub
    )


def score_leg(hold_seconds: float, percent_frames_inside: float) -> dict:
    """Full per-leg scoring bundle from a valid hold's hold time + inside-circle share."""
    hold_sub = round(hold_score(hold_seconds), 2)
    stability_sub = round(stability_score(percent_frames_inside), 2)
    combined = round(combined_score(hold_sub, stability_sub), 2)
    return {
        "holdScore": hold_sub,
        "stabilityScore": stability_sub,
        "combinedScore": combined,
        "band": score_to_band(combined),
    }
