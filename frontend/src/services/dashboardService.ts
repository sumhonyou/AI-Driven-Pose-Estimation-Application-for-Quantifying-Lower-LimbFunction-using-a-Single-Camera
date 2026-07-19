import { apiRequest } from "./apiClient";
import type { DashboardErrorTags, DashboardSummary, DashboardTrends } from "../types/api";

// Optional inclusive date window, forwarded as ISO strings to the backend.
type DateRange = { from?: string; to?: string };

function rangeQuery({ from, to }: DateRange): string {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export const dashboardService = {
  summary() {
    return apiRequest<DashboardSummary>("/api/dashboard/summary");
  },
  trends(range: DateRange = {}) {
    return apiRequest<DashboardTrends>(`/api/dashboard/trends${rangeQuery(range)}`);
  },
  errorTags(range: DateRange = {}) {
    return apiRequest<DashboardErrorTags>(`/api/dashboard/error-tags${rangeQuery(range)}`);
  },
};
