import { ImpersonationContext, TenantContext, UserContext } from "@/lib/types/auth";

export interface AuthResponse {
  user: UserContext;
  permissions: string[];
  tenant: TenantContext | null;
  impersonation?: ImpersonationContext | null;
  must_reset_password?: boolean;
}

export interface ImpersonationStartRequest {
  tenant_id?: string;
  target_user_id?: string;
  reason?: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface PasswordChangeResponse {
  message: string;
}
