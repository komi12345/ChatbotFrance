"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { CampaignForm } from "@/components/campaigns/CampaignForm";
import { LoadingSpinner, ErrorMessage, useToast } from "@/components/common";
import { useCategories } from "@/hooks/useCategories";
import { useCreateCampaign } from "@/hooks/useCampaigns";
import type { CampaignCreate } from "@/types/campaign";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * Page de création d'une nouvelle campagne
 * Exigences: 4.1, 4.2, 4.3, 14.1, 14.2, 14.3
 */
export default function NewCampaignPage() {
  const router = useRouter();
  const toast = useToast();
  
  // Récupérer toutes les catégories avec refetch forcé pour avoir les contact_count à jour
  const { data: categoriesData, isLoading: categoriesLoading, error: categoriesError, refetch } = useCategories({
    page: 1,
  });
  
  const createMutation = useCreateCampaign();

  // Forcer le refetch des catégories au montage pour avoir les contact_count à jour
  useEffect(() => {
    refetch();
  }, [refetch]);

  const handleSubmit = async (data: CampaignCreate) => {
    try {
      const campaign = await createMutation.mutateAsync(data);
      toast.success("Campagne créée avec succès ! L'envoi des messages a démarré.");
      // Rediriger vers la page de détails de la campagne
      router.push(`/campaigns/${campaign.id}`);
    } catch (error) {
      toast.error("Erreur lors de la création de la campagne");
      console.error("Erreur lors de la création de la campagne:", error);
    }
  };

  const handleCancel = () => {
    router.push("/campaigns");
  };

  return (
    <DashboardLayout title="Nouvelle campagne">
      <div className="space-y-6">
        {/* En-tête */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={handleCancel}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Nouvelle campagne</h2>
            <p className="text-muted-foreground">
              Configurez et envoyez une nouvelle campagne de messages
            </p>
          </div>
        </div>

        {/* Erreur de chargement des catégories */}
        {categoriesError && (
          <ErrorMessage
            message="Impossible de charger les catégories. Veuillez réessayer."
            title="Erreur de chargement"
            onRetry={() => refetch()}
          />
        )}

        {/* Chargement des catégories */}
        {categoriesLoading && (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" text="Chargement des catégories..." />
          </div>
        )}

        {/* Formulaire */}
        {!categoriesLoading && !categoriesError && (
          <CampaignForm
            categories={categoriesData?.items || []}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            isLoading={createMutation.isPending}
          />
        )}

        {/* Message d'erreur de création */}
        {createMutation.isError && (
          <ErrorMessage
            message="Une erreur est survenue lors de la création de la campagne."
            title="Erreur de création"
          />
        )}
      </div>
    </DashboardLayout>
  );
}
