"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import type { User, LoginRequest, LoginResponse, AuthState } from "@/types/auth";

// Clés localStorage
const TOKEN_KEY = "access_token";
const USER_KEY = "user";

/**
 * Hook personnalisé pour la gestion de l'authentification
 * Gère le JWT, localStorage et l'état utilisateur
 */
export function useAuth() {
  const router = useRouter();
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Initialisation : charger l'état depuis localStorage
  useEffect(() => {
    const initAuth = () => {
      if (typeof window === "undefined") return;

      const token = localStorage.getItem(TOKEN_KEY);
      const userStr = localStorage.getItem(USER_KEY);

      if (token && userStr) {
        try {
          const user = JSON.parse(userStr) as User;
          setAuthState({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch {
          // Données corrompues, nettoyer
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(USER_KEY);
          setAuthState({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } else {
        setAuthState({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    };

    initAuth();
  }, []);


  /**
   * Connexion utilisateur
   * @param credentials - Email et mot de passe
   * @returns Promise avec le résultat de la connexion
   */
  const login = useCallback(async (credentials: LoginRequest): Promise<{ success: boolean; error?: string }> => {
    try {
      setAuthState((prev) => ({ ...prev, isLoading: true }));

      const response = await api.post<LoginResponse>("/auth/login", credentials);
      const { access_token, user } = response.data;

      // Stocker dans localStorage
      localStorage.setItem(TOKEN_KEY, access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));

      setAuthState({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
      });

      return { success: true };
    } catch (error: unknown) {
      setAuthState((prev) => ({ ...prev, isLoading: false }));

      // Extraire le message d'erreur
      let errorMessage = "Erreur de connexion";
      if (error && typeof error === "object" && "response" in error) {
        const axiosError = error as { response?: { data?: { detail?: unknown } } };
        const detail = axiosError.response?.data?.detail;
        
        // Gérer les différents formats d'erreur
        if (typeof detail === "string") {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          // Erreur de validation Pydantic (tableau d'objets)
          errorMessage = detail.map((err: { msg?: string }) => err.msg || "Erreur de validation").join(", ");
        } else if (detail && typeof detail === "object" && "msg" in detail) {
          // Erreur de validation Pydantic (objet unique)
          errorMessage = (detail as { msg: string }).msg;
        }
      }

      return { success: false, error: errorMessage };
    }
  }, []);

  /**
   * Déconnexion utilisateur
   */
  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);

    setAuthState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });

    router.push("/login");
  }, [router]);

  /**
   * Récupérer l'utilisateur courant depuis l'API
   */
  const fetchCurrentUser = useCallback(async (): Promise<User | null> => {
    try {
      const response = await api.get<User>("/auth/me");
      const user = response.data;

      // Mettre à jour localStorage et state
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      setAuthState((prev) => ({ ...prev, user }));

      return user;
    } catch {
      // Token invalide ou expiré
      logout();
      return null;
    }
  }, [logout]);

  /**
   * Vérifier si l'utilisateur est Super Admin
   */
  const isSuperAdmin = useCallback((): boolean => {
    return authState.user?.role === "super_admin";
  }, [authState.user]);

  /**
   * Vérifier si l'utilisateur est Admin
   */
  const isAdmin = useCallback((): boolean => {
    return authState.user?.role === "admin";
  }, [authState.user]);

  return {
    ...authState,
    login,
    logout,
    fetchCurrentUser,
    isSuperAdmin,
    isAdmin,
  };
}

export default useAuth;
