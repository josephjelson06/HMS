export type UserType = "admin" | "hotel";

export interface TenantContext {
  id: string;
  name: string;
  slug: string;
}

export interface ImpersonationContext {
  active: boolean;
  tenant_id: string;
  tenant_name: string;
  session_id: string;
  started_at: string;
  admin_user_id?: string;
  target_user_id?: string;
}

export interface UserContext {
  id: string;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  user_type: UserType;
  tenant_id?: string | null;
  roles: string[];
}
