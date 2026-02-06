export interface Invoice {
  id: string;
  tenant_id: string;
  tenant_name?: string | null;
  subscription_id: string;
  invoice_number: string;
  status: string;
  amount_cents: number;
  currency: string;
  issued_at?: string | null;
  due_at?: string | null;
  paid_at?: string | null;
  notes?: string | null;
  plan_name?: string | null;
  plan_code?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface InvoiceListResponse {
  items: Invoice[];
  pagination: PaginationMeta;
}

export interface InvoiceCreate {
  tenant_id: string;
  subscription_id: string;
  invoice_number?: string;
  status?: string;
  amount_cents: number;
  currency?: string;
  issued_at?: string;
  due_at?: string;
  paid_at?: string;
  notes?: string;
}

export interface InvoiceUpdate {
  tenant_id?: string;
  subscription_id?: string;
  invoice_number?: string;
  status?: string;
  amount_cents?: number;
  currency?: string;
  issued_at?: string;
  due_at?: string;
  paid_at?: string;
  notes?: string;
}
