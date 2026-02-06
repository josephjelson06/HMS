export interface HotelRole {
  id: string;
  name: string;
  display_name: string;
  description?: string | null;
  is_system: boolean;
  tenant_id?: string | null;
  permissions: string[];
}

export interface HotelRoleCreate {
  name: string;
  display_name: string;
  description?: string;
  permissions: string[];
}

export interface HotelRoleUpdate {
  name?: string;
  display_name?: string;
  description?: string;
  permissions?: string[];
}

export interface PermissionOption {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  resource: string;
  action: string;
}
