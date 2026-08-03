"""STS trend against the user's previous completed STS session.

No MDC (minimal detectable change) threshold exists for STS -- unlike WBLT, there
is no published measurement-error study behind a score/completion-time delta here.
Deltas are reported plainly with no "meaningful change" claim.
"""


def _delta(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return round(current - previous, 2)


def compute_trend(current: dict, previous: dict | None) -> dict | None:
    """current/previous: {"score": float|None, "band": str|None, "completion_time_sec": float|None}.

    None when there's no previous session, or neither delta could be computed
    (e.g. both sessions missing a completion time).
    """
    if previous is None:
        return None

    score_delta = _delta(current.get("score"), previous.get("score"))
    time_delta = _delta(
        current.get("completion_time_sec"), previous.get("completion_time_sec")
    )

    if score_delta is None and time_delta is None:
        return None

    return {
        "score_delta": score_delta,
        "completion_time_delta_sec": time_delta,
        "previous_band": previous.get("band"),
    }
