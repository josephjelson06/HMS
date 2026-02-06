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
import { TextAreaInput } from "@/components/ui/primitives/textarea-input";
import { TextInput } from "@/components/ui/primitives/text-input";
import { hotelAdminApi } from "@/lib/api/admin/hotels";
import { adminInvoicesApi } from "@/lib/api/admin/invoices";
import { adminSubscriptionsApi } from "@/lib/api/admin/subscriptions";
import type { Invoice } from "@/lib/types/invoices";
import type { Subscription } from "@/lib/types/subscriptions";
import type { Hotel } from "@/lib/types/tenant";

const defaultForm = {
  tenant_id: "",
  subscription_id: "",
  invoice_number: "",
  status: "issued",
  amount_cents: 0,
  currency: "USD",
  issued_at: "",
  due_at: "",
  paid_at: "",
  notes: ""
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

export default function AdminInvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [hotels, setHotels] = useState<Hotel[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<Invoice | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Invoice | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchData = useCallback(async (nextPage = page) => {
    setLoading(true);
    setError(null);
    try {
      const [invoiceData, hotelsData, subscriptionsData] = await Promise.all([
        adminInvoicesApi.list(nextPage, limit),
        hotelAdminApi.list(1, 100),
        adminSubscriptionsApi.list(1, 100)
      ]);
      setInvoices(invoiceData.items);
      setHotels(hotelsData.items);
      setSubscriptions(subscriptionsData.items);
      setPage(invoiceData.pagination.page);
      setTotal(invoiceData.pagination.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load invoices");
    } finally {
      setLoading(false);
    }
  }, [limit, page]);

  useEffect(() => {
    void fetchData(page);
  }, [fetchData, page]);

  const handleChange = (field: keyof typeof defaultForm, value: string | number) => {
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

  const createPayload = useMemo(() => {
    return {
      tenant_id: form.tenant_id,
      subscription_id: form.subscription_id,
      invoice_number: form.invoice_number || undefined,
      status: form.status,
      amount_cents: Number(form.amount_cents),
      currency: form.currency || undefined,
      issued_at: toIso(form.issued_at),
      due_at: toIso(form.due_at),
      paid_at: toIso(form.paid_at),
      notes: form.notes || undefined
    };
  }, [form]);

  const updatePayload = useMemo(() => {
    return {
      tenant_id: form.tenant_id || undefined,
      subscription_id: form.subscription_id || undefined,
      invoice_number: form.invoice_number || undefined,
      status: form.status || undefined,
      amount_cents: Number(form.amount_cents),
      currency: form.currency || undefined,
      issued_at: toIso(form.issued_at),
      due_at: toIso(form.due_at),
      paid_at: toIso(form.paid_at),
      notes: form.notes || undefined
    };
  }, [form]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      if (editing) {
        await adminInvoicesApi.update(editing.id, updatePayload);
        toast.success("Invoice updated");
      } else {
        await adminInvoicesApi.create(createPayload);
        toast.success("Invoice created");
      }
      setFormOpen(false);
      resetForm();
      await fetchData(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save invoice";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (invoice: Invoice) => {
    setEditing(invoice);
    setForm({
      tenant_id: invoice.tenant_id,
      subscription_id: invoice.subscription_id,
      invoice_number: invoice.invoice_number,
      status: invoice.status,
      amount_cents: invoice.amount_cents,
      currency: invoice.currency,
      issued_at: toDateInput(invoice.issued_at),
      due_at: toDateInput(invoice.due_at),
      paid_at: toDateInput(invoice.paid_at),
      notes: invoice.notes ?? ""
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await adminInvoicesApi.remove(pendingDelete.id);
      toast.success("Invoice deleted");
      setPendingDelete(null);
      await fetchData(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete invoice";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <PermissionGuard
      permission="admin:invoices:read"
      fallback={<AccessDeniedState message="You do not have permission to view invoices." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Invoices"
          description="Issue invoices for hotel subscriptions and track billing status."
          count={total}
          countLabel="Invoices"
          rightSlot={
            <PermissionGuard permission="admin:invoices:create">
              <Button variant="primary" onClick={openCreate}>
                Add Invoice
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Invoice Directory"
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
                <InlineAlert tone="info" message="Loading invoices..." className="mt-3" />
              ) : invoices.length === 0 ? (
                <EmptyState description="No invoices created yet." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      {
                        key: "invoice",
                        header: "Invoice",
                        cellClassName: "font-medium",
                        render: (invoice) => invoice.invoice_number
                      },
                      {
                        key: "hotel",
                        header: "Hotel",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (invoice) => invoice.tenant_name ?? invoice.tenant_id
                      },
                      {
                        key: "plan",
                        header: "Plan",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (invoice) => invoice.plan_name ?? invoice.plan_code ?? "-"
                      },
                      {
                        key: "amount",
                        header: "Amount",
                        render: (invoice) => `${(invoice.amount_cents / 100).toFixed(2)} ${invoice.currency}`
                      },
                      { key: "status", header: "Status", render: (invoice) => invoice.status },
                      {
                        key: "due",
                        header: "Due",
                        render: (invoice) => (invoice.due_at ? new Date(invoice.due_at).toLocaleDateString() : "-")
                      },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (invoice) => (
                          <TableActionCell>
                            <PermissionGuard permission="admin:invoices:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(invoice)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="admin:invoices:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(invoice)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={invoices}
                    rowKey={(invoice) => invoice.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "admin:invoices:update" : "admin:invoices:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Invoice" : "Create Invoice"}
          description="Create invoice records and due dates for tenant billing."
          maxWidthClassName="max-w-5xl"
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Hotel" required>
              <SelectInput
                value={form.tenant_id}
                onChange={(event) => handleChange("tenant_id", event.target.value)}
                required
              >
                <option value="">Select hotel</option>
                {hotels.map((hotel) => (
                  <option key={hotel.id} value={hotel.id}>
                    {hotel.name}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Subscription" required>
              <SelectInput
                value={form.subscription_id}
                onChange={(event) => handleChange("subscription_id", event.target.value)}
                required
              >
                <option value="">Select subscription</option>
                {subscriptions.map((subscription) => (
                  <option key={subscription.id} value={subscription.id}>
                    {subscription.tenant_name ?? subscription.tenant_id} - {subscription.plan_name ?? subscription.plan_code ?? subscription.plan_id}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Invoice Number">
              <TextInput
                value={form.invoice_number}
                onChange={(event) => handleChange("invoice_number", event.target.value)}
                placeholder="INV-0001"
              />
            </Field>
            <Field label="Status">
              <TextInput
                value={form.status}
                onChange={(event) => handleChange("status", event.target.value)}
                placeholder="issued"
              />
            </Field>
            <Field label="Amount (cents)" required>
              <TextInput
                type="number"
                min={0}
                value={form.amount_cents}
                onChange={(event) => handleChange("amount_cents", Number(event.target.value))}
                placeholder="9900"
                required
              />
            </Field>
            <Field label="Currency">
              <TextInput
                value={form.currency}
                onChange={(event) => handleChange("currency", event.target.value)}
                placeholder="USD"
              />
            </Field>
            <Field label="Issued At">
              <TextInput
                type="date"
                value={form.issued_at}
                onChange={(event) => handleChange("issued_at", event.target.value)}
              />
            </Field>
            <Field label="Due At">
              <TextInput
                type="date"
                value={form.due_at}
                onChange={(event) => handleChange("due_at", event.target.value)}
              />
            </Field>
            <Field label="Paid At">
              <TextInput
                type="date"
                value={form.paid_at}
                onChange={(event) => handleChange("paid_at", event.target.value)}
              />
            </Field>
            <Field label="Notes" className="md:col-span-2">
              <TextAreaInput
                value={form.notes}
                onChange={(event) => handleChange("notes", event.target.value)}
                rows={3}
                placeholder="Optional internal notes"
              />
            </Field>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create Invoice"}
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
        title="Delete invoice"
        description={pendingDelete ? `Delete invoice ${pendingDelete.invoice_number}? This action cannot be undone.` : "Delete invoice?"}
        confirmText="Delete"
        busy={confirmBusy}
        tone="danger"
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
