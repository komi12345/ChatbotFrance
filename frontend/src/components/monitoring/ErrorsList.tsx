"use client";

import { cn } from "@/lib/utils";
import { AlertTriangle, AlertCircle, Clock, XCircle } from "lucide-react";
import type { RecentError } from "@/types/monitoring";

interface ErrorsListProps {
  /** List of recent errors */
  errors: RecentError[];
  /** Total messages sent today */
  totalSent: number;
  /** Total errors today */
  errorCount: number;
  /** Additional CSS classes */
  className?: string;
  /** Whether data is loading */
  isLoading?: boolean;
}

/**
 * Calculate error rate and determine if warning should be shown
 * Requirements: 6.2 - Alert if error rate > 10%
 */
function getErrorRateInfo(totalSent: number, errorCount: number): {
  rate: number;
  showWarning: boolean;
  message: string;
} {
  if (totalSent === 0) {
    return {
      rate: 0,
      showWarning: false,
      message: "",
    };
  }
  
  const rate = errorCount / totalSent;
  const showWarning = rate > 0.10;
  
  return {
    rate,
    showWarning,
    message: showWarning 
      ? `Taux d'erreur élevé (${(rate * 100).toFixed(1)}%). Vérifiez la configuration Wassenger.`
      : "",
  };
}

/**
 * Format timestamp to French locale
 */
function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return timestamp;
  }
}

/**
 * ErrorsList component displaying recent errors with timestamps
 * Requirements: 6.2, 6.3
 * - Displays list of 10 most recent errors with timestamps
 * - Shows alert if error rate exceeds 10%
 */
export function ErrorsList({
  errors,
  totalSent,
  errorCount,
  className,
  isLoading = false,
}: ErrorsListProps) {
  const errorRateInfo = getErrorRateInfo(totalSent, errorCount);

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
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-[#F3F4F6] animate-pulse rounded-lg" />
          ))}
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
          Erreurs récentes
        </span>
        <div className={cn(
          "flex h-10 w-10 items-center justify-center rounded-xl",
          errorRateInfo.showWarning ? "bg-red-50" : "bg-gray-100"
        )}>
          <XCircle className={cn(
            "h-5 w-5",
            errorRateInfo.showWarning ? "text-red-500" : "text-gray-400"
          )} />
        </div>
      </div>

      {/* Error rate warning */}
      {errorRateInfo.showWarning && (
        <div className="mb-4 p-3 rounded-lg bg-red-50 text-red-700 text-xs">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <span>{errorRateInfo.message}</span>
          </div>
        </div>
      )}

      {/* Error count summary */}
      <div className="mb-4 flex items-center gap-2 text-sm">
        <span className={cn(
          "font-semibold",
          errorCount > 0 ? "text-red-600" : "text-gray-600"
        )}>
          {errorCount} erreur{errorCount !== 1 ? "s" : ""}
        </span>
        <span className="text-gray-400">aujourd&apos;hui</span>
        {totalSent > 0 && (
          <span className="text-xs text-gray-400">
            ({(errorRateInfo.rate * 100).toFixed(1)}%)
          </span>
        )}
      </div>

      {/* Errors list */}
      {errors.length === 0 ? (
        <div className="py-8 text-center">
          <AlertCircle className="mx-auto h-8 w-8 text-gray-300 mb-2" />
          <p className="text-sm text-gray-500">Aucune erreur récente</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {errors.map((error, index) => (
            <div
              key={`${error.timestamp}-${index}`}
              className="p-3 rounded-lg bg-gray-50 border border-gray-100"
            >
              <div className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-700 break-words">
                    {error.error}
                  </p>
                  <div className="mt-1 flex items-center gap-3 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatTimestamp(error.timestamp)}
                    </span>
                    {error.message_id && (
                      <span>Message #{error.message_id}</span>
                    )}
                    {error.error_code && (
                      <span className="font-mono bg-gray-200 px-1 rounded">
                        {error.error_code}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ErrorsList;
