export interface Guest {
  id: string;
  tenant_id: string;
  first_name: string;
  last_name: string;
  email?: string | null;
  phone?: string | null;
  status: string;
  check_in_at?: string | null;
  check_out_at?: string | null;
  notes?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface GuestListResponse {
  items: Guest[];
  pagination: PaginationMeta;
}

export interface GuestCreate {
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  status?: string;
  check_in_at?: string;
  check_out_at?: string;
  notes?: string;
}

export interface GuestUpdate {
  first_name?: string;
  last_name?: string;
  email?: string;
  phone?: string;
  status?: string;
  check_in_at?: string;
  check_out_at?: string;
  notes?: string;
}
