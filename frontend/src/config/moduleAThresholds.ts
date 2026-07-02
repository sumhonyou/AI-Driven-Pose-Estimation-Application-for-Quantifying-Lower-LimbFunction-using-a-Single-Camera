// Frontend-only constants for Module A. Backend thresholds live in backend/app/module_a/config.py —
// these are UX-only values (live counter estimate, buffer sampling), not the authoritative rules.

/** Frames-per-second sampled into the buffer sent to POST /api/module-a/analyze. */
export const SAMPLE_FPS = 15;

/** Live-estimate knee-angle thresholds (loose hysteresis) — the server recount is authoritative. */
export const LIVE_KNEE_STAND_ENTER = 160;
export const LIVE_KNEE_SIT_ENTER = 110;
/** Knee angle at which we consider someone to have started rising (used for failed-rep detection). */
export const LIVE_KNEE_RISING_ENTER = 130;
export const LIVE_MIN_REP_GAP_MS = 500;

export const STS_TARGET_REPS = 5;

/** Below this capture-quality score, live feedback should warn the user instead of showing progress. */
export const LIVE_MIN_VISIBILITY = 0.6;
