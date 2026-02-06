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
import { adminHelpdeskApi } from "@/lib/api/admin/helpdesk";
import { hotelAdminApi } from "@/lib/api/admin/hotels";
import { adminUsersApi } from "@/lib/api/admin/users";
import type { HelpdeskTicket } from "@/lib/types/helpdesk";
import type { AdminUser } from "@/lib/types/user";
import type { Hotel } from "@/lib/types/tenant";

const defaultForm = {
  tenant_id: "",
  requester_name: "",
  requester_email: "",
  subject: "",
  description: "",
  status: "open",
  priority: "normal",
  assigned_to: ""
};

export default function AdminHelpdeskPage() {
  const [tickets, setTickets] = useState<HelpdeskTicket[]>([]);
  const [hotels, setHotels] = useState<Hotel[]>([]);
  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [editing, setEditing] = useState<HelpdeskTicket | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<HelpdeskTicket | null>(null);
  const [confirmBusy, setConfirmBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);

  const fetchData = useCallback(async (nextPage = page) => {
    setLoading(true);
    setError(null);
    try {
      const [ticketData, hotelData, adminData] = await Promise.all([
        adminHelpdeskApi.list({ page: nextPage, limit }),
        hotelAdminApi.list(1, 100),
        adminUsersApi.list(1, 100)
      ]);
      setTickets(ticketData.items);
      setHotels(hotelData.items);
      setAdmins(adminData.items);
      setPage(ticketData.pagination.page);
      setTotal(ticketData.pagination.total);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load helpdesk tickets");
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

  const payload = useMemo(() => {
    return {
      tenant_id: form.tenant_id || undefined,
      requester_name: form.requester_name || undefined,
      requester_email: form.requester_email || undefined,
      subject: form.subject,
      description: form.description || undefined,
      status: form.status || undefined,
      priority: form.priority || undefined,
      assigned_to: form.assigned_to || undefined
    };
  }, [form]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      if (editing) {
        await adminHelpdeskApi.update(editing.id, payload);
        toast.success("Ticket updated");
      } else {
        await adminHelpdeskApi.create(payload);
        toast.success("Ticket created");
      }
      setFormOpen(false);
      resetForm();
      await fetchData(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to save ticket";
      setError(message);
      toast.error(message);
    }
  };

  const handleEdit = (ticket: HelpdeskTicket) => {
    setEditing(ticket);
    setForm({
      tenant_id: ticket.tenant_id ?? "",
      requester_name: ticket.requester_name ?? "",
      requester_email: ticket.requester_email ?? "",
      subject: ticket.subject,
      description: ticket.description ?? "",
      status: ticket.status,
      priority: ticket.priority,
      assigned_to: ticket.assigned_to ?? ""
    });
    setFormOpen(true);
  };

  const confirmDelete = async () => {
    if (!pendingDelete) return;
    setConfirmBusy(true);
    try {
      await adminHelpdeskApi.remove(pendingDelete.id);
      toast.success("Ticket deleted");
      setPendingDelete(null);
      await fetchData(page);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to delete ticket";
      setError(message);
      toast.error(message);
    } finally {
      setConfirmBusy(false);
    }
  };

  return (
    <PermissionGuard
      permission="admin:helpdesk:read"
      fallback={<AccessDeniedState message="You do not have permission to view HelpDesk tickets." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="HelpDesk"
          description="Track support requests from hotels and internal teams."
          count={total}
          countLabel="Tickets"
          rightSlot={
            <PermissionGuard permission="admin:helpdesk:create">
              <Button variant="primary" onClick={openCreate}>
                Add Ticket
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Ticket Queue"
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
                <InlineAlert tone="info" message="Loading tickets..." className="mt-3" />
              ) : tickets.length === 0 ? (
                <EmptyState description="No tickets created yet." />
              ) : (
                <div className="mt-3">
                  <DataTable
                    columns={[
                      {
                        key: "subject",
                        header: "Subject",
                        cellClassName: "font-medium",
                        render: (ticket) => ticket.subject
                      },
                      {
                        key: "hotel",
                        header: "Hotel",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (ticket) => ticket.tenant_name ?? "Platform"
                      },
                      { key: "status", header: "Status", render: (ticket) => ticket.status },
                      { key: "priority", header: "Priority", render: (ticket) => ticket.priority },
                      {
                        key: "assignee",
                        header: "Assignee",
                        cellClassName: "text-[color:var(--color-text-muted)]",
                        render: (ticket) => ticket.assignee_email ?? "Unassigned"
                      },
                      {
                        key: "actions",
                        header: "Actions",
                        render: (ticket) => (
                          <TableActionCell>
                            <PermissionGuard permission="admin:helpdesk:update">
                              <Button size="sm" variant="outline" onClick={() => handleEdit(ticket)}>
                                Edit
                              </Button>
                            </PermissionGuard>
                            <PermissionGuard permission="admin:helpdesk:delete">
                              <Button size="sm" variant="danger" onClick={() => setPendingDelete(ticket)}>
                                Delete
                              </Button>
                            </PermissionGuard>
                          </TableActionCell>
                        )
                      }
                    ]}
                    rows={tickets}
                    rowKey={(ticket) => ticket.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission={editing ? "admin:helpdesk:update" : "admin:helpdesk:create"}>
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title={editing ? "Edit Ticket" : "Create Ticket"}
          description="Create and assign support tickets for hotels and internal requests."
          maxWidthClassName="max-w-5xl"
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
            <Field label="Hotel">
              <SelectInput
                value={form.tenant_id}
                onChange={(event) => handleChange("tenant_id", event.target.value)}
              >
                <option value="">Platform / Internal</option>
                {hotels.map((hotel) => (
                  <option key={hotel.id} value={hotel.id}>
                    {hotel.name}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Assigned To">
              <SelectInput
                value={form.assigned_to}
                onChange={(event) => handleChange("assigned_to", event.target.value)}
              >
                <option value="">Unassigned</option>
                {admins.map((admin) => (
                  <option key={admin.id} value={admin.id}>
                    {admin.email}
                  </option>
                ))}
              </SelectInput>
            </Field>
            <Field label="Requester Name">
              <TextInput
                value={form.requester_name}
                onChange={(event) => handleChange("requester_name", event.target.value)}
                placeholder="Jane Doe"
              />
            </Field>
            <Field label="Requester Email">
              <TextInput
                value={form.requester_email}
                onChange={(event) => handleChange("requester_email", event.target.value)}
                placeholder="jane@example.com"
              />
            </Field>
            <Field label="Subject" required className="md:col-span-2">
              <TextInput
                value={form.subject}
                onChange={(event) => handleChange("subject", event.target.value)}
                placeholder="Issue with booking sync"
                required
              />
            </Field>
            <Field label="Description" className="md:col-span-2">
              <TextAreaInput
                value={form.description}
                onChange={(event) => handleChange("description", event.target.value)}
                rows={3}
                placeholder="Describe the issue or request"
              />
            </Field>
            <Field label="Status">
              <TextInput
                value={form.status}
                onChange={(event) => handleChange("status", event.target.value)}
                placeholder="open"
              />
            </Field>
            <Field label="Priority">
              <TextInput
                value={form.priority}
                onChange={(event) => handleChange("priority", event.target.value)}
                placeholder="normal"
              />
            </Field>
            <div className="md:col-span-2 flex flex-wrap justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setFormOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary">
                {editing ? "Save Changes" : "Create Ticket"}
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
        title="Delete ticket"
        description={pendingDelete ? `Delete ticket \"${pendingDelete.subject}\"? This action cannot be undone.` : "Delete ticket?"}
        confirmText="Delete"
        busy={confirmBusy}
        tone="danger"
        onConfirm={confirmDelete}
      />
    </PermissionGuard>
  );
}
