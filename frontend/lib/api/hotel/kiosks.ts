import { apiFetch } from "@/lib/api/client";
import type { Kiosk, KioskCreate, KioskListResponse, KioskUpdate } from "@/lib/types/kiosks";

export const hotelKiosksApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<KioskListResponse>(`/hotel/kiosks?page=${page}&limit=${limit}`),
  get: (id: string) => apiFetch<Kiosk>(`/hotel/kiosks/${id}`),
  create: (payload: KioskCreate) =>
    apiFetch<Kiosk>("/hotel/kiosks", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: KioskUpdate) =>
    apiFetch<Kiosk>(`/hotel/kiosks/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/hotel/kiosks/${id}`, { method: "DELETE" })
};
