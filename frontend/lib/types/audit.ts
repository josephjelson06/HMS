export interface AuditLogRecord {
  id: string;
  tenant_id?: string | null;
  user_id?: string | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  changes?: Record<string, unknown> | null;
  ip_address?: string | null;
  user_agent?: string | null;
  impersonated_by?: string | null;
  created_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface AuditLogListResponse {
  items: AuditLogRecord[];
  pagination: PaginationMeta;
}
