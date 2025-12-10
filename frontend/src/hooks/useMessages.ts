"use client";

import { useQuery } from "@tanstack/react-query";
import api, { PaginatedResponse } from "@/lib/api";
import type { Message, MessageFilters, MessageStats } from "@/types/message";

// Clés de cache pour React Query
export const messageKeys = {
  all: ["messages"] as const,
  lists: () => [...messageKeys.all, "list"] as const,
  list: (params: MessageFilters) => [...messageKeys.lists(), params] as const,
  details: () => [...messageKeys.all, "detail"] as const,
  detail: (id: number) => [...messageKeys.details(), id] as const,
  stats: () => [...messageKeys.all, "stats"] as const,
};

/**
 * Hook pour récupérer la liste des messages avec pagination
 */
export function useMessages(params: MessageFilters = {}) {
  const { page = 1, size = 50, campaign_id, contact_id, status, message_type } = params;

  return useQuery({
    queryKey: messageKeys.list(params),
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      searchParams.append("page", page.toString());
      searchParams.append("size", size.toString());
      if (campaign_id) {
        searchParams.append("campaign_id", campaign_id.toString());
      }
      if (contact_id) {
        searchParams.append("contact_id", contact_id.toString());
      }
      if (status) {
        searchParams.append("status", status);
      }
      if (message_type) {
        searchParams.append("message_type", message_type);
      }

      const response = await api.get<PaginatedResponse<Message>>(
        `/messages?${searchParams.toString()}`
      );
      return response.data;
    },
  });
}

/**
 * Hook pour récupérer les détails d'un message
 */
export function useMessage(id: number) {
  return useQuery({
    queryKey: messageKeys.detail(id),
    queryFn: async () => {
      const response = await api.get<Message>(`/messages/${id}`);
      return response.data;
    },
    enabled: !!id,
  });
}

/**
 * Hook pour récupérer les statistiques globales des messages
 */
export function useMessageStats() {
  return useQuery({
    queryKey: messageKeys.stats(),
    queryFn: async () => {
      const response = await api.get<MessageStats>("/messages/stats");
      return response.data;
    },
  });
}

export default useMessages;
