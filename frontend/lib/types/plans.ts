export interface Plan {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  price_cents: number;
  currency: string;
  billing_interval: string;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface PlanListResponse {
  items: Plan[];
  pagination: PaginationMeta;
}

export interface PlanCreate {
  name: string;
  code?: string;
  description?: string | null;
  price_cents: number;
  currency?: string;
  billing_interval?: string;
  is_active?: boolean;
}

export interface PlanUpdate {
  name?: string;
  code?: string;
  description?: string | null;
  price_cents?: number;
  currency?: string;
  billing_interval?: string;
  is_active?: boolean;
}
