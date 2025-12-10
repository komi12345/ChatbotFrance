"use client";

import { useState, useEffect } from "react";
import { ProtectedRoute } from "./ProtectedRoute";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import type { UserRole } from "@/types/auth";

interface DashboardLayoutProps {
  children: React.ReactNode;
  title?: string;
  allowedRoles?: UserRole[];
}

export function DashboardLayout({
  children,
  title,
  allowedRoles,
}: DashboardLayoutProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setIsMobileMenuOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isMobileMenuOpen]);

  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  return (
    <ProtectedRoute allowedRoles={allowedRoles}>
      <div className="min-h-screen bg-[#F9FAFB]">
        {/* Sidebar - Desktop */}
        <div className="hidden md:block">
          <Sidebar />
        </div>

        {/* Sidebar - Mobile (overlay) */}
        {isMobileMenuOpen && (
          <>
            <div
              className="fixed inset-0 z-40 bg-black/50 md:hidden animate-in fade-in duration-200"
              onClick={closeMobileMenu}
              aria-hidden="true"
            />
            <div className="fixed inset-y-0 left-0 z-50 md:hidden animate-in slide-in-from-left duration-200">
              <Sidebar onClose={closeMobileMenu} isMobile />
            </div>
          </>
        )}

        {/* Contenu principal */}
        <div className="md:pl-64">
          <Header
            title={title}
            onMenuClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          />
          <main className="p-4 md:p-6 lg:p-8">{children}</main>
        </div>
      </div>
    </ProtectedRoute>
  );
}

export default DashboardLayout;
