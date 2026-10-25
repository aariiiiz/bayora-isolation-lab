export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";

export type RiskLevel = "CLEAN" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | "PENDING";

export interface Finding {
  id: string;
  experiment_id: string;
  rule_id: string;
  title: string;
  severity: Severity;
  description: string;
  evidence: Record<string, any>;
  remediation: string;
  detection_method: string;
  confidence: string;
  limitations?: string;
  created_at: string;
}

export interface Experiment {
  id: string;
  name: string;
  environment: string;
  operation: "isolation_access" | "audit_integrity" | "prompt_injection" | "config_risk";
  profile: "strict" | "standard" | "permissive";
  description?: string;
  artifact_filename: string;
  artifact_type: string;
  artifact_size_bytes: number;
  parameters: Record<string, any>;
  status: "queued" | "running" | "completed" | "failed";
  risk_score: number;
  risk_level: RiskLevel;
  summary: {
    critical?: number;
    high?: number;
    medium?: number;
    low?: number;
    info?: number;
    total_findings?: number;
    operation_name?: string;
    raw_lines_analyzed?: number;
  };
  error_message?: string;
  ai_analysis?: string;
  tenant_id?: string;
  parent_experiment_id?: string;
  created_at: string;
  updated_at: string;
  findings?: Finding[];
}

export interface Policy {
  id: string;
  rule_id: string;
  name: string;
  category: "isolation" | "audit" | "prompt" | "config";
  severity: Severity;
  is_enabled: boolean;
  description: string;
  explanation: string;
  remediation: string;
  parameters: Record<string, any>;
  is_baseline: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  id: string;
  sequence_number?: number;
  tenant_id?: string;
  user_id?: string;
  event_type: string;
  experiment_id?: string;
  actor: string;
  timestamp: string;
  details: Record<string, any>;
  prev_hash: string;
  record_hash: string;
}

export interface AuditVerificationReport {
  valid: boolean;
  break_detected: boolean;
  total_verified: number;
  latest_hash?: string;
  latest_sequence?: number;
  broken_index?: number;
  event_id?: string;
  failure_category?: string;
  reason?: string;
  verification_timestamp?: string;
  checkpoint_status?: {
    verified: boolean;
    message?: string;
    expected_seq?: number;
    db_seq?: number;
  };
  message: string;
}

export interface DashboardSummary {
  total_experiments: number;
  total_findings: number;
  findings_by_severity: Record<Severity, number>;
  experiments_by_status: Record<string, number>;
  avg_risk_score: number;
  recent_experiments: Experiment[];
  recent_audit_events: Array<{
    id: string;
    event_type: string;
    experiment_id?: string;
    actor: string;
    timestamp: string;
    record_hash: string;
  }>;
  active_policies_count: number;
}

export interface TenantMembership {
  tenant_id: string;
  tenant_name: string;
  role: "admin" | "analyst" | "viewer";
}

export interface ActiveTenant {
  id: string;
  name: string;
  role: "admin" | "analyst" | "viewer";
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  memberships: TenantMembership[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
  active_tenant: ActiveTenant;
}

export type TestExecutionStatus = "PASS" | "FAIL" | "ERROR" | "SKIPPED";

export interface SyntheticScenarioResult {
  test_id: string;
  name: string;
  expected_outcome: string;
  actual_outcome: string;
  status: TestExecutionStatus;
  status_code: number;
  message: string;
  tenant_label: string;
  target_label: string;
  evidence: Record<string, any>;
  execution_timestamp: string;
  audit_event_id?: string;
}

export interface SyntheticMatrixReport {
  executed_at: string;
  fixture_version: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  error_tests: number;
  all_enforced: boolean;
  results: SyntheticScenarioResult[];
  scenarios?: SyntheticScenarioResult[];
  audit_events_recorded: number;
  security_boundary_notice: string;
}
