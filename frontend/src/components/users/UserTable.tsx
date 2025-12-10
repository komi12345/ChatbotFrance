"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Plus,
  Loader2,
  Edit,
  Trash2,
  Shield,
  ShieldCheck,
  UserCheck,
  UserX,
} from "lucide-react";
import type { User } from "@/types/auth";

interface UserTableProps {
  /** Liste des utilisateurs */
  users: User[];
  /** Utilisateur courant (pour empêcher l'auto-suppression) */
  currentUserId?: number;
  /** État de chargement */
  isLoading?: boolean;
  /** Callback pour créer un utilisateur */
  onCreate?: () => void;
  /** Callback pour éditer un utilisateur */
  onEdit?: (user: User) => void;
  /** Callback pour supprimer un utilisateur */
  onDelete?: (user: User) => void;
  /** Callback pour la recherche */
  onSearch?: (search: string) => void;
  /** Valeur de recherche initiale */
  initialSearch?: string;
}

/**
 * Table des utilisateurs avec recherche
 * Accessible uniquement aux Super Admins
 */
export function UserTable({
  users,
  currentUserId,
  isLoading = false,
  onCreate,
  onEdit,
  onDelete,
  onSearch,
  initialSearch = "",
}: UserTableProps) {
  const [searchValue, setSearchValue] = useState(initialSearch);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(e.target.value);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch?.(searchValue);
  };

  // Formater le rôle pour l'affichage
  const formatRole = (role: string) => {
    return role === "super_admin" ? "Super Admin" : "Admin";
  };

  // Obtenir la variante du badge selon le rôle
  const getRoleBadgeVariant = (role: string) => {
    return role === "super_admin" ? "default" : "secondary";
  };

  return (
    <div className="space-y-4">
      {/* Barre de recherche et bouton création */}
      <div className="flex flex-col sm:flex-row gap-4">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Rechercher par email..."
              value={searchValue}
              onChange={handleSearchChange}
              className="pl-10"
            />
          </div>
          <Button type="submit" variant="secondary">
            Rechercher
          </Button>
        </form>

        {onCreate && (
          <Button onClick={onCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Nouvel utilisateur
          </Button>
        )}
      </div>

      {/* État de chargement */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Liste vide */}
      {!isLoading && users.length === 0 && (
        <div className="text-center py-12 border rounded-lg">
          <p className="text-muted-foreground">
            {searchValue
              ? "Aucun utilisateur trouvé pour cette recherche."
              : "Aucun utilisateur créé pour le moment."}
          </p>
          {!searchValue && onCreate && (
            <Button onClick={onCreate} className="mt-4">
              <Plus className="h-4 w-4 mr-2" />
              Créer votre premier utilisateur
            </Button>
          )}
        </div>
      )}

      {/* Table des utilisateurs - Responsive avec colonnes masquées sur mobile */}
      {!isLoading && users.length > 0 && (
        <div className="border rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-3 sm:px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    Email
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden sm:table-cell">
                    Rôle
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-left text-sm font-medium text-muted-foreground">
                    Statut
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-left text-sm font-medium text-muted-foreground hidden md:table-cell">
                    Date
                  </th>
                  <th className="px-3 sm:px-4 py-3 text-right text-sm font-medium text-muted-foreground">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {users.map((user) => (
                  <tr
                    key={user.id}
                    className="hover:bg-muted/30 transition-colors"
                  >
                    <td className="px-3 sm:px-4 py-3 text-sm font-medium">
                      <div className="flex items-center gap-2 flex-wrap">
                        {user.role === "super_admin" ? (
                          <ShieldCheck className="h-4 w-4 text-primary flex-shrink-0" />
                        ) : (
                          <Shield className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                        )}
                        <span className="truncate max-w-[120px] sm:max-w-none">{user.email}</span>
                        {user.id === currentUserId && (
                          <Badge variant="outline" className="text-xs">
                            Vous
                          </Badge>
                        )}
                        {/* Afficher le rôle sur mobile sous l'email */}
                        <span className="block sm:hidden w-full mt-1">
                          <Badge variant={getRoleBadgeVariant(user.role)} className="text-xs">
                            {formatRole(user.role)}
                          </Badge>
                        </span>
                      </div>
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-sm hidden sm:table-cell">
                      <Badge variant={getRoleBadgeVariant(user.role)}>
                        {formatRole(user.role)}
                      </Badge>
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-sm">
                      {user.is_active ? (
                        <div className="flex items-center gap-1 text-green-600">
                          <UserCheck className="h-4 w-4" />
                          <span className="hidden sm:inline">Actif</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1 text-red-600">
                          <UserX className="h-4 w-4" />
                          <span className="hidden sm:inline">Inactif</span>
                        </div>
                      )}
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-sm text-muted-foreground hidden md:table-cell">
                      {new Date(user.created_at).toLocaleDateString("fr-FR", {
                        day: "2-digit",
                        month: "2-digit",
                        year: "numeric",
                      })}
                    </td>
                    <td className="px-3 sm:px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1 sm:gap-2">
                        {/* Empêcher l'édition de son propre compte via cette interface */}
                        {onEdit && user.id !== currentUserId && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onEdit(user)}
                            title="Modifier"
                            className="h-9 w-9 p-0 sm:h-8 sm:w-8 touch-manipulation"
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                        )}
                        {/* Empêcher la suppression de son propre compte */}
                        {onDelete && user.id !== currentUserId && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onDelete(user)}
                            className="text-destructive hover:text-destructive h-9 w-9 p-0 sm:h-8 sm:w-8 touch-manipulation"
                            title="Supprimer"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                        {/* Message si c'est l'utilisateur courant */}
                        {user.id === currentUserId && (
                          <span className="text-xs text-muted-foreground">
                            -
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default UserTable;
