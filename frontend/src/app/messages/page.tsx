"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ErrorMessage, Skeleton } from "@/components/common";
import { WassengerInfoBanner, WassengerErrorMessage, getWassengerErrorType } from "@/components/wassenger";
import { useMessages } from "@/hooks/useMessages";
import type { MessageStatus, MessageType } from "@/types/message";
import {
  CheckCircle,
  XCircle,
  Clock,
  Send,
  Eye,
  MessageSquare,
} from "lucide-react";

/**
 * Badge de statut de message
 */
function StatusBadge({ status }: { status: MessageStatus }) {
  const config = {
    pending: { label: "En attente", class: "bg-[#FEF3C7] text-[#D97706]", icon: Clock },
    sent: { label: "Envoyé", class: "bg-[#DBEAFE] text-[#1D4ED8]", icon: Send },
    delivered: { label: "Délivré", class: "bg-[#D1FAE5] text-[#059669]", icon: CheckCircle },
    read: { label: "Lu", class: "bg-[#D1FAE5] text-[#047857]", icon: Eye },
    failed: { label: "Échoué", class: "bg-[#FEE2E2] text-[#DC2626]", icon: XCircle },
  };

  const { label, class: className, icon: Icon } = config[status];

  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-md font-medium ${className}`}>
      <Icon className="h-3 w-3" />
      {label}
    </span>
  );
}

/**
 * Badge de type de message
 */
function TypeBadge({ type }: { type: MessageType }) {
  const config = {
    message_1: { label: "Message 1", class: "bg-[#E0E7FF] text-[#4338CA]" },
    message_2: { label: "Message 2", class: "bg-[#CFFAFE] text-[#0891B2]" },
  };

  const { label, class: className } = config[type];

  return (
    <span className={`inline-flex items-center text-xs px-2.5 py-1 rounded-md font-medium ${className}`}>
      {label}
    </span>
  );
}

/**
 * Page de liste des messages
 */
export default function MessagesPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<MessageStatus | "all">("all");
  const [typeFilter, setTypeFilter] = useState<MessageType | "all">("all");

  const { data, isLoading, error } = useMessages({
    page,
    status: statusFilter === "all" ? undefined : statusFilter,
    message_type: typeFilter === "all" ? undefined : typeFilter,
  });

  return (
    <DashboardLayout title="Messages">
      <div className="space-y-6">
        {/* En-tête */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Messages</h2>
            <p className="text-muted-foreground">
              Historique de tous les messages envoyés
            </p>
          </div>
        </div>

        {/* Bandeau Wassenger */}
        <WassengerInfoBanner compact />

        {/* Filtres */}
        <div className="flex items-center gap-4">
          <div className="w-48">
            <Select
              value={statusFilter}
              onValueChange={(value) => {
                setStatusFilter(value as MessageStatus | "all");
                setPage(1);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Filtrer par statut" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous les statuts</SelectItem>
                <SelectItem value="pending">En attente</SelectItem>
                <SelectItem value="sent">Envoyé</SelectItem>
                <SelectItem value="delivered">Délivré</SelectItem>
                <SelectItem value="read">Lu</SelectItem>
                <SelectItem value="failed">Échoué</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="w-48">
            <Select
              value={typeFilter}
              onValueChange={(value) => {
                setTypeFilter(value as MessageType | "all");
                setPage(1);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Filtrer par type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous les types</SelectItem>
                <SelectItem value="message_1">Message 1</SelectItem>
                <SelectItem value="message_2">Message 2</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Erreur */}
        {error && (
          <ErrorMessage
            message="Une erreur est survenue lors du chargement des messages."
            title="Erreur de chargement"
          />
        )}

        {/* Chargement */}
        {isLoading && (
          <div className="space-y-4">
            {[...Array(10)].map((_, i) => (
              <Card key={i}>
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between">
                    <Skeleton className="h-5 w-1/3" />
                    <Skeleton className="h-6 w-20" />
                  </div>
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-2/3" />
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Liste des messages */}
        {!isLoading && data && (
          <>
            {data.items.length === 0 ? (
              <div className="text-center py-12">
                <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium">Aucun message</h3>
                <p className="text-muted-foreground">
                  Aucun message ne correspond aux filtres sélectionnés
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.items.map((message) => (
                  <Card key={message.id} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="font-medium truncate">
                              {message.contact?.first_name && message.contact?.last_name
                                ? `${message.contact.first_name} ${message.contact.last_name}`
                                : message.contact?.phone_number || "Contact inconnu"}
                            </p>
                            <TypeBadge type={message.message_type} />
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {message.contact?.full_number || message.contact?.phone_number}
                          </p>
                          {message.campaign && (
                            <p className="text-xs text-muted-foreground mt-1">
                              Campagne: {message.campaign.name}
                            </p>
                          )}
                        </div>
                        <StatusBadge status={message.status} />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
                        {message.content}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        {message.sent_at && (
                          <span>
                            Envoyé: {new Date(message.sent_at).toLocaleString("fr-FR")}
                          </span>
                        )}
                        {message.delivered_at && (
                          <span>
                            Délivré: {new Date(message.delivered_at).toLocaleString("fr-FR")}
                          </span>
                        )}
                        {message.read_at && (
                          <span>
                            Lu: {new Date(message.read_at).toLocaleString("fr-FR")}
                          </span>
                        )}
                      </div>
                      {message.error_message && (
                        <div className="mt-2">
                          {message.error_message.includes("device_not_connected") || 
                           message.error_message.includes("invalid_phone_number") ||
                           message.error_message.includes("session_expired") ||
                           message.error_message.includes("rate_limit") ? (
                            <WassengerErrorMessage
                              errorType={getWassengerErrorType(undefined, message.error_message)}
                              originalMessage={message.error_message}
                            />
                          ) : (
                            <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                              <strong>Erreur:</strong> {message.error_message}
                            </div>
                          )}
                        </div>
                      )}
                      {message.retry_count > 0 && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Tentatives: {message.retry_count}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Pagination */}
            {data.pages > 1 && (
              <div className="flex items-center justify-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Précédent
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} sur {data.pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page === data.pages}
                >
                  Suivant
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
