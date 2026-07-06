// Lightweight client-side Single-Leg Stance balance-hold detector for live UX only.
// It does not decide validity — it just detects "balance lost" or duration updates fast,
// with an optimistic best-guess reason. The authoritative hold_duration comes from
// the backend (POST /analyze), called periodically during the hold.
import { LM, type WorldLandmark } from "../types/pose";
import {
  // SLS_TARGET_HOLD_SEC, // Unused in this module, backend uses config value
  SLS_ANKLE_HEIGHT_DIFF_M,
  LIVE_MIN_QUALITY_FOR_VALID_REP,
} from "../config/moduleAThresholds";

export type SlsEvent = "balance_lost" | "time_update" | null;
export type SlsPhase = "two_leg_stance" | "standing_on_one_leg" | "balance_lost_recovery";
export type InvalidReasonCode = "low_visibility" | "excessive_sway" | "none";

export interface SlsLiveUpdate {
  holdDurationSec: number;
  event: SlsEvent;
  reasonCode: InvalidReasonCode | null;
  currentPhase: SlsPhase;
  ankleHeightDiffM: number;
  estimatedHoldQualityScore: number; // 0-1, for live display
}

export function createSlsLiveEstimator() {
  let phase: SlsPhase = "two_leg_stance";
  let holdStartTimeMs: number | null = null;
  let lastUpdateMs = 0;

  // Per-hold metrics
  let qualitySum = 0;
  let qualityCount = 0;
  let maxAnkleHeightDiff = 0;
  let swayCount = 0;

  function resetHoldWindow() {
    qualitySum = 0;
    qualityCount = 0;
    maxAnkleHeightDiff = 0;
    swayCount = 0;
  }

  return {
    update(worldLandmarks: WorldLandmark[], nowMs: number, frameQuality: number): SlsLiveUpdate {
      if (!worldLandmarks || worldLandmarks.length < 33) {
        return {
          holdDurationSec: 0,
          event: null,
          reasonCode: null,
          currentPhase: phase,
          ankleHeightDiffM: 0,
          estimatedHoldQualityScore: 0,
        };
      }

      const ankleL = worldLandmarks[LM.LEFT_ANKLE];
      const ankleR = worldLandmarks[LM.RIGHT_ANKLE];
      const hipL = worldLandmarks[LM.LEFT_HIP];
      const hipR = worldLandmarks[LM.RIGHT_HIP];

      if (!ankleL || !ankleR || !hipL || !hipR) {
        return {
          holdDurationSec: 0,
          event: null,
          reasonCode: null,
          currentPhase: phase,
          ankleHeightDiffM: 0,
          estimatedHoldQualityScore: 0,
        };
      }

      const ankleHeightDiff = Math.abs(ankleL.y - ankleR.y);
      const isOneLegStance = ankleHeightDiff > SLS_ANKLE_HEIGHT_DIFF_M;

      let event: SlsEvent = null;
      let reasonCode: InvalidReasonCode | null = null;

      if (phase === "two_leg_stance") {
        if (isOneLegStance) {
          // Transitioned to one-leg stance
          phase = "standing_on_one_leg";
          holdStartTimeMs = nowMs;
          lastUpdateMs = nowMs;
          resetHoldWindow();
          qualitySum = frameQuality;
          qualityCount = 1;
        }
      } else if (phase === "standing_on_one_leg") {
        qualitySum += frameQuality;
        qualityCount++;
        maxAnkleHeightDiff = Math.max(maxAnkleHeightDiff, ankleHeightDiff);

        if (!isOneLegStance) {
          // Fell back to two legs (balance lost)
          event = "balance_lost";
          reasonCode =
            qualityCount > 0 && qualitySum / qualityCount < LIVE_MIN_QUALITY_FOR_VALID_REP
              ? "low_visibility"
              : swayCount > 2
                ? "excessive_sway"
                : null;
          phase = "balance_lost_recovery";
        } else if (nowMs - lastUpdateMs >= 500) {
          // Regular time update (every 500ms while holding)
          event = "time_update";
          reasonCode = null;
          lastUpdateMs = nowMs;
        }
      } else if (phase === "balance_lost_recovery") {
        if (isOneLegStance) {
          // Resumed one-leg stance after a brief loss (user found balance again)
          phase = "standing_on_one_leg";
          holdStartTimeMs = nowMs;
          lastUpdateMs = nowMs;
          resetHoldWindow();
        }
      }

      const holdDurationSec = holdStartTimeMs ? (nowMs - holdStartTimeMs) / 1000 : 0;
      const estimatedQuality = qualityCount > 0 ? qualitySum / qualityCount : 0;

      return {
        holdDurationSec: Math.max(0, holdDurationSec),
        event,
        reasonCode,
        currentPhase: phase,
        ankleHeightDiffM: ankleHeightDiff,
        estimatedHoldQualityScore: estimatedQuality,
      };
    },

    reset() {
      phase = "two_leg_stance";
      holdStartTimeMs = null;
      lastUpdateMs = 0;
      resetHoldWindow();
    },
  };
}
