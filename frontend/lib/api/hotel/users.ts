import { apiFetch } from "@/lib/api/client";
import type { HotelRole, HotelUser, HotelUserListResponse } from "@/lib/types/hotel-users";

export const hotelUsersApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<HotelUserListResponse>(`/hotel/users?page=${page}&limit=${limit}`),
  get: (id: string) => apiFetch<HotelUser>(`/hotel/users/${id}`),
  create: (payload: {
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    role_id: string;
    is_active?: boolean;
  }) => apiFetch<HotelUser>("/hotel/users", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: {
    email?: string;
    password?: string;
    first_name?: string;
    last_name?: string;
    role_id?: string;
    is_active?: boolean;
  }) => apiFetch<HotelUser>(`/hotel/users/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/hotel/users/${id}`, { method: "DELETE" }),
  roles: () => apiFetch<HotelRole[]>("/hotel/users/roles")
};
