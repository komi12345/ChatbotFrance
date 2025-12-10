"use client";

import { AlertTriangle, MessageCircle, Clock, RefreshCw, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export type SandboxErrorType = 
  | "not_registered"    // Erreur 63007 - destinataire non inscrit
  | "session_expired"   // Session 24h expirée
  | "rate_limited"      // Limite de débit atteinte
  | "generic";          // Erreur générique

interface SandboxErrorMessageProps {
  /** Type d'erreur Sandbox */
  errorType: SandboxErrorType;
  /** Code d'erreur Twilio (optionnel) */
  errorCode?: number;
  /** Message d'erreur original (optionnel) */
  originalMessage?: string;
  /** Callback pour réessayer */
  onRetry?: () => void;
  /** Code de join personnalisé */
  joinCode?: string;
}

/**
 * Message d'erreur explicatif pour les erreurs Twilio Sandbox
 * Affiche les instructions de résolution selon le type d'erreur
 * Requirements: 9.4, 9.5
 */
export function SandboxErrorMessage({
  errorType,
  errorCode,
  originalMessage,
  onRetry,
  joinCode = "join <votre-code>",
}: SandboxErrorMessageProps) {
  const sandboxNumber = "+1 415 523 8886";

  const errorConfigs = {
    not_registered: {
      title: "Destinataire non inscrit au Sandbox",
      icon: AlertTriangle,
      iconBg: "bg-[#FEF3C7]",
      iconColor: "text-[#D97706]",
      bgColor: "bg-[#FFFBEB]",
      borderColor: "border-[#FDE68A]",
      textColor: "text-[#92400E]",
      description: "Le destinataire n'a pas rejoint le Twilio WhatsApp Sandbox. Il doit s'inscrire avant de pouvoir recevoir des messages.",
      instructions: [
        `Demander au destinataire d'ouvrir WhatsApp`,
        `Envoyer le message "${joinCode}" au numéro ${sandboxNumber}`,
        `Attendre la confirmation de Twilio`,
        `Réessayer l'envoi du message`,
      ],
    },
    session_expired: {
      title: "Session Sandbox expirée",
      icon: Clock,
      iconBg: "bg-[#DBEAFE]",
      iconColor: "text-[#2563EB]",
      bgColor: "bg-[#EFF6FF]",
      borderColor: "border-[#93C5FD]",
      textColor: "text-[#1E40AF]",
      description: "La session Sandbox du destinataire a expiré (durée maximale : 24 heures). Il doit se réinscrire.",
      instructions: [
        `Demander au destinataire de renvoyer "${joinCode}" au ${sandboxNumber}`,
        `Attendre la confirmation de réinscription`,
        `Réessayer l'envoi du message`,
      ],
    },
    rate_limited: {
      title: "Limite de débit atteinte",
      icon: RefreshCw,
      iconBg: "bg-[#FEE2E2]",
      iconColor: "text-[#DC2626]",
      bgColor: "bg-[#FEF2F2]",
      borderColor: "border-[#FECACA]",
      textColor: "text-[#991B1B]",
      description: "Le Sandbox Twilio limite l'envoi à 1 message toutes les 3 secondes. Veuillez patienter avant de réessayer.",
      instructions: [
        `Attendre quelques secondes`,
        `Réessayer l'envoi`,
        `Pour les envois en masse, le système respecte automatiquement cette limite`,
      ],
    },
    generic: {
      title: "Erreur d'envoi Sandbox",
      icon: XCircle,
      iconBg: "bg-[#FEE2E2]",
      iconColor: "text-[#DC2626]",
      bgColor: "bg-[#FEF2F2]",
      borderColor: "border-[#FECACA]",
      textColor: "text-[#991B1B]",
      description: originalMessage || "Une erreur est survenue lors de l'envoi du message via le Sandbox Twilio.",
      instructions: [
        `Vérifier que le destinataire est inscrit au Sandbox`,
        `Vérifier le format du numéro de téléphone`,
        `Réessayer l'envoi`,
      ],
    },
  };

  const config = errorConfigs[errorType];
  const Icon = config.icon;

  return (
    <div className={`rounded-xl ${config.bgColor} border ${config.borderColor} p-4 sm:p-5`}>
      <div className="flex items-start gap-4">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${config.iconBg} flex-shrink-0`}>
          <Icon className={`h-5 w-5 ${config.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className={`font-semibold ${config.textColor}`}>{config.title}</h3>
            {errorCode && (
              <span className={`text-xs px-1.5 py-0.5 rounded ${config.bgColor} ${config.textColor} font-mono`}>
                Code: {errorCode}
              </span>
            )}
          </div>
          
          <p className={`mt-1 text-sm ${config.textColor} opacity-90`}>
            {config.description}
          </p>

          {/* Instructions de résolution */}
          <div className="mt-3">
            <p className={`text-sm font-medium ${config.textColor} mb-2`}>
              Comment résoudre :
            </p>
            <ol className={`text-sm ${config.textColor} opacity-80 space-y-1 list-decimal list-inside`}>
              {config.instructions.map((instruction, index) => (
                <li key={index}>{instruction}</li>
              ))}
            </ol>
          </div>

          {/* Limitations Sandbox */}
          <div className="mt-4 pt-3 border-t border-current/10">
            <p className={`text-xs ${config.textColor} opacity-70`}>
              <strong>Rappel des limitations Sandbox :</strong> 1 message / 3 secondes • Session 24h • Inscription requise
            </p>
          </div>

          {/* Bouton réessayer */}
          {onRetry && (
            <Button
              onClick={onRetry}
              variant="outline"
              size="sm"
              className={`mt-4 border-current/30 ${config.textColor} hover:bg-current/5`}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Réessayer
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Détermine le type d'erreur Sandbox à partir du code d'erreur Twilio
 */
export function getSandboxErrorType(errorCode?: number): SandboxErrorType {
  switch (errorCode) {
    case 63007:
    case 21608:
      return "not_registered";
    case 63016:
      return "session_expired";
    case 20429:
      return "rate_limited";
    default:
      return "generic";
  }
}

export default SandboxErrorMessage;
