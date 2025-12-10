"use client";

import { cn } from "@/lib/utils";
import { Users, AlertTriangle, XCircle } from "lucide-react";

interface CapacityCardProps {
  /** Estimated number of contacts that can still be contacted today */
  remainingCapacity: number;
  /** Number of messages remaining before limit (180 - total_sent) */
  remainingMessages: number;
  /** Current interaction rate (message_2 / message_1) */
  interactionRate: number;
  /** Whether message sending is currently blocked */
  isBlocked?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Whether data is loading */
  isLoading?: boolean;
}

/**
 * Get status info based on remaining capacity
 * Requirements: 5.3, 5.4
 */
function getCapacityStatus(capacity: number, isBlocked: boolean): {
  color: string;
  bgColor: string;
  iconColor: string;
  message: string;
  showWarning: boolean;
} {
  if (isBlocked || capacity <= 0) {
    return {
      color: "text-gray-500",
      bgColor: "bg-gray-100",
      iconColor: "text-gray-400",
      message: "Aucun contact ne peut être ajouté aujourd'hui. Attendez demain pour reprendre les envois.",
      showWarning: true,
    };
  }
  
  if (capacity < 10) {
    return {
      color: "text-yellow-600",
      bgColor: "bg-yellow-50",
      iconColor: "text-yellow-500",
      message: "Capacité faible. Il est recommandé d'attendre demain pour ajouter de nouveaux contacts.",
      showWarning: true,
    };
  }
  
  return {
    color: "text-emerald-600",
    bgColor: "bg-emerald-50",
    iconColor: "text-emerald-500",
    message: "",
    showWarning: false,
  };
}

/**
 * Card component displaying remaining contact capacity
 * Requirements: 5.1, 5.3, 5.4
 * - Displays remaining capacity calculated with interaction rate
 * - Shows warning if < 10 contacts
 * - Shows blocked message if capacity is zero
 */
export function CapacityCard({
  remainingCapacity,
  remainingMessages,
  interactionRate,
  isBlocked = false,
  className,
  isLoading = false,
}: CapacityCardProps) {
  const status = getCapacityStatus(remainingCapacity, isBlocked);
  
  if (isLoading) {
    return (
      <div className={cn(
        "rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50",
        className
      )}>
        <div className="flex items-center justify-between mb-4">
          <div className="h-4 w-32 bg-[#F3F4F6] animate-pulse rounded" />
          <div className="h-10 w-10 bg-[#F3F4F6] animate-pulse rounded-xl" />
        </div>
        <div className="space-y-2">
          <div className="h-8 w-20 bg-[#F3F4F6] animate-pulse rounded-lg" />
          <div className="h-4 w-40 bg-[#F3F4F6] animate-pulse rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className={cn(
      "rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50",
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-[#6B7280]">
          Capacité restante
        </span>
        <div className={cn(
          "flex h-10 w-10 items-center justify-center rounded-xl",
          status.bgColor
        )}>
          {isBlocked || remainingCapacity <= 0 ? (
            <XCircle className={cn("h-5 w-5", status.iconColor)} />
          ) : status.showWarning ? (
            <AlertTriangle className={cn("h-5 w-5", status.iconColor)} />
          ) : (
            <Users className={cn("h-5 w-5", status.iconColor)} />
          )}
        </div>
      </div>
      
      {/* Main value */}
      <div className={cn("text-2xl md:text-3xl font-bold mb-1", status.color)}>
        {remainingCapacity} contacts
      </div>
      
      {/* Details */}
      <div className="space-y-1">
        <p className="text-xs text-[#6B7280]">
          {remainingMessages} messages restants sur 180
        </p>
        <p className="text-xs text-[#9CA3AF]">
          Taux d&apos;interaction : {(interactionRate * 100).toFixed(1)}%
        </p>
      </div>
      
      {/* Warning message */}
      {status.showWarning && (
        <div className={cn(
          "mt-4 p-3 rounded-lg text-xs",
          isBlocked || remainingCapacity <= 0 
            ? "bg-gray-50 text-gray-600" 
            : "bg-yellow-50 text-yellow-700"
        )}>
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <span>{status.message}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default CapacityCard;
