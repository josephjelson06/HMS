import { apiFetch } from "@/lib/api/client";
import type { Room, RoomCreate, RoomListResponse, RoomUpdate } from "@/lib/types/rooms";

export const hotelRoomsApi = {
  list: (params?: { page?: number; limit?: number; search?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.limit) query.set("limit", params.limit.toString());
    if (params?.search) query.set("search", params.search);
    const qs = query.toString();
    return apiFetch<RoomListResponse>(`/hotel/rooms${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => apiFetch<Room>(`/hotel/rooms/${id}`),
  create: (payload: RoomCreate) =>
    apiFetch<Room>("/hotel/rooms", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: RoomUpdate) =>
    apiFetch<Room>(`/hotel/rooms/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/hotel/rooms/${id}`, { method: "DELETE" })
};
