"""Sit-to-Stand (STS) thresholds — blueprint §5.1 / §6 / §12."""

# --- Knee-angle hysteresis FSM (degrees) ---
KNEE_STAND_ENTER = 160.0
KNEE_STAND_EXIT = 150.0
KNEE_SIT_ENTER = 110.0
KNEE_SIT_EXIT = 120.0

# --- Rep confirmation ---
MIN_REP_GAP_MS = 500  # refractory period between reps to avoid double counting

TARGET_REP_COUNT = 5  # STS: 5 reps

# --- Time bands (5 reps) ---
TIME_GOOD_MAX_SEC = 12.0
TIME_FAIR_MAX_SEC = 16.0
