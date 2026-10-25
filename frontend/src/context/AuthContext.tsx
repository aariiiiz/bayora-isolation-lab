import React, { createContext, useContext, useState, useEffect } from "react";
import { api, authStorage } from "../services/api";
import { UserProfile, ActiveTenant } from "../types";

interface AuthContextType {
  user: UserProfile | null;
  activeTenant: ActiveTenant | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  switchDemoUser: (role: "admin" | "analyst" | "viewer" | "beta_lead") => Promise<void>;
  switchTenant: (tenantId: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [activeTenant, setActiveTenant] = useState<ActiveTenant | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize session: try stored token or auto-login with default analyst account
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = authStorage.getToken();
      if (storedToken) {
        try {
          const profile = await api.getProfile();
          setUser(profile);
          const tenantId = authStorage.getActiveTenant() || profile.memberships[0]?.tenant_id || "tenant-alpha";
          const mem = profile.memberships.find(m => m.tenant_id === tenantId) || profile.memberships[0];
          setActiveTenant({
            id: mem.tenant_id,
            name: mem.tenant_name,
            role: mem.role
          });
          setIsLoading(false);
          return;
        } catch {
          // Token invalid/expired
          authStorage.clearToken();
        }
      }

      // Default auto-login as Alice Safety Analyst for instant hackathon demonstration
      try {
        const res = await api.login("analyst@alpha.io", "Bayora@Analyst2026!");
        setUser(res.user);
        setActiveTenant(res.active_tenant);
      } catch {
        // Backend not online or not seeded yet
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, pass: string) => {
    setIsLoading(true);
    try {
      const res = await api.login(email, pass);
      setUser(res.user);
      setActiveTenant(res.active_tenant);
    } finally {
      setIsLoading(false);
    }
  };

  const switchDemoUser = async (role: "admin" | "analyst" | "viewer" | "beta_lead") => {
    setIsLoading(true);
    try {
      if (role === "admin") {
        await login("admin@alpha.io", "Bayora@Admin2026!");
      } else if (role === "analyst") {
        await login("analyst@alpha.io", "Bayora@Analyst2026!");
      } else if (role === "viewer") {
        await login("viewer@alpha.io", "Bayora@Viewer2026!");
      } else if (role === "beta_lead") {
        await login("admin@beta.io", "Bayora@Admin2026!");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const switchTenant = async (tenantId: string) => {
    setIsLoading(true);
    try {
      const res = await api.switchTenant(tenantId);
      setUser(res.user);
      setActiveTenant(res.active_tenant);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
    setActiveTenant(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        activeTenant,
        isAuthenticated: !!user,
        isLoading,
        login,
        switchDemoUser,
        switchTenant,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
