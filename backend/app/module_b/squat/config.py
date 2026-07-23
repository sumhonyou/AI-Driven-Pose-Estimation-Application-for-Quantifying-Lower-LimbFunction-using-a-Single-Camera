"""Squat identity config; movement thresholds arrive in later Phase 4 stages."""

SQUAT_CONFIG = {
    # [dataset-derived] Stable REHAB24-6 exercise identifier selected in Stage 4.0.
    "exercise_code": "squat",
    # [dataset-derived] REHAB24-6/runtime-compatible sagittal capture orientation.
    "required_view": "side_view",
    # [proposed heuristic] Phase 4 stub key; replaced by a versioned artifact in Phase 5.
    "model_key": "squat",
    # [dataset-derived, Stage 5.11] Committed binary Good/Poor policy (HY, 2026-07-19):
    # squat no longer abstains into Fair. The band is a single cut on the fused 0-10
    # score, chosen for max macro-F1 on the out-of-fold predictions (the aggressive,
    # safety-first operating point: recall(Poor)=1.0, so no poor rep is ever called
    # Good, at the cost of ~31% of Good reps flagged for improvement). w_rule=0 because
    # the ROM rule is inverted for this population (Stage 5.4-5.6), so any rule weight
    # pulls a deep/Poor rep's score toward Good. See tune_squat_binary_band.py and
    # ml/reports/SQUAT_EVALUATION_REPORT_2BAND.md. "Poor" is displayed as "Needs
    # Improvement" in the UI (i18n only; the stored band value stays "Poor").
    # Stage 5.13: the threshold above is applied to EVERY rep, then the set's band is a
    # strict majority of the per-rep verdicts (a rep is Good only if the model passes it
    # and no fault gate fired on it). Voting keeps the cut where it was calibrated -- a
    # mean over reps has a much narrower spread, so the same cut would mean something
    # different -- and it survives the accepted ~31% per-rep false-alarm rate, which over
    # 10 reps would otherwise make a spurious flag near-certain. See core/set_scoring.py.
    "band_policy": {
        "scheme": "binary",
        "decision_threshold": 8.447974,
        "w_rule": 0.0,
        "w_ml": 1.0,
        "aggregation": "majority_vote",
    },
    # [dataset-derived, R5.3] Stage 5.4 bake-off winner, replacing the thigh_length
    # placeholder: trunk_length left less cross-subject spread in both normalised
    # features (mean CV 0.180 vs 0.201 over 98 side-view reps / 9 subjects), winning
    # on scale-invariant CV and raw variance alike. See ml/reports/NORM_REF_BAKEOFF.md.
    "norm_ref_strategy": "trunk_length",
    "segmentation": {
        # [proposed heuristic, R9] Flexion from standing that starts a descent.
        "enter_descending_deg": 30.0,
        # [proposed heuristic, R9] Lower exit creates hysteresis against jitter.
        "exit_standing_deg": 20.0,
        # [proposed heuristic, R9] Blocks a rebound from becoming a second rep.
        "refractory_s": 0.5,
        # [proposed heuristic, R9] Rejects very brief threshold-noise candidates.
        "min_rep_duration_s": 0.5,
        # Counts a final rep whose capture stopped inside the 20-30 deg hysteresis
        # deadband: without this the set loses a rep the user actually completed.
        "flush_trailing_rep": True,
    },
    "rules": {
        "rom": {
            # [clinical norm, S1] Lower edge of the shallow-ROM band.
            "shallow_start_deg": 60.0,
            # [clinical norm, S1] Lower edge of the parallel-ROM band.
            "parallel_start_deg": 90.0,
            # [clinical norm, S1] Lower edge of the deep-ROM band.
            "deep_start_deg": 110.0,
            # [proposed heuristic, pilot-tune] Reaches the top of deep-band interpolation.
            "deep_full_score_deg": 130.0,
            # [proposed heuristic, R3] Low shank-forward proxy may indicate limited DF.
            "df_limit_proxy_max_deg": 20.0,
            # [proposed heuristic, R3] Avoids treating a possible mobility cap as zero control.
            "df_limit_score_floor": 2.0,
        },
        "tempo": {
            # [proposed heuristic, R6] Consistent duration CV earns 9–10.
            "high_consistency_cv_max": 0.10,
            # [proposed heuristic, R6] Moderate duration CV earns 5–8.
            "moderate_consistency_cv_max": 0.25,
            # [proposed heuristic, R6] CV at or above this reaches zero.
            "poor_consistency_cv_zero_score": 0.50,
        },
        "stability": {
            # [proposed heuristic, R6] In-plane jitter at this value receives zero jitter credit.
            "jitter_zero_score_norm": 0.10,
            # [proposed heuristic, R6] Prevents a very brief still sample earning full control credit.
            "full_duration_credit_s": 1.0,
        },
    },
    # Stage 5.12: interpretable fault gates (depth / lean / heel-rise). A separate
    # override layer, NOT part of fusion or of RuleScores' equal-weight mean — if any
    # enabled gate fails on any rep, router.py forces the band to Poor with a specific
    # reason. Each threshold's provenance differs by design; see
    # ml/reports/SQUAT_FAULT_GATE_ANALYSIS.md (Phase A) for the full derivation.
    "fault_gates": {
        "depth": {
            "enabled": True,
            # [clinical norm, Stage 5.12] NOT data-driven: REHAB24-6's own labels run
            # the opposite direction (Poor reps are deeper), so a "too shallow" cut
            # cannot be learned here. This is the clinical parallel-squat norm
            # (rules.rom.parallel_start_deg = 90°) adjusted for the pipeline's measured
            # -11.96° peak-flexion under-read vs OptiTrack (MOCAP_AGREEMENT.md): a true
            # 90° squat reads ~78° on this pipeline's scale. Fires when knee_flex_peak
            # stays below this for the whole rep.
            "min_knee_flex_peak_deg": 78.04,
            "tag": "insufficient_depth",
            # Stage 5.20: quotes the threshold above so the advice is actionable against
            # the same angle the live gauge shows. ⚠ The number must stay in step with
            # `min_knee_flex_peak_deg` -- `test_module_b_fault_gates.py` asserts it does.
            # ⚠ Known cosmetic mismatch: `rules.rom` labels 60-90° "Shallow" and 90°+
            # "Parallel", because those bands are raw clinical norms that were never
            # corrected for the -11.96° under-read this gate WAS corrected for. So 78°
            # still sits inside the gauge's amber band. Deliberately not fixed here --
            # re-basing the ROM bands would change `rom_subscore` and the rule score, which
            # needs its own validation stage (HY's call, 2026-07-20).
            "message": "Didn't reach enough depth — aim for a knee bend of at least 78° (thighs close to parallel).",
        },
        "lean": {
            "enabled": True,
            # [dataset-derived, Stage 5.12] Youden's-J-optimal cut on the REHAB24-6
            # Good/Poor separation of trunk_lean_peak_deg (a real KEEP feature, AUC
            # 0.762, Poor leans more — FEATURE_VALIDITY.md). Fires when peak trunk lean
            # reaches this value.
            "fault_trunk_lean_peak_deg": 41.42411876009375,
            "tag": "excessive_forward_lean",
            "message": "Leaning too far forward — keep your chest more upright.",
        },
        "heel_rise": {
            "enabled": True,
            # [dataset-derived, Stage 5.12; re-derived Stage R1 2026-07-24] Rule-only
            # signal outside the frozen ML feature vector (no schema bump/retrain).
            # Passed the heel-visibility go/no-go census and the standard KEEP/DROP
            # validity check (AUC 0.714, Poor higher). Youden's-J cut on
            # heel_rise_peak_norm = peak NEAR-LEG (camera-side, chosen by visibility)
            # (toe_y − heel_y) rise from a settle-window baseline, debounced over a
            # sustained-frame window, normalized by trunk length. Re-derived under
            # this construction (was 0.08399336939375095 under the old bilateral,
            # single-frame-baseline construction) after UAT found it false-positiving
            # on good-form squats (docs/PhysioFit_UserTesting_Analysis.md T8); the new
            # construction trades a small AUC drop (0.728->0.714) for materially
            # better specificity (0.569->0.625 in-sample, 0.583->0.597 out-of-fold) --
            # i.e. fewer false alarms on Good reps, the actual defect being fixed. See
            # ml/reports/SQUAT_FAULT_GATE_ANALYSIS.md. Fires when the peak heel lift
            # reaches this value.
            "fault_heel_rise_peak_norm": 0.07098522548163665,
            "tag": "heel_lift",
            "message": "Heels lifting off the floor — keep your weight through your heels.",
        },
    },
}
