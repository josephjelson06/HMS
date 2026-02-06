export interface Incident {
  id: string;
  tenant_id: string;
  title: string;
  description?: string | null;
  status: string;
  severity: string;
  category?: string | null;
  occurred_at?: string | null;
  resolved_at?: string | null;
  reported_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface IncidentListResponse {
  items: Incident[];
  pagination: PaginationMeta;
}

export interface IncidentCreate {
  title: string;
  description?: string;
  status?: string;
  severity?: string;
  category?: string;
  occurred_at?: string;
  resolved_at?: string;
  reported_by?: string;
}

export interface IncidentUpdate {
  title?: string;
  description?: string;
  status?: string;
  severity?: string;
  category?: string;
  occurred_at?: string;
  resolved_at?: string;
  reported_by?: string;
}
