"""Squat trend against the user's previous squat session.

No MDC (minimal detectable change) threshold exists for squat's fused score or rep
count -- mirrors app/module_a/sts/trend.py's rule: deltas are reported plainly with
no "meaningful change" claim.
"""


def _delta(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return round(current - previous, 2)


def compute_trend(current: dict, previous: dict | None) -> dict | None:
    """current/previous: {"score": float|None, "band": str|None, "rep_count": int|None}.

    None when there's no previous session, or neither delta could be computed
    (e.g. both sessions missing a rep count).
    """
    if previous is None:
        return None

    score_delta = _delta(current.get("score"), previous.get("score"))
    rep_delta = _delta(current.get("rep_count"), previous.get("rep_count"))

    if score_delta is None and rep_delta is None:
        return None

    return {
        "score_delta": score_delta,
        "rep_count_delta": rep_delta,
        "previous_band": previous.get("band"),
    }
