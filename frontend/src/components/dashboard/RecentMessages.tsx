"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface RecentMessage {
  id: number;
  contact_name: string | null;
  contact_phone: string;
  campaign_name: string;
  status: string;
  sent_at: string | null;
  message_type: string;
}

interface RecentMessagesProps {
  messages: RecentMessage[];
  title?: string;
  isLoading?: boolean;
}

const STATUS_CONFIG: Record<string, { label: string; variant: "success" | "warning" | "error" | "default" | "sent" | "delivered" | "read" | "failed" | "pending" }> = {
  pending: { label: "En attente", variant: "pending" },
  sent: { label: "Envoyé", variant: "sent" },
  delivered: { label: "Délivré", variant: "delivered" },
  read: { label: "Lu", variant: "read" },
  failed: { label: "Échoué", variant: "failed" },
};

function formatRelativeTime(dateStr: string | null): string {
  if (!dateStr) return "—";
  
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "À l'instant";
  if (diffMins < 60) return `Il y a ${diffMins} min`;
  if (diffHours < 24) return `Il y a ${diffHours}h`;
  if (diffDays < 7) return `Il y a ${diffDays}j`;
  
  return date.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
}

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] || { label: status, variant: "default" as const };
  
  return (
    <Badge variant={config.variant as "success" | "warning" | "error" | "default"} className="text-xs">
      {config.label}
    </Badge>
  );
}

export function RecentMessages({
  messages,
  title = "Messages récents",
  isLoading = false,
}: RecentMessagesProps) {
  if (isLoading) {
    return (
      <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
        <h3 className="text-lg font-semibold text-[#111827] mb-4">{title}</h3>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4 p-3 rounded-xl bg-[#F9FAFB]">
              <div className="h-10 w-10 bg-[#E5E7EB] animate-pulse rounded-full flex-shrink-0" />
              <div className="flex-1 space-y-2 min-w-0">
                <div className="h-4 w-32 bg-[#E5E7EB] animate-pulse rounded" />
                <div className="h-3 w-24 bg-[#E5E7EB] animate-pulse rounded" />
              </div>
              <div className="h-6 w-16 bg-[#E5E7EB] animate-pulse rounded flex-shrink-0" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!messages || messages.length === 0) {
    return (
      <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
        <h3 className="text-lg font-semibold text-[#111827] mb-4">{title}</h3>
        <div className="flex items-center justify-center py-8">
          <p className="text-[#6B7280] text-sm">Aucun message récent</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-white p-5 md:p-6 shadow-soft border border-[#E5E7EB]/50">
      <h3 className="text-lg font-semibold text-[#111827] mb-4">{title}</h3>
      <div className="space-y-2">
        {messages.map((message) => (
          <div
            key={message.id}
            className="flex items-center gap-3 sm:gap-4 p-3 rounded-xl hover:bg-[#F9FAFB] transition-colors"
          >
            {/* Avatar */}
            <div className={cn(
              "h-10 w-10 rounded-full flex items-center justify-center text-white font-medium text-sm flex-shrink-0",
              message.status === "failed" ? "bg-[#EF4444]" : "bg-emerald-500"
            )}>
              {message.contact_name
                ? message.contact_name.charAt(0).toUpperCase()
                : message.contact_phone.slice(-2)}
            </div>

            {/* Informations */}
            <div className="flex-1 min-w-0">
              <p className="font-medium text-[#111827] truncate text-sm sm:text-base">
                {message.contact_name || message.contact_phone}
              </p>
              <p className="text-xs sm:text-sm text-[#6B7280] truncate">
                <span className="hidden sm:inline">{message.campaign_name} • </span>
                {message.message_type === "message_1" ? "Msg 1" : "Msg 2"}
              </p>
            </div>

            {/* Statut et date */}
            <div className="flex flex-col items-end gap-1 flex-shrink-0">
              <StatusBadge status={message.status} />
              <span className="text-xs text-[#9CA3AF]">
                {formatRelativeTime(message.sent_at)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default RecentMessages;
