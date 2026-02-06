"use client";

import type { ReactNode } from "react";
import clsx from "clsx";

export interface SidebarDrawerProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

export function SidebarDrawer({ open, onClose, children }: SidebarDrawerProps) {
  return (
    <>
      <button
        type="button"
        aria-label="Close sidebar"
        className={clsx("sidebar-drawer-overlay", open && "sidebar-drawer-overlay-open")}
        onClick={onClose}
      />
      <aside
        className={clsx("sidebar-drawer ui-anim", open && "sidebar-drawer-open")}
        aria-hidden={!open}
      >
        {children}
      </aside>
    </>
  );
}
