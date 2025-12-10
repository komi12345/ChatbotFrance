"use client";

import { useState, useMemo } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { StatsCard, LineChart, PieChart } from "@/components/dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SkeletonTableRow } from "@/components/common";
import {
  useMessageStats,
  useDailyStats,
  useStatusDistribution,
  useRecentMessages,
} from "@/hooks/useStats";
import {
  MessageSquare,
  TrendingUp,
  CheckCircle,
  CheckCircle2,
  XCircle,
  Clock,
  Download,
  Send,
  Search,
  Filter,
} from "lucide-react";

/**
 * Configuration des statuts pour l'affichage
 */
const STATUS_CONFIG: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" | "success" | "warning" }> = {
  pending: { label: "En attente", variant: "warning" },
  sent: { label: "Envoyé", variant: "default" },
  delivered: { label: "Délivré", variant: "success" },
  read: { label: "Lu", variant: "success" },
  failed: { label: "Échoué", variant: "destructive" },
};

/**
 * Page Statistiques - Vue détaillée des statistiques
 * Affiche les métriques détaillées avec recherche, filtrage et export CSV
 * 
 * Exigences: 6.7, 6.8, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8
 */
export default function StatisticsPage() {
  // États pour la recherche et le filtrage
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // Récupération des données
  const { data: messageStats, isLoading: isLoadingStats } = useMessageStats();
  const { data: dailyStats, isLoading: isLoadingDaily } = useDailyStats(7);
  const { data: statusDistribution, isLoading: isLoadingDistribution } = useStatusDistribution();
  const { data: allMessages, isLoading: isLoadingMessages } = useRecentMessages(100);

  // Filtrage des messages
  const filteredMessages = useMemo(() => {
    if (!allMessages) return [];
    
    return allMessages.filter((msg) => {
      // Filtre par recherche (nom ou téléphone)
      const matchesSearch = searchQuery === "" ||
        (msg.contact_name?.toLowerCase().includes(searchQuery.toLowerCase())) ||
        msg.contact_phone.includes(searchQuery);
      
      // Filtre par statut
      const matchesStatus = statusFilter === "all" || msg.status === statusFilter;
      
      return matchesSearch && matchesStatus;
    });
  }, [allMessages, searchQuery, statusFilter]);

  // Pagination
  const totalPages = Math.ceil(filteredMessages.length / itemsPerPage);
  const paginatedMessages = filteredMessages.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Formatage du taux
  const formatRate = (rate: number | undefined) => {
    if (rate === undefined) return "0%";
    return `${rate.toFixed(1)}%`;
  };

  // Export CSV
  const handleExportCSV = () => {
    if (!filteredMessages || filteredMessages.length === 0) return;

    const headers = ["ID", "Contact", "Téléphone", "Campagne", "Type", "Statut", "Date d'envoi"];
    const rows = filteredMessages.map((msg) => [
      msg.id,
      msg.contact_name || "",
      msg.contact_phone,
      msg.campaign_name,
      msg.message_type === "message_1" ? "Message 1" : "Message 2",
      STATUS_CONFIG[msg.status]?.label || msg.status,
      msg.sent_at ? new Date(msg.sent_at).toLocaleString("fr-FR") : "",
    ]);

    const csvContent = [
      headers.join(";"),
      ...rows.map((row) => row.join(";")),
    ].join("\n");

    const blob = new Blob(["\ufeff" + csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `statistiques_messages_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
  };

  // Formatage de la date
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleString("fr-FR", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <DashboardLayout title="Statistiques détaillées">
      <div className="space-y-6">
        {/* Cartes de statistiques principales */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
          <StatsCard
            title="Total messages"
            value={messageStats?.total_messages ?? 0}
            icon={MessageSquare}
            isLoading={isLoadingStats}
          />
          <StatsCard
            title="Taux de réussite"
            value={formatRate(messageStats?.success_rate)}
            icon={TrendingUp}
            isLoading={isLoadingStats}
          />
          <StatsCard
            title="Envoyés"
            value={messageStats?.sent_count ?? 0}
            icon={Send}
            isLoading={isLoadingStats}
          />
          <StatsCard
            title="Délivrés"
            value={messageStats?.delivered_count ?? 0}
            description={formatRate(messageStats?.delivery_rate)}
            icon={CheckCircle2}
            isLoading={isLoadingStats}
          />
          <StatsCard
            title="Échoués"
            value={messageStats?.failed_count ?? 0}
            icon={XCircle}
            isLoading={isLoadingStats}
          />
          <StatsCard
            title="En attente"
            value={messageStats?.pending_count ?? 0}
            icon={Clock}
            isLoading={isLoadingStats}
          />
        </div>

        {/* Graphiques */}
        <div className="grid gap-4 md:grid-cols-2">
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

        {/* Historique des messages avec recherche et filtrage */}
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <CardTitle>Historique des messages</CardTitle>
              <Button variant="outline" onClick={handleExportCSV} disabled={filteredMessages.length === 0}>
                <Download className="mr-2 h-4 w-4" />
                Exporter CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {/* Filtres */}
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Rechercher par nom ou téléphone..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    setCurrentPage(1);
                  }}
                  className="pl-10"
                />
              </div>
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <Select
                  value={statusFilter}
                  onValueChange={(value) => {
                    setStatusFilter(value);
                    setCurrentPage(1);
                  }}
                >
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Filtrer par statut" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tous les statuts</SelectItem>
                    <SelectItem value="pending">En attente</SelectItem>
                    <SelectItem value="sent">Envoyé</SelectItem>
                    <SelectItem value="delivered">Délivré</SelectItem>
                    <SelectItem value="read">Lu</SelectItem>
                    <SelectItem value="failed">Échoué</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Tableau des messages */}
            {isLoadingMessages ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-3 px-2 font-medium">Contact</th>
                      <th className="text-left py-3 px-2 font-medium">Téléphone</th>
                      <th className="text-left py-3 px-2 font-medium hidden md:table-cell">Campagne</th>
                      <th className="text-left py-3 px-2 font-medium hidden sm:table-cell">Type</th>
                      <th className="text-left py-3 px-2 font-medium">Statut</th>
                      <th className="text-left py-3 px-2 font-medium hidden lg:table-cell">Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...Array(5)].map((_, i) => (
                      <SkeletonTableRow key={i} columns={6} />
                    ))}
                  </tbody>
                </table>
              </div>
            ) : paginatedMessages.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                Aucun message trouvé
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3 px-2 font-medium">Contact</th>
                        <th className="text-left py-3 px-2 font-medium">Téléphone</th>
                        <th className="text-left py-3 px-2 font-medium hidden md:table-cell">Campagne</th>
                        <th className="text-left py-3 px-2 font-medium hidden sm:table-cell">Type</th>
                        <th className="text-left py-3 px-2 font-medium">Statut</th>
                        <th className="text-left py-3 px-2 font-medium hidden lg:table-cell">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {paginatedMessages.map((msg) => (
                        <tr key={msg.id} className="border-b hover:bg-muted/50">
                          <td className="py-3 px-2">
                            {msg.contact_name || <span className="text-muted-foreground">—</span>}
                          </td>
                          <td className="py-3 px-2 font-mono text-sm">{msg.contact_phone}</td>
                          <td className="py-3 px-2 hidden md:table-cell">{msg.campaign_name}</td>
                          <td className="py-3 px-2 hidden sm:table-cell">
                            <Badge variant="outline">
                              {msg.message_type === "message_1" ? "Msg 1" : "Msg 2"}
                            </Badge>
                          </td>
                          <td className="py-3 px-2">
                            <Badge variant={STATUS_CONFIG[msg.status]?.variant || "secondary"}>
                              {STATUS_CONFIG[msg.status]?.label || msg.status}
                            </Badge>
                          </td>
                          <td className="py-3 px-2 text-sm text-muted-foreground hidden lg:table-cell">
                            {formatDate(msg.sent_at)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between mt-4">
                    <p className="text-sm text-muted-foreground">
                      {filteredMessages.length} message(s) trouvé(s)
                    </p>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                      >
                        Précédent
                      </Button>
                      <span className="text-sm">
                        Page {currentPage} sur {totalPages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                      >
                        Suivant
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
