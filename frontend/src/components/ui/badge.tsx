import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md px-2.5 py-1 text-xs font-medium transition-colors",
  {
    variants: {
      variant: {
        default: "bg-[#F3F4F6] text-[#374151]",
        secondary: "bg-[#F3F4F6] text-[#6B7280]",
        destructive: "bg-[#FEE2E2] text-[#DC2626]",
        outline: "border border-[#E5E7EB] text-[#374151]",
        success: "bg-[#D1FAE5] text-[#059669]",
        warning: "bg-[#FEF3C7] text-[#D97706]",
        pending: "bg-[#FEF3C7] text-[#D97706]",
        error: "bg-[#FEE2E2] text-[#DC2626]",
        active: "bg-[#D1FAE5] text-[#059669]",
        inactive: "bg-[#FEE2E2] text-[#DC2626]",
        sent: "bg-[#DBEAFE] text-[#1D4ED8]",
        delivered: "bg-[#D1FAE5] text-[#059669]",
        read: "bg-[#D1FAE5] text-[#047857]",
        failed: "bg-[#FEE2E2] text-[#DC2626]",
        draft: "bg-[#F3F4F6] text-[#6B7280]",
        sending: "bg-[#FEF3C7] text-[#D97706]",
        completed: "bg-[#D1FAE5] text-[#059669]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
