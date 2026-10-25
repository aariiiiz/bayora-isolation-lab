import React, { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { ChevronRight, Shield, User, Building, ChevronDown, Check } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useQueryClient } from "@tanstack/react-query";

export const Layout: React.FC = () => {
  const location = useLocation();
  const { user, activeTenant, switchDemoUser, isLoading } = useAuth();
  const queryClient = useQueryClient();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  // Generate readable breadcrumbs based on pathname
  const pathParts = location.pathname.split("/").filter(Boolean);
  const breadcrumb = pathParts.length === 0 ? "Overview" : pathParts[0].charAt(0).toUpperCase() + pathParts[0].slice(1);

  const handleRoleSwitch = async (role: "admin" | "analyst" | "viewer" | "beta_lead") => {
    setDropdownOpen(false);
    await switchDemoUser(role);
    // Invalidate queries so dashboard/experiments refresh for the new tenant/role
    queryClient.invalidateQueries();
  };

  return (
    <div className="flex min-h-screen bg-bayora-workspace text-bayora-dark">
      {/* Strict Vertical Left Sidebar Only */}
      <Sidebar />

      {/* Main Workspace Canvas */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Subtle Page Context Bar */}
        <header className="h-14 border-b border-slate-200/80 bg-white/80 backdrop-blur-xs px-6 lg:px-10 flex items-center justify-between shrink-0 z-20">
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

          <div className="flex items-center gap-3 text-xs">
            {/* Active Tenant Scope Pill */}
            <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 font-medium">
              <Building className="w-3.5 h-3.5 text-slate-500" />
              <span>{activeTenant?.name || "Alpha AI Safety Lab"}</span>
              <span className="font-mono text-[10px] text-slate-400">({activeTenant?.id || "tenant-alpha"})</span>
            </div>

            {/* Quick Demo Role Switcher Dropdown */}
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 bg-white shadow-xs hover:bg-slate-50 text-slate-700 font-medium transition-all"
                aria-label="Switch active identity"
              >
                <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-slate-800 truncate max-w-[120px]">
                    {user?.full_name?.split(" ")[0] || "Analyst"}
                  </span>
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 border border-blue-200 font-bold">
                    {activeTenant?.role || "analyst"}
                  </span>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              </button>

              {dropdownOpen && (
                <>
                  <div className="fixed inset-0 z-30" onClick={() => setDropdownOpen(false)} />
                  <div className="absolute right-0 mt-2 w-64 rounded-xl bg-white shadow-xl border border-slate-200 p-2 z-40 text-xs">
                    <div className="px-3 py-2 border-b border-slate-100 mb-1">
                      <div className="font-bold text-slate-800">Switch Identity & Tenant</div>
                      <div className="text-[10px] text-slate-500">Fast test switching for RBAC validation</div>
                    </div>
                    <div className="space-y-1">
                      <button
                        onClick={() => handleRoleSwitch("admin")}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-50 flex items-center justify-between"
                      >
                        <div>
                          <div className="font-semibold text-slate-800">Alpha Security Admin</div>
                          <div className="text-[10px] text-slate-500">Role: admin • tenant-alpha</div>
                        </div>
                        {activeTenant?.role === "admin" && activeTenant?.id === "tenant-alpha" && (
                          <Check className="w-4 h-4 text-emerald-600" />
                        )}
                      </button>

                      <button
                        onClick={() => handleRoleSwitch("analyst")}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-50 flex items-center justify-between"
                      >
                        <div>
                          <div className="font-semibold text-slate-800">Alice Safety Analyst</div>
                          <div className="text-[10px] text-slate-500">Role: analyst • tenant-alpha</div>
                        </div>
                        {activeTenant?.role === "analyst" && activeTenant?.id === "tenant-alpha" && (
                          <Check className="w-4 h-4 text-emerald-600" />
                        )}
                      </button>

                      <button
                        onClick={() => handleRoleSwitch("viewer")}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-slate-50 flex items-center justify-between"
                      >
                        <div>
                          <div className="font-semibold text-slate-800">Auditor Viewer</div>
                          <div className="text-[10px] text-slate-500">Role: viewer • tenant-alpha</div>
                        </div>
                        {activeTenant?.role === "viewer" && activeTenant?.id === "tenant-alpha" && (
                          <Check className="w-4 h-4 text-emerald-600" />
                        )}
                      </button>

                      <div className="border-t border-slate-100 my-1 pt-1"></div>

                      <button
                        onClick={() => handleRoleSwitch("beta_lead")}
                        className="w-full text-left px-3 py-2 rounded-lg hover:bg-rose-50 text-rose-900 flex items-center justify-between"
                      >
                        <div>
                          <div className="font-semibold">Beta Security Lead</div>
                          <div className="text-[10px] text-rose-700">Role: admin • tenant-beta (Cross-Tenant)</div>
                        </div>
                        {activeTenant?.id === "tenant-beta" && (
                          <Check className="w-4 h-4 text-rose-600" />
                        )}
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
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
