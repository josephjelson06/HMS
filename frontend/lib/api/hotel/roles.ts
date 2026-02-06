import { apiFetch } from "@/lib/api/client";
import type {
  HotelRole,
  HotelRoleCreate,
  HotelRoleUpdate,
  PermissionOption
} from "@/lib/types/hotel-roles";

export const hotelRolesApi = {
  list: () => apiFetch<HotelRole[]>("/hotel/roles"),
  get: (id: string) => apiFetch<HotelRole>(`/hotel/roles/${id}`),
  create: (payload: HotelRoleCreate) =>
    apiFetch<HotelRole>("/hotel/roles", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: HotelRoleUpdate) =>
    apiFetch<HotelRole>(`/hotel/roles/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/hotel/roles/${id}`, { method: "DELETE" }),
  permissions: () => apiFetch<PermissionOption[]>("/hotel/roles/permissions")
};
