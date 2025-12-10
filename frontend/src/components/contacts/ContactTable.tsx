"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Plus, Loader2, Edit, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import { formatCountryCode } from "@/lib/constants";
import type { Contact, WhatsAppStatus } from "@/types/contact";
import { WhatsAppVerificationBadge, type WhatsAppVerificationStatus } from "@/components/whatsapp/WhatsAppVerificationBadge";

interface ContactTableProps {
  /** Liste des contacts */
  contacts: Contact[];
  /** État de chargement */
  isLoading?: boolean;
  /** Callback pour créer un contact */
  onCreate?: () => void;
  /** Callback pour éditer un contact */
  onEdit?: (contact: Contact) => void;
  /** Callback pour supprimer un contact */
  onDelete?: (contact: Contact) => void;
  /** Callback pour la recherche */
  onSearch?: (search: string) => void;
  /** Valeur de recherche initiale */
  initialSearch?: string;
  /** Informations de pagination */
  pagination?: {
    page: number;
    pages: number;
    total: number;
  };
  /** Callback pour changer de page */
  onPageChange?: (page: number) => void;
  /** Callback pour importer des contacts */
  onImport?: () => void;
  /** Callback pour re-vérifier le statut WhatsApp d'un contact */
  onReVerify?: (contact: Contact) => void;
  /** ID du contact en cours de vérification */
  verifyingContactId?: number | null;
  /** Filtre WhatsApp actuel */
  whatsappFilter?: WhatsAppStatus;
  /** Callback pour changer le filtre WhatsApp */
  onWhatsAppFilterChange?: (filter: WhatsAppStatus) => void;
}

/**
 * Table des contacts avec pagination et recherche
 */
export function ContactTable({
  contacts,
  isLoading = false,
  onCreate,
  onEdit,
  onDelete,
  onSearch,
  initialSearch = "",
  pagination,
  onPageChange,
  onImport,
  onReVerify,
  verifyingContactId,
  whatsappFilter,
  onWhatsAppFilterChange,
}: ContactTableProps) {
  const [searchValue, setSearchValue] = useState(initialSearch);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch?.(searchValue);
  };

  // Formater le nom complet
  const formatName = (contact: Contact) => {
    const parts = [contact.first_name, contact.last_name].filter(Boolean);
    return parts.length > 0 ? parts.join(" ") : "-";
  };

  // Convertir le statut de vérification WhatsApp du contact vers le type du badge
  const getWhatsAppStatus = (contact: Contact): WhatsAppVerificationStatus => {
    if (contact.whatsapp_verified === true) return 'verified';
    if (contact.whatsapp_verified === false) return 'not_whatsapp';
    return 'pending';
  };

  // Options de filtre WhatsApp
  const whatsappFilterOptions: { value: WhatsAppStatus; label: string }[] = [
    { value: null, label: "Tous" },
    { value: "verified", label: "WhatsApp vérifié" },
    { value: "not_whatsapp", label: "Non-WhatsApp" },
    { value: "pending", label: "Non vérifié" },
  ];

  return (
    <div className="space-y-4">
      {/* Barre de recherche et boutons */}
      <div className="flex flex-col sm:flex-row gap-4">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Rechercher par nom ou numéro..."
              value={searchValue}
              onChange={handleSearchChange}
              className="pl-10"
            />
          </div>
          <Button type="submit" variant="secondary">
            Rechercher
          </Button>
        </form>

        {/* Filtre WhatsApp - Requirements 4.1, 4.2 */}
        {onWhatsAppFilterChange && (
          <select
            value={whatsappFilter ?? ""}
            onChange={(e) => {
              const value = e.target.value;
              if (value === "") {
                onWhatsAppFilterChange(null);
              } else {
                onWhatsAppFilterChange(value as WhatsAppStatus);
              }
            }}
            className="h-10 px-3 rounded-md border border-input bg-background text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            aria-label="Filtrer par statut WhatsApp"
          >
            {whatsappFilterOptions.map((option) => (
              <option key={option.label} value={option.value ?? ""}>
                {option.label}
              </option>
            ))}
          </select>
        )}

        <div className="flex gap-2">
          {onImport && (
            <Button variant="outline" onClick={onImport}>
              Importer CSV
            </Button>
          )}
          {onCreate && (
            <Button onClick={onCreate}>
              <Plus className="h-4 w-4 mr-2" />
              Nouveau contact
            </Button>
          )}
        </div>
      </div>

      {/* État de chargement */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Liste vide */}
      {!isLoading && contacts.length === 0 && (
        <div className="text-center py-12 border rounded-lg">
          <p className="text-muted-foreground">
            {searchValue
              ? "Aucun contact trouvé pour cette recherche."
              : "Aucun contact créé pour le moment."}
          </p>
          {!searchValue && onCreate && (
            <Button onClick={onCreate} className="mt-4">
              <Plus className="h-4 w-4 mr-2" />
              Créer votre premier contact
            </Button>
          )}
        </div>
      )}


      {/* Table des contacts - Responsive avec colonnes masquées sur mobile */}
      {!isLoading && contacts.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-3 sm:px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    Nom
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden sm:table-cell">
                    Pays
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    Numéro
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    WhatsApp
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell">
                    Catégories
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden lg:table-cell">
                    Date
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-right text-sm font-medium text-muted-foreground">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {contacts.map((contact) => (
                  <tr key={contact.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-3 sm:px-4 py-3 text-sm font-medium">
                      <div>
                        {formatName(contact)}
                        {/* Afficher le pays sur mobile sous le nom */}
                        <span className="block sm:hidden text-xs text-muted-foreground mt-0.5">
                          {formatCountryCode(contact.country_code)}
                        </span>
                      </div>
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-sm hidden sm:table-cell">
                      {formatCountryCode(contact.country_code)}
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-sm font-mono text-xs sm:text-sm">
                      {contact.full_number}
                    </td>
                    {/* WhatsApp Badge Column - Requirements 2.1, 2.2, 2.3, 3.1 */}
                    <td className="px-3 sm:px-4 py-3 text-sm">
                      <WhatsAppVerificationBadge
                        status={getWhatsAppStatus(contact)}
                        onReVerify={onReVerify ? () => onReVerify(contact) : undefined}
                        isLoading={verifyingContactId === contact.id}
                        size="sm"
                      />
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-sm hidden md:table-cell">
                      {contact.categories && contact.categories.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {contact.categories.slice(0, 3).map((cat) => (
                            <span
                              key={cat.id}
                              className="inline-flex items-center px-2 py-0.5 rounded-full text-xs bg-primary/10 text-primary"
                            >
                              {cat.name}
                            </span>
                          ))}
                          {contact.categories.length > 3 && (
                            <span className="text-xs text-muted-foreground">
                              +{contact.categories.length - 3}
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-sm text-muted-foreground hidden lg:table-cell">
                      {new Date(contact.created_at).toLocaleDateString("fr-FR")}
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1 sm:gap-2">
                        {onEdit && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onEdit(contact)}
                            className="h-9 w-9 p-0 sm:h-8 sm:w-8 touch-manipulation"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        )}
                        {onDelete && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onDelete(contact)}
                            className="text-destructive hover:text-destructive h-9 w-9 p-0 sm:h-8 sm:w-8 touch-manipulation"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>


          {/* Pagination dans la table */}
          {pagination && pagination.pages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t bg-muted/30">
              <p className="text-sm text-muted-foreground">
                {pagination.total} contact{pagination.total > 1 ? "s" : ""} au total
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPageChange?.(pagination.page - 1)}
                  disabled={pagination.page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm">
                  Page {pagination.page} sur {pagination.pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onPageChange?.(pagination.page + 1)}
                  disabled={pagination.page === pagination.pages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ContactTable;
