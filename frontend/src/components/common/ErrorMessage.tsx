"use client";

import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ title = "Erreur", message, onRetry }: ErrorMessageProps) {
  return (
    <div className="rounded-2xl bg-[#FEE2E2] border border-[#FECACA] p-6">
      <div className="flex items-start gap-4">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#EF4444]/10">
          <AlertCircle className="h-5 w-5 text-[#EF4444]" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-[#DC2626]">{title}</h3>
          <p className="mt-1 text-sm text-[#B91C1C]">{message}</p>
          {onRetry && (
            <Button
              onClick={onRetry}
              variant="outline"
              size="sm"
              className="mt-4 border-[#EF4444] text-[#EF4444] hover:bg-[#EF4444]/10"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Réessayer
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ErrorMessage;
