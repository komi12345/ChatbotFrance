"use client";

import { CheckCircle, AlertCircle, HelpCircle } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export type SandboxStatus = "registered" | "not_registered" | "unknown";

interface SandboxContactBadgeProps {
  /** Statut d'inscription au Sandbox */
  status: SandboxStatus;
  /** Afficher uniquement l'icône */
  iconOnly?: boolean;
  /** Taille du badge */
  size?: "sm" | "md";
}

/**
 * Badge indiquant le statut d'inscription d'un contact au Twilio Sandbox
 * Requirements: 9.3, 9.4
 */
export function SandboxContactBadge({
  status,
  iconOnly = false,
  size = "md",
}: SandboxContactBadgeProps) {
  const config = {
    registered: {
      label: "Inscrit au Sandbox",
      tooltip: "Ce contact a rejoint le Twilio Sandbox et peut recevoir des messages",
      className: "bg-[#D1FAE5] text-[#059669] border-[#A7F3D0]",
      icon: CheckCircle,
    },
    not_registered: {
      label: "Non inscrit",
      tooltip: "Ce contact doit rejoindre le Sandbox avant de recevoir des messages. Envoyez 'join <code>' au +1 415 523 8886",
      className: "bg-[#FEF3C7] text-[#D97706] border-[#FDE68A]",
      icon: AlertCircle,
    },
    unknown: {
      label: "Statut inconnu",
      tooltip: "Le statut d'inscription de ce contact n'a pas pu être vérifié",
      className: "bg-[#F3F4F6] text-[#6B7280] border-[#E5E7EB]",
      icon: HelpCircle,
    },
  };

  const { label, tooltip, className, icon: Icon } = config[status];
  const iconSize = size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5";
  const textSize = size === "sm" ? "text-[10px]" : "text-xs";
  const padding = size === "sm" ? "px-1.5 py-0.5" : "px-2 py-0.5";

  const badge = (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-medium ${className} ${padding} ${textSize}`}
    >
      <Icon className={iconSize} />
      {!iconOnly && <span>{label}</span>}
    </span>
  );

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{badge}</TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          <p className="text-sm">{tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default SandboxContactBadge;
