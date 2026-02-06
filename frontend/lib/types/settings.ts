export type JsonValue = Record<string, unknown> | unknown[] | string | number | boolean | null;

export interface Setting {
  id: string;
  key: string;
  value: JsonValue;
  description?: string | null;
  updated_by?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
}

export interface SettingListResponse {
  items: Setting[];
  pagination: PaginationMeta;
}

export interface SettingCreate {
  key: string;
  value: JsonValue;
  description?: string;
}

export interface SettingUpdate {
  value?: JsonValue;
  description?: string;
}
