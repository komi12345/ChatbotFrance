"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { User, UserCreate, UserUpdate, UserRole } from "@/types/auth";

// Schéma de validation pour création
const createUserSchema = z.object({
  email: z
    .string()
    .min(1, "L'email est requis")
    .email("Format d'email invalide"),
  password: z
    .string()
    .min(8, "Le mot de passe doit contenir au moins 8 caractères"),
  role: z.enum(["super_admin", "admin"], {
    message: "Le rôle est requis",
  }),
});

// Schéma de validation pour édition (mot de passe optionnel)
const updateUserSchema = z.object({
  email: z
    .string()
    .min(1, "L'email est requis")
    .email("Format d'email invalide"),
  password: z
    .string()
    .min(8, "Le mot de passe doit contenir au moins 8 caractères")
    .optional()
    .or(z.literal("")),
  is_active: z.boolean(),
});

type CreateUserFormData = z.infer<typeof createUserSchema>;
type UpdateUserFormData = z.infer<typeof updateUserSchema>;

interface UserFormProps {
  /** Utilisateur à éditer (null pour création) */
  user?: User | null;
  /** Callback lors de la soumission pour création */
  onSubmitCreate?: (data: UserCreate) => void;
  /** Callback lors de la soumission pour mise à jour */
  onSubmitUpdate?: (data: UserUpdate) => void;
  /** Callback pour annuler */
  onCancel?: () => void;
  /** État de chargement */
  isLoading?: boolean;
}

/**
 * Formulaire de création/édition d'utilisateur Admin
 * Accessible uniquement aux Super Admins
 */
export function UserForm({
  user,
  onSubmitCreate,
  onSubmitUpdate,
  onCancel,
  isLoading = false,
}: UserFormProps) {
  const isEditing = !!user;

  // Formulaire pour création
  const createForm = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      email: "",
      password: "",
      role: "admin",
    },
  });

  // Formulaire pour édition
  const updateForm = useForm<UpdateUserFormData>({
    resolver: zodResolver(updateUserSchema),
    defaultValues: {
      email: user?.email || "",
      password: "",
      is_active: user?.is_active ?? true,
    },
  });

  const handleCreateSubmit = (data: CreateUserFormData) => {
    onSubmitCreate?.({
      email: data.email,
      password: data.password,
      role: data.role as UserRole,
    });
  };

  const handleUpdateSubmit = (data: UpdateUserFormData) => {
    const updateData: UserUpdate = {
      email: data.email,
      is_active: data.is_active,
    };
    // N'inclure le mot de passe que s'il est fourni
    if (data.password && data.password.length > 0) {
      updateData.password = data.password;
    }
    onSubmitUpdate?.(updateData);
  };

  if (isEditing) {
    return (
      <form onSubmit={updateForm.handleSubmit(handleUpdateSubmit)} className="space-y-6">
        {/* Email */}
        <div className="space-y-2">
          <Label htmlFor="email">Email *</Label>
          <Input
            id="email"
            type="email"
            placeholder="admin@example.com"
            {...updateForm.register("email")}
            disabled={isLoading}
          />
          {updateForm.formState.errors.email && (
            <p className="text-sm text-destructive">
              {updateForm.formState.errors.email.message}
            </p>
          )}
        </div>

        {/* Mot de passe (optionnel en édition) */}
        <div className="space-y-2">
          <Label htmlFor="password">Nouveau mot de passe</Label>
          <Input
            id="password"
            type="password"
            placeholder="Laisser vide pour ne pas modifier"
            {...updateForm.register("password")}
            disabled={isLoading}
          />
          {updateForm.formState.errors.password && (
            <p className="text-sm text-destructive">
              {updateForm.formState.errors.password.message}
            </p>
          )}
          <p className="text-xs text-muted-foreground">
            Minimum 8 caractères. Laissez vide pour conserver le mot de passe actuel.
          </p>
        </div>

        {/* Rôle (lecture seule en édition) */}
        <div className="space-y-2">
          <Label>Rôle</Label>
          <div className="px-3 py-2 border rounded-md bg-muted text-muted-foreground">
            {user?.role === "super_admin" ? "Super Admin" : "Admin"}
          </div>
          <p className="text-xs text-muted-foreground">
            Le rôle ne peut pas être modifié après la création.
          </p>
        </div>

        {/* Statut actif */}
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="is_active"
            {...updateForm.register("is_active")}
            disabled={isLoading}
            className="h-4 w-4 rounded border-gray-300"
          />
          <Label htmlFor="is_active" className="cursor-pointer">
            Compte actif
          </Label>
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
            {isLoading ? "Chargement..." : "Modifier"}
          </Button>
        </div>
      </form>
    );
  }

  return (
    <form onSubmit={createForm.handleSubmit(handleCreateSubmit)} className="space-y-4 sm:space-y-6">
      {/* Email */}
      <div className="space-y-2">
        <Label htmlFor="email">Email *</Label>
        <Input
          id="email"
          type="email"
          placeholder="admin@example.com"
          {...createForm.register("email")}
          disabled={isLoading}
        />
        {createForm.formState.errors.email && (
          <p className="text-sm text-destructive">
            {createForm.formState.errors.email.message}
          </p>
        )}
      </div>

      {/* Mot de passe */}
      <div className="space-y-2">
        <Label htmlFor="password">Mot de passe *</Label>
        <Input
          id="password"
          type="password"
          placeholder="••••••••"
          {...createForm.register("password")}
          disabled={isLoading}
        />
        {createForm.formState.errors.password && (
          <p className="text-sm text-destructive">
            {createForm.formState.errors.password.message}
          </p>
        )}
        <p className="text-xs text-muted-foreground">
          Minimum 8 caractères
        </p>
      </div>

      {/* Rôle */}
      <div className="space-y-2">
        <Label htmlFor="role">Rôle *</Label>
        <Select
          value={createForm.watch("role")}
          onValueChange={(value) => createForm.setValue("role", value as "super_admin" | "admin")}
          disabled={isLoading}
        >
          <SelectTrigger>
            <SelectValue placeholder="Sélectionner un rôle" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="admin">Admin</SelectItem>
            <SelectItem value="super_admin">Super Admin</SelectItem>
          </SelectContent>
        </Select>
        {createForm.formState.errors.role && (
          <p className="text-sm text-destructive">
            {createForm.formState.errors.role.message}
          </p>
        )}
        <p className="text-xs text-muted-foreground">
          Les Super Admins peuvent gérer les autres utilisateurs.
        </p>
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
          {isLoading ? "Chargement..." : "Créer l'utilisateur"}
        </Button>
      </div>
    </form>
  );
}

export default UserForm;
