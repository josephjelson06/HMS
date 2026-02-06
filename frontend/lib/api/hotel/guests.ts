import { apiFetch } from "@/lib/api/client";
import type { Guest, GuestCreate, GuestListResponse, GuestUpdate } from "@/lib/types/guests";

export const hotelGuestsApi = {
  list: (params?: { page?: number; limit?: number; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.limit) query.set("limit", params.limit.toString());
    if (params?.search) query.set("search", params.search);
    const qs = query.toString();
    return apiFetch<GuestListResponse>(`/hotel/guests${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => apiFetch<Guest>(`/hotel/guests/${id}`),
  create: (payload: GuestCreate) =>
    apiFetch<Guest>("/hotel/guests", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: GuestUpdate) =>
    apiFetch<Guest>(`/hotel/guests/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/hotel/guests/${id}`, { method: "DELETE" })
};
