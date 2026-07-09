// REST client for the Single-Leg Stance (rebuild) endpoints. Mirrors the STS
// moduleAService pattern (apiRequest wrapper, bearer/session handled there).

import { apiRequest } from "../apiClient";
import type { PoseFrame } from "../../types/pose";
import type { SlsLeg } from "./liveGeometry";

export type UsedSupport = "none" | "slight" | "support";

/** One leg's official (backend-computed) per-leg metrics. */
export type SlsLegMetrics = {
  leg: SlsLeg;
  holdSeconds: number;
  cappedAtMax: boolean;
  stopReason: string;
  holdScore: number;
  stabilityScore: number;
  combinedScore: number;
  band: string;
  validFrameRatio: number;
  percentFramesInsideCircle: number;
  meanBallExcursionNorm: number;
  warningTags: string[];
};

export type SlsLegResult = {
  session_id: string;
  leg: SlsLeg;
  metrics: SlsLegMetrics;
  session_score: number;
  session_band: string;
  both_legs_done: boolean;
  capture_quality_band: string;
  valid_frame_ratio: number;
  persisted: boolean;
};

export type SlsSessionSummary = {
  session_id: string;
  combined_score: number;
  band: string;
  used_support: UsedSupport | null;
  max_hold_seconds: number;
  per_leg: Partial<Record<SlsLeg, SlsLegMetrics>>;
  left_right_hold_difference_seconds: number | null;
  session_status: string;
  warning_tags: string[];
};

export const slsApi = {
  /** Posts one leg's buffered hold; backend recomputes + persists, returns official result. */
  analyze(sessionId: string, leg: SlsLeg, frames: PoseFrame[]) {
    return apiRequest<SlsLegResult>("/api/sls/analyze", {
      method: "POST",
      body: {
        sessionId,
        leg,
        frames: frames.map((f) => ({
          timestampMs: f.timestampMs,
          worldLandmarks: f.worldLandmarks,
        })),
      },
    });
  },
  /** Records the post-session support self-report; never affects scoring. */
  support(sessionId: string, usedSupport: UsedSupport) {
    return apiRequest<SlsSessionSummary>("/api/sls/support", {
      method: "POST",
      body: { sessionId, usedSupport },
    });
  },
  /** Both-leg session summary for the report/dashboard. */
  session(sessionId: string) {
    return apiRequest<SlsSessionSummary>(`/api/sls/session/${sessionId}`);
  },
};
