import { apiFetch } from "@/lib/api/client";
import type { Invoice } from "@/lib/types/invoices";
import type { BillingSummary } from "@/lib/types/billing";

export const hotelBillingApi = {
  summary: (limit = 10) =>
    apiFetch<BillingSummary>(`/hotel/billing/summary?limit=${limit}`),
  invoices: (limit = 20) => apiFetch<Invoice[]>(`/hotel/billing/invoices?limit=${limit}`),
  invoice: (id: string) => apiFetch<Invoice>(`/hotel/billing/invoices/${id}`)
};
