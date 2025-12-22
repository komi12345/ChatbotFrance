"use client";

import { QueryClient } from "@tanstack/react-query";

// Configuration du QueryClient pour React Query
export function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Durée de cache par défaut : 30 secondes (mises à jour plus rapides)
        staleTime: 30 * 1000,
        // Durée de conservation en cache : 5 minutes
        gcTime: 5 * 60 * 1000,
        // Retry automatique en cas d'erreur
        retry: 1,
        // Refetch automatique quand la fenêtre reprend le focus
        refetchOnWindowFocus: true,
        // Refetch quand la connexion réseau revient
        refetchOnReconnect: true,
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
