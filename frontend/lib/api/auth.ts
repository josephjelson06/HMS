import { apiFetch } from "@/lib/api/client";
import {
  AuthResponse,
  ImpersonationStartRequest,
  PasswordChangeRequest,
  PasswordChangeResponse
} from "@/lib/types/api";

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  refresh: () => apiFetch<AuthResponse>("/auth/refresh", { method: "POST" }),
  logout: () => apiFetch<{ success: boolean }>("/auth/logout", { method: "POST" }),
  me: () => apiFetch<AuthResponse>("/auth/me"),
  changePassword: (payload: PasswordChangeRequest) =>
    apiFetch<PasswordChangeResponse>("/auth/password/change", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  startImpersonation: (payload: ImpersonationStartRequest) =>
    apiFetch<AuthResponse>("/auth/impersonation/start", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  stopImpersonation: () => apiFetch<AuthResponse>("/auth/impersonation/stop", { method: "POST" })
};
