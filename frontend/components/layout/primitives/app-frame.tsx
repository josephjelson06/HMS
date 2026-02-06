"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { Menu, PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { Sidebar } from "@/components/layout/sidebar";
import { SidebarDrawer } from "@/components/layout/primitives/sidebar-drawer";
import { IconButton } from "@/components/ui/primitives/icon-button";
import { cn } from "@/lib/utils/cn";

export interface AppFrameProps {
  variant: "admin" | "hotel";
  children: ReactNode;
}

export function AppFrame({ variant, children }: AppFrameProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const saved = localStorage.getItem("hms-sidebar-collapsed");
    setCollapsed(saved === "1");
  }, []);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      if (typeof window !== "undefined") {
        localStorage.setItem("hms-sidebar-collapsed", next ? "1" : "0");
      }
      return next;
    });
  };

  return (
    <div className={cn("app-shell", collapsed && "app-shell-collapsed")}>
      <div className="hidden lg:block">
        <Sidebar variant={variant} collapsed={collapsed} onToggleCollapsed={toggleCollapsed} />
      </div>
      <div className="min-w-0">
        <div className="app-mobile-topbar lg:hidden">
          <IconButton label="Open navigation" onClick={() => setDrawerOpen(true)}>
            <Menu className="size-4" />
          </IconButton>
          <p className="text-sm font-medium capitalize">{variant} workspace</p>
          <span />
        </div>
        <div className="hidden px-6 pt-6 lg:block">
          <IconButton
            label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            variant="secondary"
            onClick={toggleCollapsed}
          >
            {collapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
          </IconButton>
        </div>
        {children}
      </div>
      <div className="lg:hidden">
        <SidebarDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)}>
          <Sidebar variant={variant} onNavigate={() => setDrawerOpen(false)} />
        </SidebarDrawer>
      </div>
    </div>
  );
}
