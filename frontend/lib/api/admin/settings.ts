import { apiFetch } from "@/lib/api/client";
import type {
  Setting,
  SettingCreate,
  SettingListResponse,
  SettingUpdate
} from "@/lib/types/settings";

export const adminSettingsApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<SettingListResponse>(`/admin/settings?page=${page}&limit=${limit}`),
  get: (id: string) => apiFetch<Setting>(`/admin/settings/${id}`),
  create: (payload: SettingCreate) =>
    apiFetch<Setting>("/admin/settings", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: SettingUpdate) =>
    apiFetch<Setting>(`/admin/settings/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/admin/settings/${id}`, { method: "DELETE" })
};
