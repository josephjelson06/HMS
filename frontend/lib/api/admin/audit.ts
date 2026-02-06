import { apiFetch } from "@/lib/api/client";
import type { AuditLogListResponse, AuditLogRecord } from "@/lib/types/audit";

export const adminAuditApi = {
  list: (params: {
    page?: number;
    limit?: number;
    user_id?: string;
    tenant_id?: string;
    action?: string;
    resource_type?: string;
    date_from?: string;
    date_to?: string;
  } = {}) => {
    const searchParams = new URLSearchParams();
    if (params.page) searchParams.set("page", String(params.page));
    if (params.limit) searchParams.set("limit", String(params.limit));
    if (params.user_id) searchParams.set("user_id", params.user_id);
    if (params.tenant_id) searchParams.set("tenant_id", params.tenant_id);
    if (params.action) searchParams.set("action", params.action);
    if (params.resource_type) searchParams.set("resource_type", params.resource_type);
    if (params.date_from) searchParams.set("date_from", params.date_from);
    if (params.date_to) searchParams.set("date_to", params.date_to);

    const query = searchParams.toString();
    return apiFetch<AuditLogListResponse>(`/admin/audit?${query}`);
  },
  get: (id: string) => apiFetch<AuditLogRecord>(`/admin/audit/${id}`)
};
