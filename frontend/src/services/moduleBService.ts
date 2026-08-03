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
  // Optional per-rep verdict fields for exercises that use voting.
  ml_score?: number;
  confidence?: number;
  failed_gates?: string[];
  counted_good?: boolean;
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

// Structured after-set coaching text rendered by the report.
export type ModuleBFeedbackStructured = {
  summary: string;
  tips: string[];
};

export type ModuleBFeedback = {
  structured_feedback: string | null;
  rewritten_feedback: string | null;
  rewritten_feedback_structured: ModuleBFeedbackStructured | null;
  feedback_source: "llm" | "template";
  llm_attempted: boolean;
  provider: string | null;
  model_version: string | null;
  disclaimer_version: string | null;
};

// Previous completed squat session trend. No meaningful-change flag is exposed.
export type SquatTrend = {
  score_delta: number | null;
  rep_count_delta: number | null;
  previous_band: string | null;
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
  feedback: ModuleBFeedback | null;
  created_at: string | null;
  trend?: SquatTrend | null;
};

export const moduleBService = {
  // `targetRepCount` rides along with the frames rather than being set at session
  // start, because the user picks their goal on the live page after the session row
  // already exists. Omitted entirely when no goal was set.
  analyze(
    sessionId: string,
    exerciseCode: string,
    frames: PoseFrame[],
    targetRepCount?: number | null,
  ) {
    return apiRequest<ModuleBResult>("/api/module-b/analyze", {
      method: "POST",
      body: {
        session_id: sessionId,
        exercise_code: exerciseCode,
        target_rep_count: targetRepCount ?? null,
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
