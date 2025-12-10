"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ErrorMessage, Skeleton } from "@/components/common";
import { WassengerInfoBanner } from "@/components/wassenger";
import { useCampaigns } from "@/hooks/useCampaigns";
import type { Campaign, CampaignStatus } from "@/types/campaign";
import {
  Plus,
  Send,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  MessageSquare,
} from "lucide-react";

/**
 * Badge de statut de campagne
 */
function StatusBadge({ status }: { status: CampaignStatus }) {
  const config: Record<CampaignStatus, { label: string; class: string; icon: typeof Clock }> = {
    draft: { label: "Brouillon", class: "bg-[#F3F4F6] text-[#374151]", icon: Clock },
    sending: { label: "En cours", class: "bg-[#DBEAFE] text-[#1D4ED8]", icon: Send },
    completed: { label: "Terminée", class: "bg-[#D1FAE5] text-[#059669]", icon: CheckCircle },
    failed: { label: "Échouée", class: "bg-[#FEE2E2] text-[#DC2626]", icon: XCircle },
    stopped: { label: "Arrêtée", class: "bg-[#FEF3C7] text-[#D97706]", icon: XCircle },
  };

  const { label, class: className, icon: Icon } = config[status] || { label: status, class: "bg-[#F3F4F6] text-[#374151]", icon: Clock };

  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-md font-medium ${className}`}>
      <Icon className="h-3 w-3" />
      {label}
    </span>
  );
}

/**
 * Carte de campagne
 */
function CampaignCard({
  campaign,
  onView,
}: {
  campaign: Campaign;
  onView: (campaign: Campaign) => void;
}) {
  const successRate =
    campaign.sent_count > 0
      ? ((campaign.success_count / campaign.sent_count) * 100).toFixed(1)
      : "0";


  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <h3 className="font-semibold truncate">{campaign.name}</h3>
          <StatusBadge status={campaign.status} />
        </div>
      </CardHeader>

      <CardContent className="pb-2">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Send className="h-4 w-4" />
            <span>{campaign.sent_count} envoyés</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span>{successRate}% réussite</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <XCircle className="h-4 w-4 text-red-500" />
            <span>{campaign.failed_count} échoués</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <MessageSquare className="h-4 w-4 text-purple-500" />
            <span>{campaign.interaction_count} interactions</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          Créée le {new Date(campaign.created_at).toLocaleDateString("fr-FR")}
        </p>
      </CardContent>

      <CardFooter className="pt-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onView(campaign)}
          className="w-full"
        >
          <Eye className="h-4 w-4 mr-2" />
          Voir les détails
        </Button>
      </CardFooter>
    </Card>
  );
}

/**
 * Page de liste des campagnes
 */
export default function CampaignsPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<CampaignStatus | "all">("all");

  const { data, isLoading, error } = useCampaigns({
    page,
    status: statusFilter === "all" ? undefined : statusFilter,
  });

  const handleView = (campaign: Campaign) => {
    router.push(`/campaigns/${campaign.id}`);
  };

  const handleCreate = () => {
    router.push("/campaigns/new");
  };


  return (
    <DashboardLayout title="Campagnes">
      <div className="space-y-6">
        {/* En-tête */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Campagnes</h2>
            <p className="text-muted-foreground">
              Gérez vos campagnes de messages WhatsApp
            </p>
          </div>
          <Button onClick={handleCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Nouvelle campagne
          </Button>
        </div>

        {/* Bandeau Wassenger */}
        <WassengerInfoBanner compact />

        {/* Filtres */}
        <div className="flex items-center gap-4">
          <div className="w-48">
            <Select
              value={statusFilter}
              onValueChange={(value) => {
                setStatusFilter(value as CampaignStatus | "all");
                setPage(1);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Filtrer par statut" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous les statuts</SelectItem>
                <SelectItem value="draft">Brouillon</SelectItem>
                <SelectItem value="sending">En cours</SelectItem>
                <SelectItem value="completed">Terminée</SelectItem>
                <SelectItem value="failed">Échouée</SelectItem>
                <SelectItem value="stopped">Arrêtée</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Erreur */}
        {error && (
          <ErrorMessage
            message="Une erreur est survenue lors du chargement des campagnes."
            title="Erreur de chargement"
          />
        )}

        {/* Chargement */}
        {isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <Skeleton className="h-5 w-3/4" />
                </CardHeader>
                <CardContent className="pb-2">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-4 w-2/3" />
                    <Skeleton className="h-4 w-1/3" />
                  </div>
                </CardContent>
                <CardFooter className="pt-2">
                  <Skeleton className="h-9 w-full" />
                </CardFooter>
              </Card>
            ))}
          </div>
        )}

        {/* Liste des campagnes */}
        {!isLoading && data && (
          <>
            {data.items.length === 0 ? (
              <div className="text-center py-12">
                <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium">Aucune campagne</h3>
                <p className="text-muted-foreground mb-4">
                  Créez votre première campagne pour commencer
                </p>
                <Button onClick={handleCreate}>
                  <Plus className="h-4 w-4 mr-2" />
                  Nouvelle campagne
                </Button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {data.items.map((campaign) => (
                  <CampaignCard
                    key={campaign.id}
                    campaign={campaign}
                    onView={handleView}
                  />
                ))}
              </div>
            )}

            {/* Pagination */}
            {data.pages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Précédent
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} sur {data.pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page === data.pages}
                >
                  Suivant
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
