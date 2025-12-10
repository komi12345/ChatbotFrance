"use client";

import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { LogOut, User, Menu } from "lucide-react";

interface HeaderProps {
  title?: string;
  onMenuClick?: () => void;
}

export function Header({ title, onMenuClick }: HeaderProps) {
  const { user, logout, isSuperAdmin } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[#E5E7EB] bg-white px-4 md:px-6">
      {/* Bouton menu mobile + Titre */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden text-[#6B7280] hover:text-[#111827] hover:bg-[#F3F4F6]"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
          <span className="sr-only">Menu</span>
        </Button>

        {title && (
          <h1 className="text-lg font-semibold text-[#111827] md:text-xl">{title}</h1>
        )}
      </div>

      {/* Profil utilisateur */}
      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-3 sm:flex">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/10">
            <User className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="hidden flex-col md:flex">
            <span className="text-sm font-medium text-[#111827]">{user?.email}</span>
            <span className="text-xs text-[#6B7280]">
              {isSuperAdmin() ? "Super Admin" : "Admin"}
            </span>
          </div>
        </div>

        <Button
          variant="ghost"
          size="icon"
          onClick={logout}
          title="Déconnexion"
          className="text-[#6B7280] hover:text-[#EF4444] hover:bg-[#FEE2E2]"
        >
          <LogOut className="h-5 w-5" />
          <span className="sr-only">Déconnexion</span>
        </Button>
      </div>
    </header>
  );
}

export default Header;
