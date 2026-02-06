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
import { SelectInput } from "@/components/ui/primitives/select-input";
import { TextInput } from "@/components/ui/primitives/text-input";
import { hotelAdminApi } from "@/lib/api/admin/hotels";
import { adminPlansApi } from "@/lib/api/admin/plans";
import { adminSubscriptionsApi } from "@/lib/api/admin/subscriptions";
import type { Plan } from "@/lib/types/plans";
import type { Subscription } from "@/lib/types/subscriptions";
import type { Hotel } from "@/lib/types/tenant";

const defaultForm = {
  tenant_id: "",
  plan_id: "",
  status: "active",
  start_date: "",
  current_period_end: "",
  cancel_at: ""
};

const toIso = (value: string) => {
  if (!value) return undefined;
  const date = new Date(value);
  return isNaN(date.getTime()) ? undefined : date.toISOString();
};

const toDateInput = (value?: string | null) => {
  if (!value) return "";
  return value.slice(0, 10);
};

export default function AdminSubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [hotels, setHotels] = useState<Hotel[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<Subscription | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Subscription | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchData = useCallback(async (nextPage = page) => {
    setLoading(true);
    setError(null);
    try {
      const [subscriptionsData, hotelsData, plansData] = await Promise.all([
        adminSubscriptionsApi.list(nextPage, limit),
        hotelAdminApi.list(1, 100),
        adminPlansApi.list(1, 100)
      ]);
      setSubscriptions(subscriptionsData.items);
      setHotels(hotelsData.items);
      setPlans(plansData.items);
      setPage(subscriptionsData.pagination.page);
      setTotal(subscriptionsData.pagination.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load subscriptions");
    } finally {
      setLoading(false);
    }
  }, [limit, page]);

  useEffect(() => {
    void fetchData(page);
  }, [fetchData, page]);

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
      tenant_id: form.tenant_id,
      plan_id: form.plan_id,
      status: form.status,
      start_date: toIso(form.start_date),
      current_period_end: toIso(form.current_period_end),
      cancel_at: toIso(form.cancel_at)
    }),
    [form]
  );

  const updatePayload = useMemo(
    () => ({
      tenant_id: form.tenant_id || undefined,
      plan_id: form.plan_id || undefined,
      status: form.status || undefined,
      current_period_end: toIso(form.current_period_end),
      cancel_at: toIso(form.cancel_at)
    }),
    [form]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      if (editing) {
        await adminSubscriptionsApi.update(editing.id, updatePayload);
        toast.success("Subscription updated");
      } else {
        await adminSubscriptionsApi.create(createPayload);
        toast.success("Subscription created");
      }
      setFormOpen(false);
      resetForm();
      await fetchData(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save subscription";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (subscription: Subscription) => {
    setEditing(subscription);
    setForm({
      tenant_id: subscription.tenant_id,
      plan_id: subscription.plan_id,
      status: subscription.status,
      start_date: toDateInput(subscription.start_date),
      current_period_end: toDateInput(subscription.current_period_end),
      cancel_at: toDateInput(subscription.cancel_at)
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await adminSubscriptionsApi.remove(pendingDelete.id);
      toast.success("Subscription deleted");
      setPendingDelete(null);
      await fetchData(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete subscription";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <PermissionGuard
      permission="admin:subscriptions:read"
      fallback={<AccessDeniedState message="You do not have permission to view subscriptions." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Subscriptions"
          description="Manage hotel subscription lifecycle and plan assignment."
          count={total}
          countLabel="Subscriptions"
          rightSlot={
            <PermissionGuard permission="admin:subscriptions:create">
              <Button variant="primary" onClick={openCreate}>
                Add Subscription
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Subscription Directory"
          table={
            <>
              <DataToolbar
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchData(page)}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading subscriptions..." className="mt-3" />
              ) : subscriptions.length === 0 ? (
                <EmptyState description="No subscriptions created yet." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      {
                        key: "hotel",
                        header: "Hotel",
                        cellClassName: "font-medium",
                        render: (subscription) => subscription.tenant_name ?? subscription.tenant_id
                      },
                      {
                        key: "plan",
                        header: "Plan",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (subscription) =>
                          subscription.plan_name ?? subscription.plan_code ?? subscription.plan_id
                      },
                      { key: "status", header: "Status", render: (subscription) => subscription.status },
                      {
                        key: "period_end",
                        header: "Period End",
                        render: (subscription) =>
                          subscription.current_period_end
                            ? new Date(subscription.current_period_end).toLocaleDateString()
                            : "-"
                      },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (subscription) => (
                          <TableActionCell>
                            <PermissionGuard permission="admin:subscriptions:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(subscription)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="admin:subscriptions:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(subscription)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={subscriptions}
                    rowKey={(subscription) => subscription.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "admin:subscriptions:update" : "admin:subscriptions:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Subscription" : "Create Subscription"}
          description="Link tenant plans and billing cycle dates."
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Hotel" required>
              <SelectInput value={form.tenant_id} onChange={(event) => handleChange("tenant_id", event.target.value)} required>
                <option value="">Select hotel</option>
                {hotels.map((hotel) => (
                  <option key={hotel.id} value={hotel.id}>
                    {hotel.name}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Plan" required>
              <SelectInput value={form.plan_id} onChange={(event) => handleChange("plan_id", event.target.value)} required>
                <option value="">Select plan</option>
                {plans.map((plan) => (
                  <option key={plan.id} value={plan.id}>
                    {plan.name}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Status">
              <TextInput
                value={form.status}
                onChange={(event) => handleChange("status", event.target.value)}
                placeholder="active"
              />
            </Field>
            <Field label="Start Date">
              <TextInput
                type="date"
                value={form.start_date}
                onChange={(event) => handleChange("start_date", event.target.value)}
                disabled={Boolean(editing)}
              />
            </Field>
            <Field label="Current Period End">
              <TextInput
                type="date"
                value={form.current_period_end}
                onChange={(event) => handleChange("current_period_end", event.target.value)}
              />
            </Field>
            <Field label="Cancel At">
              <TextInput
                type="date"
                value={form.cancel_at}
                onChange={(event) => handleChange("cancel_at", event.target.value)}
              />
            </Field>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create Subscription"}
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
        title="Delete subscription"
        description="Delete this subscription? This action cannot be undone."
        confirmText="Delete"
        busy={confirmBusy}
        tone="danger"
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
