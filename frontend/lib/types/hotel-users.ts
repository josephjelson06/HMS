export interface HotelRole {
  id: string;
  name: string;
  display_name: string;
  description?: string | null;
}

export interface HotelUser {
  id: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  is_active: boolean;
  roles: string[];
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface HotelUserListResponse {
  items: HotelUser[];
  pagination: PaginationMeta;
}
