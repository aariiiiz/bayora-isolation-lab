import sys
import os
import uuid
from datetime import datetime, timedelta

# Ensure backend path is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.session import engine, Base, SessionLocal
from app.db.models.experiment import Experiment
from app.db.models.finding import Finding
from app.db.models.audit import AuditEvent
from app.services.policy_service import seed_baseline_policies
from app.utils.crypto import compute_record_hash

def seed_demo():
    print("Initializing Bayora Isolation Lab schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    print("Seeding baseline security policies...")
    seeded_policies = seed_baseline_policies(db)
    print(f"Baseline policies seeded/verified: {seeded_policies}")

    # Check if demo experiments already exist
    existing_demos = db.query(Experiment).filter(Experiment.name.like("DEMO: %")).count()
    if existing_demos > 0:
        print(f"Demo data already present ({existing_demos} runs). Skipping demo experiment generation.")
        db.close()
        return

    print("Generating documented synthetic demonstration runs...")
    
    # Track hash chain
    last_audit = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).first()
    prev_hash = last_audit.record_hash if last_audit else "GENESIS"

    demos = [
        {
            "name": "DEMO: Adversarial LLM Cluster Isolation Audit",
            "environment": "production-eu",
            "operation": "isolation_access",
            "profile": "strict",
            "description": "Baseline demonstration run evaluating multi-tenant isolation boundaries on evaluation cluster.",
            "artifact_filename": "cluster_isolation_spec.json",
            "artifact_type": "json",
            "artifact_size_bytes": 2840,
            "status": "completed",
            "risk_score": 88.0,
            "risk_level": "CRITICAL",
            "summary": {
                "critical": 2,
                "high": 1,
                "medium": 1,
                "low": 0,
                "info": 0,
                "total_findings": 4,
                "operation": "isolation_access",
                "operation_name": "Isolation & Access-Control Review"
            },
            "findings": [
                {
                    "rule_id": "ISO-001",
                    "title": "Missing or Wildcard Tenant Isolation Boundary",
                    "severity": "CRITICAL",
                    "description": "Tenant boundary field 'isolation_profile.tenant_id' is set to '*', allowing cross-tenant data leakage or bypassing tenant partitioning.",
                    "evidence": {"field_path": "isolation_profile.tenant_id", "value": "*", "line_number": 4, "excerpt": '\"tenant_id\": \"*\"'},
                    "remediation": "Enforce strict tenant scoping by assigning explicit, validated tenant UUIDs or identifiers.",
                    "detection_method": "structural_schema_inspection",
                    "confidence": "HIGH"
                },
                {
                    "rule_id": "ISO-003",
                    "title": "Insecure Session Isolation / Cross-Tenant State Reuse",
                    "severity": "CRITICAL",
                    "description": "Session isolation parameter 'isolation_profile.shared_session' is configured to true, which allows state or context leakage across sessions.",
                    "evidence": {"field_path": "isolation_profile.shared_session", "value": "True", "line_number": 7, "excerpt": '\"shared_session\": true'},
                    "remediation": "Enable session isolation and disable cross-tenant memory or cache sharing.",
                    "detection_method": "static_schema_inspection",
                    "confidence": "HIGH"
                },
                {
                    "rule_id": "ISO-002",
                    "title": "Overly Broad Wildcard Permission Granted",
                    "severity": "HIGH",
                    "description": "Field 'isolation_profile.permissions' contains wildcard permission 'admin:*', violating least privilege.",
                    "evidence": {"field_path": "isolation_profile.permissions", "matched_permission": "admin:*", "line_number": 5, "excerpt": '\"permissions\": [\"admin:*\"]'},
                    "remediation": "Replace wildcard permissions with explicit, granular role-based access control (RBAC) scopes.",
                    "detection_method": "static_permission_ast",
                    "confidence": "HIGH"
                },
                {
                    "rule_id": "ISO-004",
                    "title": "Shared Artifact Storage Path Lacks Tenant Scoping",
                    "severity": "MEDIUM",
                    "description": "Artifact storage path 'isolation_profile.storage_path' = '/tmp' does not include a dynamic tenant or session variable.",
                    "evidence": {"field_path": "isolation_profile.storage_path", "value": "/tmp", "line_number": 8, "excerpt": '\"storage_path\": \"/tmp\"'},
                    "remediation": "Configure path templates incorporating {tenant_id}/{session_id}.",
                    "detection_method": "path_pattern_analysis",
                    "confidence": "HIGH"
                }
            ]
        },
        {
            "name": "DEMO: Audit Stream Non-Repudiation Check",
            "environment": "staging",
            "operation": "audit_integrity",
            "profile": "strict",
            "description": "Demonstration run screening forensic audit logs for broken hash chains and malformed event identifiers.",
            "artifact_filename": "audit_tamper_evidence.json",
            "artifact_type": "json",
            "artifact_size_bytes": 1420,
            "status": "completed",
            "risk_score": 53.0,
            "risk_level": "HIGH",
            "summary": {
                "critical": 1,
                "high": 1,
                "medium": 0,
                "low": 0,
                "info": 0,
                "total_findings": 2,
                "operation": "audit_integrity",
                "operation_name": "Audit Log Integrity Review"
            },
            "findings": [
                {
                    "rule_id": "AUD-004",
                    "title": "Broken Cryptographic Hash Chain Link Detected",
                    "severity": "CRITICAL",
                    "description": "Tamper evidence: Record at entry 2 references prev_hash 'TAMPERED_FORGED_PREV_HASH_1234', but expected '6b86b273ff34fce1...'. The log history was broken or modified.",
                    "evidence": {"entry": 2, "expected_prev_hash": "6b86b273ff34fce1...", "actual_prev_hash": "TAMPERED_FORGED_PREV_HASH_1234"},
                    "remediation": "Investigate potential audit record truncation, deletion, or tampering.",
                    "detection_method": "cryptographic_chain_verification",
                    "confidence": "HIGH"
                },
                {
                    "rule_id": "AUD-003",
                    "title": "Duplicate Audit Event Identifier Detected",
                    "severity": "HIGH",
                    "description": "Event ID 'evt-100' at entry 3 was previously observed at entry 1. Indicates log replay or collision.",
                    "evidence": {"duplicate_event_id": "evt-100", "first_seen_entry": 1, "duplicate_entry": 3},
                    "remediation": "Use universally unique identifiers (UUIDv4) for all audit records.",
                    "detection_method": "collision_analysis",
                    "confidence": "HIGH"
                }
            ]
        }
    ]

    for d in demos:
        exp_id = str(uuid.uuid4())
        ts = datetime.utcnow() - timedelta(hours=2)
        exp = Experiment(
            id=exp_id,
            name=d["name"],
            environment=d["environment"],
            operation=d["operation"],
            profile=d["profile"],
            description=d["description"],
            artifact_filename=d["artifact_filename"],
            artifact_type=d["artifact_type"],
            artifact_size_bytes=d["artifact_size_bytes"],
            parameters={},
            status=d["status"],
            risk_score=d["risk_score"],
            risk_level=d["risk_level"],
            summary=d["summary"],
            created_at=ts,
            updated_at=ts + timedelta(minutes=1)
        )
        db.add(exp)

        for f_data in d["findings"]:
            f = Finding(
                id=str(uuid.uuid4()),
                experiment_id=exp_id,
                rule_id=f_data["rule_id"],
                title=f_data["title"],
                severity=f_data["severity"],
                description=f_data["description"],
                evidence=f_data["evidence"],
                remediation=f_data["remediation"],
                detection_method=f_data["detection_method"],
                confidence=f_data["confidence"],
                created_at=ts + timedelta(minutes=1)
            )
            db.add(f)

        # Audit event for demo creation
        details = {"demo_run_id": exp_id, "name": d["name"]}
        rec_hash = compute_record_hash(prev_hash, "DEMO_EXPERIMENT_SEEDED", ts.isoformat(), "system", details)
        audit = AuditEvent(
            event_type="DEMO_EXPERIMENT_SEEDED",
            experiment_id=exp_id,
            actor="system",
            timestamp=ts,
            details=details,
            prev_hash=prev_hash,
            record_hash=rec_hash
        )
        db.add(audit)
        prev_hash = rec_hash

    db.commit()
    db.close()
    print("Synthetic demo data successfully generated and cryptographically chained.")

if __name__ == "__main__":
    seed_demo()
