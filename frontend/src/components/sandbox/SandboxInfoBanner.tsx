"use client";

import { Info, MessageCircle, Clock, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SandboxInfoBannerProps {
  /** Afficher la version compacte */
  compact?: boolean;
  /** Code de join personnalisé (optionnel) */
  joinCode?: string;
  /** Callback pour fermer le bandeau */
  onDismiss?: () => void;
}

/**
 * Bandeau d'information sur le mode Twilio WhatsApp Sandbox
 * Affiche les informations essentielles pour utiliser le Sandbox
 * Requirements: 9.1, 9.2
 */
export function SandboxInfoBanner({
  compact = false,
  joinCode = "join <votre-code>",
  onDismiss,
}: SandboxInfoBannerProps) {
  const sandboxNumber = "+1 415 523 8886";

  if (compact) {
    return (
      <div className="rounded-lg bg-[#DBEAFE] border border-[#93C5FD] p-3">
        <div className="flex items-center gap-2 text-sm text-[#1E40AF]">
          <Info className="h-4 w-4 flex-shrink-0" />
          <span>
            <strong>Mode Sandbox</strong> - Les destinataires doivent envoyer "{joinCode}" au {sandboxNumber}
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-gradient-to-r from-[#DBEAFE] to-[#E0E7FF] border border-[#93C5FD] p-4 sm:p-6">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#3B82F6]/10 flex-shrink-0">
          <MessageCircle className="h-5 w-5 text-[#3B82F6]" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold text-[#1E40AF]">Mode Twilio WhatsApp Sandbox</h3>
            {onDismiss && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onDismiss}
                className="text-[#3B82F6] hover:text-[#1E40AF] hover:bg-[#3B82F6]/10 -mr-2"
              >
                Masquer
              </Button>
            )}
          </div>
          
          <p className="mt-1 text-sm text-[#1E3A8A]">
            Vous utilisez l'environnement de test gratuit Twilio. Les destinataires doivent s'inscrire au Sandbox avant de recevoir des messages.
          </p>

          {/* Instructions de join */}
          <div className="mt-4 p-3 bg-white/60 rounded-lg border border-[#93C5FD]/50">
            <p className="text-sm font-medium text-[#1E40AF] mb-2">
              Pour rejoindre le Sandbox :
            </p>
            <ol className="text-sm text-[#1E3A8A] space-y-1 list-decimal list-inside">
              <li>Ouvrir WhatsApp sur le téléphone du destinataire</li>
              <li>
                Envoyer le message <code className="px-1.5 py-0.5 bg-[#1E40AF]/10 rounded text-[#1E40AF] font-mono text-xs">{joinCode}</code> au numéro{" "}
                <code className="px-1.5 py-0.5 bg-[#1E40AF]/10 rounded text-[#1E40AF] font-mono text-xs">{sandboxNumber}</code>
              </li>
              <li>Attendre la confirmation de Twilio</li>
            </ol>
          </div>

          {/* Limitations */}
          <div className="mt-4 flex flex-wrap gap-3">
            <div className="flex items-center gap-1.5 text-xs text-[#1E3A8A]">
              <Clock className="h-3.5 w-3.5" />
              <span>Session 24h</span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-[#1E3A8A]">
              <AlertTriangle className="h-3.5 w-3.5" />
              <span>1 message / 3 secondes</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SandboxInfoBanner;
