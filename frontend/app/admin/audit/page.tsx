"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { PageHeader } from "@/components/layout/primitives/page-header";
import { CrudFormCard } from "@/components/ui/composed/crud-form-card";
import { DataTable } from "@/components/ui/composed/data-table";
import { DirectoryTableCard } from "@/components/ui/composed/directory-table-card";
import { EmptyState } from "@/components/ui/composed/empty-state";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/primitives/button";
import { Field } from "@/components/ui/primitives/field";
import { TextInput } from "@/components/ui/primitives/text-input";
import { adminAuditApi } from "@/lib/api/admin/audit";
import type { AuditLogRecord } from "@/lib/types/audit";

const defaultFilters = {
  action: "",
  resource_type: "",
  user_id: "",
  tenant_id: "",
  date_from: "",
  date_to: ""
};

export default function AdminAuditPage() {
  const [logs, setLogs] = useState<AuditLogRecord[]>([]);
  const [filters, setFilters] = useState(defaultFilters);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(async (currentFilters: typeof defaultFilters) => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminAuditApi.list({
        page: 1,
        limit: 50,
        action: currentFilters.action || undefined,
        resource_type: currentFilters.resource_type || undefined,
        user_id: currentFilters.user_id || undefined,
        tenant_id: currentFilters.tenant_id || undefined,
        date_from: currentFilters.date_from || undefined,
        date_to: currentFilters.date_to || undefined
      });
      setLogs(data.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchLogs(defaultFilters);
  }, [fetchLogs]);

  const handleChange = (field: keyof typeof defaultFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [field]: value }));
  };

  const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void fetchLogs(filters);
  };

  const hasResults = useMemo(() => logs.length > 0, [logs]);

  return (
    <PermissionGuard
      permission="admin:audit:read"
      fallback={
        <GlassCard className="p-6">
          <h2 className="text-2xl">Access denied</h2>
          <p className="mt-2 text-sm text-[color:var(--color-text-muted)]">
            You do not have permission to view audit logs.
          </p>
        </GlassCard>
      }
    >
      <div className="space-y-6">
        <PageHeader
          title="Audit Logs"
          description="Immutable activity trail for platform actions."
          count={logs.length}
          countLabel="Records"
        />

        <CrudFormCard title="Filters">
          <form className="grid gap-4 md:grid-cols-3" onSubmit={handleSearch}>
            <Field label="Action">
              <TextInput
                value={filters.action}
                onChange={(event) => handleChange("action", event.target.value)}
                placeholder="auth.login"
              />
            </Field>
            <Field label="Resource Type">
              <TextInput
                value={filters.resource_type}
                onChange={(event) => handleChange("resource_type", event.target.value)}
                placeholder="tenant"
              />
            </Field>
            <Field label="User ID">
              <TextInput
                value={filters.user_id}
                onChange={(event) => handleChange("user_id", event.target.value)}
                placeholder="UUID"
              />
            </Field>
            <Field label="Tenant ID">
              <TextInput
                value={filters.tenant_id}
                onChange={(event) => handleChange("tenant_id", event.target.value)}
                placeholder="UUID"
              />
            </Field>
            <Field label="From">
              <TextInput
                type="date"
                value={filters.date_from}
                onChange={(event) => handleChange("date_from", event.target.value)}
              />
            </Field>
            <Field label="To">
              <TextInput
                type="date"
                value={filters.date_to}
                onChange={(event) => handleChange("date_to", event.target.value)}
              />
            </Field>
            <div className="md:col-span-3 flex flex-wrap gap-3">
              <Button type="submit" variant="primary">
                Apply Filters
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setFilters(defaultFilters);
                  void fetchLogs(defaultFilters);
                }}
              >
                Reset
              </Button>
            </div>
          </form>
        </CrudFormCard>

        {error ? <InlineAlert tone="error" message={error} /> : null}

        {loading ? (
          <InlineAlert tone="info" message="Loading audit logs..." />
        ) : !hasResults ? (
          <EmptyState description="No audit activity yet." />
        ) : (
          <DirectoryTableCard
            title="Recent Activity"
            table={
              <DataTable
                columns={[
                  {
                    key: "action",
                    header: "Action",
                    cellClassName: "font-medium",
                    render: (log) => log.action
                  },
                  {
                    key: "resource",
                    header: "Resource",
                    cellClassName: "text-[color:var(--color-text-muted)]",
                    render: (log) => log.resource_type ?? "-"
                  },
                  {
                    key: "user",
                    header: "User",
                    cellClassName: "text-[color:var(--color-text-muted)]",
                    render: (log) => log.user_id ?? "-"
                  },
                  {
                    key: "tenant",
                    header: "Tenant",
                    cellClassName: "text-[color:var(--color-text-muted)]",
                    render: (log) => log.tenant_id ?? "-"
                  },
                  {
                    key: "when",
                    header: "When",
                    render: (log) => (log.created_at ? new Date(log.created_at).toLocaleString() : "-")
                  }
                ]}
                rows={logs}
                rowKey={(log) => log.id}
              />
            }
          />
        )}
      </div>
    </PermissionGuard>
  );
}
