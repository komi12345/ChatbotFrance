"use client";

import { cn } from "@/lib/utils";
import type { AlertLevel } from "@/types/monitoring";

interface MessageGaugeProps {
  /** Number of messages sent today */
  sent: number;
  /** Daily message limit (default: 1000) */
  limit?: number;
  /** Current alert level */
  alertLevel: AlertLevel;
  /** Additional CSS classes */
  className?: string;
  /** Whether data is loading */
  isLoading?: boolean;
}

/**
 * Get color classes based on alert level
 * Requirements: 4.1
 */
function getAlertColors(level: AlertLevel): {
  stroke: string;
  text: string;
  bg: string;
} {
  switch (level) {
    case "ok":
      return {
        stroke: "stroke-emerald-500",
        text: "text-emerald-600",
        bg: "bg-emerald-500/10",
      };
    case "attention":
      return {
        stroke: "stroke-yellow-500",
        text: "text-yellow-600",
        bg: "bg-yellow-500/10",
      };
    case "danger":
      return {
        stroke: "stroke-red-500",
        text: "text-red-600",
        bg: "bg-red-500/10",
      };
    case "blocked":
      return {
        stroke: "stroke-gray-400",
        text: "text-gray-500",
        bg: "bg-gray-400/10",
      };
  }
}

/**
 * Circular gauge component displaying messages sent vs daily limit
 * Requirements: 4.1 - Display a gauge showing messages sent vs daily limit (1000)
 */
export function MessageGauge({
  sent,
  limit = 1000,
  alertLevel,
  className,
  isLoading = false,
}: MessageGaugeProps) {
  // Calculate percentage (capped at 100% for display)
  const percentage = Math.min((sent / limit) * 100, 100);
  
  // SVG circle parameters
  const size = 160;
  const strokeWidth = 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  const colors = getAlertColors(alertLevel);

  if (isLoading) {
    return (
      <div className={cn("flex flex-col items-center", className)}>
        <div 
          className="rounded-full bg-[#F3F4F6] animate-pulse"
          style={{ width: size, height: size }}
        />
        <div className="mt-3 h-4 w-24 bg-[#F3F4F6] animate-pulse rounded" />
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col items-center", className)}>
      {/* Circular Gauge */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="#E5E7EB"
            strokeWidth={strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            className={cn("transition-all duration-500", colors.stroke)}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
          />
        </svg>
        
        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("text-3xl font-bold", colors.text)}>
            {sent}
          </span>
          <span className="text-sm text-[#6B7280]">
            / {limit}
          </span>
        </div>
      </div>
      
      {/* Label */}
      <div className="mt-3 text-center">
        <span className="text-sm font-medium text-[#374151]">
          Messages envoyés
        </span>
        <div className={cn(
          "mt-1 inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
          colors.bg,
          colors.text
        )}>
          {percentage.toFixed(0)}% de la limite
        </div>
      </div>
    </div>
  );
}

export default MessageGauge;
