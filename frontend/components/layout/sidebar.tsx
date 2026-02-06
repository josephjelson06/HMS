"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import {
  Building2,
  CircleHelp,
  ClipboardList,
  CreditCard,
  FileBarChart2,
  FileClock,
  FileText,
  Gauge,
  Hotel,
  KeySquare,
  LayoutGrid,
  LifeBuoy,
  MonitorCog,
  MoonStar,
  Receipt,
  Settings,
  ShieldCheck,
  UserCog,
  Users,
  Wrench
} from "lucide-react";

import { useAuth } from "@/lib/hooks/use-auth";
import { cn } from "@/lib/utils/cn";

type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
};

type NavSection = {
  label: string;
  items: NavItem[];
};

const adminNav: NavSection[] = [
  {
    label: "Operations",
    items: [
      { label: "Dashboard", href: "/admin/dashboard", icon: LayoutGrid },
      { label: "Hotel Registry", href: "/admin/hotels", icon: Hotel },
      { label: "Kiosk Fleet", href: "/admin/kiosks", icon: MonitorCog }
    ]
  },
  {
    label: "Business",
    items: [
      { label: "Plans", href: "/admin/plans", icon: ClipboardList },
      { label: "Subscriptions", href: "/admin/subscriptions", icon: CreditCard },
      { label: "Invoices", href: "/admin/invoices", icon: Receipt },
      { label: "Reports", href: "/admin/reports", icon: FileBarChart2 }
    ]
  },
  {
    label: "Administration",
    items: [
      { label: "Admin Users", href: "/admin/users", icon: Users },
      { label: "Admin Roles", href: "/admin/roles", icon: ShieldCheck },
      { label: "Audit Logs", href: "/admin/audit", icon: FileClock },
      { label: "HelpDesk", href: "/admin/helpdesk", icon: CircleHelp },
      { label: "My Profile", href: "/admin/profile", icon: UserCog },
      { label: "Settings", href: "/admin/settings", icon: Settings }
    ]
  }
];

const hotelNav: NavSection[] = [
  {
    label: "Operations",
    items: [
      { label: "Dashboard", href: "/hotel/dashboard", icon: LayoutGrid },
      { label: "Guest Registry", href: "/hotel/guests", icon: Users },
      { label: "Room Management", href: "/hotel/rooms", icon: Building2 },
      { label: "Incidents Record", href: "/hotel/incidents", icon: Wrench }
    ]
  },
  {
    label: "Management",
    items: [
      { label: "Users Management", href: "/hotel/users", icon: UserCog },
      { label: "Roles Management", href: "/hotel/roles", icon: ShieldCheck },
      { label: "Kiosk Settings", href: "/hotel/kiosks", icon: MonitorCog },
      { label: "Subscription & Billing", href: "/hotel/billing", icon: CreditCard }
    ]
  },
  {
    label: "Insights",
    items: [
      { label: "Help & Support", href: "/hotel/support", icon: LifeBuoy },
      { label: "Audit Logs", href: "/hotel/audit", icon: FileClock },
      { label: "Reports", href: "/hotel/reports", icon: FileBarChart2 },
      { label: "My Profile", href: "/hotel/profile", icon: KeySquare },
      { label: "Settings", href: "/hotel/settings", icon: Settings }
    ]
  }
];

export function Sidebar({
  variant,
  onNavigate,
  collapsed = false,
  onToggleCollapsed
}: {
  variant: "admin" | "hotel";
  onNavigate?: () => void;
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
}) {
  const pathname = usePathname();
  const { user } = useAuth();
  const sections = variant === "admin" ? adminNav : hotelNav;

  return (
    <aside className={cn("sidebar glass-panel", collapsed && "sidebar-collapsed")}>
      <div className="mb-5 flex items-center justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wider text-[color:var(--color-text-muted)]">HMS</p>
          <h2 className="truncate text-lg font-semibold">{variant === "admin" ? "Admin Panel" : "Hotel Panel"}</h2>
          <p className="sidebar-meta truncate text-xs text-[color:var(--color-text-muted)]">{user?.email ?? ""}</p>
        </div>
        <button
          type="button"
          className="sidebar-collapse-label rounded-lg border border-white/10 bg-white/5 p-2 text-[color:var(--color-text-muted)] ui-anim hover:bg-white/10"
          onClick={onToggleCollapsed}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <MoonStar className="size-4" />
        </button>
      </div>

      <nav className="space-y-4">
        {sections.map((section) => (
          <div key={section.label}>
            <p className="sidebar-section-label mb-2 px-1 text-xs uppercase tracking-wide text-[color:var(--color-text-muted)]">
              {section.label}
            </p>
            <div className="space-y-1">
              {section.items.map((item) => {
                const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={onNavigate}
                    className={cn("sidebar-link", active && "sidebar-link-active")}
                    title={item.label}
                  >
                    <Icon className="size-4 shrink-0" />
                    <span className="sidebar-link-label truncate text-sm">{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>
      <div className="mt-6 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-[color:var(--color-text-muted)]">
        <div className="flex items-center gap-2">
          <Gauge className="size-4" />
          <span className="sidebar-link-label">Workspace Ready</span>
        </div>
      </div>
      <div className="mt-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-[color:var(--color-text-muted)]">
        <div className="flex items-center gap-2">
          <FileText className="size-4" />
          <span className="sidebar-link-label">Secure Session</span>
        </div>
      </div>
    </aside>
  );
}
