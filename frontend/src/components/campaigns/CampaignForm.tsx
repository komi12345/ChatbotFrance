"use client";

import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MessageEditor } from "./MessageEditor";
import { MessagePreview } from "./MessagePreview";
import type { Category } from "@/types/category";
import type { CampaignCreate } from "@/types/campaign";

// Regex pour valider les URLs
const urlRegex = /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/;

// Schéma de validation
const campaignSchema = z.object({
  name: z
    .string()
    .min(1, "Le nom est requis")
    .max(255, "Le nom ne peut pas dépasser 255 caractères"),
  message_1: z
    .string()
    .min(1, "Le Message 1 est requis")
    .max(4096, "Le message ne peut pas dépasser 4096 caractères")
    .refine(
      (val) => {
        // Valider les URLs dans le message
        const urls = val.match(/(https?:\/\/[^\s]+)/g) || [];
        return urls.every((url) => urlRegex.test(url) || url.startsWith("https://wa.me/"));
      },
      { message: "Une ou plusieurs URLs sont invalides" }
    ),
  message_2: z
    .string()
    .max(4096, "Le message ne peut pas dépasser 4096 caractères")
    .optional(),
  template_name: z.string().optional(),
  category_ids: z
    .array(z.number())
    .min(1, "Sélectionnez au moins une catégorie"),
});

type CampaignFormData = z.infer<typeof campaignSchema>;

interface CampaignFormProps {
  /** Catégories disponibles */
  categories: Category[];
  /** Callback lors de la soumission */
  onSubmit: (data: CampaignCreate) => void;
  /** Callback pour annuler */
  onCancel?: () => void;
  /** État de chargement */
  isLoading?: boolean;
}


/**
 * Formulaire de création de campagne
 */
export function CampaignForm({
  categories,
  onSubmit,
  onCancel,
  isLoading = false,
}: CampaignFormProps) {
  const {
    register,
    control,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<CampaignFormData>({
    resolver: zodResolver(campaignSchema),
    defaultValues: {
      name: "",
      message_1: "",
      message_2: "",
      template_name: "",
      category_ids: [],
    },
  });

  const message1 = watch("message_1");
  const message2 = watch("message_2");
  const selectedCategories = watch("category_ids");

  // Calculer le nombre total de contacts
  const totalContacts = categories
    .filter((cat) => selectedCategories.includes(cat.id))
    .reduce((sum, cat) => sum + (cat.contact_count || 0), 0);

  const handleFormSubmit = (data: CampaignFormData) => {
    onSubmit({
      name: data.name,
      message_1: data.message_1,
      message_2: data.message_2 || undefined,
      template_name: data.template_name || undefined,
      category_ids: data.category_ids,
    });
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4 sm:space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Colonne gauche - Configuration */}
        <div className="space-y-6">
          {/* Nom de la campagne */}
          <div className="space-y-2">
            <Label htmlFor="name">Nom de la campagne *</Label>
            <Input
              id="name"
              placeholder="Ex: Promotion été 2024"
              {...register("name")}
              disabled={isLoading}
            />
            {errors.name && (
              <p className="text-sm text-destructive">{errors.name.message}</p>
            )}
          </div>

          {/* Template WhatsApp */}
          <div className="space-y-2">
            <Label htmlFor="template_name">Nom du template WhatsApp</Label>
            <Input
              id="template_name"
              placeholder="Ex: hello_world"
              {...register("template_name")}
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              Le template doit être approuvé par Meta
            </p>
          </div>


          {/* Sélection des catégories - Responsive grid */}
          <div className="space-y-2">
            <Label>Catégories cibles *</Label>
            <Controller
              name="category_ids"
              control={control}
              render={({ field }) => {
                const selectedIds = field.value ?? [];
                return (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-[40vh] sm:max-h-48 overflow-y-auto overscroll-contain p-2 border rounded-md">
                    {categories.length === 0 ? (
                      <p className="col-span-full text-sm text-muted-foreground text-center py-4">
                        Aucune catégorie disponible
                      </p>
                    ) : (
                      categories.map((category) => (
                        <label
                          key={category.id}
                          className={`flex items-center gap-2 p-3 sm:p-2 rounded cursor-pointer transition-colors min-h-[44px] touch-manipulation ${
                            selectedIds.includes(category.id)
                              ? "bg-primary/10 border-primary"
                              : "hover:bg-muted active:bg-muted"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={selectedIds.includes(category.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                field.onChange([...selectedIds, category.id]);
                              } else {
                                field.onChange(
                                  selectedIds.filter((id) => id !== category.id)
                                );
                              }
                            }}
                            disabled={isLoading}
                            className="rounded h-5 w-5 sm:h-4 sm:w-4"
                          />
                          <span className="text-sm truncate flex-1">{category.name}</span>
                          <span className="text-xs text-muted-foreground">
                            ({category.contact_count || 0})
                          </span>
                        </label>
                      ))
                    )}
                  </div>
                );
              }}
            />
            {errors.category_ids && (
              <p className="text-sm text-destructive">
                {errors.category_ids.message}
              </p>
            )}
            {totalContacts > 0 && (
              <p className="text-sm text-muted-foreground">
                {totalContacts} contact{totalContacts > 1 ? "s" : ""} sélectionné
                {totalContacts > 1 ? "s" : ""}
              </p>
            )}
          </div>

          {/* Message 1 */}
          <Controller
            name="message_1"
            control={control}
            render={({ field }) => (
              <MessageEditor
                value={field.value ?? ""}
                onChange={field.onChange}
                label="Message 1 (Template) *"
                placeholder="Saisissez le contenu du premier message..."
                error={errors.message_1?.message}
                disabled={isLoading}
              />
            )}
          />

          {/* Message 2 */}
          <Controller
            name="message_2"
            control={control}
            render={({ field }) => (
              <MessageEditor
                value={field.value ?? ""}
                onChange={field.onChange}
                label="Message 2 (Suivi automatique)"
                placeholder="Message envoyé automatiquement après interaction..."
                error={errors.message_2?.message}
                disabled={isLoading}
              />
            )}
          />
        </div>


        {/* Colonne droite - Prévisualisation */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Prévisualisation Message 1</CardTitle>
            </CardHeader>
            <CardContent>
              <MessagePreview content={message1} type="message_1" />
            </CardContent>
          </Card>

          {message2 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Prévisualisation Message 2</CardTitle>
              </CardHeader>
              <CardContent>
                <MessagePreview content={message2} type="message_2" />
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Boutons d'action - Full width sur mobile */}
      <div className="flex flex-col-reverse sm:flex-row gap-2 sm:justify-end pt-4 border-t">
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
          disabled={isLoading || totalContacts === 0}
          className="w-full sm:w-auto min-h-[44px] touch-manipulation"
        >
          {isLoading ? "Création en cours..." : `Créer et envoyer (${totalContacts})`}
        </Button>
      </div>
    </form>
  );
}

export default CampaignForm;
