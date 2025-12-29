"use client";

import { AlertCircle, Wifi, WifiOff } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export type WassengerStatus = "connected" | "disconnected" | "unknown";

interface WassengerStatusBadgeProps {
  /** Statut de connexion Wassenger */
  status: WassengerStatus;
  /** Afficher uniquement l'icône */
  iconOnly?: boolean;
  /** Taille du badge */
  size?: "sm" | "md";
}

/**
 * Badge indiquant le statut de connexion Wassenger
 */
export function WassengerStatusBadge({
  status,
  iconOnly = false,
  size = "md",
}: WassengerStatusBadgeProps) {
  const config = {
    connected: {
      label: "Connecté",
      tooltip: "L'appareil WhatsApp est connecté et prêt à envoyer des messages",
      className: "bg-[#D1FAE5] text-[#059669] border-[#A7F3D0]",
      icon: Wifi,
    },
    disconnected: {
      label: "Déconnecté",
      tooltip: "L'appareil WhatsApp doit être reconnecté via QR code dans le dashboard Wassenger",
      className: "bg-[#FEE2E2] text-[#DC2626] border-[#FECACA]",
      icon: WifiOff,
    },
    unknown: {
      label: "Inconnu",
      tooltip: "Statut de connexion inconnu",
      className: "bg-[#F3F4F6] text-[#6B7280] border-[#E5E7EB]",
      icon: AlertCircle,
    },
  };

  const { label, tooltip, className, icon: Icon } = config[status];
  const sizeClasses = size === "sm" ? "text-xs px-1.5 py-0.5" : "text-sm px-2 py-1";
  const iconSize = size === "sm" ? "h-3 w-3" : "h-4 w-4";

  const badge = (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-medium ${className} ${sizeClasses}`}
    >
      <Icon className={iconSize} />
      {!iconOnly && label}
    </span>
  );

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{badge}</TooltipTrigger>
        <TooltipContent>
          <p className="text-xs max-w-[200px]">{tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default WassengerStatusBadge;
