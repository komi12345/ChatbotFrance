"use client";

import { useState, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { CategoryForm } from "@/components/categories/CategoryForm";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ConfirmDialog, ErrorMessage, LoadingSpinner, useToast } from "@/components/common";
import {
  useCategory,
  useUpdateCategory,
  useDeleteCategory,
  useRemoveContactFromCategory,
  useAddContactsToCategory,
} from "@/hooks/useCategories";
import { useContacts } from "@/hooks/useContacts";
import type { CategoryCreate, CategoryContact } from "@/types/category";
import {
  ArrowLeft,
  Edit,
  Trash2,
  Users,
  Phone,
  UserMinus,
  UserPlus,
  Search,
} from "lucide-react";
import { CategoryWhatsAppStats, WhatsAppVerificationBadge } from "@/components/whatsapp";
import type { WhatsAppVerificationStatus } from "@/components/whatsapp";

/**
 * Page de détails d'une catégorie
 * Affiche les informations de la catégorie et la liste des contacts associés
 * Exigences: 3.1, 3.4, 3.5, 14.1, 14.2, 14.3
 */
export default function CategoryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const toast = useToast();
  const categoryId = Number(params.id);

  // État des modales
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [isAddContactsOpen, setIsAddContactsOpen] = useState(false);
  const [removingContact, setRemovingContact] = useState<CategoryContact | null>(null);
  const [selectedContactIds, setSelectedContactIds] = useState<number[]>([]);
  const [contactSearchQuery, setContactSearchQuery] = useState("");

  // Hooks React Query
  const { data: category, isLoading, error, refetch } = useCategory(categoryId);
  // Récupérer TOUS les contacts (limite augmentée à 1000)
  const { data: allContacts, isLoading: isLoadingContacts } = useContacts({ page: 1, size: 1000 });
  const updateMutation = useUpdateCategory();
  const deleteMutation = useDeleteCategory();
  const removeContactMutation = useRemoveContactFromCategory();
  const addContactsMutation = useAddContactsToCategory();

  // Handlers
  const handleBack = () => {
    router.push("/categories");
  };

  const handleEditSubmit = async (formData: CategoryCreate) => {
    try {
      await updateMutation.mutateAsync({
        id: categoryId,
        data: formData,
      });
      toast.success("Catégorie modifiée avec succès");
      setIsEditOpen(false);
    } catch (error) {
      toast.error("Erreur lors de la modification de la catégorie");
      console.error("Erreur lors de la modification:", error);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteMutation.mutateAsync(categoryId);
      toast.success("Catégorie supprimée avec succès");
      router.push("/categories");
    } catch (error) {
      toast.error("Erreur lors de la suppression de la catégorie");
      console.error("Erreur lors de la suppression:", error);
    }
  };

  const handleRemoveContact = async () => {
    if (!removingContact) return;
    
    try {
      await removeContactMutation.mutateAsync({
        categoryId,
        contactId: removingContact.id,
      });
      toast.success("Contact retiré de la catégorie");
      setRemovingContact(null);
    } catch (error) {
      toast.error("Erreur lors du retrait du contact");
      console.error("Erreur lors du retrait du contact:", error);
    }
  };

  const handleAddContacts = async () => {
    if (selectedContactIds.length === 0) return;
    
    try {
      await addContactsMutation.mutateAsync({
        categoryId,
        data: { contact_ids: selectedContactIds },
      });
      toast.success(`${selectedContactIds.length} contact(s) ajouté(s) à la catégorie`);
      setIsAddContactsOpen(false);
      setSelectedContactIds([]);
      refetch();
    } catch (error) {
      toast.error("Erreur lors de l'ajout des contacts");
      console.error("Erreur lors de l'ajout des contacts:", error);
    }
  };

  // Filtrer les contacts qui ne sont pas déjà dans la catégorie
  const availableContacts = useMemo(() => {
    const contacts = allContacts?.items?.filter(
      (contact) => !category?.contacts?.some((c) => c.id === contact.id)
    ) || [];
    
    // Filtrer par recherche si une requête est saisie
    if (contactSearchQuery.trim()) {
      const query = contactSearchQuery.toLowerCase();
      return contacts.filter((contact) => {
        const fullName = `${contact.first_name || ""} ${contact.last_name || ""}`.toLowerCase();
        const phone = contact.full_number.toLowerCase();
        return fullName.includes(query) || phone.includes(query);
      });
    }
    
    return contacts;
  }, [allContacts?.items, category?.contacts, contactSearchQuery]);

  // État de chargement
  if (isLoading) {
    return (
      <DashboardLayout title="Catégorie">
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" text="Chargement de la catégorie..." />
        </div>
      </DashboardLayout>
    );
  }

  // Erreur
  if (error || !category) {
    return (
      <DashboardLayout title="Catégorie">
        <div className="space-y-4">
          <Button variant="ghost" onClick={handleBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour aux catégories
          </Button>
          <ErrorMessage
            message="Catégorie non trouvée ou erreur lors du chargement."
            title="Erreur"
            onRetry={() => refetch()}
          />
        </div>
      </DashboardLayout>
    );
  }

  const gradient = category.color || "from-blue-500 to-cyan-500";

  return (
    <DashboardLayout title={category.name}>
      <div className="space-y-6">
        {/* Navigation */}
        <Button variant="ghost" onClick={handleBack}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Retour aux catégories
        </Button>

        {/* En-tête avec gradient */}
        <Card className="overflow-hidden">
          <div className={`bg-gradient-to-r ${gradient} p-6 text-white`}>
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-2xl font-bold">{category.name}</h1>
                <p className="mt-1 opacity-90">
                  Créée le {new Date(category.created_at).toLocaleDateString("fr-FR")}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsEditOpen(true)}
                >
                  <Edit className="h-4 w-4 mr-1" />
                  Modifier
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setIsDeleteOpen(true)}
                >
                  <Trash2 className="h-4 w-4 mr-1" />
                  Supprimer
                </Button>
              </div>
            </div>
          </div>
          <CardContent className="p-6">
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Users className="h-5 w-5" />
                <span className="text-lg">
                  {category.contacts?.length || 0} contact{(category.contacts?.length || 0) !== 1 ? "s" : ""} associé{(category.contacts?.length || 0) !== 1 ? "s" : ""}
                </span>
              </div>
              {/* WhatsApp verification percentage - Requirements 5.2 */}
              {category.contacts && category.contacts.length > 0 && (
                <CategoryWhatsAppStats contacts={category.contacts} />
              )}
            </div>
          </CardContent>
        </Card>

        {/* Liste des contacts */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Contacts de cette catégorie
            </CardTitle>
            <Button
              size="sm"
              onClick={() => setIsAddContactsOpen(true)}
              className="bg-emerald-500 hover:bg-emerald-600"
            >
              <UserPlus className="h-4 w-4 mr-1" />
              Ajouter des contacts
            </Button>
          </CardHeader>
          <CardContent>
            {category.contacts && category.contacts.length > 0 ? (
              <div className="divide-y">
                {category.contacts.map((contact) => {
                  // Convert whatsapp_verified boolean to status type
                  const whatsappStatus: WhatsAppVerificationStatus = 
                    contact.whatsapp_verified === true ? 'verified' :
                    contact.whatsapp_verified === false ? 'not_whatsapp' : 
                    'pending';
                  
                  return (
                    <div
                      key={contact.id}
                      className="flex items-center justify-between py-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                          <Phone className="h-4 w-4 text-muted-foreground" />
                        </div>
                        <div>
                          <p className="font-medium">
                            {contact.first_name || contact.last_name
                              ? `${contact.first_name || ""} ${contact.last_name || ""}`.trim()
                              : "Sans nom"}
                          </p>
                          <div className="flex items-center gap-2">
                            <p className="text-sm text-muted-foreground">
                              {contact.full_number}
                            </p>
                            <WhatsAppVerificationBadge status={whatsappStatus} size="sm" />
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setRemovingContact(contact)}
                        className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      >
                        <UserMinus className="h-4 w-4" />
                      </Button>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-center py-8 text-muted-foreground">
                Aucun contact dans cette catégorie.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Modal d'édition */}
      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Modifier la catégorie</DialogTitle>
          </DialogHeader>
          <CategoryForm
            category={category}
            onSubmit={handleEditSubmit}
            onCancel={() => setIsEditOpen(false)}
            isLoading={updateMutation.isPending}
          />
        </DialogContent>
      </Dialog>

      {/* Dialog de confirmation de suppression de catégorie */}
      <ConfirmDialog
        open={isDeleteOpen}
        onOpenChange={setIsDeleteOpen}
        title="Supprimer la catégorie ?"
        description={`Êtes-vous sûr de vouloir supprimer la catégorie "${category.name}" ? Cette action est irréversible. Les contacts associés ne seront pas supprimés.`}
        confirmText="Supprimer"
        cancelText="Annuler"
        onConfirm={handleDelete}
        variant="danger"
        isLoading={deleteMutation.isPending}
      />

      {/* Dialog de confirmation de retrait de contact */}
      <ConfirmDialog
        open={!!removingContact}
        onOpenChange={(open) => !open && setRemovingContact(null)}
        title="Retirer le contact ?"
        description={`Êtes-vous sûr de vouloir retirer le contact "${removingContact?.full_number || ""}" de cette catégorie ? Le contact ne sera pas supprimé du système.`}
        confirmText="Retirer"
        cancelText="Annuler"
        onConfirm={handleRemoveContact}
        variant="warning"
        isLoading={removeContactMutation.isPending}
      />

      {/* Modal d'ajout de contacts */}
      <Dialog open={isAddContactsOpen} onOpenChange={(open) => {
        setIsAddContactsOpen(open);
        if (!open) {
          setContactSearchQuery("");
          setSelectedContactIds([]);
        }
      }}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Ajouter des contacts à la catégorie</DialogTitle>
          </DialogHeader>
          
          {/* Barre de recherche */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Rechercher par nom ou numéro..."
              value={contactSearchQuery}
              onChange={(e) => setContactSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          
          {/* Compteur de contacts disponibles */}
          <p className="text-sm text-muted-foreground">
            {availableContacts.length} contact(s) disponible(s)
            {selectedContactIds.length > 0 && ` • ${selectedContactIds.length} sélectionné(s)`}
          </p>
          
          <div className="flex-1 overflow-y-auto">
            {isLoadingContacts ? (
              <div className="flex items-center justify-center py-8">
                <LoadingSpinner size="md" text="Chargement des contacts..." />
              </div>
            ) : availableContacts.length === 0 ? (
              <p className="text-center py-8 text-muted-foreground">
                Tous les contacts sont déjà dans cette catégorie ou aucun contact disponible.
              </p>
            ) : (
              <div className="space-y-2">
                {availableContacts.map((contact) => {
                  // Convert whatsapp_verified boolean to status type for badge display
                  // Requirements 4.3: Display WhatsApp badge next to each contact for informed selection
                  const contactWhatsappStatus: WhatsAppVerificationStatus = 
                    contact.whatsapp_verified === true ? 'verified' :
                    contact.whatsapp_verified === false ? 'not_whatsapp' : 
                    'pending';
                  
                  return (
                    <label
                      key={contact.id}
                      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedContactIds.includes(contact.id)
                          ? "bg-emerald-50 border border-emerald-200"
                          : "hover:bg-muted border border-transparent"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedContactIds.includes(contact.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedContactIds([...selectedContactIds, contact.id]);
                          } else {
                            setSelectedContactIds(selectedContactIds.filter((id) => id !== contact.id));
                          }
                        }}
                        className="rounded h-4 w-4"
                      />
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                        <Phone className="h-4 w-4 text-muted-foreground" />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium">
                          {contact.first_name || contact.last_name
                            ? `${contact.first_name || ""} ${contact.last_name || ""}`.trim()
                            : "Sans nom"}
                        </p>
                        <div className="flex items-center gap-2">
                          <p className="text-sm text-muted-foreground">
                            {contact.full_number}
                          </p>
                          <WhatsAppVerificationBadge status={contactWhatsappStatus} size="sm" />
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            )}
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => {
                setIsAddContactsOpen(false);
                setSelectedContactIds([]);
                setContactSearchQuery("");
              }}
            >
              Annuler
            </Button>
            <Button
              onClick={handleAddContacts}
              disabled={selectedContactIds.length === 0 || addContactsMutation.isPending}
              className="bg-emerald-500 hover:bg-emerald-600"
            >
              {addContactsMutation.isPending
                ? "Ajout en cours..."
                : `Ajouter ${selectedContactIds.length} contact(s)`}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
