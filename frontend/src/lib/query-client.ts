"use client";

import { QueryClient } from "@tanstack/react-query";

// Configuration du QueryClient pour React Query
// Optimisé pour réduire les requêtes réseau et améliorer la réactivité
// Requirements: 2.2, 2.3 - staleTime de 30 secondes par défaut, gcTime de 10 minutes
export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Durée de cache par défaut : 30 secondes (pour voir les changements rapidement)
        staleTime: 30 * 1000,
        // Durée de conservation en cache : 10 minutes
        gcTime: 10 * 60 * 1000,
        // Retry automatique en cas d'erreur
        retry: 1,
        // Désactivé pour éviter les requêtes inutiles lors du changement de fenêtre
        // Optimisation identifiée dans l'audit TanStack Query
        refetchOnWindowFocus: false,
        // Refetch quand la connexion réseau revient
        refetchOnReconnect: true,
        // Refetch automatiquement sur mount si données stale
        refetchOnMount: true,
      },
      mutations: {
        // Retry automatique pour les mutations
        retry: 0,
      },
    },
  });
}

// Singleton pour le client côté navigateur
let browserQueryClient: QueryClient | undefined = undefined;

export function getQueryClient() {
  if (typeof window === "undefined") {
    // Côté serveur : toujours créer un nouveau client
    return makeQueryClient();
  } else {
    // Côté client : réutiliser le même client
    if (!browserQueryClient) {
      browserQueryClient = makeQueryClient();
    }
    return browserQueryClient;
  }
}
