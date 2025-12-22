"use client";

import { useEffect, useRef } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import type { UserRole } from "@/types/auth";

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** Rôles autorisés à accéder à cette route */
  allowedRoles?: UserRole[];
}

/**
 * Composant HOC pour protéger les routes nécessitant une authentification
 * Redirige vers /login si non authentifié
 * Redirige vers /dashboard si le rôle n'est pas autorisé
 */
export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, user } = useAuth();
  const hasRedirected = useRef(false);

  useEffect(() => {
    if (isLoading) return;

    // Éviter les redirections multiples
    if (hasRedirected.current) return;

    // Rediriger vers login si non authentifié
    if (!isAuthenticated) {
      hasRedirected.current = true;
      router.push("/login");
      return;
    }

    // Vérifier les rôles si spécifiés
    if (allowedRoles && user && !allowedRoles.includes(user.role)) {
      // Utilisateur authentifié mais rôle non autorisé
      hasRedirected.current = true;
      router.push("/dashboard");
    }
  }, [isAuthenticated, isLoading, user, allowedRoles, router, pathname]);

  // Reset le flag quand le pathname change
  useEffect(() => {
    hasRedirected.current = false;
  }, [pathname]);

  // Afficher un loader pendant la vérification
  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Chargement...</p>
        </div>
      </div>
    );
  }

  // Ne pas afficher le contenu si non authentifié ou rôle non autorisé
  if (!isAuthenticated) {
    return null;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return null;
  }

  return <>{children}</>;
}

export default ProtectedRoute;
