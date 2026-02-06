export interface Room {
  id: string;
  tenant_id: string;
  number: string;
  room_type: string;
  floor?: string | null;
  status: string;
  capacity?: number | null;
  rate_cents?: number | null;
  currency: string;
  description?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface RoomListResponse {
  items: Room[];
  pagination: PaginationMeta;
}

export interface RoomCreate {
  number: string;
  room_type: string;
  floor?: string;
  status?: string;
  capacity?: number;
  rate_cents?: number;
  currency?: string;
  description?: string;
}

export interface RoomUpdate {
  number?: string;
  room_type?: string;
  floor?: string;
  status?: string;
  capacity?: number;
  rate_cents?: number;
  currency?: string;
  description?: string;
}
