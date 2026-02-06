import { apiFetch } from "@/lib/api/client";
import type { Kiosk, KioskCreate, KioskListResponse, KioskUpdate } from "@/lib/types/kiosks";

export const adminKiosksApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<KioskListResponse>(`/admin/kiosks?page=${page}&limit=${limit}`),
  get: (id: string) => apiFetch<Kiosk>(`/admin/kiosks/${id}`),
  create: (payload: KioskCreate) =>
    apiFetch<Kiosk>("/admin/kiosks", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: KioskUpdate) =>
    apiFetch<Kiosk>(`/admin/kiosks/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/admin/kiosks/${id}`, { method: "DELETE" })
};
