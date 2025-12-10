"use client";

import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface StatsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
  isLoading?: boolean;
}

export function StatsCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
  className,
  isLoading = false,
}: StatsCardProps) {
  return (
    <div className={cn(
      "rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50",
      className
    )}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-[#6B7280]">{title}</span>
        {Icon && (
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/10">
            <Icon className="h-5 w-5 text-emerald-500" />
          </div>
        )}
      </div>
      
      {isLoading ? (
        <div className="space-y-2">
          <div className="h-8 w-24 bg-[#F3F4F6] animate-pulse rounded-lg" />
          <div className="h-4 w-32 bg-[#F3F4F6] animate-pulse rounded-lg" />
        </div>
      ) : (
        <>
          <div className="text-2xl md:text-3xl font-bold text-[#111827] mb-1">
            {value}
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {description && (
              <p className="text-xs text-[#6B7280]">{description}</p>
            )}
            {trend && (
              <span
                className={cn(
                  "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
                  trend.isPositive 
                    ? "bg-[#D1FAE5] text-[#059669]" 
                    : "bg-[#FEE2E2] text-[#DC2626]"
                )}
              >
                {trend.isPositive ? "↑" : "↓"} {Math.abs(trend.value)}%
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default StatsCard;
