"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { StatsCard, LineChart, PieChart, RecentMessages } from "@/components/dashboard";
import { WassengerInfoBanner } from "@/components/wassenger";
import { useAuth } from "@/hooks/useAuth";
import {
  useDashboardStats,
  useDailyStats,
  useStatusDistribution,
  useRecentMessages,
} from "@/hooks/useStats";
import { MessageSquare, Users, FolderOpen, Send, TrendingUp, DollarSign } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function DashboardPage() {
  const { user } = useAuth();
  const [showWassengerBanner, setShowWassengerBanner] = useState(true);
  
  const { data: dashboardStats, isLoading: isLoadingStats } = useDashboardStats();
  const { data: dailyStats, isLoading: isLoadingDaily } = useDailyStats(7);
  const { data: statusDistribution, isLoading: isLoadingDistribution } = useStatusDistribution();
  const { data: recentMessages, isLoading: isLoadingRecent } = useRecentMessages(10);

  const formatSuccessRate = (rate: number | undefined) => {
    if (rate === undefined) return "0%";
    return `${rate.toFixed(1)}%`;
  };

  const formatCost = (cost: number | undefined) => {
    if (cost === undefined) return "0,00 €";
    return `${cost.toFixed(2).replace(".", ",")} €`;
  };

  return (
    <DashboardLayout title="Dashboard">
      <div className="space-y-6">
        {/* Message de bienvenue */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-[#111827]">
              Bienvenue, {user?.email?.split("@")[0]} 👋
            </h2>
            <p className="text-[#6B7280] mt-1">
              Voici un aperçu de votre activité WhatsApp
            </p>
          </div>
          <Link href="/campaigns/new">
            <Button className="bg-emerald-500 hover:bg-emerald-500/90">
              <Send className="mr-2 h-4 w-4" />
              Nouvelle campagne
            </Button>
          </Link>
        </div>

        {/* Bandeau Wassenger */}
        {showWassengerBanner && (
          <WassengerInfoBanner onDismiss={() => setShowWassengerBanner(false)} />
        )}

        {/* Cartes de statistiques principales */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatsCard
            title="Messages envoyés"
            value={dashboardStats?.total_messages ?? 0}
            description="Total des messages"
            icon={MessageSquare}
            isLoading={isLoadingStats}
          />

          <StatsCard
            title="Taux de réussite"
            value={formatSuccessRate(dashboardStats?.success_rate)}
            description="Messages envoyés avec succès"
            icon={TrendingUp}
            trend={dashboardStats?.success_rate ? { value: 2.5, isPositive: true } : undefined}
            isLoading={isLoadingStats}
          />

          <StatsCard
            title="Contacts"
            value={dashboardStats?.total_contacts ?? 0}
            description="Contacts enregistrés"
            icon={Users}
            isLoading={isLoadingStats}
          />

          <StatsCard
            title="Coût estimé"
            value={formatCost(dashboardStats?.estimated_cost)}
            description="Basé sur 0,05€/message"
            icon={DollarSign}
            isLoading={isLoadingStats}
          />
        </div>

        {/* Cartes secondaires */}
        <div className="grid gap-4 sm:grid-cols-2">
          <StatsCard
            title="Catégories"
            value={dashboardStats?.total_categories ?? 0}
            description="Catégories créées"
            icon={FolderOpen}
            isLoading={isLoadingStats}
          />

          <StatsCard
            title="Campagnes"
            value={dashboardStats?.total_campaigns ?? 0}
            description="Campagnes lancées"
            icon={Send}
            isLoading={isLoadingStats}
          />
        </div>

        {/* Graphiques */}
        <div className="grid gap-6 lg:grid-cols-2">
          <LineChart
            data={dailyStats || []}
            title="Évolution des envois (7 derniers jours)"
            isLoading={isLoadingDaily}
          />

          <PieChart
            data={statusDistribution || []}
            title="Répartition des statuts"
            isLoading={isLoadingDistribution}
          />
        </div>

        {/* Messages récents */}
        <RecentMessages
          messages={recentMessages || []}
          title="Messages récents"
          isLoading={isLoadingRecent}
        />

        {/* Lien vers statistiques détaillées */}
        <div className="flex justify-center pt-4">
          <Link href="/statistics">
            <Button variant="outline" className="border-[#E5E7EB] text-[#374151] hover:bg-[#F9FAFB]">
              Voir les statistiques détaillées
            </Button>
          </Link>
        </div>
      </div>
    </DashboardLayout>
  );
}
