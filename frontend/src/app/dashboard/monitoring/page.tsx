"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { StatsCard } from "@/components/dashboard";
import { MessageGauge, CapacityCard, ErrorsList } from "@/components/monitoring";
import { useMonitoring } from "@/hooks/useMonitoring";
import { 
  MessageSquare, 
  MessageCircle, 
  AlertTriangle, 
  TrendingUp,
  RefreshCw 
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Line,
} from "recharts";
import type { DailyHistory } from "@/types/monitoring";

/**
 * Format date for chart display
 */
function formatDate(dateStr: string, short: boolean = false): string {
  try {
    const date = new Date(dateStr);
    if (short) {
      return date.toLocaleDateString("fr-FR", { day: "2-digit" });
    }
    return date.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
  } catch {
    return dateStr;
  }
}

/**
 * Hook to detect screen size for responsive chart
 */
function useScreenSize() {
  const [screenSize, setScreenSize] = useState<"mobile" | "tablet" | "desktop">("desktop");

  useEffect(() => {
    const checkSize = () => {
      if (window.innerWidth < 640) {
        setScreenSize("mobile");
      } else if (window.innerWidth < 1024) {
        setScreenSize("tablet");
      } else {
        setScreenSize("desktop");
      }
    };

    checkSize();
    window.addEventListener("resize", checkSize);
    return () => window.removeEventListener("resize", checkSize);
  }, []);

  return screenSize;
}


/**
 * Monitoring History Chart Component
 * Displays 7-day history of message_1, message_2, and errors
 * Requirements: 4.4
 */
interface MonitoringChartProps {
  data: DailyHistory[];
  isLoading?: boolean;
}

function MonitoringHistoryChart({ data, isLoading = false }: MonitoringChartProps) {
  const screenSize = useScreenSize();
  const isMobile = screenSize === "mobile";
  const isTablet = screenSize === "tablet";

  if (isLoading) {
    return (
      <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
        <h3 className="text-lg font-semibold text-[#111827] mb-4">
          Historique des 7 derniers jours
        </h3>
        <div className="h-[250px] sm:h-[300px] bg-[#F3F4F6] animate-pulse rounded-xl" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
        <h3 className="text-lg font-semibold text-[#111827] mb-4">
          Historique des 7 derniers jours
        </h3>
        <div className="h-[250px] sm:h-[300px] flex items-center justify-center">
          <p className="text-[#6B7280] text-sm">Aucune donnée disponible</p>
        </div>
      </div>
    );
  }

  const margins = isMobile
    ? { top: 10, right: 10, left: 0, bottom: 5 }
    : isTablet
    ? { top: 10, right: 20, left: 10, bottom: 5 }
    : { top: 10, right: 30, left: 20, bottom: 5 };

  // Transform data for chart (add total field)
  const chartData = data.map((item) => ({
    ...item,
    total: item.message_1 + item.message_2,
  }));

  return (
    <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
      <h3 className="text-lg font-semibold text-[#111827] mb-4">
        Historique des 7 derniers jours
      </h3>
      <div className="h-[250px] sm:h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={margins}>
            <defs>
              <linearGradient id="colorMsg1" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.1} />
                <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorMsg2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.1} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="date"
              tickFormatter={(val) => formatDate(val, isMobile)}
              tick={{ fill: "#6B7280", fontSize: isMobile ? 10 : 12 }}
              tickMargin={isMobile ? 5 : 10}
              interval={isMobile ? 1 : 0}
              axisLine={{ stroke: "#E5E7EB" }}
              tickLine={{ stroke: "#E5E7EB" }}
            />
            <YAxis
              tick={{ fill: "#6B7280", fontSize: isMobile ? 10 : 12 }}
              width={isMobile ? 30 : 40}
              axisLine={{ stroke: "#E5E7EB" }}
              tickLine={{ stroke: "#E5E7EB" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#FFFFFF",
                border: "1px solid #E5E7EB",
                borderRadius: "12px",
                fontSize: isMobile ? "12px" : "14px",
                boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
              }}
              labelFormatter={(val) => formatDate(val as string, false)}
            />
            <Legend
              wrapperStyle={{ fontSize: isMobile ? "10px" : "12px", paddingTop: "10px" }}
              iconSize={isMobile ? 8 : 14}
            />
            <Area
              type="monotone"
              dataKey="message_1"
              name="Message 1"
              stroke="#10B981"
              strokeWidth={2}
              fill="url(#colorMsg1)"
              dot={isMobile ? false : { fill: "#10B981", strokeWidth: 2, r: 3 }}
              activeDot={{ r: isMobile ? 4 : 6, fill: "#10B981" }}
            />
            <Area
              type="monotone"
              dataKey="message_2"
              name="Message 2"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#colorMsg2)"
              dot={isMobile ? false : { fill: "#3B82F6", strokeWidth: 2, r: 3 }}
              activeDot={{ r: isMobile ? 4 : 6, fill: "#3B82F6" }}
            />
            <Line
              type="monotone"
              dataKey="errors"
              name="Erreurs"
              stroke="#EF4444"
              strokeWidth={2}
              dot={isMobile ? false : { fill: "#EF4444", strokeWidth: 2, r: 3 }}
              activeDot={{ r: isMobile ? 4 : 6 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}


/**
 * Monitoring Dashboard Page
 * Requirements: 4.1, 4.2, 4.3, 4.4, 8.3
 * - Displays gauge showing messages sent vs daily limit (500)
 * - Displays separate counters for message_1 and message_2
 * - Displays current interaction rate
 * - Displays line chart showing last 7 days
 * - Uses existing DashboardLayout and Tailwind CSS styling
 */
export default function MonitoringPage() {
  const { stats, history, errors, isLoading, refetch } = useMonitoring();

  // Calculate interaction rate percentage for display
  const interactionRatePercent = stats?.interaction_rate 
    ? (stats.interaction_rate * 100).toFixed(1) 
    : "0.0";

  return (
    <DashboardLayout title="Monitoring WhatsApp">
      <div className="space-y-6">
        {/* Header with refresh button */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-[#111827]">
              Monitoring WhatsApp 📊
            </h2>
            <p className="text-[#6B7280] mt-1">
              Suivi en temps réel des messages envoyés (limite : 1000/jour)
            </p>
          </div>
          <Button 
            variant="outline" 
            onClick={() => refetch()}
            className="border-[#E5E7EB] text-[#374151] hover:bg-[#F9FAFB]"
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Actualiser
          </Button>
        </div>

        {/* Main gauge and capacity section */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Message Gauge - Takes 1 column */}
          <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50 flex items-center justify-center">
            <MessageGauge
              sent={stats?.total_sent ?? 0}
              limit={stats?.daily_limit ?? 500}
              alertLevel={stats?.alert_level ?? "ok"}
              isLoading={isLoading}
            />
          </div>

          {/* Capacity Card - Takes 1 column */}
          <CapacityCard
            remainingCapacity={stats?.remaining_capacity ?? 0}
            remainingMessages={stats?.remaining ?? 1000}
            interactionRate={stats?.interaction_rate ?? 0}
            isBlocked={stats?.is_blocked ?? false}
            isLoading={isLoading}
          />

          {/* Stats Cards - Takes 1 column with 2 stacked cards */}
          <div className="space-y-4">
            <StatsCard
              title="Message 1 (Initial)"
              value={stats?.message_1_count ?? 0}
              description="Premiers contacts envoyés"
              icon={MessageSquare}
              isLoading={isLoading}
            />
            <StatsCard
              title="Message 2 (Suivi)"
              value={stats?.message_2_count ?? 0}
              description="Messages de suivi envoyés"
              icon={MessageCircle}
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* Secondary stats row */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <StatsCard
            title="Taux d'interaction"
            value={`${interactionRatePercent}%`}
            description="Contacts ayant répondu au Message 1"
            icon={TrendingUp}
            isLoading={isLoading}
          />
          <StatsCard
            title="Erreurs aujourd'hui"
            value={stats?.error_count ?? 0}
            description={
              stats && stats.total_sent > 0
                ? `${((stats.error_count / stats.total_sent) * 100).toFixed(1)}% du total`
                : "Aucun message envoyé"
            }
            icon={AlertTriangle}
            isLoading={isLoading}
          />
          <StatsCard
            title="Dernière synchronisation"
            value={
              stats?.last_sync
                ? new Date(stats.last_sync).toLocaleTimeString("fr-FR", {
                    hour: "2-digit",
                    minute: "2-digit",
                  })
                : "—"
            }
            description={
              stats?.last_sync
                ? new Date(stats.last_sync).toLocaleDateString("fr-FR")
                : "Pas encore synchronisé"
            }
            icon={RefreshCw}
            isLoading={isLoading}
          />
        </div>

        {/* History chart and errors list */}
        <div className="grid gap-6 lg:grid-cols-2">
          <MonitoringHistoryChart data={history} isLoading={isLoading} />
          <ErrorsList
            errors={errors}
            totalSent={stats?.total_sent ?? 0}
            errorCount={stats?.error_count ?? 0}
            isLoading={isLoading}
          />
        </div>

        {/* Info footer */}
        <div className="rounded-2xl bg-blue-50 p-4 border border-blue-100">
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100">
              <MessageSquare className="h-4 w-4 text-blue-600" />
            </div>
            <div>
              <h4 className="text-sm font-medium text-blue-900">
                À propos de la limite quotidienne
              </h4>
              <p className="mt-1 text-xs text-blue-700">
                La limite est configurée à 1000 messages par jour pour protéger votre numéro WhatsApp.
                Cette limite se réinitialise automatiquement à minuit (UTC).
                La capacité restante est calculée en tenant compte du taux d&apos;interaction
                (contacts susceptibles de répondre et déclencher un Message 2).
              </p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
