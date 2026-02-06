"use client";

import { format } from "date-fns";
import { useParams } from "next/navigation";
import type { DateRange } from "react-day-picker";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { PageHeader } from "@/components/layout/primitives/page-header";
import { AccessDeniedState } from "@/components/ui/composed/access-denied-state";
import { DataTable, type DataTableColumn } from "@/components/ui/composed/data-table";
import { DirectoryTableCard } from "@/components/ui/composed/directory-table-card";
import { EmptyState } from "@/components/ui/composed/empty-state";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { SectionCard } from "@/components/ui/composed/section-card";
import { Button } from "@/components/ui/primitives/button";
import { DataToolbar } from "@/components/ui/primitives/data-toolbar";
import { DateRangePicker } from "@/components/ui/primitives/date-range-picker";
import { Pagination } from "@/components/ui/primitives/pagination";
import { SelectInput } from "@/components/ui/primitives/select-input";
import { TextInput } from "@/components/ui/primitives/text-input";
import { hotelReportsApi } from "@/lib/api/hotel/reports";
import type { ReportDetail, ReportExport, ReportExportFormat } from "@/lib/types/reports";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

type ReportFilters = { date_from?: string; date_to?: string; status?: string };
type ReportRow = Record<string, string | number | null>;

function compareValues(left: string | number | null, right: string | number | null) {
  if (left == null && right == null) return 0;
  if (left == null) return 1;
  if (right == null) return -1;

  const leftNumber = typeof left === "number" ? left : Number(left);
  const rightNumber = typeof right === "number" ? right : Number(right);
  const numeric = Number.isFinite(leftNumber) && Number.isFinite(rightNumber);

  if (numeric) return leftNumber - rightNumber;
  return String(left).localeCompare(String(right), undefined, { sensitivity: "base" });
}

function toDateString(value?: Date) {
  return value ? format(value, "yyyy-MM-dd") : undefined;
}

export default function HotelReportDetailPage() {
  const params = useParams<{ code: string }>();
  const reportCode = params.code;

  const [detail, setDetail] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [dateRange, setDateRange] = useState<DateRange | undefined>();
  const [status, setStatus] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [exportInfo, setExportInfo] = useState<ReportExport | null>(null);
  const [exportFormat, setExportFormat] = useState<ReportExportFormat>("csv");
  const [exporting, setExporting] = useState(false);
  const [sortValue, setSortValue] = useState("");
  const [page, setPage] = useState(1);
  const [limit] = useState(20);

  const buildFilters = useCallback((): ReportFilters => {
    return {
      date_from: toDateString(dateRange?.from),
      date_to: toDateString(dateRange?.to),
      status: status.trim() || undefined
    };
  }, [dateRange, status]);

  const fetchReport = useCallback(async (code: string, filters?: ReportFilters) => {
    if (!code) return;
    setLoading(true);
    setError(null);
    try {
      const data = await hotelReportsApi.get(code, filters);
      setDetail(data);
      setPage(1);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load report";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!reportCode) return;
    void fetchReport(reportCode);
  }, [fetchReport, reportCode]);

  const handleApply = () => {
    if (!reportCode) return;
    setPage(1);
    void fetchReport(reportCode, buildFilters());
  };

  const handleExport = async () => {
    if (!reportCode) return;
    setError(null);
    setExporting(true);
    try {
      const filters = buildFilters();
      const exportData = await hotelReportsApi.export(reportCode, {
        format: exportFormat,
        date_from: filters.date_from,
        date_to: filters.date_to,
        status: filters.status
      });
      setExportInfo(exportData);
      toast.success("Export requested");

      if (exportData.status === "pending" || exportData.status === "processing") {
        for (let attempt = 0; attempt < 60; attempt += 1) {
          await sleep(1000);
          const latest = await hotelReportsApi.getExport(exportData.id);
          setExportInfo(latest);
          if (latest.status === "completed" || latest.status === "failed") break;
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to export report";
      setError(message);
      toast.error(message);
    } finally {
      setExporting(false);
    }
  };

  const downloadUrl = useMemo(() => {
    if (!exportInfo?.download_path) return null;
    return `${API_BASE}${exportInfo.download_path}`;
  }, [exportInfo]);

  const tableColumns = useMemo<DataTableColumn<ReportRow>[]>(() => {
    if (!detail) return [];
    return detail.columns.map((column) => ({
      key: column.key,
      header: column.label,
      render: (row) => row[column.key] ?? "-"
    }));
  }, [detail]);

  const sortOptions = useMemo(() => {
    if (!detail) return [];
    return detail.columns.flatMap((column) => [
      { value: `${column.key}:asc`, label: `${column.label} (A-Z)` },
      { value: `${column.key}:desc`, label: `${column.label} (Z-A)` }
    ]);
  }, [detail]);

  const sortedRows = useMemo(() => {
    if (!detail) return [];
    if (!sortValue) return detail.rows;

    const [sortKey, sortDirection] = sortValue.split(":");
    const direction = sortDirection === "desc" ? -1 : 1;

    return [...detail.rows].sort((left, right) => {
      return compareValues(left[sortKey] ?? null, right[sortKey] ?? null) * direction;
    });
  }, [detail, sortValue]);

  const pagedRows = useMemo(() => {
    const start = (page - 1) * limit;
    const end = start + limit;
    return sortedRows.slice(start, end);
  }, [limit, page, sortedRows]);

  return (
    <PermissionGuard
      permission="hotel:reports:read"
      fallback={<AccessDeniedState message="You do not have permission to view this report." />}
    >
      <div className="space-y-6">
        <PageHeader title={detail?.title ?? "Report"} description={detail?.description} />

        <SectionCard title="Filters & Export">
          <DataToolbar
            filtersSlot={
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                <div>
                  <label className="mb-1.5 block text-xs text-[color:var(--color-text-muted)]">Date Range</label>
                  <DateRangePicker value={dateRange} onChange={setDateRange} className="w-full" numberOfMonths={2} />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs text-[color:var(--color-text-muted)]">Status</label>
                  <TextInput value={status} onChange={(event) => setStatus(event.target.value)} placeholder="optional" />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs text-[color:var(--color-text-muted)]">Export Format</label>
                  <SelectInput
                    value={exportFormat}
                    onChange={(event) => setExportFormat(event.target.value as ReportExportFormat)}
                  >
                    <option value="csv">CSV</option>
                    <option value="pdf">PDF</option>
                    <option value="excel">Excel</option>
                  </SelectInput>
                </div>
              </div>
            }
            actionsSlot={
              <>
                <Button variant="primary" onClick={handleApply}>
                  Apply
                </Button>
                <PermissionGuard permission="hotel:reports:export">
                  <Button variant="secondary" onClick={() => void handleExport()} disabled={exporting}>
                    {exporting ? "Queuing..." : "Request Export"}
                  </Button>
                </PermissionGuard>
              </>
            }
          />

          {exportInfo ? (
            <div className="mt-3 space-y-1 text-sm">
              <p>
                Export status: <span className="font-semibold capitalize">{exportInfo.status}</span> (
                {exportInfo.export_format.toUpperCase()})
              </p>
              {downloadUrl ? (
                <p>
                  File ready:{" "}
                  <a className="underline" href={downloadUrl} target="_blank" rel="noreferrer">
                    Download {exportInfo.export_format.toUpperCase()}
                  </a>
                </p>
              ) : null}
              {exportInfo.status === "failed" && exportInfo.error_message ? (
                <InlineAlert tone="error" message={exportInfo.error_message} />
              ) : null}
            </div>
          ) : null}

          {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
        </SectionCard>

        {loading ? (
          <InlineAlert tone="info" message="Loading report..." />
        ) : detail ? (
          <div className="space-y-4">
            {detail.summary.length > 0 ? (
              <SectionCard title="Summary">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {detail.summary.map((metric) => (
                    <div key={metric.label} className="flex items-center justify-between text-sm">
                      <span className="text-[color:var(--color-text-muted)]">{metric.label}</span>
                      <span className="font-semibold">{metric.value}</span>
                    </div>
                  ))}
                </div>
              </SectionCard>
            ) : null}

            {detail.columns.length > 0 ? (
              <DirectoryTableCard
                title="Report Data"
                table={
                  <>
                    <DataToolbar
                      sortValue={sortValue}
                      sortOptions={sortOptions}
                      onSortChange={setSortValue}
                      actionsSlot={
                        <Button variant="secondary" onClick={handleApply}>
                          Refresh
                        </Button>
                      }
                    />
                    {pagedRows.length === 0 ? (
                      <EmptyState description="No data for the selected filters." />
                    ) : (
                      <div className="mt-3">
                        <DataTable
                          columns={tableColumns}
                          rows={pagedRows}
                          rowKey={(_row, rowIndex) => `${page}-${rowIndex}`}
                        />
                      </div>
                    )}
                  </>
                }
                footer={<Pagination page={page} limit={limit} total={sortedRows.length} onPageChange={setPage} />}
              />
            ) : (
              <EmptyState description="This report provides summary metrics only." />
            )}
          </div>
        ) : null}
      </div>
    </PermissionGuard>
  );
}
