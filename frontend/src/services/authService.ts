import { apiRequest } from "./apiClient";
import type { LoginPayload, RegisterPayload, TokenResponse, User } from "../types/api";

export const authService = {
  login(payload: LoginPayload) {
    return apiRequest<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: payload,
      auth: false,
    });
  },
  register(payload: RegisterPayload) {
    return apiRequest<TokenResponse>("/api/auth/register", {
      method: "POST",
      body: payload,
      auth: false,
    });
  },
  me() {
    return apiRequest<User>("/api/auth/me");
  },
};
