"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
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
import { TextInput } from "@/components/ui/primitives/text-input";
import { hotelAdminApi } from "@/lib/api/admin/hotels";
import { useAuth } from "@/lib/hooks/use-auth";
import type { Hotel } from "@/lib/types/tenant";

const defaultForm = {
  name: "",
  slug: "",
  status: "active",
  subscription_tier: ""
};

export default function HotelRegistryPage() {
  const router = useRouter();
  const { startImpersonation } = useAuth();

  const [hotels, setHotels] = useState<Hotel[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<Hotel | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Hotel | null>(null);
  const [pendingImpersonation, setPendingImpersonation] = useState<Hotel | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [impersonatingHotelId, setImpersonatingHotelId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchHotels = useCallback(async (nextPage = page) => {
    setLoading(true);
    setError(null);
    try {
      const data = await hotelAdminApi.list(nextPage, limit);
      setHotels(data.items);
      setPage(data.pagination.page);
      setTotal(data.pagination.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load hotels");
    } finally {
      setLoading(false);
    }
  }, [limit, page]);

  useEffect(() => {
    void fetchHotels(page);
  }, [fetchHotels, page]);

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

  const payload = useMemo(
    () => ({
      name: form.name,
      slug: form.slug || undefined,
      status: form.status || undefined,
      subscription_tier: form.subscription_tier || undefined
    }),
    [form]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      if (editing) {
        await hotelAdminApi.update(editing.id, payload);
        toast.success("Hotel updated");
      } else {
        await hotelAdminApi.create(payload);
        toast.success("Hotel created");
      }
      setFormOpen(false);
      resetForm();
      await fetchHotels(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save hotel";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (hotel: Hotel) => {
    setEditing(hotel);
    setForm({
      name: hotel.name,
      slug: hotel.slug,
      status: hotel.status,
      subscription_tier: hotel.subscription_tier ?? ""
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await hotelAdminApi.remove(pendingDelete.id);
      toast.success("Hotel deleted");
      setPendingDelete(null);
      await fetchHotels(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete hotel";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  const confirmImpersonation = async () => {
    if (!pendingImpersonation) return;
    setError(null);
    setConfirmBusy(true);
    setImpersonatingHotelId(pendingImpersonation.id);
    try {
      await startImpersonation({ tenant_id: pendingImpersonation.id });
      toast.success(`Impersonating ${pendingImpersonation.name}`);
      router.push("/hotel/dashboard");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to start impersonation";
      setError(message);
      toast.error(message);
      setImpersonatingHotelId(null);
    } finally {
      setConfirmBusy(false);
      setPendingImpersonation(null);
    }
  };

  return (
    <PermissionGuard
      permission="admin:hotels:read"
      fallback={<AccessDeniedState message="You do not have permission to view the hotel registry." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Hotel Registry"
          description="Manage tenants and onboard new hotels to the platform."
          count={total}
          countLabel="Hotels"
          rightSlot={
            <PermissionGuard permission="admin:hotels:create">
              <Button variant="primary" onClick={openCreate}>
                Add Hotel
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Hotel Directory"
          table={
            <>
              <DataToolbar
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchHotels(page)}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading hotels..." className="mt-3" />
              ) : hotels.length === 0 ? (
                <EmptyState description="No hotels created yet." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      {
                        key: "name",
                        header: "Name",
                        cellClassName: "font-medium",
                        render: (hotel) => hotel.name
                      },
                      {
                        key: "slug",
                        header: "Slug",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (hotel) => hotel.slug
                      },
                      {
                        key: "status",
                        header: "Status",
                        render: (hotel) => hotel.status
                      },
                      {
                        key: "tier",
                        header: "Tier",
                        render: (hotel) => hotel.subscription_tier ?? "-"
                      },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (hotel) => (
                          <TableActionCell>
                            <PermissionGuard permission="admin:hotels:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(hotel)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="admin:hotels:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(hotel)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="admin:impersonation:start">
                              <Button
                                size="sm"
                                variant="secondary"
                                onClick={() => setPendingImpersonation(hotel)}
                                disabled={impersonatingHotelId === hotel.id}
                              >
                                {impersonatingHotelId === hotel.id ? "Starting..." : "Impersonate"}
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={hotels}
                    rowKey={(hotel) => hotel.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "admin:hotels:update" : "admin:hotels:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Hotel" : "Add Hotel"}
          description="Create or update tenant profile details."
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Hotel Name" required>
              <TextInput
                value={form.name}
                onChange={(event) => handleChange("name", event.target.value)}
                placeholder="Oceanview Suites"
              />
            </Field>
            <Field label="Slug">
              <TextInput
                value={form.slug}
                onChange={(event) => handleChange("slug", event.target.value)}
                placeholder="oceanview-suites"
              />
            </Field>
            <Field label="Status">
              <TextInput
                value={form.status}
                onChange={(event) => handleChange("status", event.target.value)}
                placeholder="active"
              />
            </Field>
            <Field label="Subscription Tier">
              <TextInput
                value={form.subscription_tier}
                onChange={(event) => handleChange("subscription_tier", event.target.value)}
                placeholder="premium"
              />
            </Field>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create Hotel"}
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
        title="Delete hotel"
        description={
          pendingDelete
            ? `Delete ${pendingDelete.name}? This action cannot be undone.`
            : "Delete this hotel?"
        }
        confirmText="Delete"
        busy={confirmBusy}
        tone="danger"
        onConfirm={confirmDelete}
      />

      <ConfirmDialog
        open={Boolean(pendingImpersonation)}
        onOpenChange={(open) => {
          if (!open) setPendingImpersonation(null);
        }}
        title="Start impersonation"
        description={
          pendingImpersonation
            ? `Start impersonation session for ${pendingImpersonation.name}?`
            : "Start impersonation session?"
        }
        confirmText="Start"
        tone="primary"
        busy={confirmBusy}
        onConfirm={confirmImpersonation}
      />
    </PermissionGuard>
  );
}
