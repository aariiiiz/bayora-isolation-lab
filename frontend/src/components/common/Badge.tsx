import React from "react";
import { cn } from "../../lib/utils";
import { Severity, RiskLevel } from "../../types";

interface BadgeProps {
  variant?: Severity | RiskLevel | "default" | "outline" | "success" | "neutral";
  children: React.ReactNode;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export const Badge: React.FC<BadgeProps> = ({
  variant = "default",
  children,
  className,
  size = "md",
}) => {
  const sizeClasses = {
    sm: "px-2 py-0.5 text-[10px]",
    md: "px-2.5 py-1 text-xs",
    lg: "px-3 py-1.5 text-sm",
  };

  const getVariantStyles = () => {
    switch (variant) {
      case "CRITICAL":
        return "bg-rose-50 text-rose-700 border-rose-200 font-semibold";
      case "HIGH":
        return "bg-orange-50 text-orange-700 border-orange-200 font-semibold";
      case "MEDIUM":
        return "bg-amber-50 text-amber-700 border-amber-200 font-semibold";
      case "LOW":
        return "bg-blue-50 text-blue-700 border-blue-200 font-medium";
      case "INFO":
        return "bg-slate-50 text-slate-700 border-slate-200 font-medium";
      case "CLEAN":
      case "success":
        return "bg-emerald-50 text-emerald-700 border-emerald-200 font-semibold";
      case "neutral":
        return "bg-slate-100 text-slate-600 border-slate-200";
      default:
        return "bg-slate-100 text-slate-800 border-slate-200";
    }
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border transition-colors",
        sizeClasses[size],
        getVariantStyles(),
        className
      )}
    >
      {children}
    </span>
  );
};
