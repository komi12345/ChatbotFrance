"use client";

import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  MonitoringStats,
  DailyHistory,
  RecentError,
} from "@/types/monitoring";

/**
 * Cache keys for React Query
 */
export const monitoringKeys = {
  all: ["monitoring"] as const,
  stats: () => [...monitoringKeys.all, "stats"] as const,
  history: (days: number) => [...monitoringKeys.all, "history", days] as const,
  errors: (limit: number) => [...monitoringKeys.all, "errors", limit] as const,
};

/**
 * Default auto-refresh interval (30 seconds)
 * Optimized from 10s to 30s to reduce network requests by 66%
 * Requirements: 4.5
 */
const DEFAULT_REFRESH_INTERVAL = 30000;

/**
 * Hook to fetch real-time monitoring statistics
 * GET /api/monitoring/stats
 * Requirements: 4.5
 * 
 * @param refreshInterval - Auto-refresh interval in milliseconds (default: 10000)
 * @returns Query result with MonitoringStats
 */
export function useMonitoringStats(refreshInterval: number = DEFAULT_REFRESH_INTERVAL) {
  return useQuery({
    queryKey: monitoringKeys.stats(),
    queryFn: async (): Promise<MonitoringStats> => {
      const response = await api.get<MonitoringStats>("/monitoring/stats");
      return response.data;
    },
    refetchInterval: refreshInterval,
    staleTime: refreshInterval / 2, // Consider data stale after half the refresh interval
  });
}

/**
 * Hook to fetch historical monitoring data
 * GET /api/monitoring/history?days=7
 * Requirements: 4.5
 * 
 * @param days - Number of days of history to fetch (default: 7)
 * @param refreshInterval - Auto-refresh interval in milliseconds (default: 10000)
 * @returns Query result with DailyHistory array
 */
export function useMonitoringHistory(
  days: number = 7,
  refreshInterval: number = DEFAULT_REFRESH_INTERVAL
) {
  return useQuery({
    queryKey: monitoringKeys.history(days),
    queryFn: async (): Promise<DailyHistory[]> => {
      const response = await api.get<DailyHistory[]>(
        `/monitoring/history?days=${days}`
      );
      return response.data;
    },
    refetchInterval: refreshInterval,
    staleTime: refreshInterval / 2,
  });
}

/**
 * Hook to fetch recent errors
 * GET /api/monitoring/errors?limit=10
 * Requirements: 4.5
 * 
 * @param limit - Maximum number of errors to fetch (default: 10)
 * @param refreshInterval - Auto-refresh interval in milliseconds (default: 10000)
 * @returns Query result with RecentError array
 */
export function useMonitoringErrors(
  limit: number = 10,
  refreshInterval: number = DEFAULT_REFRESH_INTERVAL
) {
  return useQuery({
    queryKey: monitoringKeys.errors(limit),
    queryFn: async (): Promise<RecentError[]> => {
      const response = await api.get<RecentError[]>(
        `/monitoring/errors?limit=${limit}`
      );
      return response.data;
    },
    refetchInterval: refreshInterval,
    staleTime: refreshInterval / 2,
  });
}

/**
 * Combined hook for all monitoring data
 * Convenience hook that fetches stats, history, and errors together
 * Requirements: 4.5
 * 
 * @param refreshInterval - Auto-refresh interval in milliseconds (default: 10000)
 * @returns Object containing all monitoring queries
 */
export function useMonitoring(refreshInterval: number = DEFAULT_REFRESH_INTERVAL) {
  const statsQuery = useMonitoringStats(refreshInterval);
  const historyQuery = useMonitoringHistory(7, refreshInterval);
  const errorsQuery = useMonitoringErrors(10, refreshInterval);

  return {
    stats: statsQuery.data,
    history: historyQuery.data ?? [],
    errors: errorsQuery.data ?? [],
    isLoading: statsQuery.isLoading || historyQuery.isLoading || errorsQuery.isLoading,
    isError: statsQuery.isError || historyQuery.isError || errorsQuery.isError,
    error: statsQuery.error || historyQuery.error || errorsQuery.error,
    refetch: () => {
      statsQuery.refetch();
      historyQuery.refetch();
      errorsQuery.refetch();
    },
  };
}

export default useMonitoring;
