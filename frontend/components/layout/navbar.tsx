"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { LogOut, Moon, ShieldOff, Sun } from "lucide-react";
import { toast } from "sonner";

import { useTheme } from "@/components/providers/theme-provider";
import { Button } from "@/components/ui/primitives/button";
import { useAuth } from "@/lib/hooks/use-auth";

export function Navbar() {
  const router = useRouter();
  const { toggleTheme, theme } = useTheme();
  const { user, logout, impersonation, stopImpersonation } = useAuth();
  const [stoppingImpersonation, setStoppingImpersonation] = useState(false);

  const handleStopImpersonation = async () => {
    setStoppingImpersonation(true);
    try {
      await stopImpersonation();
      toast.success("Impersonation ended");
      router.push("/admin/dashboard");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Unable to stop impersonation");
    } finally {
      setStoppingImpersonation(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast.success("Logged out");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Logout failed");
    }
  };

  return (
    <>
      {impersonation?.active && (
        <div className="mx-6 mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-amber-300/30 bg-amber-500/10 px-4 py-3 text-sm">
          <p>
            Impersonating hotel tenant <span className="font-semibold">{impersonation.tenant_name}</span>
          </p>
          <button
            className="inline-flex items-center gap-1.5 rounded-full border border-amber-200/40 px-4 py-1.5 text-xs font-semibold ui-anim"
            onClick={() => void handleStopImpersonation()}
            disabled={stoppingImpersonation}
          >
            <ShieldOff className="size-3.5" />
            {stoppingImpersonation ? "Exiting..." : "Exit impersonation"}
          </button>
        </div>
      )}
      <header className="navbar">
        <div>
          <h1 className="text-2xl">Welcome, {user?.first_name ?? "there"}</h1>
          <p className="text-sm text-[color:var(--muted)]">
            {impersonation?.active ? "Admin impersonation active." : "Foundation module ready."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" onClick={toggleTheme}>
            {theme === "dark" ? <Sun className="mr-1 size-4" /> : <Moon className="mr-1 size-4" />}
            {theme === "dark" ? "Light" : "Dark"} mode
          </Button>
          <Button variant="secondary" onClick={() => void handleLogout()}>
            <LogOut className="mr-1 size-4" />
            Logout
          </Button>
        </div>
      </header>
    </>
  );
}
