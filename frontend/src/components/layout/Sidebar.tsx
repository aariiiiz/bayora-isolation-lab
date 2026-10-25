import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FlaskConical,
  ShieldAlert,
  FileText,
  Sliders,
  Settings,
  Menu,
  X,
  Cpu,
  User,
  Building,
  ChevronDown,
  Check,
  ShieldCheck
} from "lucide-react";
import { cn } from "../../lib/utils";
import { useAuth } from "../../context/AuthContext";
import { useQueryClient } from "@tanstack/react-query";

interface SidebarProps {
  apiStatus?: "online" | "offline";
}

export const Sidebar: React.FC<SidebarProps> = ({ apiStatus = "online" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);
  const { user, activeTenant, switchDemoUser } = useAuth();
  const queryClient = useQueryClient();

  const handleRoleSwitch = async (role: "admin" | "analyst" | "viewer" | "beta_lead") => {
    setProfileDropdownOpen(false);
    await switchDemoUser(role);
    queryClient.invalidateQueries();
  };

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all duration-150 relative",
      isActive
        ? "bg-[#E0EEFD] text-bayora-primary font-bold shadow-xs border-l-3 border-bayora-primary"
        : "text-slate-600 hover:text-slate-900 hover:bg-slate-200/50"
    );

  const sidebarContent = (
    <div className="flex flex-col h-full bg-bayora-sidebar border-r border-bayora-sidebarBorder w-64 select-none">
      {/* Branding Header with Tasteful Cyan-to-Blue Logo Accent */}
      <div className="p-5 pb-4 border-b border-bayora-sidebarBorder">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center shadow-md relative overflow-hidden shrink-0">
            <div className="absolute inset-0 bg-gradient-to-tr from-bayora-cyan to-bayora-primary opacity-90"></div>
            <span className="font-heading font-extrabold text-white text-xl relative z-10 tracking-wider">
              B
            </span>
          </div>
          <div>
            <div className="font-heading font-bold text-base tracking-wider text-slate-900 leading-none">
              BAYORA
            </div>
            <div className="text-[10px] font-semibold tracking-widest text-slate-500 uppercase mt-1">
              ISOLATION LAB
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 overflow-y-auto px-3.5 py-4 space-y-5">
        {/* Main Workspace Navigation */}
        <div>
          <div className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-heading">
            Platform
          </div>
          <nav className="space-y-1">
            <NavLink to="/" end className={navLinkClass} onClick={() => setIsOpen(false)}>
              <LayoutDashboard className="w-4 h-4 text-slate-500 shrink-0" />
              <span>Overview</span>
            </NavLink>
            <NavLink to="/experiments" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <FlaskConical className="w-4 h-4 text-slate-500 shrink-0" />
              <span>Experiments</span>
            </NavLink>
            <NavLink to="/policies" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <Sliders className="w-4 h-4 text-slate-500 shrink-0" />
              <span>Isolation Policies</span>
            </NavLink>
            <NavLink to="/audit" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <ShieldAlert className="w-4 h-4 text-slate-500 shrink-0" />
              <span>Audit Trail</span>
            </NavLink>
            <NavLink to="/reports" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <FileText className="w-4 h-4 text-slate-500 shrink-0" />
              <span>Reports</span>
            </NavLink>
          </nav>
        </div>

        {/* Tools & Settings Section */}
        <div>
          <div className="px-3 mb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-heading">
            Environment
          </div>
          <nav className="space-y-1">
            <NavLink to="/sandbox" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <Cpu className="w-4 h-4 text-slate-500 shrink-0" />
              <span>Synthetic Sandbox</span>
            </NavLink>
            <NavLink to="/settings" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <Settings className="w-4 h-4 text-slate-500 shrink-0" />
              <span>Settings</span>
            </NavLink>
          </nav>
        </div>
      </div>

      {/* User / Profile Area Near Bottom */}
      <div className="p-3 border-t border-bayora-sidebarBorder bg-white/60">
        <div className="relative">
          <button
            onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
            className="w-full flex items-center justify-between p-2 rounded-lg hover:bg-slate-100 transition-all text-left"
            aria-label="User identity and role settings"
          >
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs">
                {user?.full_name?.charAt(0) || "U"}
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-800 truncate">
                  {user?.full_name || "Alice Analyst"}
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="text-[10px] font-mono uppercase px-1 py-0.2 rounded bg-blue-50 text-blue-700 border border-blue-200 font-bold">
                    {activeTenant?.role || "analyst"}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono truncate max-w-[80px]">
                    {activeTenant?.id || "tenant-alpha"}
                  </span>
                </div>
              </div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0 ml-1" />
          </button>

          {/* Quick Demo Switcher Popover */}
          {profileDropdownOpen && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setProfileDropdownOpen(false)}
              />
              <div className="absolute bottom-full left-0 mb-2 w-64 rounded-xl bg-white shadow-xl border border-slate-200 p-2 z-50 text-xs">
                <div className="px-3 py-2 border-b border-slate-100 mb-1">
                  <div className="font-bold text-slate-800">Switch Identity & Tenant</div>
                  <div className="text-[10px] text-slate-500">Test RBAC and boundary enforcement</div>
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

        {/* Engine Status Pill */}
        <div className="mt-2.5 pt-2 border-t border-slate-200/80 flex items-center justify-between text-[11px] text-slate-500 px-1">
          <div className="flex items-center gap-1.5">
            <span
              className={cn(
                "w-2 h-2 rounded-full",
                apiStatus === "online" ? "bg-emerald-500 animate-pulse" : "bg-rose-500"
              )}
            />
            <span className="font-medium text-slate-600">Engine {apiStatus}</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            HACK IN HILLS ’26
          </span>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Drawer Toggle Button */}
      <div className="lg:hidden fixed top-3 left-4 z-50">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 rounded-lg bg-white shadow-md border border-slate-200 text-slate-700 hover:bg-slate-50"
          aria-label="Toggle navigation menu"
        >
          {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Desktop Persistent Sidebar */}
      <aside className="hidden lg:block shrink-0 sticky top-0 h-screen z-30">
        {sidebarContent}
      </aside>

      {/* Mobile Collapsible Navigation Drawer */}
      <aside
        className={cn(
          "lg:hidden fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 ease-in-out shadow-2xl",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {sidebarContent}
      </aside>
    </>
  );
};
