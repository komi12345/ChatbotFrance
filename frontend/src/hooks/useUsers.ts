"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type { User, UserCreate, UserUpdate } from "@/types/auth";

// Clés de cache pour React Query
const USERS_KEY = "users";

interface UseUsersOptions {
  search?: string;
  role?: "super_admin" | "admin";
  is_active?: boolean;
}

/**
 * Hook pour récupérer la liste des utilisateurs
 * Accessible uniquement aux Super Admins
 */
export function useUsers(options: UseUsersOptions = {}) {
  const { search, role, is_active } = options;

  return useQuery({
    queryKey: [USERS_KEY, { search, role, is_active }],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (search) params.append("search", search);
      if (role) params.append("role", role);
      if (is_active !== undefined) params.append("is_active", String(is_active));

      const response = await api.get<User[]>(`/users?${params.toString()}`);
      return response.data;
    },
  });
}

/**
 * Hook pour récupérer un utilisateur par ID
 */
export function useUser(userId: number | null) {
  return useQuery({
    queryKey: [USERS_KEY, userId],
    queryFn: async () => {
      if (!userId) return null;
      const response = await api.get<User>(`/users/${userId}`);
      return response.data;
    },
    enabled: !!userId,
  });
}

/**
 * Hook pour créer un utilisateur
 */
export function useCreateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UserCreate) => {
      const response = await api.post<User>("/users", data);
      return response.data;
    },
    onSuccess: () => {
      // Invalider le cache pour rafraîchir la liste
      queryClient.invalidateQueries({ queryKey: [USERS_KEY] });
    },
  });
}

/**
 * Hook pour mettre à jour un utilisateur
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: UserUpdate }) => {
      const response = await api.put<User>(`/users/${id}`, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      // Invalider le cache pour rafraîchir la liste et l'utilisateur spécifique
      queryClient.invalidateQueries({ queryKey: [USERS_KEY] });
      queryClient.invalidateQueries({ queryKey: [USERS_KEY, variables.id] });
    },
  });
}

/**
 * Hook pour supprimer un utilisateur
 */
export function useDeleteUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (userId: number) => {
      await api.delete(`/users/${userId}`);
      return userId;
    },
    onSuccess: () => {
      // Invalider le cache pour rafraîchir la liste
      queryClient.invalidateQueries({ queryKey: [USERS_KEY] });
    },
  });
}

export default useUsers;
