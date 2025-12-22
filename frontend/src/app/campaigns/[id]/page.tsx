"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { CampaignStats } from "@/components/campaigns/CampaignStats";
import { MessagePreview } from "@/components/campaigns/MessagePreview";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner, ErrorMessage, useToast, SendingProgress, ConfirmDialog } from "@/components/common";
import { useCampaign, useCampaignStats, useRetryCampaign, useDeleteCampaign, useSendCampaign, useStopCampaign, useForceDeleteCampaign, useRelaunchCampaign } from "@/hooks/useCampaigns";
import { ArrowLeft, Calendar, Tag, Trash2, Play, RotateCcw, StopCircle, AlertTriangle, RefreshCw } from "lucide-react";
import type { CampaignStatus } from "@/types/campaign";

/**
 * Badge de statut de campagne
 */
function StatusBadge({ status }: { status: CampaignStatus }) {
  const config: Record<CampaignStatus, { label: string; class: string }> = {
    draft: { label: "Brouillon", class: "bg-gray-100 text-gray-700" },
    sending: { label: "En cours", class: "bg-blue-100 text-blue-700" },
    completed: { label: "Terminée", class: "bg-green-100 text-green-700" },
    failed: { label: "Échouée", class: "bg-red-100 text-red-700" },
    stopped: { label: "Arrêtée", class: "bg-orange-100 text-orange-700" },
  };

  const { label, class: className } = config[status] || { label: status, class: "bg-gray-100 text-gray-700" };

  return (
    <span className={`text-sm px-3 py-1 rounded-full ${className}`}>
      {label}
    </span>
  );
}

/**
 * Page de détails d'une campagne
 * Exigences: 6.1, 6.3, 6.4, 14.1, 14.2, 14.3, 14.4
 */
export default function CampaignDetailPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const campaignId = Number(params.id);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const { data: campaign, isLoading: campaignLoading, error: campaignError, refetch: refetchCampaign } = useCampaign(campaignId);
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useCampaignStats(campaignId, campaign?.status);
  const retryMutation = useRetryCampaign();
  const deleteMutation = useDeleteCampaign();
  const sendMutation = useSendCampaign();
  const stopMutation = useStopCampaign();
  const forceDeleteMutation = useForceDeleteCampaign();
  const relaunchMutation = useRelaunchCampaign();
  const [showForceDeleteDialog, setShowForceDeleteDialog] = useState(false);
  const [showRelaunchDialog, setShowRelaunchDialog] = useState(false);

  const handleBack = () => {
    router.push("/campaigns");
  };

  const handleRetry = async () => {
    try {
      const result = await retryMutation.mutateAsync(campaignId);
      toast.success(`${result?.retried_count || 0} message(s) remis en file d'attente`);
      refetchCampaign();
      refetchStats();
    } catch (error) {
      toast.error("Erreur lors du retry des messages");
      console.error("Erreur lors du retry:", error);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(campaignId);
      toast.success("Campagne supprimée avec succès");
      router.push("/campaigns");
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Erreur lors de la suppression");
      console.error("Erreur lors de la suppression:", error);
    }
  };

  const handleSend = async () => {
    try {
      const result = await sendMutation.mutateAsync(campaignId);
      toast.success(`Envoi lancé pour ${result?.total_messages || 0} destinataires`);
      refetchCampaign();
      refetchStats();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Erreur lors du lancement de l'envoi");
      console.error("Erreur lors de l'envoi:", error);
    }
  };

  const handleStop = async () => {
    try {
      const result = await stopMutation.mutateAsync(campaignId);
      toast.success(result?.message || "Campagne arrêtée");
      refetchCampaign();
      refetchStats();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Erreur lors de l'arrêt de la campagne");
      console.error("Erreur lors de l'arrêt:", error);
    }
  };

  const handleForceDelete = async () => {
    try {
      await forceDeleteMutation.mutateAsync({ id: campaignId, force: true });
      toast.success("Campagne supprimée avec succès");
      router.push("/campaigns");
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Erreur lors de la suppression");
      console.error("Erreur lors de la suppression forcée:", error);
    }
  };

  const handleRelaunch = async () => {
    try {
      const result = await relaunchMutation.mutateAsync(campaignId);
      toast.success(result?.message || `Campagne relancée pour ${result?.total_messages || 0} destinataires`);
      setShowRelaunchDialog(false);
      refetchCampaign();
      refetchStats();
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "Erreur lors de la relance de la campagne");
      console.error("Erreur lors de la relance:", error);
    }
  };

  const isLoading = campaignLoading || statsLoading;
  const error = campaignError || statsError;
  
  // Déterminer si on peut supprimer (draft, failed, stopped ou completed)
  const canDelete = campaign && ["draft", "failed", "stopped", "completed"].includes(campaign.status);
  // Déterminer si on peut forcer la suppression (sending)
  const canForceDelete = campaign && campaign.status === "sending";
  // Déterminer si on peut arrêter (sending)
  const canStop = campaign && campaign.status === "sending";
  // Déterminer si on peut lancer/relancer (draft)
  const canSend = campaign && campaign.status === "draft";
  // Déterminer si on peut réessayer (failed ou completed avec des échecs)
  const canRetry = campaign && (campaign.status === "failed" || (campaign.status === "completed" && campaign.failed_count > 0));
  // Déterminer si on peut relancer la campagne entière (completed ou failed)
  const canRelaunch = campaign && ["completed", "failed"].includes(campaign.status);

  return (
    <DashboardLayout title={campaign?.name || "Campagne"}>
      <div className="space-y-6">
        {/* En-tête */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={handleBack}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold tracking-tight">
                {campaign?.name || "Chargement..."}
              </h2>
              {campaign && <StatusBadge status={campaign.status} />}
            </div>
            {campaign && (
              <div className="flex items-center gap-4 text-sm text-muted-foreground mt-1">
                <span className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {new Date(campaign.created_at).toLocaleDateString("fr-FR", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                </span>
                {campaign.template_name && (
                  <span className="flex items-center gap-1">
                    <Tag className="h-4 w-4" />
                    Template: {campaign.template_name}
                  </span>
                )}
              </div>
            )}
          </div>
          
          {/* Boutons d'action */}
          {campaign && (
            <div className="flex items-center gap-2">
              {canSend && (
                <Button 
                  onClick={handleSend} 
                  disabled={sendMutation.isPending}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Play className="h-4 w-4 mr-2" />
                  {sendMutation.isPending ? "Lancement..." : "Lancer l'envoi"}
                </Button>
              )}
              {canStop && (
                <Button 
                  onClick={handleStop} 
                  disabled={stopMutation.isPending}
                  variant="outline"
                  className="border-orange-500 text-orange-600 hover:bg-orange-50"
                >
                  <StopCircle className="h-4 w-4 mr-2" />
                  {stopMutation.isPending ? "Arrêt..." : "Arrêter"}
                </Button>
              )}
              {canRetry && (
                <Button 
                  onClick={handleRetry} 
                  disabled={retryMutation.isPending}
                  variant="outline"
                >
                  <RotateCcw className={`h-4 w-4 mr-2 ${retryMutation.isPending ? "animate-spin" : ""}`} />
                  {retryMutation.isPending ? "Réessai..." : "Réessayer les échecs"}
                </Button>
              )}
              {canRelaunch && (
                <Button 
                  onClick={() => setShowRelaunchDialog(true)} 
                  disabled={relaunchMutation.isPending}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${relaunchMutation.isPending ? "animate-spin" : ""}`} />
                  {relaunchMutation.isPending ? "Relance..." : "Relancer la campagne"}
                </Button>
              )}
              {canDelete && (
                <Button 
                  onClick={() => setShowDeleteDialog(true)} 
                  variant="destructive"
                  disabled={deleteMutation.isPending}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Supprimer
                </Button>
              )}
              {canForceDelete && (
                <Button 
                  onClick={() => setShowForceDeleteDialog(true)} 
                  variant="destructive"
                  disabled={forceDeleteMutation.isPending}
                >
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Supprimer (forcé)
                </Button>
              )}
            </div>
          )}
        </div>
        
        {/* Dialog de confirmation de suppression */}
        <ConfirmDialog
          open={showDeleteDialog}
          onOpenChange={setShowDeleteDialog}
          title="Supprimer la campagne"
          description={`Êtes-vous sûr de vouloir supprimer la campagne "${campaign?.name}" ? Cette action est irréversible.`}
          confirmText="Supprimer"
          cancelText="Annuler"
          onConfirm={handleDelete}
          variant="danger"
        />
        
        {/* Dialog de confirmation de suppression forcée */}
        <ConfirmDialog
          open={showForceDeleteDialog}
          onOpenChange={setShowForceDeleteDialog}
          title="⚠️ Suppression forcée"
          description={`ATTENTION: La campagne "${campaign?.name}" est en cours d'envoi. La suppression forcée va arrêter tous les envois en cours et supprimer la campagne. Cette action est irréversible.`}
          confirmText="Supprimer quand même"
          cancelText="Annuler"
          onConfirm={handleForceDelete}
          variant="danger"
        />
        
        {/* Dialog de confirmation de relance */}
        <ConfirmDialog
          open={showRelaunchDialog}
          onOpenChange={setShowRelaunchDialog}
          title="Relancer la campagne"
          description={`Voulez-vous relancer la campagne "${campaign?.name}" ? Tous les anciens messages seront supprimés et de nouveaux messages seront envoyés à tous les contacts des catégories ciblées.`}
          confirmText="Relancer"
          cancelText="Annuler"
          onConfirm={handleRelaunch}
          variant="info"
        />

        {/* Erreur */}
        {error && (
          <ErrorMessage
            message="Une erreur est survenue lors du chargement de la campagne."
            title="Erreur de chargement"
            onRetry={() => {
              refetchCampaign();
              refetchStats();
            }}
          />
        )}

        {/* Chargement */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" text="Chargement de la campagne..." />
          </div>
        )}

        {/* Barre de progression pour campagne en cours */}
        {!isLoading && campaign && campaign.status === "sending" && (
          <SendingProgress
            sent={campaign.sent_count}
            total={campaign.total_recipients}
            success={campaign.success_count}
            failed={campaign.failed_count}
          />
        )}

        {/* Contenu */}
        {!isLoading && campaign && stats && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Colonne principale - Statistiques */}
            <div className="lg:col-span-2">
              <CampaignStats
                stats={stats}
                onRetry={handleRetry}
                isRetrying={retryMutation.isPending}
              />
            </div>

            {/* Colonne latérale - Messages */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Message 1</CardTitle>
                </CardHeader>
                <CardContent>
                  <MessagePreview content={campaign.message_1} type="message_1" />
                </CardContent>
              </Card>

              {campaign.message_2 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Message 2 (Suivi)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <MessagePreview content={campaign.message_2} type="message_2" />
                  </CardContent>
                </Card>
              )}

              {/* Catégories ciblées */}
              {campaign.categories && campaign.categories.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Catégories ciblées</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {campaign.categories.map((cat) => (
                        <span
                          key={cat.id}
                          className={`text-xs px-2 py-1 rounded-full text-white bg-gradient-to-r ${
                            cat.color || "from-blue-500 to-cyan-500"
                          }`}
                        >
                          {cat.name}
                        </span>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
