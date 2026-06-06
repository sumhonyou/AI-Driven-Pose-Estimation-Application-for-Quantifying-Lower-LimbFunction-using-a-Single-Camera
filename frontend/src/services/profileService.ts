import { apiRequest } from "./apiClient";
import type { Profile, ProfileUpdatePayload } from "../types/api";

export const profileService = {
  get() {
    return apiRequest<Profile>("/api/users/me/profile");
  },
  update(payload: ProfileUpdatePayload) {
    return apiRequest<Profile>("/api/users/me/profile", {
      method: "PUT",
      body: payload,
    });
  },
};
