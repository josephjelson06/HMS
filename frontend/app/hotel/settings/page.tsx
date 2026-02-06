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
import { hotelSettingsApi } from "@/lib/api/hotel/settings";
import type { Setting } from "@/lib/types/settings";

const defaultForm = {
  key: "",
  value: "{}",
  description: ""
};

const safeStringify = (value: unknown) => {
  try {
    return JSON.stringify(value ?? {}, null, 2);
  } catch {
    return "{}";
  }
};

export default function HotelSettingsPage() {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<Setting | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Setting | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchSettings = useCallback(async (nextPage: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await hotelSettingsApi.list(nextPage, limit);
      setSettings(data.items);
      setPage(data.pagination.page);
      setTotal(data.pagination.total);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load settings";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    void fetchSettings(page);
  }, [fetchSettings, page]);

  const visibleSettings = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return settings;

    return settings.filter((setting) => {
      return (
        setting.key.toLowerCase().includes(term) ||
        (setting.description ?? "").toLowerCase().includes(term)
      );
    });
  }, [search, settings]);

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

  const parsedValue = useMemo(() => {
    try {
      return form.value ? JSON.parse(form.value) : null;
    } catch {
      return null;
    }
  }, [form.value]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (parsedValue === null && form.value.trim() !== "") {
      setError("Value must be valid JSON.");
      return;
    }

    try {
      if (editing) {
        await hotelSettingsApi.update(editing.id, {
          value: parsedValue,
          description: form.description || undefined
        });
        toast.success("Setting updated");
      } else {
        await hotelSettingsApi.create({
          key: form.key,
          value: parsedValue,
          description: form.description || undefined
        });
        toast.success("Setting created");
      }

      setFormOpen(false);
      resetForm();
      await fetchSettings(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save setting";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (setting: Setting) => {
    setEditing(setting);
    setForm({
      key: setting.key,
      value: safeStringify(setting.value),
      description: setting.description ?? ""
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await hotelSettingsApi.remove(pendingDelete.id);
      toast.success("Setting deleted");
      setPendingDelete(null);
      await fetchSettings(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete setting";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <PermissionGuard
      permission="hotel:settings:read"
      fallback={<AccessDeniedState message="You do not have permission to view hotel settings." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Settings"
          description="Configure hotel-level preferences and operational flags."
          count={total}
          countLabel="Settings"
          rightSlot={
            <PermissionGuard permission="hotel:settings:create">
              <Button variant="primary" onClick={openCreate}>
                Add Setting
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Settings Registry"
          table={
            <>
              <DataToolbar
                search={search}
                onSearchChange={(value) => setSearch(value)}
                searchPlaceholder="Search key or description"
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchSettings(page)}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading settings..." className="mt-3" />
              ) : visibleSettings.length === 0 ? (
                <EmptyState description="No settings found for this page/filter." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      { key: "key", header: "Key", cellClassName: "font-medium", render: (setting) => setting.key },
                      {
                        key: "value",
                        header: "Value",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (setting) => (
                          <pre className="whitespace-pre-wrap font-mono text-xs">{safeStringify(setting.value)}</pre>
                        )
                      },
                      { key: "description", header: "Description", render: (setting) => setting.description ?? "-" },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (setting) => (
                          <TableActionCell>
                            <PermissionGuard permission="hotel:settings:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(setting)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="hotel:settings:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(setting)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={visibleSettings}
                    rowKey={(setting) => setting.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "hotel:settings:update" : "hotel:settings:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Setting" : "Create Setting"}
          description="Create or update hotel configuration values."
          maxWidthClassName="max-w-5xl"
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Key" required>
              <TextInput
                value={form.key}
                onChange={(event) => handleChange("key", event.target.value)}
                placeholder="hotel.preferences"
                required
                disabled={Boolean(editing)}
              />
            </Field>
            <Field label="Description">
              <TextInput
                value={form.description}
                onChange={(event) => handleChange("description", event.target.value)}
                placeholder="Hotel preference configuration"
              />
            </Field>
            <Field label="Value (JSON)" className="md:col-span-2">
              <TextAreaInput
                value={form.value}
                onChange={(event) => handleChange("value", event.target.value)}
                className="font-mono"
                rows={8}
                placeholder='{"enabled": true}'
              />
            </Field>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create Setting"}
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
        title="Delete setting"
        description={
          pendingDelete
            ? `Delete setting \"${pendingDelete.key}\"? This action cannot be undone.`
            : "Delete this setting?"
        }
        confirmText="Delete"
        tone="danger"
        busy={confirmBusy}
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
