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
import { adminPlansApi } from "@/lib/api/admin/plans";
import type { Plan } from "@/lib/types/plans";

const defaultForm = {
  name: "",
  code: "",
  description: "",
  price_cents: 0,
  currency: "USD",
  billing_interval: "monthly",
  is_active: true
};

export default function AdminPlansPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<Plan | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Plan | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchPlans = useCallback(async (nextPage = page) => {
    setLoading(true);
    setError(null);
    try {
      const data = await adminPlansApi.list(nextPage, limit);
      setPlans(data.items);
      setPage(data.pagination.page);
      setTotal(data.pagination.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load plans");
    } finally {
      setLoading(false);
    }
  }, [limit, page]);

  useEffect(() => {
    void fetchPlans(page);
  }, [fetchPlans, page]);

  const handleChange = (field: keyof typeof defaultForm, value: string | number | boolean) => {
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
      code: form.code || undefined,
      description: form.description || undefined,
      price_cents: Number(form.price_cents),
      currency: form.currency || undefined,
      billing_interval: form.billing_interval || undefined,
      is_active: form.is_active
    }),
    [form]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      if (editing) {
        await adminPlansApi.update(editing.id, payload);
        toast.success("Plan updated");
      } else {
        await adminPlansApi.create(payload);
        toast.success("Plan created");
      }
      setFormOpen(false);
      resetForm();
      await fetchPlans(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save plan";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (plan: Plan) => {
    setEditing(plan);
    setForm({
      name: plan.name,
      code: plan.code,
      description: plan.description ?? "",
      price_cents: plan.price_cents,
      currency: plan.currency,
      billing_interval: plan.billing_interval,
      is_active: plan.is_active
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await adminPlansApi.remove(pendingDelete.id);
      toast.success("Plan deleted");
      setPendingDelete(null);
      await fetchPlans(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete plan";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <PermissionGuard
      permission="admin:plans:read"
      fallback={<AccessDeniedState message="You do not have permission to view plans." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Plans"
          description="Manage subscription plans and pricing tiers."
          count={total}
          countLabel="Plans"
          rightSlot={
            <PermissionGuard permission="admin:plans:create">
              <Button variant="primary" onClick={openCreate}>
                Add Plan
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Plan Directory"
          table={
            <>
              <DataToolbar
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchPlans(page)}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading plans..." className="mt-3" />
              ) : plans.length === 0 ? (
                <EmptyState description="No plans created yet." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      { key: "name", header: "Name", cellClassName: "font-medium", render: (plan) => plan.name },
                      {
                        key: "code",
                        header: "Code",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (plan) => plan.code
                      },
                      {
                        key: "price",
                        header: "Price",
                        render: (plan) => `${(plan.price_cents / 100).toFixed(2)} ${plan.currency}`
                      },
                      { key: "interval", header: "Interval", render: (plan) => plan.billing_interval },
                      { key: "status", header: "Status", render: (plan) => (plan.is_active ? "Active" : "Inactive") },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (plan) => (
                          <TableActionCell>
                            <PermissionGuard permission="admin:plans:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(plan)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="admin:plans:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(plan)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={plans}
                    rowKey={(plan) => plan.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "admin:plans:update" : "admin:plans:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Plan" : "Create Plan"}
          description="Define pricing, billing cadence, and availability."
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Plan Name" required>
              <TextInput
                value={form.name}
                onChange={(event) => handleChange("name", event.target.value)}
                placeholder="Pro"
                required
              />
            </Field>
            <Field label="Code">
              <TextInput
                value={form.code}
                onChange={(event) => handleChange("code", event.target.value)}
                placeholder="pro"
              />
            </Field>
            <Field label="Price (cents)">
              <TextInput
                type="number"
                min={0}
                value={form.price_cents}
                onChange={(event) => handleChange("price_cents", Number(event.target.value))}
                placeholder="9900"
              />
            </Field>
            <Field label="Currency">
              <TextInput
                value={form.currency}
                onChange={(event) => handleChange("currency", event.target.value)}
                placeholder="USD"
              />
            </Field>
            <Field label="Billing Interval">
              <TextInput
                value={form.billing_interval}
                onChange={(event) => handleChange("billing_interval", event.target.value)}
                placeholder="monthly"
              />
            </Field>
            <div className="flex items-center gap-2 pt-8">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => handleChange("is_active", event.target.checked)}
              />
              <span className="text-sm">Active</span>
            </div>
            <Field label="Description" className="md:col-span-2">
              <TextAreaInput
                value={form.description}
                onChange={(event) => handleChange("description", event.target.value)}
                placeholder="Best for growing hotel groups"
                rows={3}
              />
            </Field>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create Plan"}
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
        title="Delete plan"
        description={pendingDelete ? `Delete ${pendingDelete.name}? This action cannot be undone.` : "Delete this plan?"}
        confirmText="Delete"
        busy={confirmBusy}
        tone="danger"
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
