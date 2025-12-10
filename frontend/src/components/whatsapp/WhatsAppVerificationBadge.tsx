"use client";

import { CheckCircle, XCircle, HelpCircle, Loader2, RefreshCw } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export type WhatsAppVerificationStatus = 'verified' | 'not_whatsapp' | 'pending' | null;

interface WhatsAppVerificationBadgeProps {
  /** Statut de vérification WhatsApp */
  status: WhatsAppVerificationStatus;
  /** Callback pour re-vérifier le contact */
  onReVerify?: () => void;
  /** Indique si une vérification est en cours */
  isLoading?: boolean;
  /** Taille du badge */
  size?: "sm" | "md";
}

/**
 * Badge indiquant le statut de vérification WhatsApp d'un contact
 * 
 * - Green badge with WhatsApp icon when verified (Requirements 2.1)
 * - Red badge with warning icon when not_whatsapp (Requirements 2.2)
 * - Gray badge with "non vérifié" when pending/null (Requirements 2.3)
 * - Tooltip with status explanation (Requirements 2.4)
 */
export function WhatsAppVerificationBadge({
  status,
  onReVerify,
  isLoading = false,
  size = "md",
}: WhatsAppVerificationBadgeProps) {
  const config = {
    verified: {
      label: "WhatsApp",
      tooltip: "Ce numéro est enregistré sur WhatsApp et peut recevoir des messages",
      className: "bg-[#D1FAE5] text-[#059669] border-[#A7F3D0]",
      icon: CheckCircle,
    },
    not_whatsapp: {
      label: "Non-WhatsApp",
      tooltip: "Ce numéro n'est pas enregistré sur WhatsApp",
      className: "bg-[#FEE2E2] text-[#DC2626] border-[#FECACA]",
      icon: XCircle,
    },
    pending: {
      label: "Non vérifié",
      tooltip: "La vérification WhatsApp n'a pas encore été effectuée ou a échoué",
      className: "bg-[#F3F4F6] text-[#6B7280] border-[#E5E7EB]",
      icon: HelpCircle,
    },
  };

  // Map null to 'pending' for display purposes
  const displayStatus = status === null ? 'pending' : status;
  const { label, tooltip, className, icon: Icon } = config[displayStatus];
  
  const sizeClasses = size === "sm" ? "text-xs px-1.5 py-0.5" : "text-sm px-2 py-1";
  const iconSize = size === "sm" ? "h-3 w-3" : "h-4 w-4";
  const buttonSize = size === "sm" ? "h-4 w-4 p-0.5" : "h-5 w-5 p-0.5";

  const badge = (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-medium ${className} ${sizeClasses}`}
    >
      {isLoading ? (
        <Loader2 className={`${iconSize} animate-spin`} />
      ) : (
        <Icon className={iconSize} />
      )}
      {label}
      {onReVerify && !isLoading && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onReVerify();
          }}
          className={`ml-1 rounded-full hover:bg-black/10 transition-colors ${buttonSize}`}
          aria-label="Re-vérifier le statut WhatsApp"
        >
          <RefreshCw className={size === "sm" ? "h-2.5 w-2.5" : "h-3 w-3"} />
        </button>
      )}
    </span>
  );

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{badge}</TooltipTrigger>
        <TooltipContent>
          <p className="text-xs max-w-[200px]">
            {isLoading ? "Vérification en cours..." : tooltip}
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default WhatsAppVerificationBadge;
