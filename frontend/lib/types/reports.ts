export interface ReportMetric {
  label: string;
  value: string | number;
}

export interface ReportCard {
  code: string;
  title: string;
  description: string;
  metrics: ReportMetric[];
}

export interface ReportsListResponse {
  items: ReportCard[];
}

export interface ReportColumn {
  key: string;
  label: string;
}

export interface ReportDetail {
  code: string;
  title: string;
  description: string;
  filters: Record<string, string | null>;
  summary: ReportMetric[];
  columns: ReportColumn[];
  rows: Record<string, string | number | null>[];
}

export interface ReportExport {
  id: string;
  report_code: string;
  export_format: string;
  status: "pending" | "processing" | "completed" | "failed" | string;
  file_name?: string | null;
  download_path?: string | null;
  error_message?: string | null;
  created_at?: string | null;
  completed_at?: string | null;
}

export type ReportExportFormat = "csv" | "pdf" | "excel";

export interface ReportExportRequest {
  format: ReportExportFormat;
  date_from?: string;
  date_to?: string;
  status?: string;
}
