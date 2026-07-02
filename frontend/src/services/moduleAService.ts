import { apiRequest } from "./apiClient";
import type { PoseFrame } from "../types/pose";

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
};

export type ModuleAResult = {
  session_id: string;
  band: "good" | "fair" | "poor" | "invalid" | string;
  score: number;
  metrics: ModuleAMetrics;
  warning_tags: string[];
  capture_quality_band: string;
  valid_frame_ratio: number;
};

export const moduleAService = {
  analyze(sessionId: string, exerciseType: string, frames: PoseFrame[]) {
    return apiRequest<ModuleAResult>("/api/module-a/analyze", {
      method: "POST",
      body: {
        sessionId,
        exerciseType,
        frames: frames.map((f) => ({
          timestampMs: f.timestampMs,
          worldLandmarks: f.worldLandmarks,
        })),
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
