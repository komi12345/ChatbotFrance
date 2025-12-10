"use client";

import { CheckCircle, XCircle, Clock, Users } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Props for WhatsAppVerificationStats component
 * Requirements: 5.1
 */
interface WhatsAppVerificationStatsProps {
  verifiedCount: number;
  notWhatsappCount: number;
  pendingCount: number;
  totalCount: number;
  isLoading?: boolean;
  className?: string;
}

/**
 * Component to display WhatsApp verification statistics summary
 * Shows counts: verified, not_whatsapp, pending as inline stats cards
 * 
 * Requirements: 5.1 - Display verification statistics summary on contacts page
 */
export function WhatsAppVerificationStats({
  verifiedCount,
  notWhatsappCount,
  pendingCount,
  totalCount,
  isLoading = false,
  className,
}: WhatsAppVerificationStatsProps) {
  const stats = [
    {
      label: "WhatsApp vérifié",
      value: verifiedCount,
      icon: CheckCircle,
      color: "text-emerald-500",
      bgColor: "bg-emerald-500/10",
    },
    {
      label: "Non-WhatsApp",
      value: notWhatsappCount,
      icon: XCircle,
      color: "text-red-500",
      bgColor: "bg-red-500/10",
    },
    {
      label: "Non vérifié",
      value: pendingCount,
      icon: Clock,
      color: "text-gray-500",
      bgColor: "bg-gray-500/10",
    },
    {
      label: "Total",
      value: totalCount,
      icon: Users,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
    },
  ];

  if (isLoading) {
    return (
      <div className={cn("grid grid-cols-2 md:grid-cols-4 gap-3", className)}>
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="rounded-xl bg-white p-4 shadow-soft border border-[#E5E7EB]/50"
          >
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-[#F3F4F6] animate-pulse" />
              <div className="space-y-1.5">
                <div className="h-3 w-16 bg-[#F3F4F6] animate-pulse rounded" />
                <div className="h-5 w-8 bg-[#F3F4F6] animate-pulse rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={cn("grid grid-cols-2 md:grid-cols-4 gap-3", className)}>
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-xl bg-white p-4 shadow-soft border border-[#E5E7EB]/50"
        >
          <div className="flex items-center gap-3">
            <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg", stat.bgColor)}>
              <stat.icon className={cn("h-5 w-5", stat.color)} />
            </div>
            <div>
              <p className="text-xs text-[#6B7280]">{stat.label}</p>
              <p className="text-lg font-semibold text-[#111827]">{stat.value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default WhatsAppVerificationStats;
