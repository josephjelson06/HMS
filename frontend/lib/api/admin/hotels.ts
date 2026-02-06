import { apiFetch } from "@/lib/api/client";
import type { Hotel, HotelListResponse } from "@/lib/types/tenant";

export const hotelAdminApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<HotelListResponse>(`/admin/hotels?page=${page}&limit=${limit}`),
  get: (id: string) => apiFetch<Hotel>(`/admin/hotels/${id}`),
  create: (payload: {
    name: string;
    slug?: string;
    status?: string;
    subscription_tier?: string;
  }) => apiFetch<Hotel>("/admin/hotels", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: {
    name?: string;
    slug?: string;
    status?: string;
    subscription_tier?: string;
  }) => apiFetch<Hotel>(`/admin/hotels/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/admin/hotels/${id}`, { method: "DELETE" })
};
