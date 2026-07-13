"""Official WBLT per-attempt analysis — pure function over a posted landmark sequence.

Called directly by POST /api/wblt/analyze and, unchanged, by any future replay
harness (no HTTP dependency here). Deterministic: same frames -> same metrics.
This is the single source of truth for the stored per-attempt result; the
frontend's live numbers are only a helper that should agree closely.

Stage 4 scope (blueprint §9) adds the persisted audit trail (profile snapshot,
agreement pairs) on top of Stage 3's capture-quality gate Q = min(
lateral_alignment, leg_visibility, landmark_conf), Stage 2's guided bracket
(§4.2), both legs, and symmetry (§4.4).
"""

from app.module_a.core.banding import score_to_band
from app.module_a.core.quality import session_quality
from app.module_a.core.smoothing import LandmarkSmoother
from app.module_a.wblt import config
from app.module_a.wblt import geometry as geo
from app.module_a.wblt.age_band import (age_to_band, resolve_ageband_sex,
                                        sex_from_gender)

_CFG = config.WBLT_CONFIG

# Landmarks WBLT needs visible on the tested leg, per frame.
_REQUIRED_LANDMARKS = {
    "left": (
        geo.KNEE["left"],
        geo.ANKLE["left"],
        geo.HEEL["left"],
        geo.FOOT_INDEX["left"],
    ),
    "right": (
        geo.KNEE["right"],
        geo.ANKLE["right"],
        geo.HEEL["right"],
        geo.FOOT_INDEX["right"],
    ),
}


def _frame_valid_for_wblt(world: list[dict], leg: str) -> bool:
    if not world or len(world) < 33:
        return False
    return all(
        world[i].get("visibility", 0.0) >= config.MIN_VISIBILITY
        for i in _REQUIRED_LANDMARKS[leg]
    )


def _average_visibility(world: list[dict], leg: str) -> float:
    if not world:
        return 0.0
    idxs = _REQUIRED_LANDMARKS[leg]
    return sum(world[i].get("visibility", 0.0) for i in idxs) / len(idxs)


def compute_score_0_10(
    distance_cm: float, poor_max_cm: float, good_min_cm: float
) -> float:
    """Anchors 4.0 at poor_max_cm and 7.0 at good_min_cm; display only (§4.3)."""
    span = good_min_cm - poor_max_cm
    if abs(span) < 1e-9:
        score = 7.0 if distance_cm >= good_min_cm else 4.0
    else:
        slope = 3.0 / span
        score = 4.0 + slope * (distance_cm - poor_max_cm)
    return max(0.0, min(10.0, round(score, 2)))


def compute_distance_band(distance_cm: float, ageband_sex: str) -> dict | None:
    """§4.3: Poor/Fair/Good from McBride Table 2, plus the display-only 0-10 score."""
    bands = _CFG["distance_bands"].get(ageband_sex)
    if bands is None:
        return None
    poor_max = bands["poor_max_cm"]
    good_min = bands["good_min_cm"]
    if distance_cm < poor_max:
        band = "Poor"
    elif distance_cm < good_min:
        band = "Fair"
    else:
        band = "Good"
    borderline = (
        abs(distance_cm - poor_max) < _CFG["distance_mdc_cm"]
        or abs(distance_cm - good_min) < _CFG["distance_mdc_cm"]
    )
    return {
        "band": band,
        "score_0_10": compute_score_0_10(distance_cm, poor_max, good_min),
        "borderline": borderline,
    }


def _empty_attempt(
    leg: str, target_distance_cm: float, touched: bool, reason: str
) -> dict:
    return {
        "leg": leg,
        "target_distance_cm": target_distance_cm,
        "touched": touched,
        "heel_lift_detected": False,
        "attempt_valid": False,
        "valid_touch": False,
        "theta_peak_deg": None,
        "distance_cm": None,
        "band": None,
        "score_0_10": None,
        "borderline": False,
        "q": 0.0,
        "q_limiting_factor": "leg_visibility",
        "quality": {
            "valid_frame_ratio": 0.0,
            "average_visibility": 0.0,
            "lateral_alignment": 0.0,
            "quality_band": "poor",
        },
        "session_status": "low_confidence",
        "warning_tags": [reason],
    }


def analyze_attempt(
    frames: list[dict],
    leg: str,
    target_distance_cm: float,
    touched: bool,
    exact_age: int | None,
    gender: str | None,
) -> dict:
    """Analyses one WBLT attempt. Returns a dict ready for the response/persistence layer.

    `exact_age`/`gender` come from the authenticated user's profile (resolved
    server-side by the router, never trusted from the client) so a tampered
    client value can never affect the band (blueprint §6 note).
    """
    if leg not in ("left", "right"):
        raise ValueError(f"leg must be 'left' or 'right', got {leg!r}")
    if not frames:
        return _empty_attempt(leg, target_distance_cm, touched, "landmarks_missing")

    smoother = LandmarkSmoother()
    heel_detector = geo.HeelLiftDetector(
        lift_tol_ratio=_CFG["heel_lift_tol_ratio"],
        hysteresis_ratio=_CFG["heel_lift_hysteresis_ratio"],
        leg=leg,
        min_calibration_frames=_CFG["heel_min_calibration_frames"],
        lift_debounce_frames=_CFG["heel_lift_debounce_frames"],
    )
    t0 = frames[0]["timestampMs"] / 1000.0

    frame_validity: list[bool] = []
    frame_avg_visibility: list[float] = []
    cal_hip_x_diffs: list[float] = []
    heel_valid_count = 0
    heel_lift_detected = False
    theta_peak: float | None = None

    for frame in frames:
        t = frame["timestampMs"] / 1000.0 - t0
        world = frame.get("worldLandmarks") or []
        valid = _frame_valid_for_wblt(world, leg)
        frame_validity.append(valid)
        frame_avg_visibility.append(_average_visibility(world, leg) if valid else 0.0)
        if not valid:
            continue

        smoothed = smoother.smooth_frame(t, world)

        if not heel_detector.calibrated:
            if t <= config.CALIBRATION_SECONDS:
                heel_detector.feed_calibration(smoothed)
                cal_hip_x_diffs.append(
                    abs(
                        smoothed[geo.HIP["left"]]["x"] - smoothed[geo.HIP["right"]]["x"]
                    )
                )
                continue
            # Calibration window has ended -- lock the baseline from whatever
            # foot-flat frames we collected. If too few arrived to trust it, we
            # can't evaluate this frame (attempt handled as a retry post-loop).
            if not heel_detector.finalize():
                continue

        heel_down = heel_detector.update(smoothed)
        if not heel_down:
            # This frame's heel is up -> exclude it from theta. Only flag the
            # attempt as heel-lifted once the debounced state has actually latched,
            # so a lone noisy frame doesn't invalidate an otherwise-clean attempt.
            if heel_detector.lifted:
                heel_lift_detected = True
            continue

        heel_valid_count += 1
        knee = smoothed[geo.KNEE[leg]]
        ankle = smoothed[geo.ANKLE[leg]]
        heel = smoothed[geo.HEEL[leg]]
        foot_index = smoothed[geo.FOOT_INDEX[leg]]
        theta = geo.dorsiflexion_angle_deg(knee, ankle, heel, foot_index)
        if theta is not None and (theta_peak is None or theta > theta_peak):
            theta_peak = theta

    # Safety net: a recording that never ran past the calibration window (very
    # short) leaves the baseline pending -- lock it now from what we have.
    heel_detector.finalize()
    if not heel_detector.calibrated:
        # Never got enough foot-flat frames to establish a baseline (e.g. the leg
        # wasn't clearly visible during the stand-still phase). Treat as a no-cost
        # retry at the same target rather than a real, bracket-stepping attempt.
        return _empty_attempt(leg, target_distance_cm, touched, "calibration_failed")

    quality = session_quality(frame_validity, frame_avg_visibility)

    # §8 lateral_alignment: median hip x-separation (calibration window) vs
    # shank length. No calibration/shank_len -> can't assess -> fails closed.
    if cal_hip_x_diffs and heel_detector.shank_len:
        median_hip_x = sorted(cal_hip_x_diffs)[len(cal_hip_x_diffs) // 2]
        hip_x_norm = median_hip_x / heel_detector.shank_len
        lateral_alignment = max(
            0.0, 1.0 - hip_x_norm / _CFG["lateral_alignment_max_hip_x_norm"]
        )
    else:
        lateral_alignment = 0.0

    sub_scores = {
        "lateral_alignment": lateral_alignment,
        "leg_visibility": quality["valid_frame_ratio"],
        "landmark_conf": quality["average_visibility"],
    }
    limiting_factor = min(sub_scores, key=lambda k: sub_scores[k])
    q = sub_scores[limiting_factor]
    quality["lateral_alignment"] = round(lateral_alignment, 3)

    attempt_valid = (
        heel_valid_count >= _CFG["min_valid_frames_per_attempt"]
        and theta_peak is not None
    )

    warning_tags: list[str] = []
    if quality["quality_band"] == "poor" or q < _CFG["q_min"]:
        warning_tags.append("poor_capture_quality")
        warning_tags.append(f"retry_{limiting_factor}")
    if heel_lift_detected:
        warning_tags.append("heel_lift_detected")

    # §4.5.3: camera overrides an over-optimistic self-report.
    valid_touch = touched and attempt_valid and not heel_lift_detected
    if touched and heel_lift_detected:
        warning_tags.append("heel_lifted_at_touch_override")

    result: dict = {
        "leg": leg,
        "target_distance_cm": target_distance_cm,
        "touched": touched,
        "heel_lift_detected": heel_lift_detected,
        "attempt_valid": attempt_valid,
        "valid_touch": valid_touch,
        "theta_peak_deg": round(theta_peak, 2) if theta_peak is not None else None,
        "distance_cm": None,
        "band": None,
        "score_0_10": None,
        "borderline": False,
        "q": round(q, 3),
        "q_limiting_factor": None,
        "quality": quality,
        "session_status": "low_confidence",
        "warning_tags": warning_tags,
    }

    if quality["quality_band"] == "poor" or q < _CFG["q_min"]:
        result["session_status"] = "low_confidence"
        result["q_limiting_factor"] = limiting_factor
        return result

    result["session_status"] = "complete" if valid_touch else "incomplete"

    if not valid_touch:
        if touched and heel_lift_detected:
            warning_tags.append("retry_shorter_distance")
        return result

    result["distance_cm"] = target_distance_cm

    ageband_sex = resolve_ageband_sex(exact_age, gender)
    if ageband_sex is None:
        warning_tags.append("profile_incomplete_no_band")
        return result

    band_result = compute_distance_band(target_distance_cm, ageband_sex)
    if band_result is None:
        warning_tags.append("profile_incomplete_no_band")
        return result

    result["band"] = band_result["band"]
    result["score_0_10"] = band_result["score_0_10"]
    result["borderline"] = band_result["borderline"]
    if band_result["borderline"]:
        warning_tags.append("borderline_distance")

    return result


def resolve_seed_cm(exact_age: int | None, gender: str | None) -> float | None:
    """McBride Table 1 mean for this account's ageband_sex, or None if unresolvable."""
    ageband_sex = resolve_ageband_sex(exact_age, gender)
    if ageband_sex is None:
        return None
    return _CFG["seed_distance_cm"].get(ageband_sex)


def bracket_state(attempts: list[dict], seed_cm: float | None) -> dict:
    """§4.2 guided bracket, as a pure function over the leg's attempts so far.

    `attempts` are prior stored attempt dicts for this leg, oldest first (each
    needs `target_distance_cm` and `valid_touch`). Returns the next target and
    whether the leg is done:

        d = seed_distance_cm[ageband_sex]           # attempt 1 target
        for each attempt:
            if valid_touch:  d += bracket_step_cm
            else:            d -= bracket_step_cm     (floor at a small minimum)

    Edge case: if every one of the base `attempts_per_leg` attempts was a
    valid touch, one optional extra attempt is offered (the true max may
    exceed what was tested) -- never more than one.
    """
    attempts_per_leg = _CFG["attempts_per_leg"]
    step = _CFG["bracket_step_cm"]
    floor = _CFG["bracket_min_distance_cm"]
    n = len(attempts)

    if n == 0:
        seed = seed_cm if seed_cm is not None else _CFG["fallback_seed_distance_cm"]
        return {
            "attempt_number": 1,
            "next_target_distance_cm": seed,
            "leg_complete": False,
        }

    last = attempts[-1]
    if n >= attempts_per_leg:
        all_valid_so_far = all(a["valid_touch"] for a in attempts[:attempts_per_leg])
        if n == attempts_per_leg and all_valid_so_far:
            next_target = round(last["target_distance_cm"] + step, 2)
            return {
                "attempt_number": n + 1,
                "next_target_distance_cm": next_target,
                "leg_complete": False,
            }
        return {
            "attempt_number": n,
            "next_target_distance_cm": None,
            "leg_complete": True,
        }

    if last["valid_touch"]:
        next_target = last["target_distance_cm"] + step
    else:
        next_target = max(floor, last["target_distance_cm"] - step)
    return {
        "attempt_number": n + 1,
        "next_target_distance_cm": round(next_target, 2),
        "leg_complete": False,
    }


def summarize_leg(attempts: list[dict]) -> dict:
    """§4.2/§4.4: leg distance score (largest valid-touch distance) + leg angle
    (max theta_peak over heel-down-valid attempts, regardless of touch outcome).

    `floor_flag` marks "every attempt failed" (§4.2 edge case) -- distance is
    below the smallest distance tested, not a real Poor-band measurement.
    """
    valid_touches = [a for a in attempts if a["valid_touch"]]
    best_attempt = (
        max(valid_touches, key=lambda a: a["target_distance_cm"])
        if valid_touches
        else None
    )
    thetas = [
        a["theta_peak_deg"] for a in attempts if a.get("theta_peak_deg") is not None
    ]
    leg_angle = max(thetas) if thetas else None
    bracket = bracket_state(attempts, seed_cm=None)

    return {
        "attempts": attempts,
        "best_distance_cm": (
            best_attempt["target_distance_cm"] if best_attempt else None
        ),
        "band": best_attempt["band"] if best_attempt else None,
        "score_0_10": best_attempt["score_0_10"] if best_attempt else None,
        "borderline": best_attempt["borderline"] if best_attempt else False,
        "leg_angle_deg": round(leg_angle, 2) if leg_angle is not None else None,
        "floor_flag": bool(attempts) and best_attempt is None,
        "leg_complete": bracket["leg_complete"],
        "attempt_number": bracket["attempt_number"],
        "next_target_distance_cm": bracket["next_target_distance_cm"],
    }


def compute_symmetry(leg_summaries: dict) -> dict:
    """§4.4: |angle_R - angle_L| symmetry proxy, only when both legs have an angle."""
    right = leg_summaries.get("right")
    left = leg_summaries.get("left")
    if not right or not left:
        return {"asym_deg": None, "status": None}
    right_angle = right.get("leg_angle_deg")
    left_angle = left.get("leg_angle_deg")
    if right_angle is None or left_angle is None:
        return {"asym_deg": None, "status": None}
    asym = abs(right_angle - left_angle)
    status = (
        "asymmetry_flag" if asym >= _CFG["angle_symmetry_flag_deg"] else "symmetric"
    )
    return {"asym_deg": round(asym, 2), "status": status}


def resolve_profile_snapshot(exact_age: int | None, gender: str | None) -> dict:
    """§9: stores the age/sex the band was ACTUALLY computed from, not just the
    band -- keeps a session auditable if the account's stored age or the band
    table (config_version) later changes. Re-deriving from a stale age at read
    time would silently rewrite history; the session must remember what it used.
    """
    return {
        "exact_age": exact_age,
        "age_band_resolved": age_to_band(exact_age) if exact_age is not None else None,
        "sex": sex_from_gender(gender),
    }


def compute_agreement_pairs(legs: dict) -> list[dict]:
    """§9: per-leg (distance, angle) pairs for the angle-vs-distance Bland-Altman
    export (Stage 7). Only legs with BOTH a resolved distance and angle qualify
    -- a floor-flagged or unbanded leg has nothing to pair."""
    pairs = []
    for leg in _CFG["leg_order"]:
        summary = legs.get(leg)
        if not summary:
            continue
        distance = summary.get("best_distance_cm")
        angle = summary.get("leg_angle_deg")
        if distance is not None and angle is not None:
            pairs.append({"leg": leg, "distance_cm": distance, "angle_deg": angle})
    return pairs


def compute_session_summary(legs: dict) -> dict:
    """Session-level score/band/status across whichever legs are complete so far.

    Mirrors sls/router.summarize()'s mean-of-completed-legs approach: legs with
    a resolved band drive the overall score; a leg with no valid touch
    (floor_flag) is excluded from the mean but still reported.
    """
    leg_order = _CFG["leg_order"]
    scoreable = {
        leg: summary
        for leg, summary in legs.items()
        if summary.get("score_0_10") is not None
    }
    if scoreable:
        overall_score = round(
            sum(s["score_0_10"] for s in scoreable.values()) / len(scoreable), 2
        )
        overall_band = score_to_band(overall_score)
    else:
        overall_score = None
        overall_band = None

    both_legs_done = all(legs.get(leg, {}).get("leg_complete") for leg in leg_order)

    if both_legs_done:
        session_status = "complete" if scoreable else "low_confidence"
    else:
        session_status = "incomplete"

    return {
        "overall_score": overall_score,
        "overall_band": overall_band,
        "both_legs_done": both_legs_done,
        "session_status": session_status,
    }


def compute_trend(current_legs: dict, previous_legs: dict | None) -> dict:
    """§11 Stage 6: per-leg distance/angle delta vs the account's previous
    completed WBLT session (fetched by the router). Sub-MDC changes are
    real-signal noise, not a real change -- Powden et al. (2015) puts distance
    MDC ~1.0-1.5cm, hence `_meaningful` suppression using the same
    `distance_mdc_cm`/`angle_mdc_deg` config values as elsewhere (§4.3/§4.4).

    A leg with no previous session, or missing a distance/angle in either
    session (e.g. floor_flag), gets `None` -- there's nothing honest to compare.
    """
    trend: dict = {}
    for leg in _CFG["leg_order"]:
        current = current_legs.get(leg)
        previous = (previous_legs or {}).get(leg)
        if not current or not previous:
            trend[leg] = None
            continue

        cur_d, prev_d = current.get("best_distance_cm"), previous.get(
            "best_distance_cm"
        )
        cur_a, prev_a = current.get("leg_angle_deg"), previous.get("leg_angle_deg")

        distance_delta = (
            round(cur_d - prev_d, 2)
            if cur_d is not None and prev_d is not None
            else None
        )
        angle_delta = (
            round(cur_a - prev_a, 2)
            if cur_a is not None and prev_a is not None
            else None
        )

        if distance_delta is None and angle_delta is None:
            trend[leg] = None
            continue

        trend[leg] = {
            "distance_delta_cm": distance_delta,
            "distance_meaningful": (
                distance_delta is not None
                and abs(distance_delta) >= _CFG["distance_mdc_cm"]
            ),
            "angle_delta_deg": angle_delta,
            "angle_meaningful": (
                angle_delta is not None and abs(angle_delta) >= _CFG["angle_mdc_deg"]
            ),
            "previous_band": previous.get("band"),
        }
    return trend


def aggregate_quality(legs: dict) -> dict:
    """Averages capture quality across every attempt in every leg so far, for
    the session-level `capture_quality`/`valid_frame_ratio`/`confidence_level`
    columns (per-attempt quality already lives in each attempt's own record)."""
    from app.module_a.core.quality import quality_band as _quality_band

    visibilities: list[float] = []
    ratios: list[float] = []
    for summary in legs.values():
        for attempt in summary.get("attempts", []):
            q = attempt.get("quality") or {}
            visibilities.append(q.get("average_visibility", 0.0))
            ratios.append(q.get("valid_frame_ratio", 0.0))

    avg_visibility = sum(visibilities) / len(visibilities) if visibilities else 0.0
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0.0
    return {
        "average_visibility": round(avg_visibility, 3),
        "valid_frame_ratio": round(avg_ratio, 3),
        "quality_band": _quality_band(avg_ratio),
    }
