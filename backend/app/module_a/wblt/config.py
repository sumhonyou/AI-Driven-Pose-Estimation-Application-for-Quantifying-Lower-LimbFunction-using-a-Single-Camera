"""Weight-Bearing Lunge Test (WBLT) thresholds — dorsiflexion ROM measurement."""

TARGET_WBLT_TRIALS = 3  # Number of lunge trials in the test
# Ankle dorsiflexion angle thresholds (degrees from 0° / neutral ankle position)
ANKLE_DORSIFLEXION_GOOD_MIN_DEG = 15.0  # Good ROM: ≥15°
ANKLE_DORSIFLEXION_FAIR_MIN_DEG = 10.0  # Fair ROM: 10–15°
# Symmetry is measured as max(|left_angle - right_angle|) during the lunge
ANKLE_SYMMETRY_EXCELLENT_MAX_DEG = 5.0  # <5° difference is excellent
ANKLE_SYMMETRY_GOOD_MAX_DEG = 10.0  # 5–10° is good, >10° is poor
# Lunge entry/exit knee angle detection (knee bending into the lunge)
LUNGE_ENTRY_KNEE_ANGLE = 100.0  # Knee angle threshold to detect lunge position
LUNGE_ENTRY_MIN_FRAMES = 5  # Require stable knee angle for N frames to confirm lunge
