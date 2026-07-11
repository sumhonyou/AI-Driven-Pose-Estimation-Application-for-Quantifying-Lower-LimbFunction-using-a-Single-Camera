// REST client for the WBLT (Weight-Bearing Lunge Test) endpoints. Mirrors the
// SLS slsApi pattern (apiRequest wrapper, bearer/session handled there).

import { apiRequest } from "../apiClient";
import type { PoseFrame } from "../../types/pose";
import type { WbltLeg } from "./wbltGeometry";

export type { WbltLeg } from "./wbltGeometry";

export type WbltAttemptResult = {
  session_id: string;
  leg: WbltLeg;
  target_distance_cm: number;
  touched: boolean;
  heel_lift_detected: boolean;
  attempt_valid: boolean;
  valid_touch: boolean;
  theta_peak_deg: number | null;
  distance_cm: number | null;
  band: "Poor" | "Fair" | "Good" | null;
  score_0_10: number | null;
  borderline: boolean;
  q: number;
  capture_quality_band: string;
  valid_frame_ratio: number;
  session_status: "complete" | "incomplete" | "low_confidence";
  warning_tags: string[];
  persisted: boolean;
  // Bracket state after this attempt (§4.2).
  attempt_number: number;
  next_target_distance_cm: number | null;
  leg_complete: boolean;
  leg_best_distance_cm: number | null;
  leg_band: "Poor" | "Fair" | "Good" | null;
  leg_angle_deg: number | null;
  both_legs_done: boolean;
};

export type WbltBracketState = {
  leg: WbltLeg;
  attempt_number: number;
  next_target_distance_cm: number | null;
  leg_complete: boolean;
  seed_available: boolean;
};

export type WbltLegSummary = {
  attempts: unknown[];
  best_distance_cm: number | null;
  band: "Poor" | "Fair" | "Good" | null;
  score_0_10: number | null;
  borderline: boolean;
  leg_angle_deg: number | null;
  floor_flag: boolean;
  leg_complete: boolean;
};

export type WbltProfileSnapshot = {
  exact_age: number | null;
  age_band_resolved: string | null;
  sex: "male" | "female" | null;
};

export type WbltAgreementPair = { leg: WbltLeg; distance_cm: number; angle_deg: number };

// §11 Stage 6: vs the account's previous completed WBLT session, per leg.
// `_meaningful` flags are already MDC-suppressed server-side.
export type WbltLegTrend = {
  distance_delta_cm: number | null;
  distance_meaningful: boolean;
  angle_delta_deg: number | null;
  angle_meaningful: boolean;
  previous_band: "Poor" | "Fair" | "Good" | null;
};

export type WbltSessionSummary = {
  session_id: string;
  legs: Partial<Record<WbltLeg, WbltLegSummary>>;
  symmetry: { asym_deg: number | null; status: "symmetric" | "asymmetry_flag" | null };
  both_legs_done: boolean;
  session_status: "complete" | "incomplete" | "low_confidence";
  warning_tags: string[];
  // §9: the audit-trail snapshot -- what the band was actually computed from.
  profile: WbltProfileSnapshot | null;
  agreement_pairs: WbltAgreementPair[];
  captured_at: string | null;
  trend: Partial<Record<WbltLeg, WbltLegTrend | null>>;
};

export type WbltDistanceBand = { poor_max_cm: number; good_min_cm: number };

export type WbltConfig = {
  version: number;
  distance_bands: Record<string, WbltDistanceBand>;
  seed_distance_cm: Record<string, number>;
  attempts_per_leg: number;
  bracket_step_cm: number;
  bracket_min_distance_cm: number;
  fallback_seed_distance_cm: number;
  distance_mdc_cm: number;
  leg_order: WbltLeg[];
  heel_baseline_frames: number;
  heel_lift_tol_ratio: number;
  heel_lift_hysteresis_ratio: number;
  min_valid_frames_per_attempt: number;
  angle_symmetry_flag_deg: number;
  angle_mdc_deg: number;
  q_min: number;
};

export const wbltApi = {
  /** Posts one attempt's buffered frames; backend recomputes + persists, returns official result. */
  analyze(
    sessionId: string,
    leg: WbltLeg,
    targetDistanceCm: number,
    touched: boolean,
    frames: PoseFrame[],
  ) {
    return apiRequest<WbltAttemptResult>("/api/wblt/analyze", {
      method: "POST",
      body: {
        sessionId,
        leg,
        targetDistanceCm,
        touched,
        frames: frames.map((f) => ({
          timestampMs: f.timestampMs,
          worldLandmarks: f.worldLandmarks,
        })),
      },
    });
  },
  /** Next target distance + attempt number for this leg -- fetch before every attempt. */
  bracket(sessionId: string, leg: WbltLeg) {
    return apiRequest<WbltBracketState>(`/api/wblt/session/${sessionId}/bracket/${leg}`);
  },
  /** Config the official analysis uses -- fetch once so live feedback matches it. */
  config() {
    return apiRequest<WbltConfig>("/api/wblt/config");
  },
  /** Full both-legs session summary for the report/dashboard. */
  session(sessionId: string) {
    return apiRequest<WbltSessionSummary>(`/api/wblt/session/${sessionId}`);
  },
};
