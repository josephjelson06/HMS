import { apiFetch } from "@/lib/api/client";
import type { AdminRole, AdminUser, AdminUserListResponse } from "@/lib/types/user";

export const adminUsersApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<AdminUserListResponse>(`/admin/users?page=${page}&limit=${limit}`),
  get: (id: string) => apiFetch<AdminUser>(`/admin/users/${id}`),
  create: (payload: {
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    role_id: string;
    is_active?: boolean;
  }) => apiFetch<AdminUser>("/admin/users", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: {
    email?: string;
    password?: string;
    first_name?: string;
    last_name?: string;
    role_id?: string;
    is_active?: boolean;
  }) => apiFetch<AdminUser>(`/admin/users/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/admin/users/${id}`, { method: "DELETE" }),
  roles: () => apiFetch<AdminRole[]>("/admin/users/roles")
};
