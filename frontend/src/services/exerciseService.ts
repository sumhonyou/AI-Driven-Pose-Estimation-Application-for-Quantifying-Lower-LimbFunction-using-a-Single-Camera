import { apiRequest } from "./apiClient";
import type { Exercise } from "../types/api";

export const exerciseService = {
  list() {
    return apiRequest<Exercise[]>("/api/exercises");
  },
  get(code: string) {
    return apiRequest<Exercise>(`/api/exercises/${code}`);
  },
};
