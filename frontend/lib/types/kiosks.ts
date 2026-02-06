export interface Kiosk {
  id: string;
  tenant_id: string;
  tenant_name?: string | null;
  name: string;
  location?: string | null;
  status: string;
  device_id?: string | null;
  token_last4?: string | null;
  last_seen_at?: string | null;
  issued_token?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface KioskListResponse {
  items: Kiosk[];
  pagination: PaginationMeta;
}

export interface KioskCreate {
  tenant_id: string;
  name: string;
  location?: string;
  status?: string;
  device_id?: string;
}

export interface KioskUpdate {
  name?: string;
  location?: string;
  status?: string;
  device_id?: string;
  rotate_token?: boolean;
}
