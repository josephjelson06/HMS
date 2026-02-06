"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { PageHeader } from "@/components/layout/primitives/page-header";
import { AccessDeniedState } from "@/components/ui/composed/access-denied-state";
import { ConfirmDialog } from "@/components/ui/composed/confirm-dialog";
import { DataTable } from "@/components/ui/composed/data-table";
import { DirectoryTableCard } from "@/components/ui/composed/directory-table-card";
import { EmptyState } from "@/components/ui/composed/empty-state";
import { FormModal } from "@/components/ui/composed/form-modal";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { TableActionCell } from "@/components/ui/composed/table-action-cell";
import { Button } from "@/components/ui/primitives/button";
import { DataToolbar } from "@/components/ui/primitives/data-toolbar";
import { Field } from "@/components/ui/primitives/field";
import { Pagination } from "@/components/ui/primitives/pagination";
import { TextAreaInput } from "@/components/ui/primitives/textarea-input";
import { TextInput } from "@/components/ui/primitives/text-input";
import { hotelIncidentsApi } from "@/lib/api/hotel/incidents";
import type { Incident } from "@/lib/types/incidents";

const defaultForm = {
  title: "",
  description: "",
  status: "open",
  severity: "medium",
  category: "",
  occurred_at: "",
  resolved_at: ""
};

const toIso = (value: string) => {
  if (!value) return undefined;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? undefined : date.toISOString();
};

const toDateInput = (value?: string | null) => {
  if (!value) return "";
  return value.slice(0, 10);
};

export default function HotelIncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<Incident | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Incident | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [statusInput, setStatusInput] = useState("");
  const [severityInput, setSeverityInput] = useState("");
  const [filters, setFilters] = useState({ search: "", status: "", severity: "" });
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchIncidents = useCallback(
    async (nextPage: number, nextFilters: { search: string; status: string; severity: string }) => {
      setLoading(true);
      setError(null);
      try {
        const data = await hotelIncidentsApi.list({
          page: nextPage,
          limit,
          search: nextFilters.search || undefined,
          status: nextFilters.status || undefined,
          severity: nextFilters.severity || undefined
        });
        setIncidents(data.items);
        setPage(data.pagination.page);
        setTotal(data.pagination.total);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to load incidents";
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    },
    [limit]
  );

  useEffect(() => {
    void fetchIncidents(page, filters);
  }, [fetchIncidents, filters, page]);

  const handleApplyFilters = () => {
    const nextFilters = {
      search: searchInput.trim(),
      status: statusInput.trim(),
      severity: severityInput.trim()
    };
    setFilters(nextFilters);
    setPage(1);
  };

  const handleChange = (field: keyof typeof defaultForm, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setForm(defaultForm);
    setEditing(null);
  };

  const openCreate = () => {
    resetForm();
    setFormOpen(true);
  };

  const createPayload = useMemo(
    () => ({
      title: form.title,
      description: form.description || undefined,
      status: form.status || undefined,
      severity: form.severity || undefined,
      category: form.category || undefined,
      occurred_at: toIso(form.occurred_at),
      resolved_at: toIso(form.resolved_at)
    }),
    [form]
  );

  const updatePayload = useMemo(
    () => ({
      title: form.title || undefined,
      description: form.description || undefined,
      status: form.status || undefined,
      severity: form.severity || undefined,
      category: form.category || undefined,
      occurred_at: toIso(form.occurred_at),
      resolved_at: toIso(form.resolved_at)
    }),
    [form]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      if (editing) {
        await hotelIncidentsApi.update(editing.id, updatePayload);
        toast.success("Incident updated");
      } else {
        await hotelIncidentsApi.create(createPayload);
        toast.success("Incident created");
      }
      setFormOpen(false);
      resetForm();
      await fetchIncidents(page, filters);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save incident";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (incident: Incident) => {
    setEditing(incident);
    setForm({
      title: incident.title,
      description: incident.description ?? "",
      status: incident.status,
      severity: incident.severity,
      category: incident.category ?? "",
      occurred_at: toDateInput(incident.occurred_at),
      resolved_at: toDateInput(incident.resolved_at)
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await hotelIncidentsApi.remove(pendingDelete.id);
      toast.success("Incident deleted");
      setPendingDelete(null);
      await fetchIncidents(page, filters);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete incident";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <PermissionGuard
      permission="hotel:incidents:read"
      fallback={<AccessDeniedState message="You do not have permission to view incidents." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Incidents Record"
          description="Track maintenance, guest issues, and safety incidents."
          count={total}
          countLabel="Incidents"
          rightSlot={
            <PermissionGuard permission="hotel:incidents:create">
              <Button variant="primary" onClick={openCreate}>
                Log Incident
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Incident Log"
          table={
            <>
              <DataToolbar
                search={searchInput}
                onSearchChange={(value) => setSearchInput(value)}
                onSearchSubmit={handleApplyFilters}
                searchPlaceholder="Search title or description"
                filtersSlot={
                  <div className="flex flex-wrap items-end gap-2">
                    <div className="min-w-[140px] flex-1">
                      <label className="mb-1.5 block text-xs text-[color:var(--color-text-muted)]">Status</label>
                      <TextInput
                        value={statusInput}
                        onChange={(event) => setStatusInput(event.target.value)}
                        placeholder="open"
                      />
                    </div>
                    <div className="min-w-[140px] flex-1">
                      <label className="mb-1.5 block text-xs text-[color:var(--color-text-muted)]">Severity</label>
                      <TextInput
                        value={severityInput}
                        onChange={(event) => setSeverityInput(event.target.value)}
                        placeholder="medium"
                      />
                    </div>
                  </div>
                }
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchIncidents(page, filters)}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading incidents..." className="mt-3" />
              ) : incidents.length === 0 ? (
                <EmptyState description="No incidents logged yet." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      {
                        key: "title",
                        header: "Title",
                        cellClassName: "font-medium",
                        render: (incident) => incident.title
                      },
                      { key: "status", header: "Status", render: (incident) => incident.status },
                      { key: "severity", header: "Severity", render: (incident) => incident.severity },
                      {
                        key: "category",
                        header: "Category",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (incident) => incident.category ?? "-"
                      },
                      {
                        key: "occurred",
                        header: "Occurred",
                        render: (incident) =>
                          incident.occurred_at ? new Date(incident.occurred_at).toLocaleDateString() : "-"
                      },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (incident) => (
                          <TableActionCell>
                            <PermissionGuard permission="hotel:incidents:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(incident)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="hotel:incidents:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(incident)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={incidents}
                    rowKey={(incident) => incident.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "hotel:incidents:update" : "hotel:incidents:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Incident" : "Log Incident"}
          description="Capture incident details for tracking and audit."
          maxWidthClassName="max-w-5xl"
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Title" required className="md:col-span-2">
              <TextInput
                value={form.title}
                onChange={(event) => handleChange("title", event.target.value)}
                placeholder="Water leak in room 204"
                required
              />
            </Field>
            <Field label="Description" className="md:col-span-2">
              <TextAreaInput
                value={form.description}
                onChange={(event) => handleChange("description", event.target.value)}
                rows={3}
              />
            </Field>
            <Field label="Status">
              <TextInput
                value={form.status}
                onChange={(event) => handleChange("status", event.target.value)}
                placeholder="open"
              />
            </Field>
            <Field label="Severity">
              <TextInput
                value={form.severity}
                onChange={(event) => handleChange("severity", event.target.value)}
                placeholder="medium"
              />
            </Field>
            <Field label="Category">
              <TextInput
                value={form.category}
                onChange={(event) => handleChange("category", event.target.value)}
                placeholder="maintenance"
              />
            </Field>
            <Field label="Occurred At">
              <TextInput
                type="date"
                value={form.occurred_at}
                onChange={(event) => handleChange("occurred_at", event.target.value)}
              />
            </Field>
            <Field label="Resolved At">
              <TextInput
                type="date"
                value={form.resolved_at}
                onChange={(event) => handleChange("resolved_at", event.target.value)}
              />
            </Field>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create Incident"}
              </Button>
            </div>
          </form>
        </FormModal>
      </PermissionGuard>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        onOpenChange={(open) => {
          if (!open) setPendingDelete(null);
        }}
        title="Delete incident"
        description={
          pendingDelete
            ? `Delete incident \"${pendingDelete.title}\"? This action cannot be undone.`
            : "Delete this incident?"
        }
        confirmText="Delete"
        tone="danger"
        busy={confirmBusy}
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
