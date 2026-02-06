export interface HelpdeskTicket {
  id: string;
  tenant_id?: string | null;
  tenant_name?: string | null;
  requester_name?: string | null;
  requester_email?: string | null;
  subject: string;
  description?: string | null;
  status: string;
  priority: string;
  assigned_to?: string | null;
  assignee_email?: string | null;
  closed_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface HelpdeskListResponse {
  items: HelpdeskTicket[];
  pagination: PaginationMeta;
}

export interface HelpdeskCreate {
  tenant_id?: string;
  requester_name?: string;
  requester_email?: string;
  subject: string;
  description?: string;
  status?: string;
  priority?: string;
  assigned_to?: string;
}

export interface HelpdeskUpdate {
  tenant_id?: string;
  requester_name?: string;
  requester_email?: string;
  subject?: string;
  description?: string;
  status?: string;
  priority?: string;
  assigned_to?: string;
  closed_at?: string;
}
