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
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/primitives/button";
import { DataToolbar } from "@/components/ui/primitives/data-toolbar";
import { Field } from "@/components/ui/primitives/field";
import { Pagination } from "@/components/ui/primitives/pagination";
import { TextInput } from "@/components/ui/primitives/text-input";
import { hotelKiosksApi } from "@/lib/api/hotel/kiosks";
import { useAuth } from "@/lib/hooks/use-auth";
import type { Kiosk } from "@/lib/types/kiosks";

const defaultForm = {
  name: "",
  location: "",
  status: "active",
  device_id: ""
};

export default function HotelKiosksPage() {
  const { tenant, user } = useAuth();
  const tenantId = tenant?.id ?? user?.tenant_id ?? "";

  const [kiosks, setKiosks] = useState<Kiosk[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<Kiosk | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Kiosk | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [issuedToken, setIssuedToken] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchKiosks = useCallback(async (nextPage: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await hotelKiosksApi.list(nextPage, limit);
      setKiosks(data.items);
      setPage(data.pagination.page);
      setTotal(data.pagination.total);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load kiosks";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    void fetchKiosks(page);
  }, [fetchKiosks, page]);

  const visibleKiosks = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return kiosks;

    return kiosks.filter((kiosk) => {
      return (
        kiosk.name.toLowerCase().includes(term) ||
        (kiosk.location ?? "").toLowerCase().includes(term) ||
        kiosk.status.toLowerCase().includes(term) ||
        (kiosk.device_id ?? "").toLowerCase().includes(term)
      );
    });
  }, [kiosks, search]);

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
      tenant_id: tenantId,
      name: form.name,
      location: form.location || undefined,
      status: form.status || undefined,
      device_id: form.device_id || undefined
    }),
    [form, tenantId]
  );

  const updatePayload = useMemo(
    () => ({
      name: form.name || undefined,
      location: form.location || undefined,
      status: form.status || undefined,
      device_id: form.device_id || undefined
    }),
    [form]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIssuedToken(null);

    if (!editing && !tenantId) {
      setError("Missing tenant context. Please re-login and try again.");
      return;
    }

    try {
      const response = editing
        ? await hotelKiosksApi.update(editing.id, updatePayload)
        : await hotelKiosksApi.create(createPayload);

      if (response.issued_token) {
        setIssuedToken(response.issued_token);
      }

      toast.success(editing ? "Kiosk updated" : "Kiosk created");
      setFormOpen(false);
      resetForm();
      await fetchKiosks(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save kiosk";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (kiosk: Kiosk) => {
    setEditing(kiosk);
    setForm({
      name: kiosk.name,
      location: kiosk.location ?? "",
      status: kiosk.status,
      device_id: kiosk.device_id ?? ""
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await hotelKiosksApi.remove(pendingDelete.id);
      toast.success("Kiosk deleted");
      setPendingDelete(null);
      await fetchKiosks(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete kiosk";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  const handleRotateToken = async (kiosk: Kiosk) => {
    setError(null);
    setIssuedToken(null);
    try {
      const response = await hotelKiosksApi.update(kiosk.id, { rotate_token: true });
      if (response.issued_token) {
        setIssuedToken(response.issued_token);
        toast.success("Kiosk token rotated");
      }
      await fetchKiosks(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to rotate token";
      setError(message);
      toast.error(message);
    }
  };

  return (
    <PermissionGuard
      permission="hotel:kiosks:read"
      fallback={<AccessDeniedState message="You do not have permission to manage kiosks." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Kiosk Settings"
          description="Manage self-registration devices for your hotel."
          count={total}
          countLabel="Kiosks"
          rightSlot={
            <PermissionGuard permission="hotel:kiosks:create">
              <Button variant="primary" onClick={openCreate}>
                Add Kiosk
              </Button>
            </PermissionGuard>
          }
        />

        {issuedToken ? (
          <GlassCard className="border border-emerald-400/40 p-6">
            <h3 className="text-lg">New Kiosk Token</h3>
            <p className="mt-2 text-sm text-[color:var(--color-text-muted)]">
              Copy this token now. It will not be shown again.
            </p>
            <div className="mt-3 rounded-xl border border-white/20 bg-white/5 px-4 py-3 font-mono text-sm">
              {issuedToken}
            </div>
          </GlassCard>
        ) : null}

        <DirectoryTableCard
          title="Kiosk Directory"
          table={
            <>
              <DataToolbar
                search={search}
                onSearchChange={(value) => setSearch(value)}
                searchPlaceholder="Search kiosk name, location, status, device"
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchKiosks(page)}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading kiosks..." className="mt-3" />
              ) : visibleKiosks.length === 0 ? (
                <EmptyState description="No kiosks found for this page/filter." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      { key: "name", header: "Name", cellClassName: "font-medium", render: (kiosk) => kiosk.name },
                      { key: "status", header: "Status", render: (kiosk) => kiosk.status },
                      {
                        key: "device",
                        header: "Device ID",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (kiosk) => kiosk.device_id ?? "-"
                      },
                      {
                        key: "token",
                        header: "Token",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (kiosk) => (kiosk.token_last4 ? `****${kiosk.token_last4}` : "-")
                      },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (kiosk) => (
                          <TableActionCell>
                            <PermissionGuard permission="hotel:kiosks:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(kiosk)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="hotel:kiosks:update">
                              <Button size="sm" variant="secondary" onClick={() => void handleRotateToken(kiosk)}>
                                Rotate Token
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="hotel:kiosks:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(kiosk)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={visibleKiosks}
                    rowKey={(kiosk) => kiosk.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "hotel:kiosks:update" : "hotel:kiosks:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Kiosk" : "Add Kiosk"}
          description="Register or update a hotel kiosk device."
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Kiosk Name" required>
              <TextInput
                value={form.name}
                onChange={(event) => handleChange("name", event.target.value)}
                placeholder="Lobby Check-in"
                required
              />
            </Field>
            <Field label="Location">
              <TextInput
                value={form.location}
                onChange={(event) => handleChange("location", event.target.value)}
                placeholder="Main lobby"
              />
            </Field>
            <Field label="Status">
              <TextInput
                value={form.status}
                onChange={(event) => handleChange("status", event.target.value)}
                placeholder="active"
              />
            </Field>
            <Field label="Device ID">
              <TextInput
                value={form.device_id}
                onChange={(event) => handleChange("device_id", event.target.value)}
                placeholder="kiosk-001"
              />
            </Field>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create Kiosk"}
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
        title="Delete kiosk"
        description={
          pendingDelete
            ? `Delete ${pendingDelete.name}? This action cannot be undone.`
            : "Delete this kiosk?"
        }
        confirmText="Delete"
        tone="danger"
        busy={confirmBusy}
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
