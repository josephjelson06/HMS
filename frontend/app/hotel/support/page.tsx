"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { PermissionGuard } from "@/components/features/auth/permission-guard";
import { PageHeader } from "@/components/layout/primitives/page-header";
import { AccessDeniedState } from "@/components/ui/composed/access-denied-state";
import { DataTable } from "@/components/ui/composed/data-table";
import { DirectoryTableCard } from "@/components/ui/composed/directory-table-card";
import { EmptyState } from "@/components/ui/composed/empty-state";
import { FormModal } from "@/components/ui/composed/form-modal";
import { InlineAlert } from "@/components/ui/composed/inline-alert";
import { Button } from "@/components/ui/primitives/button";
import { DataToolbar } from "@/components/ui/primitives/data-toolbar";
import { Field } from "@/components/ui/primitives/field";
import { Pagination } from "@/components/ui/primitives/pagination";
import { TextAreaInput } from "@/components/ui/primitives/textarea-input";
import { TextInput } from "@/components/ui/primitives/text-input";
import { hotelHelpdeskApi } from "@/lib/api/hotel/helpdesk";
import type { HelpdeskTicket } from "@/lib/types/helpdesk";

const defaultForm = {
  requester_name: "",
  requester_email: "",
  subject: "",
  description: "",
  priority: "normal"
};

const priorityRank: Record<string, number> = {
  critical: 5,
  high: 4,
  urgent: 4,
  normal: 3,
  medium: 3,
  low: 2,
  minor: 1
};

export default function HotelSupportPage() {
  const [tickets, setTickets] = useState<HelpdeskTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(defaultForm);
  const [formOpen, setFormOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(1);
  const [limit] = useState(20);

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await hotelHelpdeskApi.list(200);
      setTickets(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load helpdesk tickets";
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchTickets();
  }, [fetchTickets]);

  const filteredTickets = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return tickets;

    return tickets.filter((ticket) => {
      return (
        ticket.subject.toLowerCase().includes(term) ||
        (ticket.description ?? "").toLowerCase().includes(term) ||
        (ticket.requester_name ?? "").toLowerCase().includes(term) ||
        (ticket.requester_email ?? "").toLowerCase().includes(term) ||
        ticket.status.toLowerCase().includes(term)
      );
    });
  }, [search, tickets]);

  const sortedTickets = useMemo(() => {
    const items = [...filteredTickets];

    if (sort === "priority") {
      items.sort((a, b) => {
        const left = priorityRank[a.priority.toLowerCase()] ?? 0;
        const right = priorityRank[b.priority.toLowerCase()] ?? 0;
        return right - left;
      });
      return items;
    }

    if (sort === "status") {
      items.sort((a, b) => a.status.localeCompare(b.status));
      return items;
    }

    items.sort((a, b) => {
      const left = a.created_at ? new Date(a.created_at).getTime() : 0;
      const right = b.created_at ? new Date(b.created_at).getTime() : 0;
      return sort === "oldest" ? left - right : right - left;
    });

    return items;
  }, [filteredTickets, sort]);

  const total = sortedTickets.length;
  const totalPages = Math.max(1, Math.ceil(total / limit));

  useEffect(() => {
    setPage(1);
  }, [search, sort]);

  useEffect(() => {
    if (page > totalPages) {
      setPage(totalPages);
    }
  }, [page, totalPages]);

  const pagedTickets = useMemo(() => {
    const start = (page - 1) * limit;
    const end = start + limit;
    return sortedTickets.slice(start, end);
  }, [limit, page, sortedTickets]);

  const handleChange = (field: keyof typeof defaultForm, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const resetForm = () => {
    setForm(defaultForm);
  };

  const payload = useMemo(
    () => ({
      requester_name: form.requester_name || undefined,
      requester_email: form.requester_email || undefined,
      subject: form.subject,
      description: form.description || undefined,
      priority: form.priority || undefined
    }),
    [form]
  );

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    try {
      await hotelHelpdeskApi.create(payload);
      toast.success("Support ticket submitted");
      resetForm();
      setFormOpen(false);
      await fetchTickets();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to submit ticket";
      setError(message);
      toast.error(message);
    }
  };

  return (
    <PermissionGuard
      permission="hotel:support:read"
      fallback={<AccessDeniedState message="You do not have permission to access support tickets." />}
    >
      <div className="space-y-6">
        <PageHeader
          title="Help & Support"
          description="Submit and track support requests for your hotel."
          count={total}
          countLabel="Tickets"
          rightSlot={
            <PermissionGuard permission="hotel:support:create">
              <Button variant="primary" onClick={() => setFormOpen(true)}>
                Create Ticket
              </Button>
            </PermissionGuard>
          }
        />

        <DirectoryTableCard
          title="Recent Tickets"
          table={
            <>
              <DataToolbar
                search={search}
                onSearchChange={(value) => setSearch(value)}
                searchPlaceholder="Search subject, requester, status"
                sortValue={sort}
                onSortChange={(value) => setSort(value)}
                sortOptions={[
                  { value: "newest", label: "Newest" },
                  { value: "oldest", label: "Oldest" },
                  { value: "priority", label: "Priority" },
                  { value: "status", label: "Status" }
                ]}
                actionsSlot={
                  <Button variant="secondary" onClick={() => void fetchTickets()}>
                    Refresh
                  </Button>
                }
              />
              {error ? <InlineAlert tone="error" message={error} className="mt-3" /> : null}
              {loading ? (
                <InlineAlert tone="info" message="Loading tickets..." className="mt-3" />
              ) : pagedTickets.length === 0 ? (
                <EmptyState description="No tickets found for this page/filter." />
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
                      { key: "status", header: "Status", render: (ticket) => ticket.status },
                      { key: "priority", header: "Priority", render: (ticket) => ticket.priority },
                      {
                        key: "requester",
                        header: "Requester",
                        render: (ticket) => ticket.requester_name || ticket.requester_email || "-"
                      },
                      {
                        key: "created",
                        header: "Created",
                        render: (ticket) =>
                          ticket.created_at ? new Date(ticket.created_at).toLocaleDateString() : "-"
                      }
                    ]}
                    rows={pagedTickets}
                    rowKey={(ticket) => ticket.id}
                  />
                </div>
              )}
            </>
          }
          footer={<Pagination page={page} limit={limit} total={total} onPageChange={setPage} />}
        />
      </div>

      <PermissionGuard permission="hotel:support:create">
        <FormModal
          open={formOpen}
          onOpenChange={(open) => {
            setFormOpen(open);
            if (!open) resetForm();
          }}
          title="Create Support Ticket"
          description="Send a request to platform support."
          maxWidthClassName="max-w-4xl"
        >
          <form className="grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
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
                placeholder="jane@hotel.com"
              />
            </Field>
            <Field label="Subject" required className="md:col-span-2">
              <TextInput
                value={form.subject}
                onChange={(event) => handleChange("subject", event.target.value)}
                placeholder="POS integration issue"
                required
              />
            </Field>
            <Field label="Description" className="md:col-span-2">
              <TextAreaInput
                value={form.description}
                onChange={(event) => handleChange("description", event.target.value)}
                rows={4}
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
                Submit Ticket
              </Button>
            </div>
          </form>
        </FormModal>
      </PermissionGuard>
    </PermissionGuard>
  );
}
