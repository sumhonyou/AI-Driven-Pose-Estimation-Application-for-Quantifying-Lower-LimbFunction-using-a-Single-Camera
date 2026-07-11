import { apiRequest } from "./apiClient";
import type { PoseFrame } from "../types/pose";
import type { SlsLeg, SlsLegMetrics } from "./sls/slsApi";

export type ModuleAMetrics = {
  rep_count: number;
  target_rep_count: number;
  completion_time_sec: number | null;
  rep_durations_sec: number[];
  avg_rep_time_sec: number | null;
  fastest_rep_time_sec: number | null;
  slowest_rep_time_sec: number | null;
  knee_rom_deg: number | null;
  avg_trunk_lean_deg: number | null;
  max_trunk_lean_deg: number | null;
  wobble_count: number;
  session_duration_sec: number;
  stopped_early: boolean;
  tracked_leg: string | null;
  /** UX-only figure from the frontend's live rep-boundary FSM, echoed back for
   * the report's "Attempted reps" — the backend engine has no other way to know it. */
  client_attempted_reps: number | null;
  // SLS legacy (single-leg) metrics — pre-rebuild rows only.
  hold_duration_sec?: number;
  target_hold_sec?: number;
  max_sway_m?: number;
  // SLS rebuild (both-legs) metrics — presence of `perLeg` is the migration signal
  // Report/Dashboard/SessionHistory use to pick this render over the legacy one.
  perLeg?: Partial<Record<SlsLeg, SlsLegMetrics>>;
  combinedScore?: number;
  maxHoldSeconds?: number;
  usedSupport?: "none" | "slight" | "support" | null;
  leftRightHoldDifferenceSeconds?: number | null;
  best_hold_sec?: number;
  both_legs_done?: boolean;
  // WBLT (guided bracket) metrics — presence of `legs` is the shape signal
  // Report/Dashboard/SessionHistory use to pick this render.
  legs?: Partial<
    Record<
      "left" | "right",
      {
        attempts: unknown[];
        best_distance_cm: number | null;
        band: "Poor" | "Fair" | "Good" | null;
        score_0_10: number | null;
        borderline: boolean;
        leg_angle_deg: number | null;
        floor_flag: boolean;
        leg_complete: boolean;
      }
    >
  >;
  symmetry?: { asym_deg: number | null; status: "symmetric" | "asymmetry_flag" | null };
};

export type SessionStatus = "complete" | "incomplete" | "low_confidence";

export type ModuleAResult = {
  session_id: string;
  band: "good" | "fair" | "poor" | "invalid" | string;
  score: number;
  metrics: ModuleAMetrics;
  warning_tags: string[];
  capture_quality_band: string;
  valid_frame_ratio: number;
  /** Completeness/confidence, decoupled from `band` (movement quality only). */
  session_status: SessionStatus;
  is_partial_score: boolean;
  /** True only when this specific call actually wrote the result to the database. */
  persisted: boolean;
};

export const moduleAService = {
  analyze(
    sessionId: string,
    exerciseType: string,
    frames: PoseFrame[],
    options?: { clientAttemptedReps?: number; forceFinalize?: boolean },
  ) {
    return apiRequest<ModuleAResult>("/api/module-a/analyze", {
      method: "POST",
      body: {
        sessionId,
        exerciseType,
        frames: frames.map((f) => ({
          timestampMs: f.timestampMs,
          worldLandmarks: f.worldLandmarks,
        })),
        clientAttemptedReps: options?.clientAttemptedReps,
        forceFinalize: options?.forceFinalize ?? false,
      },
    });
  },
  get(sessionId: string) {
    return apiRequest<ModuleAResult>(`/api/module-a/sessions/${sessionId}`);
  },
  history(exerciseType?: string, limit = 20) {
    const params = new URLSearchParams({ limit: String(limit) });
    if (exerciseType) params.set("exerciseType", exerciseType);
    return apiRequest<ModuleAResult[]>(`/api/module-a/history?${params.toString()}`);
  },
};
