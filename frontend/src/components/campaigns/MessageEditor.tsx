"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Link, ExternalLink } from "lucide-react";

interface MessageEditorProps {
  /** Valeur du message */
  value: string;
  /** Callback lors du changement */
  onChange: (value: string) => void;
  /** Label du champ */
  label: string;
  /** Placeholder */
  placeholder?: string;
  /** Message d'erreur */
  error?: string;
  /** Désactivé */
  disabled?: boolean;
  /** Limite de caractères */
  maxLength?: number;
}

/**
 * Éditeur de message avec insertion de liens
 */
export function MessageEditor({
  value,
  onChange,
  label,
  placeholder = "Saisissez votre message...",
  error,
  disabled = false,
  maxLength = 4096,
}: MessageEditorProps) {
  const [showLinkInput, setShowLinkInput] = useState(false);
  const [linkUrl, setLinkUrl] = useState("");
  const [linkType, setLinkType] = useState<"web" | "whatsapp">("web");

  const handleInsertLink = () => {
    if (!linkUrl.trim()) return;

    let formattedLink = linkUrl.trim();
    
    // Formater le lien selon le type
    if (linkType === "whatsapp") {
      // Nettoyer le numéro et créer le lien wa.me
      const cleanNumber = formattedLink.replace(/[^0-9]/g, "");
      formattedLink = `https://wa.me/${cleanNumber}`;
    } else {
      // Ajouter https:// si pas de protocole
      if (!formattedLink.startsWith("http://") && !formattedLink.startsWith("https://")) {
        formattedLink = `https://${formattedLink}`;
      }
    }

    // Insérer le lien à la position du curseur ou à la fin
    const newValue = value ? `${value}\n${formattedLink}` : formattedLink;
    onChange(newValue);
    
    // Reset
    setLinkUrl("");
    setShowLinkInput(false);
  };


  const characterCount = value.length;
  const isOverLimit = characterCount > maxLength;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label>{label}</Label>
        <span className={`text-xs ${isOverLimit ? "text-destructive" : "text-muted-foreground"}`}>
          {characterCount}/{maxLength}
        </span>
      </div>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        rows={5}
        className="w-full rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-sm text-[#111827] placeholder:text-[#9CA3AF] focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/10 disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-[#F9FAFB] resize-none transition-colors"
      />

      {error && <p className="text-sm text-destructive">{error}</p>}

      {/* Boutons d'insertion de liens */}
      <div className="flex gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            setLinkType("web");
            setShowLinkInput(!showLinkInput);
          }}
          disabled={disabled}
        >
          <Link className="h-4 w-4 mr-1" />
          Lien web
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => {
            setLinkType("whatsapp");
            setShowLinkInput(!showLinkInput);
          }}
          disabled={disabled}
        >
          <ExternalLink className="h-4 w-4 mr-1" />
          Lien WhatsApp
        </Button>
      </div>

      {/* Input pour le lien */}
      {showLinkInput && (
        <div className="flex gap-2 p-3 bg-muted rounded-md">
          <input
            type="text"
            value={linkUrl}
            onChange={(e) => setLinkUrl(e.target.value)}
            placeholder={linkType === "whatsapp" ? "Numéro (ex: 33612345678)" : "URL (ex: example.com)"}
            className="flex-1 rounded-md border border-input bg-background px-3 py-1 text-sm"
          />
          <Button type="button" size="sm" onClick={handleInsertLink}>
            Insérer
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowLinkInput(false)}
          >
            Annuler
          </Button>
        </div>
      )}
    </div>
  );
}

export default MessageEditor;
