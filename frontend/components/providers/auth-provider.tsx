"use client";

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { authApi } from "@/lib/api/auth";
import { AuthResponse, ImpersonationStartRequest } from "@/lib/types/api";
import { ImpersonationContext, TenantContext, UserContext } from "@/lib/types/auth";

interface AuthContextValue {
  user: UserContext | null;
  permissions: string[];
  tenant: TenantContext | null;
  impersonation: ImpersonationContext | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<AuthResponse>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
  startImpersonation: (payload: ImpersonationStartRequest) => Promise<AuthResponse>;
  stopImpersonation: () => Promise<AuthResponse>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserContext | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [tenant, setTenant] = useState<TenantContext | null>(null);
  const [impersonation, setImpersonation] = useState<ImpersonationContext | null>(null);
  const [loading, setLoading] = useState(true);

  const applyAuth = useCallback((payload: AuthResponse) => {
    setUser(payload.user);
    setPermissions(payload.permissions);
    setTenant(payload.tenant ?? null);
    setImpersonation(payload.impersonation ?? null);
  }, []);

  const bootstrap = useCallback(async () => {
    try {
      const me = await authApi.me();
      applyAuth(me);
    } catch {
      try {
        const refreshed = await authApi.refresh();
        applyAuth(refreshed);
      } catch {
        setUser(null);
        setPermissions([]);
        setTenant(null);
        setImpersonation(null);
      }
    } finally {
      setLoading(false);
    }
  }, [applyAuth]);

  useEffect(() => {
    bootstrap();
  }, [bootstrap]);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    applyAuth(response);
    return response;
  }, [applyAuth]);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
    setPermissions([]);
    setTenant(null);
    setImpersonation(null);
  }, []);

  const refresh = useCallback(async () => {
    const response = await authApi.refresh();
    applyAuth(response);
  }, [applyAuth]);

  const startImpersonation = useCallback(async (payload: ImpersonationStartRequest) => {
    const response = await authApi.startImpersonation(payload);
    applyAuth(response);
    return response;
  }, [applyAuth]);

  const stopImpersonation = useCallback(async () => {
    const response = await authApi.stopImpersonation();
    applyAuth(response);
    return response;
  }, [applyAuth]);

  const value = useMemo(
    () => ({
      user,
      permissions,
      tenant,
      impersonation,
      loading,
      login,
      logout,
      refresh,
      startImpersonation,
      stopImpersonation
    }),
    [
      user,
      permissions,
      tenant,
      impersonation,
      loading,
      login,
      logout,
      refresh,
      startImpersonation,
      stopImpersonation
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return context;
}
