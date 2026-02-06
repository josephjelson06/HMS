import { useAuth } from "@/lib/hooks/use-auth";
import { hasPermission } from "@/lib/utils/permissions";

export function usePermissions() {
  const { permissions } = useAuth();

  return {
    has: (permission: string) => hasPermission(permissions, permission)
  };
}
