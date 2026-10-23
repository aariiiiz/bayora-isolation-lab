import { DashboardSummary, Experiment, Finding, Policy, AuditEvent, AuditVerificationReport } from "../types";

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || "/api";

class ApiError extends Error {
  status: number;
  details?: any;
  constructor(message: string, status: number, details?: any) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, options);

  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {
      // Non-json error
    }
    throw new ApiError(
      errorData.message || `Request failed with status ${response.status}`,
      response.status,
      errorData.details
    );
  }

  return response.json();
}

export const api = {
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

  // Synthetic Adapter
  runSyntheticSuite: () => request<any>("/synthetic/run", { method: "POST" }),

  getSyntheticFixtures: () => request<Record<string, { filename: string; operation: string; description: string; content: string }>>("/synthetic/fixtures"),
};
