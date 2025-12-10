"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { useMonitoringStats } from "@/hooks/useMonitoring";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  FolderOpen,
  MessageSquare,
  Send,
  BarChart3,
  UserCog,
  LogOut,
  X,
  Activity,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon: React.ReactNode;
  superAdminOnly?: boolean;
  showBadge?: boolean;
  badgeColor?: string;
}

/**
 * Determines the badge color based on alert level
 * Requirements: 8.2
 */
function getAlertBadgeColor(alertLevel: string): string {
  switch (alertLevel) {
    case 'attention':
      return 'bg-yellow-500';
    case 'danger':
      return 'bg-red-500';
    case 'blocked':
      return 'bg-gray-500';
    default:
      return '';
  }
}

/**
 * Base navigation items (static)
 */
const baseNavItems: Omit<NavItem, 'showBadge' | 'badgeColor'>[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: <LayoutDashboard className="h-5 w-5" />,
  },
  {
    href: "/categories",
    label: "Catégories",
    icon: <FolderOpen className="h-5 w-5" />,
  },
  {
    href: "/contacts",
    label: "Contacts",
    icon: <Users className="h-5 w-5" />,
  },
  {
    href: "/campaigns",
    label: "Campagnes",
    icon: <Send className="h-5 w-5" />,
  },
  {
    href: "/messages",
    label: "Messages",
    icon: <MessageSquare className="h-5 w-5" />,
  },
  {
    href: "/statistics",
    label: "Statistiques",
    icon: <BarChart3 className="h-5 w-5" />,
  },
  {
    href: "/dashboard/monitoring",
    label: "Monitoring",
    icon: <Activity className="h-5 w-5" />,
  },
  {
    href: "/admin-users",
    label: "Utilisateurs",
    icon: <UserCog className="h-5 w-5" />,
    superAdminOnly: true,
  },
];

interface SidebarProps {
  onClose?: () => void;
  isMobile?: boolean;
}

export function Sidebar({ onClose, isMobile = false }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout, isSuperAdmin } = useAuth();
  
  // Fetch monitoring stats for the alert badge
  // Requirements: 8.2 - Show warning badge when counter > 135
  const { data: monitoringStats } = useMonitoringStats(30000); // Refresh every 30s for nav

  // Build nav items with dynamic badge for monitoring
  const navItems: NavItem[] = baseNavItems.map((item) => {
    if (item.href === "/dashboard/monitoring" && monitoringStats) {
      const showBadge = monitoringStats.total_sent > 135;
      return {
        ...item,
        showBadge,
        badgeColor: showBadge ? getAlertBadgeColor(monitoringStats.alert_level) : undefined,
      };
    }
    return item;
  });

  const visibleItems = navItems.filter((item) => {
    if (item.superAdminOnly) {
      return isSuperAdmin();
    }
    return true;
  });

  const handleNavClick = () => {
    if (isMobile && onClose) {
      onClose();
    }
  };

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 bg-[#1F2937]">
      <div className="flex h-full flex-col">
        {/* Logo / Titre */}
        <div className="flex h-16 items-center justify-between px-4 md:px-6 border-b border-white/10">
          <Link href="/dashboard" className="flex items-center gap-3" onClick={handleNavClick}>
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500">
              <MessageSquare className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-semibold text-white">WhatsApp Bot</span>
          </Link>
          {isMobile && onClose && (
            <button
              onClick={onClose}
              className="p-2 -mr-2 rounded-lg text-[#9CA3AF] hover:bg-white/5 transition-colors md:hidden"
              aria-label="Fermer le menu"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-3 md:p-4">
          {visibleItems.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
            
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={handleNavClick}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-3 md:py-2.5 text-sm font-medium transition-all",
                  "min-h-[44px] touch-manipulation",
                  isActive
                    ? "bg-emerald-500/15 text-emerald-500"
                    : "text-[#9CA3AF] hover:bg-white/5 hover:text-white"
                )}
              >
                <span className={isActive ? "text-emerald-500" : "text-[#9CA3AF]"}>
                  {item.icon}
                </span>
                <span className="flex-1">{item.label}</span>
                {/* Alert badge for monitoring - Requirements: 8.2 */}
                {item.showBadge && item.badgeColor && (
                  <span
                    className={cn(
                      "h-2 w-2 rounded-full animate-pulse",
                      item.badgeColor
                    )}
                    aria-label="Alerte monitoring"
                  />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Profil utilisateur et déconnexion */}
        <div className="border-t border-white/10 p-3 md:p-4">
          <div className="mb-3 rounded-lg bg-white/5 p-3">
            <p className="text-sm font-medium text-white truncate">{user?.email}</p>
            <p className="text-xs text-[#9CA3AF] capitalize">
              {user?.role === "super_admin" ? "Super Admin" : "Admin"}
            </p>
          </div>
          <button
            onClick={() => {
              handleNavClick();
              logout();
            }}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-3 md:py-2.5 text-sm font-medium",
              "min-h-[44px] touch-manipulation",
              "text-[#9CA3AF] transition-colors hover:bg-red-500/10 hover:text-red-400"
            )}
          >
            <LogOut className="h-5 w-5" />
            Déconnexion
          </button>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
