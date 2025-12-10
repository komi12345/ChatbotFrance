"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { CategoryList } from "@/components/categories/CategoryList";
import { CategoryForm } from "@/components/categories/CategoryForm";
import { ConfirmDialog, ErrorMessage, useToast } from "@/components/common";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  useCategories,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
} from "@/hooks/useCategories";
import type { Category, CategoryCreate } from "@/types/category";

export default function CategoriesPage() {
  const router = useRouter();
  const toast = useToast();
  
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [deletingCategory, setDeletingCategory] = useState<Category | null>(null);

  const { data, isLoading, error, refetch } = useCategories({ page, search });
  const createMutation = useCreateCategory();
  const updateMutation = useUpdateCategory();
  const deleteMutation = useDeleteCategory();

  const handleCreate = () => {
    setEditingCategory(null);
    setIsFormOpen(true);
  };

  const handleEdit = (category: Category) => {
    setEditingCategory(category);
    setIsFormOpen(true);
  };

  const handleView = (category: Category) => {
    router.push(`/categories/${category.id}`);
  };

  const handleDelete = (category: Category) => {
    setDeletingCategory(category);
  };

  const handleSearch = (searchValue: string) => {
    setSearch(searchValue);
    setPage(1);
  };

  const handleFormSubmit = async (formData: CategoryCreate) => {
    try {
      if (editingCategory) {
        await updateMutation.mutateAsync({
          id: editingCategory.id,
          data: formData,
        });
        toast.success("Catégorie modifiée avec succès");
      } else {
        await createMutation.mutateAsync(formData);
        toast.success("Catégorie créée avec succès");
      }
      setIsFormOpen(false);
      setEditingCategory(null);
    } catch (error) {
      toast.error("Erreur lors de la sauvegarde de la catégorie");
      console.error("Erreur lors de la sauvegarde:", error);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingCategory) return;
    
    try {
      await deleteMutation.mutateAsync(deletingCategory.id);
      toast.success("Catégorie supprimée avec succès");
      setDeletingCategory(null);
    } catch (error) {
      toast.error("Erreur lors de la suppression de la catégorie");
      console.error("Erreur lors de la suppression:", error);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  return (
    <DashboardLayout title="Catégories">
      <div className="space-y-6">
        {/* En-tête */}
        <div>
          <h2 className="text-2xl font-bold text-[#111827]">Catégories</h2>
          <p className="text-[#6B7280] mt-1">
            Gérez vos catégories de contacts pour organiser vos campagnes
          </p>
        </div>

        {/* Erreur */}
        {error && (
          <ErrorMessage
            message="Une erreur est survenue lors du chargement des catégories."
            title="Erreur de chargement"
            onRetry={() => refetch()}
          />
        )}

        {/* Liste des catégories */}
        <CategoryList
          categories={data?.items || []}
          isLoading={isLoading}
          onCreate={handleCreate}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onView={handleView}
          onSearch={handleSearch}
          initialSearch={search}
        />

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Précédent
            </Button>
            <span className="text-sm text-[#6B7280]">
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
      </div>

      {/* Modal de création/édition */}
      <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
        <DialogContent className="bg-white rounded-2xl border-[#E5E7EB]">
          <DialogHeader>
            <DialogTitle className="text-[#111827]">
              {editingCategory ? "Modifier la catégorie" : "Nouvelle catégorie"}
            </DialogTitle>
          </DialogHeader>
          <CategoryForm
            category={editingCategory}
            onSubmit={handleFormSubmit}
            onCancel={() => setIsFormOpen(false)}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>

      {/* Dialog de confirmation de suppression */}
      <ConfirmDialog
        open={!!deletingCategory}
        onOpenChange={(open) => !open && setDeletingCategory(null)}
        title="Supprimer la catégorie ?"
        description={`Êtes-vous sûr de vouloir supprimer la catégorie "${deletingCategory?.name || ""}" ? Cette action est irréversible. Les contacts associés ne seront pas supprimés.`}
        confirmText="Supprimer"
        cancelText="Annuler"
        onConfirm={handleConfirmDelete}
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </DashboardLayout>
  );
}
