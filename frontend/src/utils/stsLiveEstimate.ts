// Lightweight client-side Sit-to-Stand rep estimate for the LIVE counter UX only.
// The authoritative rep count comes back from the backend at session end (POST /analyze).
import { LM, type WorldLandmark } from "../types/pose";
import {
  LIVE_KNEE_STAND_ENTER,
  LIVE_KNEE_SIT_ENTER,
  LIVE_KNEE_RISING_ENTER,
  LIVE_MIN_REP_GAP_MS,
} from "../config/moduleAThresholds";

export type RepEvent = "good_rep" | "failed_rep" | null;
export type StsPhase = "sitting" | "rising" | "standing";

export interface StsLiveUpdate {
  count: number;
  event: RepEvent;
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
 *   good_rep  — completed the full stand-then-sit cycle
 *   failed_rep — started rising but sat back down before reaching full stand
 */
export function createStsLiveEstimator() {
  let posture: StsPhase = "sitting";
  let repCount = 0;
  let lastRepMs = -LIVE_MIN_REP_GAP_MS;
  let lastFailedMs = -LIVE_MIN_REP_GAP_MS;
  let minKneeSinceStanding: number | null = null;

  return {
    update(worldLandmarks: WorldLandmark[], nowMs: number): StsLiveUpdate {
      if (!worldLandmarks || worldLandmarks.length < 33) {
        return {
          count: repCount,
          event: null,
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

      if (posture === "sitting") {
        if (knee >= LIVE_KNEE_RISING_ENTER) {
          posture = "rising";
        }
      } else if (posture === "rising") {
        if (knee >= LIVE_KNEE_STAND_ENTER) {
          posture = "standing";
          minKneeSinceStanding = knee;
        } else if (knee <= LIVE_KNEE_SIT_ENTER) {
          // Started rising but sat back down — count as a failed attempt
          if (nowMs - lastFailedMs >= LIVE_MIN_REP_GAP_MS) {
            event = "failed_rep";
            lastFailedMs = nowMs;
          }
          posture = "sitting";
        }
      } else if (posture === "standing") {
        if (minKneeSinceStanding === null || knee < minKneeSinceStanding) {
          minKneeSinceStanding = knee;
        }
        if (knee <= LIVE_KNEE_SIT_ENTER) {
          if (nowMs - lastRepMs >= LIVE_MIN_REP_GAP_MS) {
            repCount++;
            event = "good_rep";
            lastRepMs = nowMs;
          }
          posture = "sitting";
        }
      }

      return {
        count: repCount,
        event,
        kneeAngleDeg: knee,
        minKneeAngleDeg: minKneeSinceStanding,
        phase: posture,
      };
    },
    reset() {
      posture = "sitting";
      repCount = 0;
      lastRepMs = -LIVE_MIN_REP_GAP_MS;
      lastFailedMs = -LIVE_MIN_REP_GAP_MS;
      minKneeSinceStanding = null;
    },
  };
}
