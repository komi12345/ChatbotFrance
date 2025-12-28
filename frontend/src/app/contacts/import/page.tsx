"use client";

import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ContactImport } from "@/components/contacts/ContactImport";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/common";
import { useImportContacts } from "@/hooks/useContacts";
import { ArrowLeft } from "lucide-react";
import type { ContactImportResult } from "@/types/contact";

/**
 * Page d'import de contacts via CSV
 * Exigences: 2.3, 14.1, 14.2, 14.3, 14.4
 */
export default function ContactImportPage() {
  const router = useRouter();
  const toast = useToast();
  const importMutation = useImportContacts();

  const handleImport = async (file: File): Promise<ContactImportResult> => {
    try {
      const result = await importMutation.mutateAsync(file);
      
      // Afficher un seul message selon le résultat
      if (result.error_count === 0 && result.success_count > 0) {
        // Tout est OK
        toast.success(`${result.success_count} contact(s) importé(s) avec succès`);
      } else if (result.success_count === 0 && result.error_count > 0) {
        // Tout a échoué
        toast.error(`Échec de l'import : ${result.error_count} erreur(s)`);
      } else if (result.success_count > 0 && result.error_count > 0) {
        // Résultat mixte
        toast.warning(`${result.success_count} importé(s), ${result.error_count} erreur(s)`);
      }
      
      return result;
    } catch (error) {
      toast.error("Erreur lors de l'import des contacts");
      throw error;
    }
  };

  const handleCancel = () => {
    router.push("/contacts");
  };

  return (
    <DashboardLayout title="Import de contacts">
      <div className="space-y-6">
        {/* En-tête avec bouton retour */}
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/contacts")}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour aux contacts
          </Button>
        </div>

        {/* Titre */}
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Import de contacts</h2>
          <p className="text-muted-foreground">
            Importez plusieurs contacts à la fois depuis un fichier CSV
          </p>
        </div>

        {/* Carte d'import */}
        <Card>
          <CardHeader>
            <CardTitle>Importer un fichier CSV</CardTitle>
            <CardDescription>
              Sélectionnez un fichier CSV contenant vos contacts à importer
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ContactImport
              onImport={handleImport}
              onCancel={handleCancel}
              isLoading={importMutation.isPending}
            />
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
