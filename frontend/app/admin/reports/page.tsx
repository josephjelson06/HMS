"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { PageHeader } from "@/components/layout/primitives/page-header";
import { CrudFormCard } from "@/components/ui/composed/crud-form-card";
import { EmptyState } from "@/components/ui/composed/empty-state";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/primitives/button";
import { Field } from "@/components/ui/primitives/field";
import { TextInput } from "@/components/ui/primitives/text-input";
import { adminReportsApi } from "@/lib/api/admin/reports";
import type { ReportCard } from "@/lib/types/reports";

export default function AdminReportsPage() {
  const [reports, setReports] = useState<ReportCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [error, setError] = useState<string | null>(null);

  const fetchReports = useCallback(async (filters?: { date_from?: string; date_to?: string }) => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminReportsApi.list({
        date_from: filters?.date_from,
        date_to: filters?.date_to
      });
      setReports(data.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load reports");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchReports();
  }, [fetchReports]);

  return (
    <PermissionGuard
      permission="admin:reports:read"
      fallback={
        <GlassCard className="p-6">
          <h2 className="text-2xl">Access denied</h2>
          <p className="mt-2 text-sm text-[color:var(--color-text-muted)]">
            You do not have permission to view reports.
          </p>
        </GlassCard>
      }
    >
      <div className="space-y-6">
        <PageHeader
          title="Reports"
          description="Card-based insights across tenants, subscriptions, and billing."
          count={reports.length}
          countLabel="Reports"
        />

        <CrudFormCard title="Date Filters">
          <div className="flex flex-wrap gap-4">
            <Field label="From">
              <TextInput
                type="date"
                value={dateFrom}
                onChange={(event) => setDateFrom(event.target.value)}
              />
            </Field>
            <Field label="To">
              <TextInput
                type="date"
                value={dateTo}
                onChange={(event) => setDateTo(event.target.value)}
              />
            </Field>
            <div className="flex items-end">
              <Button
                variant="primary"
                onClick={() =>
                  void fetchReports({
                    date_from: dateFrom || undefined,
                    date_to: dateTo || undefined
                  })
                }
              >
                Apply Filters
              </Button>
            </div>
          </div>
          {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
        </CrudFormCard>

        {loading ? (
          <InlineAlert tone="info" message="Loading reports..." />
        ) : reports.length === 0 ? (
          <EmptyState description="No reports available yet." />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {reports.map((report) => (
              <GlassCard key={report.code} className="p-6 flex flex-col justify-between">
                <div>
                  <h3 className="text-lg">{report.title}</h3>
                  <p className="mt-1 text-sm text-[color:var(--color-text-muted)]">{report.description}</p>
                  <div className="mt-4 space-y-2">
                    {report.metrics.map((metric) => (
                      <div key={metric.label} className="flex items-center justify-between text-sm">
                        <span className="text-[color:var(--color-text-muted)]">{metric.label}</span>
                        <span className="font-semibold">{metric.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <Link
                  href={`/admin/reports/${report.code}`}
                  className="mt-5 ui-btn ui-btn-outline ui-btn-sm ui-anim"
                >
                  View report
                </Link>
              </GlassCard>
            ))}
          </div>
        )}
      </div>
    </PermissionGuard>
  );
}
