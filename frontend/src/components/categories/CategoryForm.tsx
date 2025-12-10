"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { Category, CategoryCreate } from "@/types/category";

// Schéma de validation
const categorySchema = z.object({
  name: z
    .string()
    .min(1, "Le nom est requis")
    .max(255, "Le nom ne peut pas dépasser 255 caractères"),
  color: z.string().optional(),
});

type CategoryFormData = z.infer<typeof categorySchema>;

// Couleurs prédéfinies pour les gradients
const GRADIENT_OPTIONS = [
  { value: "from-blue-500 to-cyan-500", label: "Bleu", preview: "bg-gradient-to-r from-blue-500 to-cyan-500" },
  { value: "from-purple-500 to-pink-500", label: "Violet", preview: "bg-gradient-to-r from-purple-500 to-pink-500" },
  { value: "from-green-500 to-emerald-500", label: "Vert", preview: "bg-gradient-to-r from-green-500 to-emerald-500" },
  { value: "from-orange-500 to-amber-500", label: "Orange", preview: "bg-gradient-to-r from-orange-500 to-amber-500" },
  { value: "from-red-500 to-rose-500", label: "Rouge", preview: "bg-gradient-to-r from-red-500 to-rose-500" },
  { value: "from-indigo-500 to-violet-500", label: "Indigo", preview: "bg-gradient-to-r from-indigo-500 to-violet-500" },
  { value: "from-teal-500 to-green-500", label: "Turquoise", preview: "bg-gradient-to-r from-teal-500 to-green-500" },
  { value: "from-fuchsia-500 to-purple-500", label: "Fuchsia", preview: "bg-gradient-to-r from-fuchsia-500 to-purple-500" },
];

interface CategoryFormProps {
  /** Catégorie à éditer (null pour création) */
  category?: Category | null;
  /** Callback lors de la soumission */
  onSubmit: (data: CategoryCreate) => void;
  /** Callback pour annuler */
  onCancel?: () => void;
  /** État de chargement */
  isLoading?: boolean;
}

/**
 * Formulaire de création/édition de catégorie
 */
export function CategoryForm({
  category,
  onSubmit,
  onCancel,
  isLoading = false,
}: CategoryFormProps) {
  const isEditing = !!category;

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<CategoryFormData>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      name: category?.name || "",
      color: category?.color || GRADIENT_OPTIONS[0].value,
    },
  });

  const selectedColor = watch("color");

  const handleFormSubmit = (data: CategoryFormData) => {
    onSubmit({
      name: data.name,
      color: data.color,
    });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Nom de la catégorie */}
      <div className="space-y-2">
        <Label htmlFor="name">Nom de la catégorie *</Label>
        <Input
          id="name"
          placeholder="Ex: Clients VIP"
          {...register("name")}
          disabled={isLoading}
        />
        {errors.name && (
          <p className="text-sm text-destructive">{errors.name.message}</p>
        )}
      </div>

      {/* Sélection de couleur - Responsive grid */}
      <div className="space-y-2">
        <Label>Couleur du gradient</Label>
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-2">
          {GRADIENT_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setValue("color", option.value)}
              className={`h-12 sm:h-10 rounded-md ${option.preview} transition-all touch-manipulation ${
                selectedColor === option.value
                  ? "ring-2 ring-offset-2 ring-primary"
                  : "hover:opacity-80 active:opacity-70"
              }`}
              title={option.label}
              disabled={isLoading}
              aria-label={option.label}
            />
          ))}
        </div>
      </div>

      {/* Prévisualisation */}
      <div className="space-y-2">
        <Label>Prévisualisation</Label>
        <div
          className={`h-16 rounded-lg bg-gradient-to-r ${selectedColor} flex items-center justify-center text-white font-semibold`}
        >
          {watch("name") || "Nom de la catégorie"}
        </div>
      </div>

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
            : "Créer la catégorie"}
        </Button>
      </div>
    </form>
  );
}

export default CategoryForm;
