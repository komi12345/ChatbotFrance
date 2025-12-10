"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type { MessageStats, DailyMessageStats, StatusDistribution } from "@/types/message";

/**
 * Types pour les statistiques du dashboard
 */
export interface DashboardStats {
  total_messages: number;
  success_rate: number;
  total_contacts: number;
  total_campaigns: number;
  total_categories: number;
  estimated_cost: number;
}

export interface DailyStats {
  date: string;
  sent: number;
  delivered: number;
  read: number;
  failed: number;
}

export interface StatusStats {
  status: string;
  count: number;
  percentage: number;
}

export interface RecentMessage {
  id: number;
  contact_name: string | null;
  contact_phone: string;
  campaign_name: string;
  status: string;
  sent_at: string | null;
  message_type: string;
}

// Clés de cache pour React Query
export const statsKeys = {
  all: ["stats"] as const,
  dashboard: () => [...statsKeys.all, "dashboard"] as const,
  messages: () => [...statsKeys.all, "messages"] as const,
  daily: (days: number) => [...statsKeys.all, "daily", days] as const,
  distribution: () => [...statsKeys.all, "distribution"] as const,
  recent: (limit: number) => [...statsKeys.all, "recent", limit] as const,
};

/**
 * Hook pour récupérer les statistiques globales du dashboard
 */
export function useDashboardStats() {
  return useQuery({
    queryKey: statsKeys.dashboard(),
    queryFn: async (): Promise<DashboardStats> => {
      // Récupérer les stats des messages
      const messagesResponse = await api.get<MessageStats>("/messages/stats");
      const messageStats = messagesResponse.data;

      // Récupérer le nombre de contacts (réponse paginée)
      const contactsResponse = await api.get("/contacts?page=1&size=1");
      const totalContacts = contactsResponse.data.total || 0;

      // Récupérer le nombre de campagnes (réponse paginée)
      const campaignsResponse = await api.get("/campaigns?page=1&size=1");
      const totalCampaigns = campaignsResponse.data.total || 0;

      // Récupérer le nombre de catégories (réponse paginée)
      const categoriesResponse = await api.get("/categories?page=1&size=1");
      const totalCategories = categoriesResponse.data.total || 0;

      // Calculer le coût estimé (environ 0.05€ par message envoyé)
      const estimatedCost = messageStats.sent_count * 0.05;

      return {
        total_messages: messageStats.total_messages,
        success_rate: messageStats.success_rate,
        total_contacts: totalContacts,
        total_campaigns: totalCampaigns,
        total_categories: totalCategories,
        estimated_cost: estimatedCost,
      };
    },
    staleTime: 30000, // 30 secondes
  });
}

/**
 * Hook pour récupérer les statistiques globales des messages
 */
export function useMessageStats() {
  return useQuery({
    queryKey: statsKeys.messages(),
    queryFn: async (): Promise<MessageStats> => {
      const response = await api.get<MessageStats>("/messages/stats");
      return response.data;
    },
    staleTime: 30000,
  });
}

/**
 * Hook pour récupérer l'évolution des envois sur les derniers jours
 */
export function useDailyStats(days: number = 7) {
  return useQuery({
    queryKey: statsKeys.daily(days),
    queryFn: async (): Promise<DailyStats[]> => {
      // Récupérer tous les messages récents (la réponse est paginée avec items)
      const response = await api.get("/messages?limit=1000");
      const messages = response.data?.items || response.data || [];

      // Générer les dates des X derniers jours
      const dailyData: Record<string, DailyStats> = {};
      const today = new Date();
      
      for (let i = days - 1; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        const dateStr = date.toISOString().split("T")[0];
        dailyData[dateStr] = {
          date: dateStr,
          sent: 0,
          delivered: 0,
          read: 0,
          failed: 0,
        };
      }

      // Compter les messages par jour et statut
      // Utiliser sent_at ou created_at pour la date
      messages.forEach((msg: { sent_at: string | null; created_at: string | null; status: string }) => {
        const dateField = msg.sent_at || msg.created_at;
        if (dateField) {
          const dateStr = dateField.split("T")[0];
          if (dailyData[dateStr]) {
            if (msg.status === "sent") dailyData[dateStr].sent++;
            else if (msg.status === "delivered") dailyData[dateStr].delivered++;
            else if (msg.status === "read") dailyData[dateStr].read++;
            else if (msg.status === "failed") dailyData[dateStr].failed++;
          }
        }
      });

      return Object.values(dailyData);
    },
    staleTime: 60000, // 1 minute
  });
}

/**
 * Hook pour récupérer la répartition des statuts
 */
export function useStatusDistribution() {
  return useQuery({
    queryKey: statsKeys.distribution(),
    queryFn: async (): Promise<StatusStats[]> => {
      const response = await api.get<MessageStats>("/messages/stats");
      const stats = response.data;

      const total = stats.total_messages || 1;
      
      return [
        {
          status: "Envoyés",
          count: stats.sent_count,
          percentage: Math.round((stats.sent_count / total) * 100),
        },
        {
          status: "Délivrés",
          count: stats.delivered_count,
          percentage: Math.round((stats.delivered_count / total) * 100),
        },
        {
          status: "Lus",
          count: stats.read_count,
          percentage: Math.round((stats.read_count / total) * 100),
        },
        {
          status: "Échoués",
          count: stats.failed_count,
          percentage: Math.round((stats.failed_count / total) * 100),
        },
        {
          status: "En attente",
          count: stats.pending_count,
          percentage: Math.round((stats.pending_count / total) * 100),
        },
      ].filter(s => s.count > 0);
    },
    staleTime: 30000,
  });
}

/**
 * Hook pour récupérer les messages récents
 */
export function useRecentMessages(limit: number = 10) {
  return useQuery({
    queryKey: statsKeys.recent(limit),
    queryFn: async (): Promise<RecentMessage[]> => {
      const response = await api.get(`/messages?limit=${limit}`);
      // La réponse est paginée avec items
      const messages = response.data?.items || response.data || [];

      return messages.map((msg: {
        id: number;
        contact_name: string | null;
        contact_full_number: string;
        campaign_id: number;
        campaign_name: string | null;
        status: string;
        sent_at: string | null;
        message_type: string;
      }) => ({
        id: msg.id,
        contact_name: msg.contact_name,
        contact_phone: msg.contact_full_number,
        campaign_name: msg.campaign_name || `Campagne #${msg.campaign_id}`,
        status: msg.status,
        sent_at: msg.sent_at,
        message_type: msg.message_type,
      }));
    },
    staleTime: 30000,
  });
}

export default useDashboardStats;
