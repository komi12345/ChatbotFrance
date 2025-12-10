"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ContactTable } from "@/components/contacts/ContactTable";
import { ContactForm } from "@/components/contacts/ContactForm";
import { ConfirmDialog, ErrorMessage, useToast } from "@/components/common";
import { WhatsAppVerificationStats } from "@/components/whatsapp";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  useContacts,
  useCreateContact,
  useUpdateContact,
  useDeleteContact,
  useVerifyContact,
  useWhatsAppVerificationStats,
} from "@/hooks/useContacts";
import type { Contact, ContactCreate, WhatsAppStatus } from "@/types/contact";

/**
 * Page de liste des contacts
 * Permet de créer, modifier, supprimer et importer des contacts
 * Exigences: 2.1, 2.3, 2.5, 2.6, 14.1, 14.2, 14.3
 */
export default function ContactsPage() {
  const router = useRouter();
  const toast = useToast();

  // État de la pagination et recherche
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  // État du filtre WhatsApp - Requirements 4.1, 4.2
  const [whatsappFilter, setWhatsappFilter] = useState<WhatsAppStatus>(null);
  // État du contact en cours de vérification
  const [verifyingContactId, setVerifyingContactId] = useState<number | null>(null);

  // État des modales
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [deletingContact, setDeletingContact] = useState<Contact | null>(null);

  // Hooks React Query
  const { data, isLoading, error, refetch } = useContacts({ 
    page, 
    search, 
    size: 50,
    whatsapp_status: whatsappFilter ?? undefined,
  });
  const createMutation = useCreateContact();
  const updateMutation = useUpdateContact();
  const deleteMutation = useDeleteContact();
  const verifyMutation = useVerifyContact();
  // WhatsApp verification statistics - Requirements 5.1
  const { data: verificationStats, isLoading: isLoadingStats } = useWhatsAppVerificationStats();

  // Handlers
  const handleCreate = () => {
    setEditingContact(null);
    setIsFormOpen(true);
  };

  const handleEdit = (contact: Contact) => {
    setEditingContact(contact);
    setIsFormOpen(true);
  };

  const handleDelete = (contact: Contact) => {
    setDeletingContact(contact);
  };

  const handleSearch = (searchValue: string) => {
    setSearch(searchValue);
    setPage(1);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
  };

  const handleImport = () => {
    router.push("/contacts/import");
  };

  // Handler pour re-vérifier le statut WhatsApp d'un contact - Requirements 3.1
  const handleReVerify = async (contact: Contact) => {
    setVerifyingContactId(contact.id);
    try {
      await verifyMutation.mutateAsync(contact.id);
      toast.success("Vérification WhatsApp effectuée");
    } catch (error) {
      toast.error("Erreur lors de la vérification WhatsApp");
      console.error("Erreur lors de la vérification:", error);
    } finally {
      setVerifyingContactId(null);
    }
  };

  // Handler pour changer le filtre WhatsApp - Requirements 4.1, 4.2
  const handleWhatsAppFilterChange = (filter: WhatsAppStatus) => {
    setWhatsappFilter(filter);
    setPage(1); // Reset to first page when filter changes
  };

  const handleFormSubmit = async (formData: ContactCreate) => {
    try {
      if (editingContact) {
        await updateMutation.mutateAsync({
          id: editingContact.id,
          data: {
            phone_number: formData.phone_number,
            country_code: formData.country_code,
            first_name: formData.first_name,
            last_name: formData.last_name,
            // Toujours envoyer category_ids pour permettre de retirer toutes les catégories
            category_ids: formData.category_ids ?? [],
          },
        });
        toast.success("Contact modifié avec succès");
      } else {
        await createMutation.mutateAsync(formData);
        toast.success("Contact créé avec succès");
      }
      setIsFormOpen(false);
      setEditingContact(null);
    } catch (error) {
      toast.error("Erreur lors de la sauvegarde du contact");
      console.error("Erreur lors de la sauvegarde:", error);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingContact) return;

    try {
      await deleteMutation.mutateAsync(deletingContact.id);
      toast.success("Contact supprimé avec succès");
      setDeletingContact(null);
    } catch (error) {
      toast.error("Erreur lors de la suppression du contact");
      console.error("Erreur lors de la suppression:", error);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  // Formater le nom du contact pour l'affichage
  const formatContactName = (contact: Contact) => {
    const parts = [contact.first_name, contact.last_name].filter(Boolean);
    return parts.length > 0 ? parts.join(" ") : contact.full_number;
  };

  return (
    <DashboardLayout title="Contacts">
      <div className="space-y-6">
        {/* En-tête */}
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Contacts</h2>
          <p className="text-muted-foreground">
            Gérez vos contacts WhatsApp et organisez-les par catégories
          </p>
        </div>

        {/* Statistiques de vérification WhatsApp - Requirements 5.1 */}
        <WhatsAppVerificationStats
          verifiedCount={verificationStats?.verified_count ?? 0}
          notWhatsappCount={verificationStats?.not_whatsapp_count ?? 0}
          pendingCount={verificationStats?.pending_count ?? 0}
          totalCount={verificationStats?.total_count ?? 0}
          isLoading={isLoadingStats}
        />

        {/* Erreur */}
        {error && (
          <ErrorMessage
            message="Une erreur est survenue lors du chargement des contacts."
            title="Erreur de chargement"
            onRetry={() => refetch()}
          />
        )}

        {/* Table des contacts */}
        <ContactTable
          contacts={data?.items || []}
          isLoading={isLoading}
          onCreate={handleCreate}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onSearch={handleSearch}
          initialSearch={search}
          onImport={handleImport}
          pagination={
            data
              ? {
                  page: data.page,
                  pages: data.pages,
                  total: data.total,
                }
              : undefined
          }
          onPageChange={handlePageChange}
          onReVerify={handleReVerify}
          verifyingContactId={verifyingContactId}
          whatsappFilter={whatsappFilter}
          onWhatsAppFilterChange={handleWhatsAppFilterChange}
        />
      </div>

      {/* Modal de création/édition */}
      <Dialog open={isFormOpen} onOpenChange={setIsFormOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingContact ? "Modifier le contact" : "Nouveau contact"}
            </DialogTitle>
          </DialogHeader>
          <ContactForm
            contact={editingContact}
            onSubmit={handleFormSubmit}
            onCancel={() => setIsFormOpen(false)}
            isLoading={isSubmitting}
          />
        </DialogContent>
      </Dialog>

      {/* Dialog de confirmation de suppression */}
      <ConfirmDialog
        open={!!deletingContact}
        onOpenChange={(open) => !open && setDeletingContact(null)}
        title="Supprimer le contact ?"
        description={`Êtes-vous sûr de vouloir supprimer le contact "${deletingContact ? formatContactName(deletingContact) : ""}" ? Cette action est irréversible. Le contact sera retiré de toutes les catégories.`}
        confirmText="Supprimer"
        cancelText="Annuler"
        onConfirm={handleConfirmDelete}
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </DashboardLayout>
  );
}
