"""Frozen Module B defaults for the Phase 4 squat slice."""

MODULE_B_CORE_CONFIG = {
    # [proposed heuristic, fixed by D6 / proposal Table 6]
    "band_thresholds": {
        "poor": {
            "min_inclusive": 0.0,
            "max_exclusive": 4.0,
        },
        "fair": {
            "min_inclusive": 4.0,
            "max_exclusive": 7.0,
        },
        "good": {
            "min_inclusive": 7.0,
            "max_inclusive": 10.0,
        },
    },
    # [proposed heuristic, R7 - to be replaced by Phase 5.6's sweep result]
    "w_rule_default": 0.4,
    # [proposed heuristic, R7 - to be replaced by Phase 5.6's sweep result]
    "w_ml_default": 0.6,
    # [proposed heuristic, R7]
    "w_rule_low_confidence": 0.7,
    # [proposed heuristic, R7 - HY 2026-07-16; binary P(Good)/P(Poor) needs >0.5]
    "confidence_low_threshold": 0.65,
    # [proposed heuristic, proposal Section 3.3.1 Tables 3 and 4]
    "q_min": 0.6,
    # [proposed heuristic, proposal Section 3.3.1 Tables 3 and 4]
    "confidence_threshold": 0.6,
    # [proposed heuristic, proposal Section 3.3.1 Tables 3 and 4]
    "quality_bands": {
        "good": {
            "min_inclusive": 0.85,
        },
        "moderate": {
            "min_inclusive": 0.70,
            "max_exclusive": 0.85,
        },
        "poor": {
            "min_inclusive": 0.0,
            "max_exclusive": 0.70,
        },
    },
    # [proposed heuristic, proposal Section 3.3.2]
    "feature_schema_version": "1.0.0",
    # [proposed heuristic, proposal Section 3.3.2]
    "interpolation_max_gap_frames": 5,
}
