// REST client for the generic Module B endpoints (registry + plugin router).
// Mirrors moduleAService.ts's shape, matching the backend's thin generic router
// (POST /api/module-b/analyze, GET /api/module-b/results/{id}, GET /api/module-b/{code}/config).
import { apiRequest } from "./apiClient";
import type { PoseFrame } from "../types/pose";

export type ModuleBSubScore = {
  code: string;
  score: number | null;
  notes: string[];
  // Report-only numeric measurements that never contribute to the sub-score's
  // own `score` (see backend core/rules.py's SubScore docstring). Optional:
  // every squat sub-score currently has no entries here.
  metrics?: Record<string, number>;
};

export type ModuleBErrorTag = {
  tag: string;
  severity: string | null;
  source: string;
  message: string | null;
};

export type ModuleBRepSummary = {
  start_timestamp_s: number;
  end_timestamp_s: number;
  duration_s: number;
  bottom_frame_index: number;
  bottom_knee_flexion_deg: number;
};

export type ModuleBMetrics = {
  rule_score: number | null;
  rule_subscores: ModuleBSubScore[];
  ml_score: number | null;
  fusion_weights: { w_rule: number; w_ml: number };
  fusion_flags: string[];
  placeholder_model_notice: boolean;
  capture_quality: {
    q: number;
    valid_frame_ratio: number;
    capture_quality_band: string;
  };
  per_rep_summaries: ModuleBRepSummary[];
};

export type ModuleBResult = {
  session_id: string;
  exercise_code: string;
  score: number | null;
  band: "Poor" | "Fair" | "Good" | null;
  confidence: number | null;
  model_version: string | null;
  feature_schema_version: string | null;
  q: number | null;
  metrics: ModuleBMetrics;
  error_tags: ModuleBErrorTag[];
  created_at: string | null;
};

export const moduleBService = {
  analyze(sessionId: string, exerciseCode: string, frames: PoseFrame[]) {
    return apiRequest<ModuleBResult>("/api/module-b/analyze", {
      method: "POST",
      body: {
        session_id: sessionId,
        exercise_code: exerciseCode,
        frames: frames.map((f) => ({
          timestampMs: f.timestampMs,
          worldLandmarks: f.worldLandmarks,
        })),
      },
    });
  },
  get(sessionId: string) {
    return apiRequest<ModuleBResult>(`/api/module-b/results/${sessionId}`);
  },
  /** Exercise config (core + exercise-specific thresholds) for frontend threshold sync. */
  config(code: string) {
    return apiRequest<{ core: Record<string, unknown>; exercise: Record<string, unknown> }>(
      `/api/module-b/${code}/config`,
    );
  },
};
