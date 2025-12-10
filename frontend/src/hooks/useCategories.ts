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
  });
}

/**
 * Hook pour récupérer les détails d'une catégorie
 */
export function useCategory(id: number) {
  return useQuery({
    queryKey: categoryKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<CategoryWithContacts>(`/categories/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}


/**
 * Hook pour créer une catégorie
 */
export function useCreateCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CategoryCreate) => {
      const response = await api.post<Category>("/categories", data);
      return response.data;
    },
    onSuccess: () => {
      // Invalider tous les caches liés
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
 * Hook pour supprimer une catégorie
 */
export function useDeleteCategory() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/categories/${id}`);
      return id;
    },
    onSuccess: () => {
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
