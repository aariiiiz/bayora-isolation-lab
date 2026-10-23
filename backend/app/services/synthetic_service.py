from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.audit import AuditEvent
from app.utils.crypto import compute_record_hash

class LocalSyntheticSandbox:
    """
    In-memory isolated test fixture simulating a multi-tenant AI testing harness.
    Validates tenant and session boundaries locally without external network probes.
    """
    def __init__(self):
        self.tenants = {
            "tenant-alpha": {
                "name": "Alpha Corp AI Safety Team",
                "secret_key": "key-alpha-998811",
                "resources": {
                    "res-eval-01": {"title": "Alpha Adversarial Prompt Suite", "content": "RESTRICTED_ALPHA_DATA"},
                    "res-eval-02": {"title": "Model Checkpoint A1", "content": "ALPHA_WEIGHTS_CONFIDENTIAL"}
                },
                "sessions": {
                    "sess-alpha-01": {"user": "alice@alpha.io", "scratchpad": "Alice private analysis notes"}
                }
            },
            "tenant-beta": {
                "name": "Beta Defense AI Labs",
                "secret_key": "key-beta-443322",
                "resources": {
                    "res-eval-99": {"title": "Beta Red-Team Exploits", "content": "RESTRICTED_BETA_EXPLOITS"}
                },
                "sessions": {
                    "sess-beta-01": {"user": "bob@beta.io", "scratchpad": "Bob private red-team scratchpad"}
                }
            }
        }

    def access_resource(self, caller_tenant_id: str, caller_token: str, target_tenant_id: str, resource_id: str) -> Dict[str, Any]:
        # Check authentication
        if not caller_tenant_id or not caller_token:
            return {
                "status_code": 401,
                "allowed": False,
                "error": "MISSING_IDENTITY_CONTEXT",
                "message": "Request denied: caller identity and authentication token were not supplied."
            }

        caller_data = self.tenants.get(caller_tenant_id)
        if not caller_data or caller_data.get("secret_key") != caller_token:
            return {
                "status_code": 401,
                "allowed": False,
                "error": "INVALID_CREDENTIALS",
                "message": "Request denied: token does not match authorized tenant key."
            }

        # Check tenant isolation boundary
        if caller_tenant_id != target_tenant_id:
            return {
                "status_code": 403,
                "allowed": False,
                "error": "CROSS_TENANT_ACCESS_DENIED",
                "message": f"Security violation: Tenant '{caller_tenant_id}' attempted unauthorized access to Tenant '{target_tenant_id}' resource '{resource_id}'. Partition isolation enforced."
            }

        target_data = self.tenants.get(target_tenant_id, {})
        resource = target_data.get("resources", {}).get(resource_id)
        if not resource:
            return {
                "status_code": 404,
                "allowed": False,
                "error": "RESOURCE_NOT_FOUND",
                "message": f"Resource '{resource_id}' does not exist in tenant domain."
            }

        return {
            "status_code": 200,
            "allowed": True,
            "message": "Authorized access granted.",
            "data": resource
        }

    def access_session_scratchpad(self, caller_tenant_id: str, caller_session_id: str, target_session_id: str) -> Dict[str, Any]:
        caller_data = self.tenants.get(caller_tenant_id)
        if not caller_data:
            return {"status_code": 401, "allowed": False, "error": "UNKNOWN_TENANT"}

        if caller_session_id != target_session_id:
            return {
                "status_code": 403,
                "allowed": False,
                "error": "CROSS_SESSION_ISOLATION_ENFORCED",
                "message": f"Session isolation violation: Session '{caller_session_id}' cannot read private scratchpad of Session '{target_session_id}'."
            }

        session_data = caller_data.get("sessions", {}).get(target_session_id)
        return {
            "status_code": 200,
            "allowed": True,
            "message": "Authorized session memory access.",
            "data": session_data
        }


def run_synthetic_isolation_suite(db: Session, actor: str = "analyst") -> Dict[str, Any]:
    """
    Executes 5 deterministic local test scenarios demonstrating isolation enforcement.
    Produces cryptographically chained audit events for each test outcome.
    """
    sandbox = LocalSyntheticSandbox()
    test_results = []
    audit_events_created = []

    # Get latest hash in audit chain
    last_audit = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).first()
    prev_hash = last_audit.record_hash if last_audit else "GENESIS"

    scenarios = [
        {
            "id": "SYNTH-01",
            "name": "Authorized In-Tenant Access",
            "caller_tenant": "tenant-alpha",
            "token": "key-alpha-998811",
            "target_tenant": "tenant-alpha",
            "resource": "res-eval-01",
            "expected_status": 200,
            "expected_allowed": True
        },
        {
            "id": "SYNTH-02",
            "name": "Unauthorized Cross-Tenant Resource Access",
            "caller_tenant": "tenant-alpha",
            "token": "key-alpha-998811",
            "target_tenant": "tenant-beta",
            "resource": "res-eval-99",
            "expected_status": 403,
            "expected_allowed": False
        },
        {
            "id": "SYNTH-03",
            "name": "Cross-Session Memory / State Access Leakage",
            "caller_tenant": "tenant-alpha",
            "caller_session": "sess-alpha-02",
            "target_session": "sess-alpha-01",
            "is_session_test": True,
            "expected_status": 403,
            "expected_allowed": False
        },
        {
            "id": "SYNTH-04",
            "name": "Missing Identity Context & Token",
            "caller_tenant": "",
            "token": "",
            "target_tenant": "tenant-alpha",
            "resource": "res-eval-01",
            "expected_status": 401,
            "expected_allowed": False
        },
        {
            "id": "SYNTH-05",
            "name": "Forged Credentials / Tampered Tenant Header",
            "caller_tenant": "tenant-alpha",
            "token": "FORGED_BEARER_TOKEN_EVIL",
            "target_tenant": "tenant-alpha",
            "resource": "res-eval-01",
            "expected_status": 401,
            "expected_allowed": False
        }
    ]

    for sc in scenarios:
        if sc.get("is_session_test"):
            res = sandbox.access_session_scratchpad(
                caller_tenant_id=sc["caller_tenant"],
                caller_session_id=sc["caller_session"],
                target_session_id=sc["target_session"]
            )
        else:
            res = sandbox.access_resource(
                caller_tenant_id=sc["caller_tenant"],
                caller_token=sc["token"],
                target_tenant_id=sc["target_tenant"],
                resource_id=sc["resource"]
            )

        passed = (res["status_code"] == sc["expected_status"] and res["allowed"] == sc["expected_allowed"])

        outcome = {
            "scenario_id": sc["id"],
            "name": sc["name"],
            "status_code": res["status_code"],
            "allowed": res["allowed"],
            "passed": passed,
            "message": res["message"],
            "evidence": {
                "caller": sc.get("caller_tenant") or "ANONYMOUS",
                "target": sc.get("target_tenant") or sc.get("target_session"),
                "returned_error": res.get("error")
            }
        }
        test_results.append(outcome)

        # Record cryptographically chained audit event
        ts = datetime.utcnow()
        details = {
            "scenario_id": sc["id"],
            "name": sc["name"],
            "passed": passed,
            "status_code": res["status_code"]
        }
        rec_hash = compute_record_hash(
            prev_hash=prev_hash,
            event_type="SYNTHETIC_TEST_EXECUTION",
            timestamp_str=ts.isoformat(),
            actor=actor,
            details=details
        )
        audit = AuditEvent(
            event_type="SYNTHETIC_TEST_EXECUTION",
            actor=actor,
            timestamp=ts,
            details=details,
            prev_hash=prev_hash,
            record_hash=rec_hash
        )
        db.add(audit)
        prev_hash = rec_hash
        audit_events_created.append(audit.id)

    db.commit()

    all_passed = all(t["passed"] for t in test_results)

    return {
        "executed_at": datetime.utcnow().isoformat() + "Z",
        "fixture": "Local Synthetic Multi-Tenant Adapter v1.0",
        "total_scenarios": len(scenarios),
        "passed_scenarios": sum(1 for t in test_results if t["passed"]),
        "all_enforced": all_passed,
        "scenarios": test_results,
        "audit_events_recorded": len(audit_events_created),
        "disclaimer": "This synthetic adapter verifies boundary enforcement against the local authorized fixture. It provides empirical evidence of isolation logic for the tested implementation."
    }
