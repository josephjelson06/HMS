import { apiFetch } from "@/lib/api/client";
import type { Invoice, InvoiceCreate, InvoiceListResponse, InvoiceUpdate } from "@/lib/types/invoices";

export const adminInvoicesApi = {
  list: (page = 1, limit = 20) =>
    apiFetch<InvoiceListResponse>(`/admin/invoices?page=${page}&limit=${limit}`),
  get: (id: string) => apiFetch<Invoice>(`/admin/invoices/${id}`),
  create: (payload: InvoiceCreate) =>
    apiFetch<Invoice>("/admin/invoices", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: InvoiceUpdate) =>
    apiFetch<Invoice>(`/admin/invoices/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => apiFetch<void>(`/admin/invoices/${id}`, { method: "DELETE" })
};
