import { apiFetch } from "@/lib/api/client";
import type {
  Setting,
  SettingCreate,
  SettingListResponse,
  SettingUpdate
} from "@/lib/types/settings";

export const hotelSettingsApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<SettingListResponse>(`/hotel/settings?page=${page}&limit=${limit}`),
  get: (id: string) => apiFetch<Setting>(`/hotel/settings/${id}`),
  create: (payload: SettingCreate) =>
    apiFetch<Setting>("/hotel/settings", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: SettingUpdate) =>
    apiFetch<Setting>(`/hotel/settings/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/hotel/settings/${id}`, { method: "DELETE" })
};
