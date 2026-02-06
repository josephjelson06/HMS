import { apiFetch } from "@/lib/api/client";
import type {
  ReportDetail,
  ReportExport,
  ReportExportRequest,
  ReportsListResponse
} from "@/lib/types/reports";

const buildQuery = (params: Record<string, string | undefined>) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const qs = query.toString();
  return qs ? `?${qs}` : "";
};

export const adminReportsApi = {
  list: (filters?: { date_from?: string; date_to?: string }) =>
    apiFetch<ReportsListResponse>(
      `/admin/reports${buildQuery({
        date_from: filters?.date_from,
        date_to: filters?.date_to
      })}`
    ),
  get: (code: string, filters?: { date_from?: string; date_to?: string; status?: string }) =>
    apiFetch<ReportDetail>(
      `/admin/reports/${code}${buildQuery({
        date_from: filters?.date_from,
        date_to: filters?.date_to,
        status: filters?.status
      })}`
    ),
  export: (code: string, payload: ReportExportRequest) =>
    apiFetch<ReportExport>(`/admin/reports/${code}/export`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  getExport: (exportId: string) =>
    apiFetch<ReportExport>(`/admin/reports/exports/${exportId}`)
};
