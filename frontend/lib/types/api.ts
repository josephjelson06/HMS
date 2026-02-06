import { ImpersonationContext, TenantContext, UserContext } from "@/lib/types/auth";

export interface AuthResponse {
  user: UserContext;
  permissions: string[];
  tenant: TenantContext | null;
  impersonation?: ImpersonationContext | null;
}

export interface ImpersonationStartRequest {
  tenant_id?: string;
  target_user_id?: string;
  reason?: string;
}
