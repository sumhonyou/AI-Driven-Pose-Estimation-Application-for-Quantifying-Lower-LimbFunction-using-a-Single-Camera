"""SLS per-leg trend against the user's previous completed SLS session.

Mirrors WBLT's app/module_a/wblt/analysis.compute_trend shape (per-leg dict,
None for a leg with no comparable data) but reads SLS's camelCase per-leg keys
(holdSeconds/combinedScore, not WBLT's best_distance_cm/leg_angle_deg) and drops
the _meaningful/MDC flags entirely -- no published measurement-error study exists
for SLS hold-time/score deltas, so no "meaningful change" claim is made (same
caveat as sts/trend.py).
"""

_LEGS = ("left", "right")


def _delta(current: float | None, previous: float | None) -> float | None:
    if current is None or previous is None:
        return None
    return round(current - previous, 2)


def compute_trend(current_legs: dict, previous_legs: dict | None) -> dict:
    """current_legs/previous_legs: the `perLeg` dict from SLS's stored summary
    (`{"left": {holdSeconds, combinedScore, band, ...}, "right": {...}}`).

    Returns `dict[leg] -> {hold_delta_sec, score_delta, previous_band} | None`,
    one entry per leg. A leg is None when either session is missing that leg
    entirely, or neither delta could be computed.
    """
    trend: dict = {}
    for leg in _LEGS:
        current = current_legs.get(leg)
        previous = (previous_legs or {}).get(leg)
        if not current or not previous:
            trend[leg] = None
            continue

        hold_delta = _delta(current.get("holdSeconds"), previous.get("holdSeconds"))
        score_delta = _delta(
            current.get("combinedScore"), previous.get("combinedScore")
        )

        if hold_delta is None and score_delta is None:
            trend[leg] = None
            continue

        trend[leg] = {
            "hold_delta_sec": hold_delta,
            "score_delta": score_delta,
            "previous_band": previous.get("band"),
        }
    return trend
