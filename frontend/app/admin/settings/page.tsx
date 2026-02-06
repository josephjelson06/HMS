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
import { adminSettingsApi } from "@/lib/api/admin/settings";
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

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<Setting | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Setting | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchSettings = useCallback(async (nextPage = page) => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminSettingsApi.list(nextPage, limit);
      setSettings(data.items);
      setPage(data.pagination.page);
      setTotal(data.pagination.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }, [limit, page]);

  useEffect(() => {
    void fetchSettings(page);
  }, [fetchSettings, page]);

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
        await adminSettingsApi.update(editing.id, {
          value: parsedValue,
          description: form.description || undefined
        });
        toast.success("Setting updated");
      } else {
        await adminSettingsApi.create({
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
      await adminSettingsApi.remove(pendingDelete.id);
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
      permission="admin:settings:read"
      fallback={<AccessDeniedState message="You do not have permission to view platform settings." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Settings"
          description="Configure platform-wide values and toggles."
          count={total}
          countLabel="Settings"
          rightSlot={
            <PermissionGuard permission="admin:settings:create">
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
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchSettings(page)}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading settings..." className="mt-3" />
              ) : settings.length === 0 ? (
                <EmptyState description="No settings created yet." />
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
                            <PermissionGuard permission="admin:settings:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(setting)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="admin:settings:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(setting)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={settings}
                    rowKey={(setting) => setting.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "admin:settings:update" : "admin:settings:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Setting" : "Create Setting"}
          description="Update JSON-based platform configuration entries."
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Key" required>
              <TextInput
                value={form.key}
                onChange={(event) => handleChange("key", event.target.value)}
                placeholder="feature.flags"
                required
                disabled={Boolean(editing)}
              />
            </Field>
            <Field label="Description">
              <TextInput
                value={form.description}
                onChange={(event) => handleChange("description", event.target.value)}
                placeholder="Feature flag configuration"
              />
            </Field>
            <Field label="Value (JSON)" className="md:col-span-2">
              <TextAreaInput
                value={form.value}
                onChange={(event) => handleChange("value", event.target.value)}
                className="font-mono"
                rows={5}
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
        description={pendingDelete ? `Delete setting \"${pendingDelete.key}\"? This action cannot be undone.` : "Delete setting?"}
        confirmText="Delete"
        busy={confirmBusy}
        tone="danger"
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
