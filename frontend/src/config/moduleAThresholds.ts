// Frontend-only constants for Module A. Backend thresholds live in backend/app/module_a/config.py —
// these are UX-only values (live counter estimate, buffer sampling), not the authoritative rules.

/** Frames-per-second sampled into the buffer sent to POST /api/module-a/analyze. */
export const SAMPLE_FPS = 15;

/** Live-estimate knee-angle thresholds (hysteresis) — the server recount is authoritative. */
export const LIVE_KNEE_STAND_ENTER = 160;
export const LIVE_KNEE_SIT_ENTER = 110;
/** Exit bands (mirrors backend KNEE_STAND_EXIT/KNEE_SIT_EXIT) — lets the live FSM
 * recognise a mid-stand wobble as continuing the same attempt instead of misreading
 * it as two separate rep-boundary events. */
export const LIVE_KNEE_STAND_EXIT = 150;
export const LIVE_KNEE_SIT_EXIT = 120;
/** Knee angle at which we consider someone to have started rising (used for failed-rep detection). */
export const LIVE_KNEE_RISING_ENTER = 130;
export const LIVE_MIN_REP_GAP_MS = 500;

export const STS_TARGET_REPS = 5;
/** Mirrors backend MAX_SESSION_SECONDS — auto-finalizes a session that never reaches
 * STS_TARGET_REPS valid reps instead of running forever. */
export const MAX_SESSION_SECONDS = 60;

/** Single-Leg Stance (legacy single-leg engine): target hold duration in seconds. */
export const SLS_TARGET_HOLD_SEC = 30;
/** One-leg stance detection: vertical distance (meters) between ankles above which
 * we consider the user to be standing on one leg. (legacy) */
export const SLS_ANKLE_HEIGHT_DIFF_M = 0.15;

// --- SLS REBUILD geometry — KEEP IN SYNC with backend app/module_a/config.py ---
// These drive live feedback (lift-line, ball-in-circle) so the on-screen numbers
// match the backend's official recompute. Prototype values, tunable after pilot.
export const SLS_MAX_HOLD_SEC = 45; // per-leg hold cap (seconds)
export const SLS_CALIBRATION_SEC = 2.0; // both-feet-planted baseline window
export const SLS_LIFT_LINE_NORM = 0.15; // lift-line height / stance-leg length
export const SLS_LIFT_HYSTERESIS_NORM = 0.03; // drop margin below the line
export const SLS_LIFT_PERSIST_FRAMES = 3; // frames above line to confirm a lift
export const SLS_DROP_PERSIST_FRAMES = 3; // frames below line to confirm a drop
export const SLS_CIRCLE_RADIUS_NORM = 0.6; // tolerance-circle radius / hip width
export const SLS_LEG_ORDER = ["right", "left"] as const; // prompted lift order

/** Below this capture-quality score, live feedback should warn the user instead of showing progress. */
export const LIVE_MIN_VISIBILITY = 0.6;
/** Below this average per-rep capture quality, the live estimator's optimistic
 * guess for why a rep didn't count is "low visibility" — stricter than
 * LIVE_MIN_VISIBILITY since it judges a whole completed attempt, not one frame. */
export const LIVE_MIN_QUALITY_FOR_VALID_REP = 0.7;
