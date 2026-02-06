export interface PermissionOption {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  resource: string;
  action: string;
}

export interface AdminRole {
  id: string;
  name: string;
  display_name: string;
  description?: string | null;
  is_system: boolean;
  permissions: string[];
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AdminRoleCreate {
  name: string;
  display_name: string;
  description?: string | null;
  permissions: string[];
}

export interface AdminRoleUpdate {
  name?: string;
  display_name?: string;
  description?: string | null;
  permissions?: string[];
}
