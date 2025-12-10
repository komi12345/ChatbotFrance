"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Upload, FileText, CheckCircle, XCircle, Loader2, Download } from "lucide-react";
import type { ContactImportResult } from "@/types/contact";

interface ContactImportProps {
  /** Callback lors de l'import */
  onImport: (file: File) => Promise<ContactImportResult>;
  /** Callback pour annuler */
  onCancel?: () => void;
  /** État de chargement */
  isLoading?: boolean;
}

/**
 * Composant d'import de contacts via CSV
 */
export function ContactImport({
  onImport,
  onCancel,
  isLoading = false,
}: ContactImportProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<ContactImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith(".csv")) {
        setError("Veuillez sélectionner un fichier CSV");
        return;
      }
      setSelectedFile(file);
      setError(null);
      setResult(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      if (!file.name.endsWith(".csv")) {
        setError("Veuillez sélectionner un fichier CSV");
        return;
      }
      setSelectedFile(file);
      setError(null);
      setResult(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };


  const handleImport = async () => {
    if (!selectedFile) return;

    try {
      setError(null);
      const importResult = await onImport(selectedFile);
      setResult(importResult);
    } catch (err) {
      setError("Une erreur est survenue lors de l'import");
      console.error("Import error:", err);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Générer un exemple de CSV
  const downloadTemplate = () => {
    const csvContent = `country_code,phone_number,first_name,last_name
+33,612345678,Jean,Dupont
+33,698765432,Marie,Martin
+1,5551234567,John,Doe`;
    
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "contacts_template.csv";
    link.click();
  };

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <div className="p-4 bg-muted rounded-lg">
        <h4 className="font-medium mb-2">Format du fichier CSV</h4>
        <p className="text-sm text-muted-foreground mb-2">
          Le fichier doit contenir les colonnes suivantes :
        </p>
        <ul className="text-sm text-muted-foreground list-disc list-inside space-y-1">
          <li><code className="bg-background px-1 rounded">country_code</code> - Indicatif pays (ex: +33)</li>
          <li><code className="bg-background px-1 rounded">phone_number</code> - Numéro sans indicatif (ex: 612345678)</li>
          <li><code className="bg-background px-1 rounded">first_name</code> - Prénom (optionnel)</li>
          <li><code className="bg-background px-1 rounded">last_name</code> - Nom (optionnel)</li>
        </ul>
        <Button
          variant="link"
          size="sm"
          onClick={downloadTemplate}
          className="mt-2 p-0 h-auto"
        >
          <Download className="h-4 w-4 mr-1" />
          Télécharger un modèle CSV
        </Button>
      </div>


      {/* Zone de dépôt de fichier */}
      {!result && (
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            selectedFile
              ? "border-primary bg-primary/5"
              : "border-muted-foreground/25 hover:border-primary/50"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileSelect}
            className="hidden"
          />
          
          {selectedFile ? (
            <div className="space-y-2">
              <FileText className="h-12 w-12 mx-auto text-primary" />
              <p className="font-medium">{selectedFile.name}</p>
              <p className="text-sm text-muted-foreground">
                {(selectedFile.size / 1024).toFixed(2)} Ko
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
              <p className="font-medium">Glissez-déposez votre fichier CSV ici</p>
              <p className="text-sm text-muted-foreground">
                ou cliquez pour sélectionner un fichier
              </p>
            </div>
          )}
        </div>
      )}

      {/* Erreur */}
      {error && (
        <div className="p-4 bg-destructive/10 text-destructive rounded-lg flex items-center gap-2">
          <XCircle className="h-5 w-5 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {/* Résultat de l'import */}
      {result && (
        <div className="space-y-4">
          {/* Résumé */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-[#D1FAE5] rounded-xl">
              <div className="flex items-center gap-2 text-[#059669]">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">Importés avec succès</span>
              </div>
              <p className="text-2xl font-bold mt-2 text-[#065F46]">{result.success_count}</p>
            </div>
            <div className="p-4 bg-[#FEE2E2] rounded-xl">
              <div className="flex items-center gap-2 text-[#DC2626]">
                <XCircle className="h-5 w-5" />
                <span className="font-medium">Erreurs</span>
              </div>
              <p className="text-2xl font-bold mt-2 text-[#991B1B]">{result.error_count}</p>
            </div>
          </div>


          {/* Détails des erreurs */}
          {result.errors.length > 0 && (
            <div className="border rounded-lg overflow-hidden">
              <div className="px-4 py-2 bg-muted font-medium text-sm">
                Détails des erreurs
              </div>
              <div className="max-h-48 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="px-4 py-2 text-left">Ligne</th>
                      <th className="px-4 py-2 text-left">Numéro</th>
                      <th className="px-4 py-2 text-left">Erreur</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {result.errors.map((err, index) => (
                      <tr key={index}>
                        <td className="px-4 py-2">{err.row}</td>
                        <td className="px-4 py-2 font-mono">{err.phone_number}</td>
                        <td className="px-4 py-2 text-destructive">{err.error}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Boutons d'action */}
      <div className="flex gap-2 justify-end">
        {onCancel && (
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
          >
            {result ? "Fermer" : "Annuler"}
          </Button>
        )}
        
        {result ? (
          <Button onClick={handleReset}>
            Importer un autre fichier
          </Button>
        ) : (
          <Button
            onClick={handleImport}
            disabled={!selectedFile || isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Import en cours...
              </>
            ) : (
              <>
                <Upload className="h-4 w-4 mr-2" />
                Importer les contacts
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}

export default ContactImport;
