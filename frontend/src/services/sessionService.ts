import { API_BASE_URL, apiRequest, TOKEN_KEY } from "./apiClient";
import type { SessionDTO } from "../types/api";

export const sessionService = {
  start(payload: { mode: string; exercise_code: string; device_info?: string }) {
    return apiRequest<{ session_id: string; status: string }>("/api/sessions/start", {
      method: "POST",
      body: payload,
    });
  },
  end(sessionId: string, payload: { capture_quality?: number; valid_frame_ratio?: number } = {}) {
    return apiRequest<SessionDTO>(`/api/sessions/${sessionId}/end`, {
      method: "POST",
      body: payload,
    });
  },
  // Aborts an in-progress session without scoring it — never appears as completed.
  cancel(sessionId: string) {
    return apiRequest<SessionDTO>(`/api/sessions/${sessionId}/cancel`, {
      method: "POST",
    });
  },
  list() {
    return apiRequest<SessionDTO[]>("/api/sessions");
  },
  get(sessionId: string) {
    return apiRequest<SessionDTO>(`/api/sessions/${sessionId}`);
  },
};

// Dedupes double-click / remount cancel POSTs — Set, not a queue (no FIFO needed).
const pendingCancelIds = new Set<string>();

/** Fire-and-forget cancel. Does not block navigation. Safe to call twice for the same id. */
export function enqueueCancel(sessionId: string) {
  if (pendingCancelIds.has(sessionId)) return;
  pendingCancelIds.add(sessionId);
  console.log("[Session] Cancel enqueued", sessionId);
  sessionService
    .cancel(sessionId)
    .catch((err) => console.error("[Session] Cancel failed", err))
    .finally(() => pendingCancelIds.delete(sessionId));
}

/**
 * Best-effort cancellation for a tab close, reload, or hard navigation.
 * `keepalive` lets the browser continue this small authenticated request while
 * the page is being discarded. Starting another session is the server fallback
 * if a browser cannot deliver the request.
 */
export function cancelOnPageExit(sessionId: string) {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return;

  console.log("[Session] Cancelling active session on page exit", sessionId);
  void fetch(`${API_BASE_URL}/api/sessions/${sessionId}/cancel`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    keepalive: true,
  }).catch(() => {
    // The tab is closing, so there is nowhere useful to surface this error.
  });
}
