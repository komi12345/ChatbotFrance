"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api, { PaginatedResponse } from "@/lib/api";
import type {
  Category,
  CategoryCreate,
  CategoryUpdate,
  CategoryWithContacts,
  AddContactsToCategory,
} from "@/types/category";
import type { Contact } from "@/types/contact";

// Clés de cache pour React Query
export const categoryKeys = {
  all: ["categories"] as const,
  lists: () => [...categoryKeys.all, "list"] as const,
  list: (params: { page?: number; search?: string }) =>
    [...categoryKeys.lists(), params] as const,
  details: () => [...categoryKeys.all, "detail"] as const,
  detail: (id: number) => [...categoryKeys.details(), id] as const,
};

/**
 * Hook pour récupérer la liste des catégories avec pagination
 * Requirements: 2.3 - staleTime de 2 minutes pour les listes
 */
export function useCategories(params: { page?: number; search?: string } = {}) {
  const { page = 1, search = "" } = params;

  return useQuery({
    queryKey: categoryKeys.list({ page, search }),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      searchParams.append("page", page.toString());
      searchParams.append("size", "50");
      if (search) {
        searchParams.append("search", search);
      }

      const response = await api.get<PaginatedResponse<Category>>(
        `/categories?${searchParams.toString()}`
      );
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes - Requirements 2.3
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook pour récupérer les détails d'une catégorie
 * Requirements: 2.3 - staleTime de 2 minutes pour les listes
 */
export function useCategory(id: number) {
  return useQuery({
    queryKey: categoryKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<CategoryWithContacts>(`/categories/${id}`);
      return response.data;
    },
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 minutes - Requirements 2.3
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook pour récupérer les contacts disponibles (non présents dans une catégorie)
 * Utilise le nouvel endpoint backend avec pagination et recherche côté serveur
 */
export function useAvailableContactsForCategory(
  categoryId: number,
  params: { page?: number; search?: string; size?: number } = {}
) {
  const { page = 1, search = "", size = 100 } = params;

  return useQuery({
    queryKey: [...categoryKeys.detail(categoryId), "available-contacts", { page, search, size }],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      searchParams.append("page", page.toString());
      searchParams.append("size", size.toString());
      if (search) {
        searchParams.append("search", search);
      }

      const response = await api.get<PaginatedResponse<Contact>>(
        `/categories/${categoryId}/available-contacts?${searchParams.toString()}`
      );
      return response.data;
    },
    enabled: !!categoryId,
    staleTime: 30 * 1000, // 30 secondes - données qui changent fréquemment
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}


/**
 * Hook pour créer une catégorie avec mise à jour optimiste
 * Requirements: 2.1 - Mise à jour optimiste des statistiques
 */
export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CategoryCreate) => {
      const response = await api.post<Category>("/categories", data);
      return response.data;
    },
    onMutate: async () => {
      // Annuler les requêtes en cours pour éviter les conflits
      await queryClient.cancelQueries({ queryKey: ["stats"] });

      // Snapshot des données actuelles pour rollback
      const previousDashboardStats = queryClient.getQueryData(["stats", "dashboard"]);

      // Mise à jour optimiste du compteur de catégories
      queryClient.setQueryData(["stats", "dashboard"], (old: { total_categories?: number } | undefined) => {
        if (!old) return old;
        return {
          ...old,
          total_categories: (old.total_categories || 0) + 1,
        };
      });

      // Retourner le contexte pour rollback
      return { previousDashboardStats };
    },
    onError: (_err, _newCategory, context) => {
      // Rollback en cas d'erreur
      if (context?.previousDashboardStats) {
        queryClient.setQueryData(["stats", "dashboard"], context.previousDashboardStats);
      }
    },
    onSettled: () => {
      // Invalider pour synchroniser avec le serveur
      queryClient.invalidateQueries({ queryKey: categoryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour mettre à jour une catégorie
 */
export function useUpdateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: CategoryUpdate }) => {
      const response = await api.put<Category>(`/categories/${id}`, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      // Invalider tous les caches liés
      queryClient.invalidateQueries({ queryKey: categoryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: categoryKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour supprimer une catégorie avec mise à jour optimiste
 * Requirements: 3.1, 3.2 - Mise à jour optimiste et rollback automatique
 */
export function useDeleteCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/categories/${id}`);
      return id;
    },
    onMutate: async (deletedId) => {
      // Annuler les requêtes en cours pour éviter les conflits
      await queryClient.cancelQueries({ queryKey: ["stats"] });
      await queryClient.cancelQueries({ queryKey: categoryKeys.lists() });

      // Snapshot des données actuelles pour rollback
      const previousDashboardStats = queryClient.getQueryData(["stats", "dashboard"]);

      // Mise à jour optimiste du compteur de catégories
      queryClient.setQueryData(["stats", "dashboard"], (old: { total_categories?: number } | undefined) => {
        if (!old) return old;
        return {
          ...old,
          total_categories: Math.max((old.total_categories || 0) - 1, 0),
        };
      });

      // Retourner le contexte pour rollback
      return { previousDashboardStats, deletedId };
    },
    onError: (_err, _deletedId, context) => {
      // Rollback en cas d'erreur
      if (context?.previousDashboardStats) {
        queryClient.setQueryData(["stats", "dashboard"], context.previousDashboardStats);
      }
    },
    onSettled: () => {
      // Invalider tous les caches liés
      queryClient.invalidateQueries({ queryKey: categoryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour ajouter des contacts à une catégorie
 */
export function useAddContactsToCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      categoryId,
      data,
    }: {
      categoryId: number;
      data: AddContactsToCategory;
    }) => {
      const response = await api.post<Category>(
        `/categories/${categoryId}/contacts`,
        data
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      // Invalider tous les caches liés
      queryClient.invalidateQueries({ queryKey: categoryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: categoryKeys.detail(variables.categoryId) });
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour retirer un contact d'une catégorie
 */
export function useRemoveContactFromCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      categoryId,
      contactId,
    }: {
      categoryId: number;
      contactId: number;
    }) => {
      await api.delete(`/categories/${categoryId}/contacts/${contactId}`);
      return { categoryId, contactId };
    },
    onSuccess: (_, variables) => {
      // Invalider tous les caches liés
      queryClient.invalidateQueries({ queryKey: categoryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: categoryKeys.detail(variables.categoryId) });
      queryClient.invalidateQueries({ queryKey: ["contacts"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

export default useCategories;
