"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api, { PaginatedResponse } from "@/lib/api";
import type {
  Contact,
  ContactCreate,
  ContactUpdate,
  ContactFilters,
  ContactImportResult,
  WhatsAppVerificationResult,
  BulkVerificationResponse,
} from "@/types/contact";

// Clés de cache pour React Query
export const contactKeys = {
  all: ["contacts"] as const,
  lists: () => [...contactKeys.all, "list"] as const,
  list: (params: ContactFilters) => [...contactKeys.lists(), params] as const,
  details: () => [...contactKeys.all, "detail"] as const,
  detail: (id: number) => [...contactKeys.details(), id] as const,
};

/**
 * Hook pour récupérer la liste des contacts avec pagination et filtres
 * Requirements: 2.3 - staleTime de 2 minutes pour les listes
 */
export function useContacts(params: ContactFilters = {}) {
  const { page = 1, size = 50, search = "", category_id, whatsapp_status } = params;

  return useQuery({
    queryKey: contactKeys.list({ page, size, search, category_id, whatsapp_status }),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      searchParams.append("page", page.toString());
      searchParams.append("size", size.toString());
      if (search) {
        searchParams.append("search", search);
      }
      if (category_id) {
        searchParams.append("category_id", category_id.toString());
      }
      // WhatsApp status filter - Requirements 4.1, 4.2
      if (whatsapp_status) {
        searchParams.append("whatsapp_status", whatsapp_status);
      }

      const response = await api.get<PaginatedResponse<Contact>>(
        `/contacts?${searchParams.toString()}`
      );
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes - Requirements 2.3
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook pour récupérer les détails d'un contact
 * Requirements: 2.3 - staleTime de 2 minutes pour les listes
 */
export function useContact(id: number) {
  return useQuery({
    queryKey: contactKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Contact>(`/contacts/${id}`);
      return response.data;
    },
    enabled: !!id,
    staleTime: 2 * 60 * 1000, // 2 minutes - Requirements 2.3
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}


/**
 * Hook pour créer un contact avec mise à jour optimiste
 * Requirements: 2.1 - Mise à jour optimiste des statistiques
 */
export function useCreateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: ContactCreate) => {
      const response = await api.post<Contact>("/contacts", data);
      return response.data;
    },
    onMutate: async () => {
      // Annuler les requêtes en cours pour éviter les conflits
      await queryClient.cancelQueries({ queryKey: ["stats"] });

      // Snapshot des données actuelles pour rollback
      const previousDashboardStats = queryClient.getQueryData(["stats", "dashboard"]);

      // Mise à jour optimiste du compteur de contacts
      queryClient.setQueryData(["stats", "dashboard"], (old: { total_contacts?: number } | undefined) => {
        if (!old) return old;
        return {
          ...old,
          total_contacts: (old.total_contacts || 0) + 1,
        };
      });

      // Retourner le contexte pour rollback
      return { previousDashboardStats };
    },
    onError: (_err, _newContact, context) => {
      // Rollback en cas d'erreur
      if (context?.previousDashboardStats) {
        queryClient.setQueryData(["stats", "dashboard"], context.previousDashboardStats);
      }
    },
    onSettled: () => {
      // Invalider pour synchroniser avec le serveur
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      // Invalider les stats de vérification WhatsApp
      queryClient.invalidateQueries({ queryKey: [...contactKeys.all, "verification-stats"] });
    },
  });
}

/**
 * Hook pour mettre à jour un contact
 */
export function useUpdateContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: ContactUpdate }) => {
      const response = await api.put<Contact>(`/contacts/${id}`, data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      // Invalider tous les caches liés (contacts et catégories)
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contactKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      // Invalider les stats de vérification WhatsApp
      queryClient.invalidateQueries({ queryKey: [...contactKeys.all, "verification-stats"] });
    },
  });
}

/**
 * Hook pour supprimer un contact
 */
export function useDeleteContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/contacts/${id}`);
      return id;
    },
    onSuccess: () => {
      // Invalider tous les caches liés
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      // Invalider les stats de vérification WhatsApp
      queryClient.invalidateQueries({ queryKey: [...contactKeys.all, "verification-stats"] });
    },
  });
}

/**
 * Hook pour importer des contacts depuis un fichier CSV
 * Invalide tous les caches liés après import réussi
 */
export function useImportContacts() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File): Promise<ContactImportResult> => {
      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post<ContactImportResult>(
        "/contacts/import",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      
      // S'assurer que la réponse contient les données attendues
      const result = response.data;
      
      // Valider la structure de la réponse
      if (typeof result.success !== 'number' || typeof result.failed !== 'number') {
        throw new Error("Réponse invalide du serveur");
      }
      
      return {
        success: result.success || 0,
        failed: result.failed || 0,
        skipped: result.skipped || 0,
        total: result.total || (result.success + result.failed + (result.skipped || 0)),
        errors: result.errors || [],
      };
    },
    onSuccess: () => {
      // Invalider tous les caches liés pour mise à jour instantanée
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      queryClient.invalidateQueries({ queryKey: [...contactKeys.all, "verification-stats"] });
    },
  });
}

/**
 * Hook pour vérifier le statut WhatsApp d'un contact
 * Mutation for POST /api/verify/{contact_id}
 * Requirements: 3.1
 */
export function useVerifyContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (contactId: number) => {
      const response = await api.post<WhatsAppVerificationResult>(
        `/verify/${contactId}`
      );
      return response.data;
    },
    onSuccess: (data) => {
      // Invalider le cache des contacts pour refléter le nouveau statut
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contactKeys.detail(data.contact_id) });
      // Invalider aussi les stats car elles incluent les comptages de vérification
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour vérifier le statut WhatsApp de plusieurs contacts en masse
 * Mutation for POST /api/verify/bulk
 * Requirements: 6.1
 */
export function useBulkVerify() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (contactIds: number[]) => {
      const response = await api.post<BulkVerificationResponse>(
        "/verify/bulk",
        { contact_ids: contactIds }
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalider le cache des contacts - les résultats arriveront de manière asynchrone
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Interface pour les statistiques de vérification WhatsApp
 * Requirements: 5.1
 */
export interface WhatsAppVerificationStats {
  verified_count: number;
  not_whatsapp_count: number;
  pending_count: number;
  total_count: number;
}

/**
 * Hook pour récupérer les statistiques de vérification WhatsApp
 * Requirements: 5.1, 2.3 - staleTime de 2 minutes
 */
export function useWhatsAppVerificationStats() {
  return useQuery({
    queryKey: [...contactKeys.all, "verification-stats"],
    queryFn: async () => {
      const response = await api.get<WhatsAppVerificationStats>("/verify/stats");
      return response.data;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes - Requirements 2.3
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

export default useContacts;
