import { apiRequest } from "./apiClient";
import type { DashboardSummary } from "../types/api";

export const dashboardService = {
  summary() {
    return apiRequest<DashboardSummary>("/api/dashboard/summary");
  },
  trends() {
    return apiRequest<Array<{ label: string; score: number | null }>>(
      "/api/dashboard/trends",
    );
  },
  errorTags() {
    return apiRequest<Array<{ tag_code: string; severity: string | null; count: number }>>(
      "/api/dashboard/error-tags",
    );
  },
};
