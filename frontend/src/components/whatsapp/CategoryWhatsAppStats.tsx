"use client";

import { CheckCircle, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { CategoryContact } from "@/types/category";

/**
 * Props for CategoryWhatsAppStats component
 * Requirements: 5.2
 */
interface CategoryWhatsAppStatsProps {
  contacts: CategoryContact[];
  /** Threshold percentage below which to show warning (default: 50) */
  warningThreshold?: number;
  className?: string;
}

/**
 * Calculate WhatsApp verification percentage for a category
 * Property 7: Category verification percentage
 * Validates: Requirements 5.2
 * 
 * @param contacts - Array of contacts in the category
 * @returns Percentage rounded to one decimal place
 */
export function calculateVerificationPercentage(contacts: CategoryContact[]): number {
  if (!contacts || contacts.length === 0) {
    return 0;
  }
  
  const verifiedCount = contacts.filter(c => c.whatsapp_verified === true).length;
  const percentage = (verifiedCount / contacts.length) * 100;
  
  // Round to one decimal place
  return Math.round(percentage * 10) / 10;
}

/**
 * Component to display WhatsApp verification percentage for a category
 * Shows warning if percentage is below threshold
 * 
 * Requirements: 5.2 - Display percentage of WhatsApp-verified contacts in category
 */
export function CategoryWhatsAppStats({
  contacts,
  warningThreshold = 50,
  className,
}: CategoryWhatsAppStatsProps) {
  const totalCount = contacts?.length || 0;
  const verifiedCount = contacts?.filter(c => c.whatsapp_verified === true).length || 0;
  const percentage = calculateVerificationPercentage(contacts);
  const isLow = percentage < warningThreshold && totalCount > 0;

  if (totalCount === 0) {
    return null;
  }

  return (
    <div className={cn("flex items-center gap-3", className)}>
      <div
        className={cn(
          "flex items-center gap-2 rounded-lg px-3 py-2",
          isLow
            ? "bg-amber-50 border border-amber-200"
            : "bg-emerald-50 border border-emerald-200"
        )}
      >
        {isLow ? (
          <AlertTriangle className="h-4 w-4 text-amber-500" />
        ) : (
          <CheckCircle className="h-4 w-4 text-emerald-500" />
        )}
        <div className="flex flex-col">
          <span
            className={cn(
              "text-sm font-medium",
              isLow ? "text-amber-700" : "text-emerald-700"
            )}
          >
            {percentage}% WhatsApp vérifié
          </span>
          <span className="text-xs text-muted-foreground">
            {verifiedCount} sur {totalCount} contact{totalCount !== 1 ? "s" : ""}
          </span>
        </div>
      </div>
      {isLow && (
        <span className="text-xs text-amber-600">
          Attention : moins de {warningThreshold}% des contacts sont vérifiés WhatsApp
        </span>
      )}
    </div>
  );
}

export default CategoryWhatsAppStats;
