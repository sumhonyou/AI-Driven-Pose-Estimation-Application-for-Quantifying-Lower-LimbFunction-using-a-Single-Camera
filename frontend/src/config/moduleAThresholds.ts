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

/** Below this capture-quality score, live feedback should warn the user instead of showing progress. */
export const LIVE_MIN_VISIBILITY = 0.6;
/** Below this average per-rep capture quality, the live estimator's optimistic
 * guess for why a rep didn't count is "low visibility" — stricter than
 * LIVE_MIN_VISIBILITY since it judges a whole completed attempt, not one frame. */
export const LIVE_MIN_QUALITY_FOR_VALID_REP = 0.7;
