from typing import List, Dict, Any
from app.engine.artifact_parser import ParsedArtifact

def check_isolation_and_access(parsed: ParsedArtifact, profile: str = "strict", active_policies: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Operation A: Isolation and access-control review.
    Analyzes supplied configuration for risky access rules, missing tenant boundaries,
    overly broad permissions, insecure defaults, and session isolation concerns.
    """
    findings = []
    active_policies = active_policies or {}

    def is_rule_enabled(rule_id: str) -> bool:
        if rule_id in active_policies:
            return active_policies[rule_id].get("is_enabled", True)
        return True

    data = parsed.structured_data
    raw_lines = parsed.raw_lines

    # 1. ISO-001: Missing Tenant Isolation Boundary / Wildcard Tenant
    if is_rule_enabled("ISO-001"):
        # Check structured dict or list
        def inspect_tenant_boundary(obj, path=""):
            if isinstance(obj, dict):
                # Check for tenant_id wildcards or absence
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if k.lower() in ("tenant_id", "tenant", "tenant_scope", "organization_id"):
                        if v in ("*", "all", "global", "default", None, ""):
                            # Search line
                            line_no = None
                            for idx, line in enumerate(raw_lines, 1):
                                if k in line and str(v) in line:
                                    line_no = idx
                                    break
                            findings.append({
                                "rule_id": "ISO-001",
                                "title": "Missing or Wildcard Tenant Isolation Boundary",
                                "severity": "CRITICAL",
                                "description": f"Tenant boundary field '{current_path}' is set to '{v}', allowing cross-tenant data leakage or bypassing tenant partitioning.",
                                "evidence": {
                                    "field_path": current_path,
                                    "value": str(v),
                                    "line_number": line_no,
                                    "excerpt": raw_lines[line_no - 1] if line_no and line_no <= len(raw_lines) else f"\"{k}\": \"{v}\""
                                },
                                "remediation": "Enforce strict tenant scoping by assigning explicit, validated tenant UUIDs or identifiers. Disallow wildcard or null tenant boundaries.",
                                "detection_method": "structural_schema_inspection",
                                "confidence": "HIGH",
                                "limitations": "Inspects declared tenant attributes. Runtime enforcement depends on application middleware enforcing this constraint."
                            })
                    else:
                        inspect_tenant_boundary(v, current_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    inspect_tenant_boundary(item, f"{path}[{idx}]")

        inspect_tenant_boundary(data)

    # 2. ISO-002: Overly Permissive Wildcard Access Grants
    if is_rule_enabled("ISO-002"):
        def inspect_permissions(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if k.lower() in ("permissions", "roles", "privileges", "actions", "allowed_ops", "scopes"):
                        items = [v] if isinstance(v, (str, bool)) else (v if isinstance(v, list) else [])
                        for item in items:
                            if str(item).strip() in ("*", "all", "admin:*", "FullAccess", "superuser", "root"):
                                line_no = None
                                for idx, line in enumerate(raw_lines, 1):
                                    if str(item) in line:
                                        line_no = idx
                                        break
                                findings.append({
                                    "rule_id": "ISO-002",
                                    "title": "Overly Broad Wildcard Permission Granted",
                                    "severity": "HIGH",
                                    "description": f"Field '{current_path}' contains wildcard or unbounded permission '{item}', violating the principle of least privilege.",
                                    "evidence": {
                                        "field_path": current_path,
                                        "matched_permission": str(item),
                                        "line_number": line_no,
                                        "excerpt": raw_lines[line_no - 1] if line_no and line_no <= len(raw_lines) else f"\"{k}\": {item}"
                                    },
                                    "remediation": "Replace wildcard permissions with explicit, granular role-based access control (RBAC) scopes.",
                                    "detection_method": "static_permission_ast",
                                    "confidence": "HIGH",
                                    "limitations": "Verifies static declarative permissions. Cannot detect dynamic permission resolution at runtime."
                                })
                    else:
                        inspect_permissions(v, current_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    inspect_permissions(item, f"{path}[{idx}]")

        inspect_permissions(data)

    # 3. ISO-003: Insecure Session Isolation / Shared State Across Tenants
    if is_rule_enabled("ISO-003"):
        def inspect_session_isolation(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    flag_name = k.lower()
                    # Check flags that disable isolation or enable cross-session reuse
                    if (flag_name in ("isolate_sessions", "session_isolation", "tenant_isolation") and v is False) or \
                       (flag_name in ("shared_session", "session_reuse", "cross_tenant_memory", "persist_state_across_tenants") and v is True):
                        line_no = None
                        for idx, line in enumerate(raw_lines, 1):
                            if k in line:
                                line_no = idx
                                break
                        findings.append({
                            "rule_id": "ISO-003",
                            "title": "Insecure Session Isolation / Cross-Tenant State Reuse",
                            "severity": "CRITICAL",
                            "description": f"Session isolation parameter '{current_path}' is configured to insecure value '{v}', which allows state or context leakage across sessions.",
                            "evidence": {
                                "field_path": current_path,
                                "value": str(v),
                                "line_number": line_no,
                                "excerpt": raw_lines[line_no - 1] if line_no and line_no <= len(raw_lines) else f"\"{k}\": {v}"
                            },
                            "remediation": "Enable session isolation and disable cross-tenant memory or cache sharing across test executions.",
                            "detection_method": "static_schema_inspection",
                            "confidence": "HIGH",
                            "limitations": "Detects configuration flags. Runtime session containerization should be verified in test harness."
                        })
                    else:
                        inspect_session_isolation(v, current_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    inspect_session_isolation(item, f"{path}[{idx}]")

        inspect_session_isolation(data)

    # 4. ISO-004: Missing Namespace or Storage Path Isolation
    if is_rule_enabled("ISO-004"):
        def inspect_storage_paths(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if k.lower() in ("storage_path", "artifacts_dir", "scratchpad_dir", "output_dir", "temp_dir") and isinstance(v, str):
                        # Flag global shared paths like /tmp, /var/tmp, or paths without {tenant_id} or {session_id}
                        if v in ("/tmp", "/var/tmp", "C:\\temp", "C:\\tmp", "./shared", "/shared") or ("{" not in v and "tenant" not in v.lower()):
                            line_no = None
                            for idx, line in enumerate(raw_lines, 1):
                                if k in line and v in line:
                                    line_no = idx
                                    break
                            findings.append({
                                "rule_id": "ISO-004",
                                "title": "Shared Artifact Storage Path Lacks Tenant Scoping",
                                "severity": "MEDIUM",
                                "description": f"Artifact storage path '{current_path}' = '{v}' does not include a dynamic tenant or session variable, risking artifact cross-contamination.",
                                "evidence": {
                                    "field_path": current_path,
                                    "value": v,
                                    "line_number": line_no,
                                    "excerpt": raw_lines[line_no - 1] if line_no and line_no <= len(raw_lines) else f"\"{k}\": \"{v}\""
                                },
                                "remediation": "Configure path templates incorporating {tenant_id}/{session_id} to ensure storage partition isolation.",
                                "detection_method": "path_pattern_analysis",
                                "confidence": "HIGH",
                                "limitations": "Applies when artifacts are stored on local filesystem or object stores."
                            })
                    else:
                        inspect_storage_paths(v, current_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    inspect_storage_paths(item, f"{path}[{idx}]")

        inspect_storage_paths(data)

    # 5. ISO-005: Unrestricted Impersonation or Authentication Bypass
    if is_rule_enabled("ISO-005"):
        def inspect_impersonation(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if (k.lower() in ("allow_impersonation", "bypass_auth", "disable_auth", "anonymous_access") and v is True) or \
                       (k.lower() in ("enforce_auth", "require_token") and v is False):
                        line_no = None
                        for idx, line in enumerate(raw_lines, 1):
                            if k in line:
                                line_no = idx
                                break
                        findings.append({
                            "rule_id": "ISO-005",
                            "title": "Authentication Bypass or Unrestricted Impersonation Enabled",
                            "severity": "CRITICAL",
                            "description": f"Security configuration '{current_path}' permits unauthenticated access or impersonation without authorization credentials.",
                            "evidence": {
                                "field_path": current_path,
                                "value": str(v),
                                "line_number": line_no,
                                "excerpt": raw_lines[line_no - 1] if line_no and line_no <= len(raw_lines) else f"\"{k}\": {v}"
                            },
                            "remediation": "Disable authentication bypass flags. Implement strict cryptographic identity checks and mTLS/OAuth2 tokens for test harnesses.",
                            "detection_method": "static_flag_detection",
                            "confidence": "HIGH",
                            "limitations": "Static flag detection. Does not evaluate external IAM provider policies."
                        })
                    else:
                        inspect_impersonation(v, current_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    inspect_impersonation(item, f"{path}[{idx}]")

        inspect_impersonation(data)

    return findings
