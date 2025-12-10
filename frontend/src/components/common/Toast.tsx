"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { CheckCircle, XCircle, AlertTriangle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
  success: (message: string, title?: string) => void;
  error: (message: string, title?: string) => void;
  warning: (message: string, title?: string) => void;
  info: (message: string, title?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

const toastConfig = {
  success: {
    icon: CheckCircle,
    bgColor: "bg-[#D1FAE5]",
    iconColor: "text-[#059669]",
    borderColor: "border-[#10B981]",
    textColor: "text-[#065F46]",
  },
  error: {
    icon: XCircle,
    bgColor: "bg-[#FEE2E2]",
    iconColor: "text-[#DC2626]",
    borderColor: "border-[#EF4444]",
    textColor: "text-[#991B1B]",
  },
  warning: {
    icon: AlertTriangle,
    bgColor: "bg-[#FEF3C7]",
    iconColor: "text-[#D97706]",
    borderColor: "border-[#F59E0B]",
    textColor: "text-[#92400E]",
  },
  info: {
    icon: Info,
    bgColor: "bg-[#DBEAFE]",
    iconColor: "text-[#1D4ED8]",
    borderColor: "border-[#3B82F6]",
    textColor: "text-[#1E40AF]",
  },
};

function ToastItem({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const config = toastConfig[toast.type];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-xl border p-4 shadow-lg",
        config.bgColor,
        config.borderColor,
        "animate-in slide-in-from-right-full duration-300"
      )}
      role="alert"
    >
      <Icon className={cn("h-5 w-5 flex-shrink-0 mt-0.5", config.iconColor)} />
      
      <div className="flex-1 min-w-0">
        {toast.title && (
          <h4 className={cn("font-semibold text-sm", config.textColor)}>{toast.title}</h4>
        )}
        <p className={cn("text-sm", config.textColor, "opacity-90")}>{toast.message}</p>
      </div>

      <button
        onClick={onClose}
        className={cn("rounded-lg p-1 opacity-70 hover:opacity-100 transition-opacity", config.textColor)}
        aria-label="Fermer"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const addToast = useCallback(
    (toast: Omit<Toast, "id">) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast = { ...toast, id };
      
      setToasts((prev) => [...prev, newToast]);

      const duration = toast.duration ?? 5000;
      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const success = useCallback(
    (message: string, title?: string) => {
      addToast({ type: "success", message, title });
    },
    [addToast]
  );

  const error = useCallback(
    (message: string, title?: string) => {
      addToast({ type: "error", message, title });
    },
    [addToast]
  );

  const warning = useCallback(
    (message: string, title?: string) => {
      addToast({ type: "warning", message, title });
    },
    [addToast]
  );

  const info = useCallback(
    (message: string, title?: string) => {
      addToast({ type: "info", message, title });
    },
    [addToast]
  );

  return (
    <ToastContext.Provider
      value={{ toasts, addToast, removeToast, success, error, warning, info }}
    >
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
}

function ToastContainer({
  toasts,
  removeToast,
}: {
  toasts: Toast[];
  removeToast: (id: string) => void;
}) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          toast={toast}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast doit être utilisé dans un ToastProvider");
  }
  return context;
}

export default ToastProvider;
