import React from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { ChevronRight } from "lucide-react";

export const Layout: React.FC = () => {
  const location = useLocation();

  // Generate readable breadcrumbs based on pathname
  const pathParts = location.pathname.split("/").filter(Boolean);
  const breadcrumb = pathParts.length === 0 ? "Overview" : pathParts[0].charAt(0).toUpperCase() + pathParts[0].slice(1);

  return (
    <div className="flex min-h-screen bg-bayora-workspace text-bayora-dark">
      {/* Strict Vertical Left Sidebar Only */}
      <Sidebar />

      {/* Main Workspace Canvas */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Subtle Page Context Bar (Breadcrumbs & Workspace indicator, NOT a top navigation bar) */}
        <header className="h-14 border-b border-slate-200/80 bg-white/70 backdrop-blur-xs px-6 lg:px-10 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2 text-xs text-slate-500 font-medium pl-10 lg:pl-0">
            <span className="text-slate-400">Bayora</span>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-800 font-semibold">{breadcrumb}</span>
            {pathParts.length > 1 && (
              <>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-bayora-primary font-mono text-[11px] truncate max-w-xs">{pathParts[1]}</span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span className="hidden sm:inline-block px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-600 font-medium">
              Target: Adversarial AI Infra
            </span>
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-10 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
