"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { UserTable } from "@/components/users/UserTable";
import { UserForm } from "@/components/users/UserForm";
import { ConfirmDialog, ErrorMessage, LoadingSpinner, useToast } from "@/components/common";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAuth } from "@/hooks/useAuth";
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
} from "@/hooks/useUsers";
import type { User, UserCreate, UserUpdate } from "@/types/auth";
import { ShieldAlert } from "lucide-react";

/**
 * Page de gestion des utilisateurs
 * Accessible uniquement aux Super Admins
 * Permet de créer, modifier et supprimer des comptes Admin
 * Exigences: 1.2, 1.3, 1.4, 14.1, 14.2, 14.3
 */
export default function AdminUsersPage() {
  const router = useRouter();
  const toast = useToast();
  const { user: currentUser, isSuperAdmin, isLoading: authLoading } = useAuth();

  // État de la recherche
  const [search, setSearch] = useState("");

  // État des modales
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);

  // Hooks React Query
  const { data: users, isLoading, error, refetch } = useUsers({ search });
  const createMutation = useCreateUser();
  const updateMutation = useUpdateUser();
  const deleteMutation = useDeleteUser();

  // Vérifier l'accès Super Admin
  useEffect(() => {
    if (!authLoading && !isSuperAdmin()) {
      router.push("/dashboard");
    }
  }, [authLoading, isSuperAdmin, router]);

  // Handlers
  const handleCreate = () => {
    setEditingUser(null);
    setIsFormOpen(true);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setIsFormOpen(true);
  };

  const handleDelete = (user: User) => {
    setDeletingUser(user);
  };

  const handleSearch = (searchValue: string) => {
    setSearch(searchValue);
  };

  const handleCreateSubmit = async (formData: UserCreate) => {
    try {
      await createMutation.mutateAsync(formData);
      toast.success("Utilisateur créé avec succès");
      setIsFormOpen(false);
    } catch (error) {
      toast.error("Erreur lors de la création de l'utilisateur");
      console.error("Erreur lors de la création:", error);
    }
  };

  const handleUpdateSubmit = async (formData: UserUpdate) => {
    if (!editingUser) return;

    try {
      await updateMutation.mutateAsync({
        id: editingUser.id,
        data: formData,
      });
      toast.success("Utilisateur modifié avec succès");
      setIsFormOpen(false);
      setEditingUser(null);
    } catch (error) {
      toast.error("Erreur lors de la modification de l'utilisateur");
      console.error("Erreur lors de la mise à jour:", error);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingUser) return;

    try {
      await deleteMutation.mutateAsync(deletingUser.id);
      toast.success("Utilisateur supprimé avec succès");
      setDeletingUser(null);
    } catch (error) {
      toast.error("Erreur lors de la suppression de l'utilisateur");
      console.error("Erreur lors de la suppression:", error);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  // Afficher un loader pendant la vérification d'authentification
  if (authLoading) {
    return (
      <DashboardLayout title="Gestion des utilisateurs">
        <div className="flex items-center justify-center min-h-[400px]">
          <LoadingSpinner size="lg" text="Vérification des permissions..." />
        </div>
      </DashboardLayout>
    );
  }

  // Afficher un message d'accès refusé si non Super Admin
  if (!isSuperAdmin()) {
    return (
      <DashboardLayout title="Accès refusé">
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center">
          <ShieldAlert className="h-16 w-16 text-destructive mb-4" />
          <h2 className="text-2xl font-bold mb-2">Accès refusé</h2>
          <p className="text-muted-foreground max-w-md">
            Cette page est réservée aux Super Admins. Vous n&apos;avez pas les
            permissions nécessaires pour accéder à la gestion des utilisateurs.
          </p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title="Gestion des utilisateurs">
      <div className="space-y-6">
        {/* En-tête */}
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Gestion des utilisateurs
          </h2>
          <p className="text-muted-foreground">
            Créez et gérez les comptes Admin de votre plateforme
          </p>
        </div>

        {/* Erreur */}
        {error && (
          <ErrorMessage
            message="Une erreur est survenue lors du chargement des utilisateurs."
            title="Erreur de chargement"
            onRetry={() => refetch()}
          />
        )}

        {/* Table des utilisateurs */}
        <UserTable
          users={users || []}
          currentUserId={currentUser?.id}
          isLoading={isLoading}
          onCreate={handleCreate}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onSearch={handleSearch}
          initialSearch={search}
        />
      </div>

      {/* Modal de création/édition */}
      <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingUser ? "Modifier l'utilisateur" : "Nouvel utilisateur"}
            </DialogTitle>
          </DialogHeader>
          <UserForm
            user={editingUser}
            onSubmitCreate={handleCreateSubmit}
            onSubmitUpdate={handleUpdateSubmit}
            onCancel={() => {
              setIsFormOpen(false);
              setEditingUser(null);
            }}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>

      {/* Dialog de confirmation de suppression */}
      <ConfirmDialog
        open={!!deletingUser}
        onOpenChange={(open) => !open && setDeletingUser(null)}
        title="Supprimer l'utilisateur ?"
        description={`Êtes-vous sûr de vouloir supprimer l'utilisateur "${deletingUser?.email || ""}" ? Cette action est irréversible. L'utilisateur ne pourra plus se connecter à la plateforme.`}
        confirmText="Supprimer"
        cancelText="Annuler"
        onConfirm={handleConfirmDelete}
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </DashboardLayout>
  );
}
