import { apiFetch } from "@/lib/api/client";
import type { AdminRole, AdminRoleCreate, AdminRoleUpdate, PermissionOption } from "@/lib/types/roles";

export const adminRolesApi = {
  list: () => apiFetch<AdminRole[]>("/admin/roles"),
  get: (id: string) => apiFetch<AdminRole>(`/admin/roles/${id}`),
  create: (payload: AdminRoleCreate) =>
    apiFetch<AdminRole>("/admin/roles", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: AdminRoleUpdate) =>
    apiFetch<AdminRole>(`/admin/roles/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/admin/roles/${id}`, { method: "DELETE" }),
  permissions: () => apiFetch<PermissionOption[]>("/admin/roles/permissions")
};
