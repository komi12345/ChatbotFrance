"use client";

import { AlertTriangle, XCircle, Wifi, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export type WassengerErrorType = 
  | "device_not_connected"  // Appareil WhatsApp déconnecté
  | "invalid_phone_number"  // Numéro de téléphone invalide
  | "rate_limit_exceeded"   // Limite de débit atteinte
  | "session_expired"       // Session WhatsApp expirée
  | "generic";              // Erreur générique

interface WassengerErrorMessageProps {
  /** Type d'erreur Wassenger */
  errorType: WassengerErrorType;
  /** Code d'erreur Wassenger (optionnel) */
  errorCode?: string;
  /** Message d'erreur original (optionnel) */
  originalMessage?: string;
  /** Callback pour réessayer */
  onRetry?: () => void;
}

/**
 * Message d'erreur explicatif pour les erreurs Wassenger
 * Affiche les instructions de résolution selon le type d'erreur
 */
export function WassengerErrorMessage({
  errorType,
  errorCode,
  originalMessage,
  onRetry,
}: WassengerErrorMessageProps) {
  const errorConfigs = {
    device_not_connected: {
      title: "Appareil WhatsApp déconnecté",
      icon: Wifi,
      iconBg: "bg-[#FEF3C7]",
      iconColor: "text-[#D97706]",
      bgColor: "bg-[#FFFBEB]",
      borderColor: "border-[#FDE68A]",
      textColor: "text-[#92400E]",
      description: "L'appareil WhatsApp n'est plus connecté à Wassenger. Il doit être reconnecté via QR code.",
      instructions: [
        "Ouvrir le dashboard Wassenger",
        "Aller dans la section 'Devices'",
        "Scanner le QR code avec WhatsApp",
        "Réessayer l'envoi du message",
      ],
    },
    invalid_phone_number: {
      title: "Numéro de téléphone invalide",
      icon: AlertTriangle,
      iconBg: "bg-[#FEF3C7]",
      iconColor: "text-[#D97706]",
      bgColor: "bg-[#FFFBEB]",
      borderColor: "border-[#FDE68A]",
      textColor: "text-[#92400E]",
      description: "Le format du numéro de téléphone est incorrect. Utilisez le format international sans le préfixe +.",
      instructions: [
        "Vérifier le format du numéro (ex: 22890123456)",
        "Retirer le préfixe + si présent",
        "Vérifier que le numéro est valide",
      ],
    },
    rate_limit_exceeded: {
      title: "Limite de débit atteinte",
      icon: RefreshCw,
      iconBg: "bg-[#FEE2E2]",
      iconColor: "text-[#DC2626]",
      bgColor: "bg-[#FEF2F2]",
      borderColor: "border-[#FECACA]",
      textColor: "text-[#991B1B]",
      description: "Trop de messages envoyés en peu de temps. Veuillez patienter avant de réessayer.",
      instructions: [
        "Attendre 60 secondes",
        "Réessayer l'envoi",
      ],
    },
    session_expired: {
      title: "Session WhatsApp expirée",
      icon: XCircle,
      iconBg: "bg-[#FEE2E2]",
      iconColor: "text-[#DC2626]",
      bgColor: "bg-[#FEF2F2]",
      borderColor: "border-[#FECACA]",
      textColor: "text-[#991B1B]",
      description: "La session WhatsApp a expiré. Reconnectez l'appareil dans le dashboard Wassenger.",
      instructions: [
        "Ouvrir le dashboard Wassenger",
        "Reconnecter l'appareil via QR code",
        "Réessayer l'envoi",
      ],
    },
    generic: {
      title: "Erreur d'envoi",
      icon: XCircle,
      iconBg: "bg-[#FEE2E2]",
      iconColor: "text-[#DC2626]",
      bgColor: "bg-[#FEF2F2]",
      borderColor: "border-[#FECACA]",
      textColor: "text-[#991B1B]",
      description: originalMessage || "Une erreur est survenue lors de l'envoi du message via Wassenger.",
      instructions: [
        "Vérifier la connexion de l'appareil WhatsApp",
        "Vérifier le format du numéro de téléphone",
        "Réessayer l'envoi",
      ],
    },
  };

  const config = errorConfigs[errorType];
  const Icon = config.icon;

  return (
    <div className={`rounded-lg ${config.bgColor} border ${config.borderColor} p-4`}>
      <div className="flex items-start gap-3">
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${config.iconBg} flex-shrink-0`}>
          <Icon className={`h-4 w-4 ${config.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className={`font-medium ${config.textColor}`}>
            {config.title}
            {errorCode && (
              <span className="ml-2 text-xs opacity-70">({errorCode})</span>
            )}
          </h4>
          <p className={`mt-1 text-sm ${config.textColor} opacity-80`}>
            {config.description}
          </p>

          {/* Instructions */}
          <div className="mt-3">
            <p className={`text-xs font-medium ${config.textColor} mb-1`}>
              Pour résoudre :
            </p>
            <ol className={`text-xs ${config.textColor} opacity-70 space-y-0.5 list-decimal list-inside`}>
              {config.instructions.map((instruction, index) => (
                <li key={index}>{instruction}</li>
              ))}
            </ol>
          </div>

          {/* Bouton réessayer */}
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className={`mt-3 ${config.textColor} border-current/30 hover:bg-current/5`}
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Réessayer
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export function getWassengerErrorType(errorCode?: string, errorMessage?: string): WassengerErrorType {
  if (errorCode === "device_not_connected" || errorMessage?.includes("device_not_connected")) {
    return "device_not_connected";
  }
  if (errorCode === "invalid_phone_number" || errorMessage?.includes("invalid_phone_number")) {
    return "invalid_phone_number";
  }
  if (errorCode === "rate_limit_exceeded" || errorMessage?.includes("rate_limit")) {
    return "rate_limit_exceeded";
  }
  if (errorCode === "session_expired" || errorMessage?.includes("session_expired")) {
    return "session_expired";
  }
  return "generic";
}

export default WassengerErrorMessage;
