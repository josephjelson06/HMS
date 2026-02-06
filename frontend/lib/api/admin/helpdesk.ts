import { apiFetch } from "@/lib/api/client";
import type {
  HelpdeskCreate,
  HelpdeskListResponse,
  HelpdeskTicket,
  HelpdeskUpdate
} from "@/lib/types/helpdesk";

export const adminHelpdeskApi = {
  list: (params?: { page?: number; limit?: number; status?: string; priority?: string; tenant_id?: string }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.limit) query.set("limit", params.limit.toString());
    if (params?.status) query.set("status", params.status);
    if (params?.priority) query.set("priority", params.priority);
    if (params?.tenant_id) query.set("tenant_id", params.tenant_id);
    const qs = query.toString();
    return apiFetch<HelpdeskListResponse>(`/admin/helpdesk${qs ? `?${qs}` : ""}`);
  },
  get: (id: string) => apiFetch<HelpdeskTicket>(`/admin/helpdesk/${id}`),
  create: (payload: HelpdeskCreate) =>
    apiFetch<HelpdeskTicket>("/admin/helpdesk", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: HelpdeskUpdate) =>
    apiFetch<HelpdeskTicket>(`/admin/helpdesk/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/admin/helpdesk/${id}`, { method: "DELETE" })
};
