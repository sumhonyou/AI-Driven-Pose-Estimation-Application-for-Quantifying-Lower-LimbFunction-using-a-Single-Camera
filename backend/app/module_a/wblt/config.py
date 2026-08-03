"""Weight-Bearing Lunge Test (WBLT) config.

Dual output: official band = user-measured distance -> McBride et al. (2026)
Table 2 (distance_bands) and Table 1 means (seed_distance_cm, used to seed the
guided bracket). Secondary = camera-measured dorsiflexion angle (reported,
never invent-banded — see angle_symmetry_flag_deg / angle_mdc_deg docstrings).

Every threshold lives here, never inlined in analysis.py/geometry.py/router.py,
so a single edit to this file changes both live feedback (once the frontend
fetches GET /api/wblt/config) and the official backend analysis.
"""

# Calibration window at the start of each attempt, before the lunge — foot-flat
# baseline for the heel-lift detector. Mirrors sls/config.CALIBRATION_SECONDS
# in spirit but WBLT calibrates per-attempt, not once per session. Declared here
# (not inline in the dict below) because analysis.py references it directly as
# `config.CALIBRATION_SECONDS`; also mirrored into WBLT_CONFIG so GET /api/wblt/config
# exposes it — the frontend's live tracker uses it to decide the EXACT SAME
# calibration/hold frame boundary the backend uses (by frame timestamp, not a
# separately-drifting UI timer), so the two can't disagree about which frames
# were "baseline" vs "evaluated for a lift".
CALIBRATION_SECONDS = 2.0

WBLT_CONFIG = {
    "version": 1,
    # === OFFICIAL DISTANCE BANDS — McBride et al. (2026), Table 2 ===
    # Poor  = below ~15th pct  -> distance_cm < poor_max_cm
    # Fair  = ~15th-25th pct   -> poor_max_cm <= distance_cm < good_min_cm
    # Good  = >=25th pct       -> distance_cm >= good_min_cm
    # Keyed "ageband_sex"; ageband resolved server-side via age_to_band(exact_age) —
    # never accepted from the client. Values in cm.
    "distance_bands": {
        "18-29_male": {"poor_max_cm": 7.2, "good_min_cm": 8.0},
        "18-29_female": {"poor_max_cm": 9.0, "good_min_cm": 9.8},
        "30-39_male": {"poor_max_cm": 7.3, "good_min_cm": 8.8},
        "30-39_female": {"poor_max_cm": 7.6, "good_min_cm": 9.8},
        "40-49_male": {"poor_max_cm": 7.7, "good_min_cm": 8.0},
        "40-49_female": {"poor_max_cm": 7.8, "good_min_cm": 8.6},
        "50-59_male": {"poor_max_cm": 7.0, "good_min_cm": 7.5},
        "50-59_female": {"poor_max_cm": 7.0, "good_min_cm": 7.5},
        "60-69_male": {"poor_max_cm": 6.4, "good_min_cm": 7.0},
        "60-69_female": {"poor_max_cm": 5.8, "good_min_cm": 7.0},
        "70-79_male": {"poor_max_cm": 5.0, "good_min_cm": 5.8},
        "70-79_female": {"poor_max_cm": 4.0, "good_min_cm": 5.0},
        "80+_male": {"poor_max_cm": 4.8, "good_min_cm": 5.0},
        "80+_female": {"poor_max_cm": 4.7, "good_min_cm": 5.0},
    },
    # === Seed distances for bracketing — McBride Table 1 age/sex mean (cm) ===
    # Used to seed guided bracket targets.
    "seed_distance_cm": {
        "18-29_male": 11.0,
        "18-29_female": 11.3,
        "30-39_male": 11.2,
        "30-39_female": 11.4,
        "40-49_male": 11.0,
        "40-49_female": 10.4,
        "50-59_male": 10.4,
        "50-59_female": 9.5,
        "60-69_male": 9.5,
        "60-69_female": 8.0,
        "70-79_male": 7.4,
        "70-79_female": 6.5,
        "80+_male": 6.6,
        "80+_female": 5.7,
    },
    # === Bracketing interaction ===
    "attempts_per_leg": 3,
    "bracket_step_cm": 2.0,  # step out on valid touch, in on fail
    "bracket_min_distance_cm": 2.0,  # floor so step-in on a fail can't go negative/absurd
    # Used only when the account's exact age/sex can't resolve a McBride seed
    # (incomplete profile, §13 edge case) -- the bracket still needs SOME
    # starting target so the test isn't blocked outright; banding stays blocked
    # regardless, only the angle is unblocked in that case (see analysis.py).
    "fallback_seed_distance_cm": 10.0,
    "distance_mdc_cm": 1.5,  # distance MDC; suppress sub-MDC trend/borderline
    "leg_order": ["right", "left"],
    "calibration_seconds": CALIBRATION_SECONDS,
    # === Heel-lift detection (camera validity gate) — §5.2 ===
    # Calibration is TIME-windowed (all valid frames with t <= CALIBRATION_SECONDS),
    # finalising on whatever was collected as long as at least `heel_min_calibration_frames`
    # arrived — never depends on hitting an exact frame count at an assumed frame rate
    # (the old silent-fail bug). The frontend live tracker mirrors this exactly, frame
    # timestamp for frame timestamp (not a separately-drifting UI countdown), so the
    # two can't disagree about which frames were "baseline" vs "evaluated for a lift".
    "heel_min_calibration_frames": 5,
    "heel_lift_tol_ratio": 0.10,  # heel rise / shank length -> lifted (was 0.15 ≈ 6cm; 0.10 ≈ 4cm)
    "heel_lift_hysteresis_ratio": 0.06,  # drop below this to clear the lifted state
    # A lift must persist this many frames above tol before it's flagged, so a single
    # noisy world-landmark frame can't spuriously invalidate an honest attempt (or,
    # with the immediate-abort UX, cut a good hold short).
    "heel_lift_debounce_frames": 3,
    "min_valid_frames_per_attempt": 10,
    # === Secondary angle (reported, NOT officially banded) ===
    "angle_symmetry_flag_deg": 4.6,  # |theta_R - theta_L| >= this -> asymmetry flag
    "angle_mdc_deg": 4.6,  # suppress sub-MDC angle trend claims
    # If an angle BAND is ever added, source it from McKay (2017); do not invent.
    # === Capture-quality gate Q (0..1) — §8 ===
    # Q = min(lateral_alignment, leg_visibility, landmark_conf). leg_visibility
    # and landmark_conf reuse the generic valid_frame_ratio/average_visibility
    # already computed for every Module A exercise; lateral_alignment is WBLT's
    # own sub-check (2D ankle/dorsiflexion geometry is viewpoint-sensitive —
    # penalise a near-frontal camera, not just a poorly-tracked one).
    "q_min": 0.6,
    # hip_x_separation_norm() at/above this ratio scores lateral_alignment 0
    # (treated as fully frontal). Real anatomical hip width is roughly
    # 0.3-0.5x thigh/shank length, so this is a conservative "definitely not
    # side-on" cutoff, not the boundary of a merely-imperfect angle.
    "lateral_alignment_max_hip_x_norm": 0.45,
}

MIN_VISIBILITY = 0.5
