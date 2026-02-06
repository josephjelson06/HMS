export interface Subscription {
  id: string;
  tenant_id: string;
  tenant_name?: string | null;
  plan_id: string;
  plan_name?: string | null;
  plan_code?: string | null;
  status: string;
  start_date?: string | null;
  current_period_start?: string | null;
  current_period_end?: string | null;
  cancel_at?: string | null;
  canceled_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface SubscriptionListResponse {
  items: Subscription[];
  pagination: PaginationMeta;
}

export interface SubscriptionCreate {
  tenant_id: string;
  plan_id: string;
  status?: string;
  start_date?: string;
  current_period_end?: string;
  cancel_at?: string;
}

export interface SubscriptionUpdate {
  tenant_id?: string;
  plan_id?: string;
  status?: string;
  current_period_end?: string;
  cancel_at?: string;
  canceled_at?: string;
}
