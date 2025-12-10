"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { COUNTRY_CODES } from "@/lib/constants";
import { useCategories } from "@/hooks/useCategories";
import type { Contact, ContactCreate } from "@/types/contact";
import { Search, ChevronDown } from "lucide-react";

// Schéma de validation
const contactSchema = z.object({
  country_code: z.string().min(1, "L'indicatif pays est requis"),
  phone_number: z
    .string()
    .min(1, "Le numéro de téléphone est requis")
    .regex(/^[0-9]+$/, "Le numéro ne doit contenir que des chiffres"),
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  category_ids: z.array(z.number()).optional(),
});

type ContactFormData = z.infer<typeof contactSchema>;

interface ContactFormProps {
  /** Contact à éditer (null pour création) */
  contact?: Contact | null;
  /** Callback lors de la soumission */
  onSubmit: (data: ContactCreate) => void;
  /** Callback pour annuler */
  onCancel?: () => void;
  /** État de chargement */
  isLoading?: boolean;
}

/**
 * Formulaire de création/édition de contact
 */
export function ContactForm({
  contact,
  onSubmit,
  onCancel,
  isLoading = false,
}: ContactFormProps) {
  const isEditing = !!contact;
  const [isCountryDropdownOpen, setIsCountryDropdownOpen] = useState(false);
  const [countrySearch, setCountrySearch] = useState("");

  // Récupérer les catégories disponibles
  const { data: categoriesData } = useCategories({ page: 1 });
  const categories = categoriesData?.items || [];

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      country_code: contact?.country_code || "+33",
      phone_number: contact?.phone_number || "",
      first_name: contact?.first_name || "",
      last_name: contact?.last_name || "",
      category_ids: contact?.categories?.map((c) => c.id) || [],
    },
  });

  // Réinitialiser le formulaire quand le contact change (pour l'édition)
  useEffect(() => {
    reset({
      country_code: contact?.country_code || "+33",
      phone_number: contact?.phone_number || "",
      first_name: contact?.first_name || "",
      last_name: contact?.last_name || "",
      category_ids: contact?.categories?.map((c) => c.id) || [],
    });
  }, [contact, reset]);

  const selectedCountryCode = watch("country_code");

  // Filtrer les pays selon la recherche
  const filteredCountries = COUNTRY_CODES.filter(
    (country) =>
      country.country.toLowerCase().includes(countrySearch.toLowerCase()) ||
      country.code.includes(countrySearch)
  );

  // Trouver le pays sélectionné
  const selectedCountry = COUNTRY_CODES.find(
    (c) => c.code === selectedCountryCode
  );

  const selectedCategoryIds = watch("category_ids") || [];

  const handleFormSubmit = (data: ContactFormData) => {
    onSubmit({
      country_code: data.country_code,
      phone_number: data.phone_number,
      first_name: data.first_name || undefined,
      last_name: data.last_name || undefined,
      // Toujours envoyer category_ids (même vide) pour permettre de retirer toutes les catégories
      category_ids: data.category_ids || [],
    });
  };

  const handleSelectCountry = (code: string) => {
    setValue("country_code", code);
    setIsCountryDropdownOpen(false);
    setCountrySearch("");
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Nom et prénom - Stack sur mobile, côte à côte sur desktop */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="first_name">Prénom</Label>
          <Input
            id="first_name"
            placeholder="Jean"
            {...register("first_name")}
            disabled={isLoading}
            className="h-11 sm:h-10" // Plus grand sur mobile pour le tactile
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="last_name">Nom</Label>
          <Input
            id="last_name"
            placeholder="Dupont"
            {...register("last_name")}
            disabled={isLoading}
            className="h-11 sm:h-10"
          />
        </div>
      </div>

      {/* Indicatif pays */}
      <div className="space-y-2">
        <Label>Indicatif pays *</Label>
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsCountryDropdownOpen(!isCountryDropdownOpen)}
            className="w-full flex items-center justify-between px-3 py-3 sm:py-2 border rounded-md bg-background hover:bg-accent transition-colors min-h-[44px] touch-manipulation"
            disabled={isLoading}
          >
            <span className="truncate">
              {selectedCountry
                ? `${selectedCountry.flag} ${selectedCountry.code} ${selectedCountry.country}`
                : "Sélectionner un pays"}
            </span>
            <ChevronDown className="h-4 w-4 text-muted-foreground flex-shrink-0 ml-2" />
          </button>


          {/* Dropdown des pays - Plus grand sur mobile */}
          {isCountryDropdownOpen && (
            <div 
              className="absolute z-[100] w-full mt-1 border rounded-md shadow-xl max-h-[50vh] sm:max-h-60 overflow-hidden"
              style={{ backgroundColor: '#ffffff' }}
            >
              {/* Recherche */}
              <div className="p-2 border-b sticky top-0" style={{ backgroundColor: '#ffffff' }}>
                <div className="relative">
                  <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Rechercher un pays..."
                    value={countrySearch}
                    onChange={(e) => setCountrySearch(e.target.value)}
                    className="pl-8 h-11 sm:h-10"
                    style={{ backgroundColor: '#ffffff' }}
                    autoFocus
                  />
                </div>
              </div>
              {/* Liste des pays - Touch-friendly */}
              <div className="max-h-[40vh] sm:max-h-48 overflow-y-auto overscroll-contain" style={{ backgroundColor: '#ffffff' }}>
                {filteredCountries.length === 0 ? (
                  <div className="p-3 text-center text-muted-foreground" style={{ backgroundColor: '#ffffff' }}>
                    Aucun pays trouvé
                  </div>
                ) : (
                  filteredCountries.map((country, index) => (
                    <button
                      key={`${country.code}-${country.country}-${index}`}
                      type="button"
                      onClick={() => handleSelectCountry(country.code)}
                      className={`w-full px-3 py-3 sm:py-2 text-left transition-colors min-h-[44px] touch-manipulation`}
                      style={{ 
                        backgroundColor: selectedCountryCode === country.code ? '#f3f4f6' : '#ffffff'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = selectedCountryCode === country.code ? '#f3f4f6' : '#ffffff'}
                    >
                      {country.flag} {country.code} {country.country}
                    </button>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
        {errors.country_code && (
          <p className="text-sm text-destructive">{errors.country_code.message}</p>
        )}
      </div>

      {/* Numéro de téléphone */}
      <div className="space-y-2">
        <Label htmlFor="phone_number">Numéro de téléphone *</Label>
        <div className="flex gap-2">
          <div className="w-20 sm:w-24 px-2 sm:px-3 py-3 sm:py-2 border rounded-md bg-muted text-muted-foreground text-sm sm:text-base flex items-center justify-center">
            {selectedCountryCode}
          </div>
          <Input
            id="phone_number"
            placeholder="612345678"
            {...register("phone_number")}
            disabled={isLoading}
            className="flex-1 h-11 sm:h-10"
            inputMode="tel" // Clavier numérique sur mobile
            autoComplete="tel"
          />
        </div>
        {errors.phone_number && (
          <p className="text-sm text-destructive">{errors.phone_number.message}</p>
        )}
        <p className="text-xs text-muted-foreground">
          Entrez le numéro sans l&apos;indicatif pays (ex: 612345678)
        </p>
      </div>

      {/* Prévisualisation du numéro complet */}
      <div className="p-3 bg-muted rounded-md">
        <p className="text-sm text-muted-foreground">Numéro complet :</p>
        <p className="font-mono font-medium">
          {selectedCountryCode}{watch("phone_number") || "XXXXXXXXX"}
        </p>
      </div>

      {/* Sélection des catégories */}
      {categories.length > 0 && (
        <div className="space-y-2">
          <Label>Catégories (optionnel)</Label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-y-auto p-2 border rounded-md">
            {categories.map((category) => (
              <label
                key={category.id}
                className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors min-h-[40px] ${
                  selectedCategoryIds.includes(category.id)
                    ? "bg-emerald-50 border border-emerald-200"
                    : "hover:bg-muted border border-transparent"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedCategoryIds.includes(category.id)}
                  onChange={(e) => {
                    const newCategoryIds = e.target.checked
                      ? [...selectedCategoryIds, category.id]
                      : selectedCategoryIds.filter((id) => id !== category.id);
                    setValue("category_ids", newCategoryIds, { shouldDirty: true, shouldValidate: true });
                  }}
                  disabled={isLoading}
                  className="rounded h-4 w-4"
                />
                <span className="text-sm truncate">{category.name}</span>
              </label>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            Sélectionnez les catégories auxquelles ajouter ce contact
          </p>
        </div>
      )}

      {/* Boutons d'action - Full width sur mobile */}
      <div className="flex flex-col-reverse sm:flex-row gap-2 sm:justify-end">
        {onCancel && (
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isLoading}
            className="w-full sm:w-auto min-h-[44px] touch-manipulation"
          >
            Annuler
          </Button>
        )}
        <Button 
          type="submit" 
          disabled={isLoading}
          className="w-full sm:w-auto min-h-[44px] touch-manipulation"
        >
          {isLoading
            ? "Chargement..."
            : isEditing
            ? "Modifier"
            : "Créer le contact"}
        </Button>
      </div>
    </form>
  );
}

export default ContactForm;
