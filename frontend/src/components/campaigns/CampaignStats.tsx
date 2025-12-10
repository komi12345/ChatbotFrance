"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Send,
  CheckCircle,
  XCircle,
  MessageSquare,
  RefreshCw,
  Download,
} from "lucide-react";
import type { CampaignStats as CampaignStatsType } from "@/types/campaign";

interface CampaignStatsProps {
  /** Statistiques de la campagne */
  stats: CampaignStatsType;
  /** Callback pour retry les messages échoués */
  onRetry?: () => void;
  /** État de chargement du retry */
  isRetrying?: boolean;
  /** Callback pour exporter en CSV */
  onExport?: () => void;
}

/**
 * Affichage des statistiques détaillées d'une campagne
 */
export function CampaignStats({
  stats,
  onRetry,
  isRetrying = false,
  onExport,
}: CampaignStatsProps) {
  const successRate = stats.success_rate || 0;
  // Utiliser delivered_count + read_count comme success_count si non défini
  const successCount = stats.success_count ?? ((stats as any).delivered_count || 0) + ((stats as any).read_count || 0);
  const interactionCount = stats.interaction_count ?? 0;

  // Couleur du taux de réussite
  const getSuccessRateColor = (rate: number) => {
    if (rate >= 80) return "text-green-500";
    if (rate >= 50) return "text-yellow-500";
    return "text-red-500";
  };

  // Messages avec valeur par défaut
  const messages = stats.messages || [];

  // Exporter les données en CSV
  const handleExport = () => {
    if (onExport) {
      onExport();
      return;
    }

    // Export par défaut
    const headers = ["Contact", "Téléphone", "Type", "Statut", "Erreur", "Envoyé le"];
    const rows = messages.map((msg) => [
      msg.contact_name || "N/A",
      msg.contact_phone,
      msg.message_type === "message_1" ? "Message 1" : "Message 2",
      msg.status,
      msg.error_message || "",
      msg.sent_at ? new Date(msg.sent_at).toLocaleString("fr-FR") : "N/A",
    ]);

    const csvContent = [headers, ...rows]
      .map((row) => row.map((cell) => `"${cell}"`).join(","))
      .join("\n");

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `campagne-${stats.campaign_id || stats.id}-stats.csv`;
    link.click();
  };


  return (
    <div className="space-y-6">
      {/* Cartes de métriques */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total envoyés
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Send className="h-5 w-5 text-blue-500" />
              <span className="text-2xl font-bold">{stats.sent_count}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Réussis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span className="text-2xl font-bold">{successCount}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Échoués
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <XCircle className="h-5 w-5 text-red-500" />
              <span className="text-2xl font-bold">{stats.failed_count || 0}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Interactions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-purple-500" />
              <span className="text-2xl font-bold">{interactionCount}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Taux de réussite */}
      <Card>
        <CardHeader>
          <CardTitle>Taux de réussite</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="h-4 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 transition-all duration-500"
                  style={{ width: `${successRate}%` }}
                />
              </div>
            </div>
            <span className={`text-2xl font-bold ${getSuccessRateColor(successRate)}`}>
              {successRate.toFixed(1)}%
            </span>
          </div>
        </CardContent>
      </Card>


      {/* Actions */}
      <div className="flex gap-2">
        {(stats.failed_count || 0) > 0 && onRetry && (
          <Button onClick={onRetry} disabled={isRetrying} variant="outline">
            <RefreshCw className={`h-4 w-4 mr-2 ${isRetrying ? "animate-spin" : ""}`} />
            {isRetrying ? "Réessai en cours..." : `Réessayer (${stats.failed_count || 0})`}
          </Button>
        )}
        <Button onClick={handleExport} variant="outline">
          <Download className="h-4 w-4 mr-2" />
          Exporter CSV
        </Button>
      </div>

      {/* Liste des messages */}
      {messages.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Détails par contact</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2">Contact</th>
                    <th className="text-left py-2 px-2">Téléphone</th>
                    <th className="text-left py-2 px-2">Type</th>
                    <th className="text-left py-2 px-2">Statut</th>
                    <th className="text-left py-2 px-2">Envoyé le</th>
                  </tr>
                </thead>
                <tbody>
                  {messages.map((msg) => (
                    <tr key={msg.id} className="border-b hover:bg-muted/50">
                      <td className="py-2 px-2">{msg.contact_name || "N/A"}</td>
                      <td className="py-2 px-2 font-mono text-xs">{msg.contact_phone}</td>
                      <td className="py-2 px-2">
                        <span className="text-xs bg-muted px-2 py-0.5 rounded">
                          {msg.message_type === "message_1" ? "Msg 1" : "Msg 2"}
                        </span>
                      </td>
                      <td className="py-2 px-2">
                        <StatusBadge status={msg.status} />
                      </td>
                      <td className="py-2 px-2 text-muted-foreground">
                        {msg.sent_at
                          ? new Date(msg.sent_at).toLocaleString("fr-FR")
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/**
 * Badge de statut coloré
 */
function StatusBadge({ status }: { status: string }) {
  const getStatusStyle = () => {
    switch (status) {
      case "sent":
        return "bg-blue-100 text-blue-700";
      case "delivered":
        return "bg-green-100 text-green-700";
      case "read":
        return "bg-purple-100 text-purple-700";
      case "failed":
        return "bg-red-100 text-red-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getStatusLabel = () => {
    switch (status) {
      case "pending":
        return "En attente";
      case "sent":
        return "Envoyé";
      case "delivered":
        return "Livré";
      case "read":
        return "Lu";
      case "failed":
        return "Échoué";
      default:
        return status;
    }
  };

  return (
    <span className={`text-xs px-2 py-0.5 rounded ${getStatusStyle()}`}>
      {getStatusLabel()}
    </span>
  );
}

export default CampaignStats;
