import {
  DashboardSummary,
  Experiment,
  Finding,
  Policy,
  AuditEvent,
  AuditVerificationReport,
  AuthResponse,
  UserProfile,
  SyntheticMatrixReport
} from "../types";

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || "/api";

export class ApiError extends Error {
  status: number;
  details?: any;
  constructor(message: string, status: number, details?: any) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

// Token management in localStorage
export const authStorage = {
  getToken: (): string | null => localStorage.getItem("bayora_access_token"),
  setToken: (token: string): void => localStorage.setItem("bayora_access_token", token),
  clearToken: (): void => {
    localStorage.removeItem("bayora_access_token");
    localStorage.removeItem("bayora_active_tenant");
    localStorage.removeItem("bayora_user");
  },
  getActiveTenant: (): string | null => localStorage.getItem("bayora_active_tenant"),
  setActiveTenant: (tenantId: string): void => localStorage.setItem("bayora_active_tenant", tenantId),
  getUser: (): any | null => {
    const raw = localStorage.getItem("bayora_user");
    return raw ? JSON.parse(raw) : null;
  },
  setUser: (user: any): void => localStorage.setItem("bayora_user", JSON.stringify(user))
};

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  // Automatically attach authorization token if present
  const token = authStorage.getToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Automatically attach active tenant header if present
  const activeTenant = authStorage.getActiveTenant();
  if (activeTenant && !headers.has("X-Tenant-ID")) {
    headers.set("X-Tenant-ID", activeTenant);
  }

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {
      // Non-json response
    }

    // Auto clear if token expired
    if (response.status === 401 && endpoint !== "/auth/login") {
      // We don't necessarily clear immediately to allow user to re-authenticate
    }

    throw new ApiError(
      errorData.detail || errorData.message || `Request failed with status ${response.status}`,
      response.status,
      errorData.details
    );
  }

  return response.json();
}

export const api = {
  // Auth
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const res = await request<AuthResponse>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    authStorage.setToken(res.access_token);
    authStorage.setActiveTenant(res.active_tenant.id);
    authStorage.setUser(res.user);
    return res;
  },

  getProfile: (): Promise<UserProfile> => request<UserProfile>("/auth/me"),

  switchTenant: async (tenantId: string): Promise<AuthResponse> => {
    const res = await request<AuthResponse>(`/auth/switch-tenant/${tenantId}`, {
      method: "POST"
    });
    authStorage.setToken(res.access_token);
    authStorage.setActiveTenant(res.active_tenant.id);
    authStorage.setUser(res.user);
    return res;
  },

  logout: async (): Promise<{ success: boolean; message: string }> => {
    try {
      await request<{ success: boolean; message: string }>("/auth/logout", {
        method: "POST"
      });
    } finally {
      authStorage.clearToken();
    }
    return { success: true, message: "Logged out." };
  },

  // Dashboard
  getDashboardSummary: () => request<DashboardSummary>("/dashboard/summary"),

  // Experiments
  getExperiments: (params?: { limit?: number; offset?: number; operation?: string; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    if (params?.operation) query.set("operation", params.operation);
    if (params?.status) query.set("status", params.status);
    return request<{ items: Experiment[]; total: number }>(`/experiments?${query.toString()}`);
  },

  getExperiment: (id: string) => request<Experiment>(`/experiments/${id}`),

  getExperimentFindings: (id: string) => request<Finding[]>(`/experiments/${id}/findings`),

  createExperiment: (formData: FormData) => {
    return request<Experiment>("/experiments", {
      method: "POST",
      body: formData,
    });
  },

  getExperimentReport: (id: string) => request<any>(`/experiments/${id}/report`),

  requestAiAdvisory: (id: string) => request<{ experiment_id: string; ai_analysis: string }>(`/experiments/${id}/ai-advise`, {
    method: "POST"
  }),

  // Audit
  getAuditEvents: (params?: { limit?: number; offset?: number; event_type?: string }) => {
    const query = new URLSearchParams();
    if (params?.limit) query.set("limit", String(params.limit));
    if (params?.offset) query.set("offset", String(params.offset));
    if (params?.event_type) query.set("event_type", params.event_type);
    return request<{ items: AuditEvent[]; total: number }>(`/audit-events?${query.toString()}`);
  },

  verifyAuditChain: () => request<AuditVerificationReport>("/audit-events/verify-chain"),

  // Policies
  getPolicies: (params?: { category?: string; is_enabled?: boolean }) => {
    const query = new URLSearchParams();
    if (params?.category) query.set("category", params.category);
    if (params?.is_enabled !== undefined) query.set("is_enabled", String(params.is_enabled));
    return request<Policy[]>(`/policies?${query.toString()}`);
  },

  updatePolicy: (id: string, data: Partial<Policy>) => {
    return request<Policy>(`/policies/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },

  createPolicy: (data: Omit<Policy, "id" | "created_at" | "updated_at">) => {
    return request<Policy>("/policies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },

  deletePolicy: (id: string) => {
    return request<{ success: boolean; message: string }>(`/policies/${id}`, {
      method: "DELETE",
    });
  },

  // Synthetic Matrix Adapter
  runSyntheticSuite: () => request<SyntheticMatrixReport>("/synthetic/run", { method: "POST" }),

  getSyntheticFixtures: () => request<Record<string, { filename: string; operation: string; description: string; content: string }>>("/synthetic/fixtures"),
};
