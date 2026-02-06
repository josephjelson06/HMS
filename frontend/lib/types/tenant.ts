export interface Hotel {
  id: string;
  name: string;
  slug: string;
  status: string;
  subscription_tier?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface HotelListResponse {
  items: Hotel[];
  pagination: PaginationMeta;
}
