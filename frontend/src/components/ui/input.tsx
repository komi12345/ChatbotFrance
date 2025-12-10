import * as React from "react";

import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-lg border border-[#E5E7EB] bg-white px-3 py-2 text-sm text-[#111827] placeholder:text-[#9CA3AF]",
          "file:border-0 file:bg-transparent file:text-sm file:font-medium",
          "focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/10",
          "disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-[#F9FAFB]",
          "transition-colors",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
