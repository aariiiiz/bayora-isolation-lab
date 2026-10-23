# Bayora Isolation Lab: API Reference

All endpoints are prefixed with `/api`.

## 1. System & Dashboard

### `GET /api/health`
Checks server readiness, version, and optional AI advisor integration status.
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "Bayora Isolation Lab",
  "version": "1.0.0",
  "timestamp": "2026-10-23T05:54:28Z",
  "ai_advisor_enabled": true
}
```

### `GET /api/dashboard/summary`
Calculates real-time statistics dynamically from the database.
- **Response `200 OK`**:
```json
{
  "total_experiments": 3,
  "total_findings": 9,
  "findings_by_severity": { "CRITICAL": 3, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0 },
  "experiments_by_status": { "completed": 3, "running": 0, "failed": 0, "queued": 0 },
  "avg_risk_score": 76.3,
  "recent_experiments": [...],
  "recent_audit_events": [...],
  "active_policies_count": 10
}
```

---

## 2. Experiments

### `POST /api/experiments`
Uploads artifact, validates size/MIME type, executes selected security operation, and saves findings.
- **Request (Multipart Form)**:
  - `file`: Uploaded file (JSON, JSONL, CSV, TXT, YAML)
  - `name`: String (e.g. "Cluster Isolation Audit")
  - `operation`: String (`isolation_access`, `audit_integrity`, `prompt_injection`, `config_risk`)
  - `environment`: String (e.g. `staging`, `production`)
  - `profile`: String (`strict`, `standard`, `permissive`)
  - `enable_ai_advisor`: Boolean (true/false)

### `GET /api/experiments`
Lists historical runs with pagination (`limit`, `offset`) and status filters.

### `GET /api/experiments/{run_id}`
Returns full experiment details and findings list.

### `GET /api/experiments/{run_id}/findings`
Returns findings for a given experiment run.

### `POST /api/experiments/{run_id}/ai-advise`
Triggers Groq LLaMA 3.3 threat modeling synthesis.

---

## 3. Audit Trail & Hash Chaining

### `GET /api/audit-events`
Returns chronological audit events with canonical SHA-256 record hashes.

### `GET /api/audit-events/verify-chain`
Iterates through all audit records from genesis and verifies sequential SHA-256 links.
- **Response `200 OK`**:
```json
{
  "valid": true,
  "break_detected": false,
  "total_verified": 8,
  "latest_hash": "a4b8f...39c0",
  "message": "Cryptographic integrity verified across all 8 events."
}
```

---

## 4. Policies

### `GET /api/policies`
Lists all active and baseline security rules.

### `POST /api/policies`
Creates a user-defined custom rule.

### `PATCH /api/policies/{policy_id}`
Toggles rule `is_enabled` status or updates parameters.

### `DELETE /api/policies/{policy_id}`
Deletes custom rules. Baseline rules are protected from deletion.

---

## 5. Controlled Synthetic Sandbox

### `POST /api/synthetic/run`
Executes the local multi-tenant test suite verifying:
- In-tenant authorized access
- Cross-tenant denial
- Cross-session memory boundary
- Unauthenticated rejection
- Tampered token rejection

### `GET /api/synthetic/fixtures`
Returns bundled safe and vulnerable sample artifacts.
