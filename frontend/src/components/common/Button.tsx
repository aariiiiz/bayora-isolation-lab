import React from "react";
import { cn } from "../../lib/utils";
import { Loader2 } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  className,
  disabled,
  ...props
}) => {
  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs rounded-md",
    md: "px-4 py-2 text-sm rounded-lg",
    lg: "px-5 py-2.5 text-base rounded-lg",
  };

  const variantStyles = {
    primary:
      "bg-bayora-primary text-white hover:bg-bayora-primaryHover shadow-xs focus:ring-2 focus:ring-bayora-primary/20",
    secondary:
      "bg-slate-100 text-slate-800 hover:bg-slate-200/80 focus:ring-2 focus:ring-slate-300",
    outline:
      "bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 focus:ring-2 focus:ring-slate-200",
    danger:
      "bg-rose-600 text-white hover:bg-rose-700 focus:ring-2 focus:ring-rose-200",
    ghost:
      "bg-transparent text-slate-600 hover:bg-slate-100/70 hover:text-slate-900",
  };

  return (
    <button
      disabled={disabled || isLoading}
      className={cn(
        "inline-flex items-center justify-center font-medium transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed select-none",
        sizeStyles[size],
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
      {children}
    </button>
  );
};
