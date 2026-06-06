import { apiRequest } from "./apiClient";
import type { SessionDTO } from "../types/api";

export const sessionService = {
  start(payload: { mode: string; exercise_code: string; device_info?: string }) {
    return apiRequest<{ session_id: string; status: string }>("/api/sessions/start", {
      method: "POST",
      body: payload,
    });
  },
  end(
    sessionId: string,
    payload: { capture_quality?: number; valid_frame_ratio?: number } = {},
  ) {
    return apiRequest<SessionDTO>(`/api/sessions/${sessionId}/end`, {
      method: "POST",
      body: payload,
    });
  },
  list() {
    return apiRequest<SessionDTO[]>("/api/sessions");
  },
  get(sessionId: string) {
    return apiRequest<SessionDTO>(`/api/sessions/${sessionId}`);
  },
};
