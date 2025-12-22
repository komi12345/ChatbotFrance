"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api, { PaginatedResponse } from "@/lib/api";
import type {
  Campaign,
  CampaignCreate,
  CampaignStats,
  CampaignFilters,
} from "@/types/campaign";

// Clés de cache pour React Query
export const campaignKeys = {
  all: ["campaigns"] as const,
  lists: () => [...campaignKeys.all, "list"] as const,
  list: (params: CampaignFilters) => [...campaignKeys.lists(), params] as const,
  details: () => [...campaignKeys.all, "detail"] as const,
  detail: (id: number) => [...campaignKeys.details(), id] as const,
  stats: (id: number) => [...campaignKeys.all, "stats", id] as const,
};

/**
 * Hook pour récupérer la liste des campagnes avec pagination
 */
export function useCampaigns(params: CampaignFilters = {}) {
  const { page = 1, size = 50, status } = params;

  return useQuery({
    queryKey: campaignKeys.list(params),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      searchParams.append("page", page.toString());
      searchParams.append("size", size.toString());
      if (status) {
        searchParams.append("status", status);
      }

      const response = await api.get<PaginatedResponse<Campaign>>(
        `/campaigns?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

/**
 * Hook pour récupérer les détails d'une campagne
 * Avec polling automatique toutes les 3 secondes si la campagne est en cours d'envoi
 */
export function useCampaign(id: number, options?: { enablePolling?: boolean }) {
  const { enablePolling = true } = options || {};
  
  return useQuery({
    queryKey: campaignKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Campaign>(`/campaigns/${id}`);
      return response.data;
    },
    enabled: !!id,
    // Polling toutes les 3 secondes si la campagne est en cours
    refetchInterval: (query) => {
      if (!enablePolling) return false;
      const data = query.state.data as Campaign | undefined;
      // Polling actif seulement si status = "sending"
      return data?.status === "sending" ? 3000 : false;
    },
  });
}


/**
 * Hook pour récupérer les statistiques d'une campagne
 * Avec polling automatique toutes les 3 secondes si la campagne est en cours d'envoi
 */
export function useCampaignStats(id: number, campaignStatus?: string) {
  return useQuery({
    queryKey: campaignKeys.stats(id),
    queryFn: async () => {
      const response = await api.get<CampaignStats>(`/campaigns/${id}/stats`);
      return response.data;
    },
    enabled: !!id,
    // Polling toutes les 3 secondes si la campagne est en cours
    refetchInterval: campaignStatus === "sending" ? 3000 : false,
  });
}

/**
 * Hook pour créer une campagne
 */
export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CampaignCreate) => {
      const response = await api.post<Campaign>("/campaigns", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour réessayer les messages échoués d'une campagne
 */
export function useRetryCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post<{ message: string; retried_count: number }>(
        `/campaigns/${id}/retry`
      );
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.stats(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour supprimer une campagne
 */
export function useDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/campaigns/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour lancer/relancer l'envoi d'une campagne
 */
export function useSendCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post<{ campaign_id: number; status: string; total_messages: number; message: string }>(
        `/campaigns/${id}/send`
      );
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.stats(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour remettre une campagne en brouillon (pour modification)
 */
export function useResetCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.put<Campaign>(`/campaigns/${id}`, { status: "draft" });
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

/**
 * Hook pour arrêter une campagne en cours
 */
export function useStopCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post<{ campaign_id: number; status: string; cancelled_messages: number; message: string }>(
        `/campaigns/${id}/stop`
      );
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.stats(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour supprimer une campagne avec option force
 */
export function useForceDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, force = false }: { id: number; force?: boolean }) => {
      await api.delete(`/campaigns/${id}?force=${force}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

/**
 * Hook pour relancer une campagne terminée ou échouée
 * Supprime les anciens messages et relance l'envoi pour tous les contacts
 */
export function useRelaunchCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post<{
        campaign_id: number;
        status: string;
        total_messages: number;
        deleted_messages: number;
        message: string;
      }>(`/campaigns/${id}/relaunch`);
      return response.data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.stats(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

export default useCampaigns;
