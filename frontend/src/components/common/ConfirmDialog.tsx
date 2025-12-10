"use client";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { cn } from "@/lib/utils";
import { AlertTriangle, Trash2, Info } from "lucide-react";

type DialogVariant = "danger" | "warning" | "info";

interface ConfirmDialogProps {
  /** État d'ouverture du dialog */
  open: boolean;
  /** Callback pour changer l'état d'ouverture */
  onOpenChange: (open: boolean) => void;
  /** Titre du dialog */
  title: string;
  /** Description/message du dialog */
  description: string;
  /** Texte du bouton de confirmation */
  confirmText?: string;
  /** Texte du bouton d'annulation */
  cancelText?: string;
  /** Callback lors de la confirmation */
  onConfirm: () => void;
  /** Callback lors de l'annulation */
  onCancel?: () => void;
  /** Variante du dialog */
  variant?: DialogVariant;
  /** État de chargement */
  isLoading?: boolean;
}

const variantConfig = {
  danger: {
    icon: Trash2,
    iconColor: "text-destructive",
    iconBg: "bg-destructive/10",
    buttonClass: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  },
  warning: {
    icon: AlertTriangle,
    iconColor: "text-yellow-600",
    iconBg: "bg-yellow-500/10",
    buttonClass: "bg-yellow-600 text-white hover:bg-yellow-700",
  },
  info: {
    icon: Info,
    iconColor: "text-blue-600",
    iconBg: "bg-blue-500/10",
    buttonClass: "bg-blue-600 text-white hover:bg-blue-700",
  },
};

/**
 * Composant ConfirmDialog - Dialog de confirmation pour les actions importantes
 * Utilisé pour confirmer les suppressions et autres actions destructives
 */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmText = "Confirmer",
  cancelText = "Annuler",
  onConfirm,
  onCancel,
  variant = "danger",
  isLoading = false,
}: ConfirmDialogProps) {
  const config = variantConfig[variant];
  const Icon = config.icon;

  const handleCancel = () => {
    onCancel?.();
    onOpenChange(false);
  };

  const handleConfirm = () => {
    onConfirm();
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center gap-4">
            <div className={cn("p-3 rounded-full", config.iconBg)}>
              <Icon className={cn("h-6 w-6", config.iconColor)} />
            </div>
            <div>
              <AlertDialogTitle>{title}</AlertDialogTitle>
              <AlertDialogDescription className="mt-2">
                {description}
              </AlertDialogDescription>
            </div>
          </div>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleCancel} disabled={isLoading}>
            {cancelText}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            className={config.buttonClass}
            disabled={isLoading}
          >
            {isLoading ? "Chargement..." : confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default ConfirmDialog;
