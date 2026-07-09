// Lightweight client-side Sit-to-Stand rep-BOUNDARY detector for the LIVE UX only.
// It does not decide validity -- it just detects "an attempt just concluded" fast,
// with an optimistic best-guess reason for instant feedback. The authoritative
// valid-rep count comes back from the backend (POST /analyze), called once per
// boundary from LiveSession.tsx.
import { LM, type WorldLandmark } from "../../types/pose";
import {
  LIVE_KNEE_STAND_ENTER,
  LIVE_KNEE_STAND_EXIT,
  LIVE_KNEE_SIT_ENTER,
  LIVE_KNEE_RISING_ENTER,
  LIVE_MIN_REP_GAP_MS,
  LIVE_MIN_QUALITY_FOR_VALID_REP,
} from "../../config/moduleAThresholds";

export type RepEvent = "rep_boundary" | null;
export type StsPhase = "sitting" | "rising" | "standing";
export type InvalidReasonCode = "low_visibility" | "too_unstable" | "incomplete";

export interface StsLiveUpdate {
  attemptedRepCount: number;
  event: RepEvent;
  /** Optimistic, client-only guess at why the concluded attempt might not count.
   * Purely cosmetic — the backend's response is what actually decides validity. */
  reasonCode: InvalidReasonCode | null;
  /** Current smoothed-less knee angle in degrees (average of both legs), for live display only. */
  kneeAngleDeg: number;
  /** Lowest knee angle seen since the current standing phase began; null until the user has stood up once. */
  minKneeAngleDeg: number | null;
  phase: StsPhase;
}

function angleDeg(a: WorldLandmark, b: WorldLandmark, c: WorldLandmark): number {
  const v1 = { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z };
  const v2 = { x: c.x - b.x, y: c.y - b.y, z: c.z - b.z };
  const dot = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
  const cross = {
    x: v1.y * v2.z - v1.z * v2.y,
    y: v1.z * v2.x - v1.x * v2.z,
    z: v1.x * v2.y - v1.y * v2.x,
  };
  const crossMag = Math.sqrt(cross.x ** 2 + cross.y ** 2 + cross.z ** 2);
  return (Math.atan2(crossMag, dot) * 180) / Math.PI;
}

/**
 * Three-state machine: sitting → rising → standing → sitting.
 * Every concluded attempt (a full cycle, or giving up mid-rise) fires one
 * "rep_boundary" event and increments attemptedRepCount — never a validity
 * decision, just "something happened, go ask the backend."
 */
export function createStsLiveEstimator() {
  let posture: StsPhase = "sitting";
  let attemptedRepCount = 0;
  let lastBoundaryMs = -LIVE_MIN_REP_GAP_MS;
  let minKneeSinceStanding: number | null = null;

  // Per-attempt bookkeeping, reset at every boundary.
  let qualitySum = 0;
  let qualityCount = 0;
  let leftFullStand = false; // started descending from full stand without confirming a sit
  let wobbleCount = 0;

  function resetAttemptWindow() {
    qualitySum = 0;
    qualityCount = 0;
    leftFullStand = false;
    wobbleCount = 0;
  }

  return {
    update(worldLandmarks: WorldLandmark[], nowMs: number, frameQuality: number): StsLiveUpdate {
      if (!worldLandmarks || worldLandmarks.length < 33) {
        return {
          attemptedRepCount,
          event: null,
          reasonCode: null,
          kneeAngleDeg: 0,
          minKneeAngleDeg: minKneeSinceStanding,
          phase: posture,
        };
      }

      const kneeL = angleDeg(
        worldLandmarks[LM.LEFT_HIP],
        worldLandmarks[LM.LEFT_KNEE],
        worldLandmarks[LM.LEFT_ANKLE],
      );
      const kneeR = angleDeg(
        worldLandmarks[LM.RIGHT_HIP],
        worldLandmarks[LM.RIGHT_KNEE],
        worldLandmarks[LM.RIGHT_ANKLE],
      );
      const knee = (kneeL + kneeR) / 2;

      let event: RepEvent = null;
      let reasonCode: InvalidReasonCode | null = null;

      if (posture === "sitting") {
        if (knee >= LIVE_KNEE_RISING_ENTER) {
          posture = "rising";
          qualitySum = frameQuality;
          qualityCount = 1;
        }
      } else if (posture === "rising") {
        qualitySum += frameQuality;
        qualityCount++;
        if (knee >= LIVE_KNEE_STAND_ENTER) {
          posture = "standing";
          minKneeSinceStanding = knee;
          leftFullStand = false;
          wobbleCount = 0;
        } else if (knee <= LIVE_KNEE_SIT_ENTER) {
          // Gave up before reaching full stand.
          if (nowMs - lastBoundaryMs >= LIVE_MIN_REP_GAP_MS) {
            attemptedRepCount++;
            event = "rep_boundary";
            reasonCode = "incomplete";
            lastBoundaryMs = nowMs;
          }
          posture = "sitting";
          resetAttemptWindow();
        }
      } else if (posture === "standing") {
        qualitySum += frameQuality;
        qualityCount++;
        if (minKneeSinceStanding === null || knee < minKneeSinceStanding) {
          minKneeSinceStanding = knee;
        }
        if (knee < LIVE_KNEE_STAND_EXIT && !leftFullStand) {
          leftFullStand = true;
        }
        if (leftFullStand && knee >= LIVE_KNEE_STAND_ENTER) {
          // Bounced back up without confirming a sit — a wobble within this attempt.
          wobbleCount++;
          leftFullStand = false;
        }
        if (knee <= LIVE_KNEE_SIT_ENTER) {
          if (nowMs - lastBoundaryMs >= LIVE_MIN_REP_GAP_MS) {
            attemptedRepCount++;
            event = "rep_boundary";
            const avgQuality = qualityCount > 0 ? qualitySum / qualityCount : 0;
            if (avgQuality < LIVE_MIN_QUALITY_FOR_VALID_REP) {
              reasonCode = "low_visibility";
            } else if (wobbleCount > 0) {
              reasonCode = "too_unstable";
            } else {
              reasonCode = null; // looks valid client-side; backend response confirms
            }
            lastBoundaryMs = nowMs;
          }
          posture = "sitting";
          resetAttemptWindow();
        }
      }

      return {
        attemptedRepCount,
        event,
        reasonCode,
        kneeAngleDeg: knee,
        minKneeAngleDeg: minKneeSinceStanding,
        phase: posture,
      };
    },
    reset() {
      posture = "sitting";
      attemptedRepCount = 0;
      lastBoundaryMs = -LIVE_MIN_REP_GAP_MS;
      minKneeSinceStanding = null;
      resetAttemptWindow();
    },
  };
}
