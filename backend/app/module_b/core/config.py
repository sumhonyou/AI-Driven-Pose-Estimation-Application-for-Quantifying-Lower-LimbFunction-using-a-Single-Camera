"""Shared Module B defaults for scoring, quality, and feature extraction."""

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
    # Dataset-derived fusion weight. ROM rules are weak for squat, so ML dominates.
    "w_rule_default": 0.2,
    # Complements w_rule_default.
    "w_ml_default": 0.8,
    # [proposed heuristic, R7]
    "w_rule_low_confidence": 0.7,
    # Dataset-derived low-confidence cutoff, swept with the fusion weights.
    "confidence_low_threshold": 0.85,
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
