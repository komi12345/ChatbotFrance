"use client";

import { Info, MessageCircle, Wifi, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface WassengerInfoBannerProps {
  /** Afficher la version compacte */
  compact?: boolean;
  /** Callback pour fermer le bandeau */
  onDismiss?: () => void;
}

/**
 * Bandeau d'information sur le mode Wassenger WhatsApp
 * Affiche les informations essentielles pour utiliser Wassenger
 */
export function WassengerInfoBanner({
  compact = false,
  onDismiss,
}: WassengerInfoBannerProps) {
  if (compact) {
    return (
      <div className="rounded-lg bg-[#D1FAE5] border border-[#A7F3D0] p-3">
        <div className="flex items-center gap-2 text-sm text-[#059669]">
          <CheckCircle className="h-4 w-4 flex-shrink-0" />
          <span>
            <strong>Mode Wassenger</strong> - Envoi direct via WhatsApp Business connecté
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-gradient-to-r from-[#D1FAE5] to-[#ECFDF5] border border-[#A7F3D0] p-4 sm:p-6">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#10B981]/10 flex-shrink-0">
          <MessageCircle className="h-5 w-5 text-[#10B981]" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold text-[#059669]">Mode Wassenger WhatsApp</h3>
            {onDismiss && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onDismiss}
                className="text-[#10B981] hover:text-[#059669] hover:bg-[#10B981]/10 -mr-2"
              >
                Masquer
              </Button>
            )}
          </div>

          <p className="mt-1 text-sm text-[#047857]">
            Vous utilisez Wassenger pour envoyer des messages WhatsApp. Votre appareil WhatsApp Business est connecté et prêt à envoyer.
          </p>

          {/* Statut de connexion */}
          <div className="mt-4 p-3 bg-white/60 rounded-lg border border-[#A7F3D0]/50">
            <p className="text-sm font-medium text-[#059669] mb-2">
              Avantages Wassenger :
            </p>
            <ul className="text-sm text-[#047857] space-y-1 list-disc list-inside">
              <li>Envoi direct sans inscription préalable des contacts</li>
              <li>Profil Business WhatsApp personnalisé</li>
              <li>Pas de limite de session 24h pour les messages initiés</li>
              <li>Webhooks en temps réel pour le suivi des statuts</li>
            </ul>
          </div>

          {/* Indicateurs */}
          <div className="mt-4 flex flex-wrap gap-3">
            <div className="flex items-center gap-1.5 text-xs text-[#047857]">
              <Wifi className="h-3.5 w-3.5" />
              <span>Appareil connecté</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-[#047857]">
              <CheckCircle className="h-3.5 w-3.5" />
              <span>Prêt à envoyer</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WassengerInfoBanner;
