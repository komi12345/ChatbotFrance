"use client";

import { cn } from "@/lib/utils";

interface ProgressBarProps {
  /** Valeur actuelle (0-100) */
  value: number;
  /** Valeur maximale */
  max?: number;
  /** Afficher le pourcentage */
  showPercentage?: boolean;
  /** Afficher le texte de progression (ex: "50/100") */
  showProgress?: boolean;
  /** Texte personnalisé */
  label?: string;
  /** Taille de la barre */
  size?: "sm" | "md" | "lg";
  /** Variante de couleur */
  variant?: "default" | "success" | "warning" | "error";
  /** Classes CSS additionnelles */
  className?: string;
  /** État animé (pour les opérations en cours) */
  animated?: boolean;
}

const sizeClasses = {
  sm: "h-1",
  md: "h-2",
  lg: "h-4",
};

const variantClasses = {
  default: "bg-primary",
  success: "bg-green-500",
  warning: "bg-yellow-500",
  error: "bg-destructive",
};

/**
 * Composant ProgressBar - Barre de progression pour les opérations longues
 * Utilisé pour les envois massifs de messages et les imports
 */
export function ProgressBar({
  value,
  max = 100,
  showPercentage = false,
  showProgress = false,
  label,
  size = "md",
  variant = "default",
  className,
  animated = false,
}: ProgressBarProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={cn("w-full", className)}>
      {/* Label et pourcentage */}
      {(label || showPercentage || showProgress) && (
        <div className="flex items-center justify-between mb-2">
          {label && (
            <span className="text-sm font-medium text-foreground">{label}</span>
          )}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {showProgress && (
              <span>
                {value} / {max}
              </span>
            )}
            {showPercentage && <span>{percentage.toFixed(0)}%</span>}
          </div>
        </div>
      )}

      {/* Barre de progression */}
      <div
        className={cn(
          "w-full overflow-hidden rounded-full bg-secondary",
          sizeClasses[size]
        )}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        <div
          className={cn(
            "h-full rounded-full transition-all duration-300 ease-out",
            variantClasses[variant],
            animated && "animate-pulse"
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

/**
 * Composant pour afficher la progression d'un envoi massif
 */
export function SendingProgress({
  sent,
  total,
  success,
  failed,
  className,
}: {
  sent: number;
  total: number;
  success: number;
  failed: number;
  className?: string;
}) {
  const isComplete = sent >= total;

  return (
    <div className={cn("space-y-4 p-4 rounded-lg border bg-card", className)}>
      <div className="flex items-center justify-between">
        <h4 className="font-semibold">Envoi en cours...</h4>
        <span className="text-sm text-muted-foreground">
          {sent} / {total} messages
        </span>
      </div>

      <ProgressBar
        value={sent}
        max={total}
        size="lg"
        variant={isComplete ? "success" : "default"}
        animated={!isComplete}
      />

      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-2xl font-bold text-foreground">{sent}</p>
          <p className="text-xs text-muted-foreground">Envoyés</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-green-500">{success}</p>
          <p className="text-xs text-muted-foreground">Réussis</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-destructive">{failed}</p>
          <p className="text-xs text-muted-foreground">Échoués</p>
        </div>
      </div>

      {isComplete && (
        <div className="text-center text-sm text-green-600 font-medium">
          ✓ Envoi terminé
        </div>
      )}
    </div>
  );
}

export default ProgressBar;
