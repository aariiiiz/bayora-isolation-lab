import React, { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FlaskConical,
  ShieldAlert,
  FileText,
  Sliders,
  Menu,
  X,
  Cpu,
  CheckCircle2,
  AlertCircle
} from "lucide-react";
import { cn } from "../../lib/utils";

interface SidebarProps {
  apiStatus?: "online" | "offline";
}

export const Sidebar: React.FC<SidebarProps> = ({ apiStatus = "online" }) => {
  const [isOpen, setIsOpen] = useState(false);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
      isActive
        ? "bg-bayora-sidebarActive text-bayora-primary font-semibold shadow-xs"
        : "text-slate-600 hover:text-bayora-dark hover:bg-slate-100/70"
    );

  const sidebarContent = (
    <div className="flex flex-col h-full bg-bayora-sidebar border-r border-bayora-sidebarBorder w-64 select-none">
      {/* Branding Header */}
      <div className="p-6 pb-4 border-b border-bayora-sidebarBorder">
        <div className="flex items-center gap-3">
          {/* Cyan-to-Blue gradient Bayora B logo */}
          <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center shadow-md relative overflow-hidden">
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
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-6">
        {/* Workspace Section */}
        <div>
          <div className="px-3 mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400 font-heading">
            Workspace
          </div>
          <nav className="space-y-1">
            <NavLink to="/" end className={navLinkClass} onClick={() => setIsOpen(false)}>
              <LayoutDashboard className="w-4 h-4 text-slate-500" />
              <span>Overview</span>
            </NavLink>
            <NavLink to="/experiments" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <FlaskConical className="w-4 h-4 text-slate-500" />
              <span>Experiments</span>
            </NavLink>
            <NavLink to="/audit" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <ShieldAlert className="w-4 h-4 text-slate-500" />
              <span>Audit Trail</span>
            </NavLink>
            <NavLink to="/sandbox" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <Cpu className="w-4 h-4 text-slate-500" />
              <span>Synthetic Sandbox</span>
            </NavLink>
          </nav>
        </div>

        {/* Configuration Section */}
        <div>
          <div className="px-3 mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400 font-heading">
            Configuration
          </div>
          <nav className="space-y-1">
            <NavLink to="/policies" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <Sliders className="w-4 h-4 text-slate-500" />
              <span>Isolation Policies</span>
            </NavLink>
            <NavLink to="/reports" className={navLinkClass} onClick={() => setIsOpen(false)}>
              <FileText className="w-4 h-4 text-slate-500" />
              <span>Reports</span>
            </NavLink>
          </nav>
        </div>
      </div>

      {/* System Status Footer */}
      <div className="p-4 border-t border-bayora-sidebarBorder bg-bayora-sidebar/50">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "w-2 h-2 rounded-full animate-pulse",
                apiStatus === "online" ? "bg-emerald-500" : "bg-rose-500"
              )}
            />
            <span className="font-medium text-slate-600">Engine {apiStatus}</span>
          </div>
          <span className="text-[10px] font-mono bg-white px-2 py-0.5 rounded border border-slate-200">
            v1.0.0
          </span>
        </div>
        <div className="mt-2 text-[10px] text-slate-400 leading-tight">
          HACK IN HILLS ’26 • PS-04
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Drawer Toggle Button */}
      <div className="lg:hidden fixed top-4 left-4 z-50">
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
