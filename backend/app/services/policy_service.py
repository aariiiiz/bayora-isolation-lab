from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.policy import Policy
from app.schemas.policy import PolicyCreate, PolicyUpdate
from app.core.errors import BayoraException, ResourceNotFoundError
from app.services.audit_service import log_audit_event

BASELINE_POLICIES = [
    {
        "rule_id": "ISO-001",
        "name": "Mandatory Tenant Isolation Boundaries",
        "category": "isolation",
        "severity": "CRITICAL",
        "is_enabled": True,
        "description": "Verifies that all tenant scopes and context objects are explicitly defined and do not contain wildcards (* or all).",
        "explanation": "Missing or wildcard tenant scoping permits cross-tenant data access and state contamination during testing.",
        "remediation": "Scope all test resources to explicit tenant identifiers.",
        "parameters": {"disallowed_values": ["*", "all", "global", "default", "null"]},
        "is_baseline": True
    },
    {
        "rule_id": "ISO-002",
        "name": "Principle of Least Privilege (No Wildcard Permissions)",
        "category": "isolation",
        "severity": "HIGH",
        "is_enabled": True,
        "description": "Disallows wildcard access permissions (e.g., admin:* or FullAccess) in test executor configurations.",
        "explanation": "Overly broad roles undermine isolation by granting tests arbitrary capabilities outside their domain.",
        "remediation": "Replace wildcards with bounded role scopes.",
        "parameters": {"disallowed_roles": ["*", "admin:*", "FullAccess", "superuser"]},
        "is_baseline": True
    },
    {
        "rule_id": "ISO-003",
        "name": "Enforce Session Isolation and Prevent Shared State",
        "category": "isolation",
        "severity": "CRITICAL",
        "is_enabled": True,
        "description": "Ensures session isolation is enabled and cross-tenant memory or cache reuse is prohibited.",
        "explanation": "Reusing memory contexts across sessions leaks conversational state between adversarial test runs.",
        "remediation": "Enable session isolation and disable cross-tenant caching.",
        "parameters": {},
        "is_baseline": True
    },
    {
        "rule_id": "ISO-004",
        "name": "Storage Path Namespace Scoping",
        "category": "isolation",
        "severity": "MEDIUM",
        "is_enabled": True,
        "description": "Requires artifact storage paths to include explicit tenant or session directories.",
        "explanation": "Shared global paths like /tmp permit race condition collisions and accidental leakage.",
        "remediation": "Use {tenant_id}/{session_id} storage template paths.",
        "parameters": {},
        "is_baseline": True
    },
    {
        "rule_id": "ISO-005",
        "name": "Prohibit Unrestricted Impersonation",
        "category": "isolation",
        "severity": "CRITICAL",
        "is_enabled": True,
        "description": "Flags configuration settings that permit authentication bypass or arbitrary identity impersonation.",
        "explanation": "Bypassing authentication breaks the fundamental trust boundary required for multi-tenant safety validation.",
        "remediation": "Disable bypass flags and require cryptographic authentication tokens.",
        "parameters": {},
        "is_baseline": True
    },
    {
        "rule_id": "AUD-001",
        "name": "Mandatory Audit Record Schema Fields",
        "category": "audit",
        "severity": "HIGH",
        "is_enabled": True,
        "description": "Ensures all audit records include event_id, timestamp, event_type, and actor.",
        "explanation": "Incomplete audit logs cannot be correlated during incident response or regulatory review.",
        "remediation": "Capture complete event taxonomy in every audit call.",
        "parameters": {"required_fields": ["event_id", "timestamp", "event_type", "actor"]},
        "is_baseline": True
    },
    {
        "rule_id": "AUD-004",
        "name": "Cryptographic Audit Hash Chain Validation",
        "category": "audit",
        "severity": "CRITICAL",
        "is_enabled": True,
        "description": "Verifies that sequential audit events form a continuous, tamper-evident SHA-256 hash chain.",
        "explanation": "A broken hash chain indicates log omission, truncation, or unauthorized modification.",
        "remediation": "Investigate log stream interruptions and reconcile against secure immutable storage.",
        "parameters": {},
        "is_baseline": True
    },
    {
        "rule_id": "PRM-001",
        "name": "Adversarial Instruction Override Screening",
        "category": "prompt",
        "severity": "HIGH",
        "is_enabled": True,
        "description": "Detects prompts instructing models to ignore system instructions or activate persona jailbreaks.",
        "explanation": "Heuristic detection of common prompt injection vectors attempting to subvert safety alignment.",
        "remediation": "Apply prompt isolation delimiters and dual-LLM input verification.",
        "parameters": {},
        "is_baseline": True
    },
    {
        "rule_id": "CFG-001",
        "name": "Prohibit Hardcoded Credentials and API Keys",
        "category": "config",
        "severity": "CRITICAL",
        "is_enabled": True,
        "description": "Scans configurations for exposed API keys, bearer tokens, and plaintext passwords.",
        "explanation": "Committed credentials in test configs risk unauthorized access and credential leakage.",
        "remediation": "Extract secrets into environment variables or secrets manager vaults.",
        "parameters": {},
        "is_baseline": True
    },
    {
        "rule_id": "CFG-003",
        "name": "Enforce Encrypted Network Communication and TLS",
        "category": "config",
        "severity": "CRITICAL",
        "is_enabled": True,
        "description": "Flags disabled TLS certificate verification or plaintext HTTP endpoints.",
        "explanation": "Unencrypted traffic allows network adversaries to intercept or tamper with safety evaluation results.",
        "remediation": "Enforce HTTPS and verify TLS certificates.",
        "parameters": {},
        "is_baseline": True
    }
]

def seed_baseline_policies(db: Session) -> int:
    """
    Seeds documented baseline policies if they do not already exist.
    Never overwrites existing user modifications.
    """
    count = 0
    for p_data in BASELINE_POLICIES:
        existing = db.query(Policy).filter(Policy.rule_id == p_data["rule_id"]).first()
        if not existing:
            new_policy = Policy(**p_data)
            db.add(new_policy)
            count += 1
    if count > 0:
        db.commit()
        log_audit_event(
            db=db,
            event_type="POLICIES_SEEDED",
            actor="system",
            details={"seeded_count": count}
        )
    return count

def get_policies(db: Session, category: Optional[str] = None, is_enabled: Optional[bool] = None) -> List[Policy]:
    query = db.query(Policy)
    if category:
        query = query.filter(Policy.category == category)
    if is_enabled is not None:
        query = query.filter(Policy.is_enabled == is_enabled)
    return query.order_by(Policy.rule_id.asc()).all()

def get_policy(db: Session, policy_id: str) -> Policy:
    policy = db.query(Policy).filter((Policy.id == policy_id) | (Policy.rule_id == policy_id)).first()
    if not policy:
        raise ResourceNotFoundError(f"Policy with identifier '{policy_id}' not found.")
    return policy

def create_policy(db: Session, data: PolicyCreate, actor: str = "analyst") -> Policy:
    # Check if rule_id already exists
    existing = db.query(Policy).filter(Policy.rule_id == data.rule_id).first()
    if existing:
        raise BayoraException(f"Policy with rule ID '{data.rule_id}' already exists.", status_code=409)

    policy = Policy(
        rule_id=data.rule_id,
        name=data.name,
        category=data.category,
        severity=data.severity,
        is_enabled=data.is_enabled,
        description=data.description,
        explanation=data.explanation,
        remediation=data.remediation,
        parameters=data.parameters or {},
        is_baseline=False
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    log_audit_event(
        db=db,
        event_type="POLICY_CREATED",
        actor=actor,
        details={"rule_id": policy.rule_id, "name": policy.name, "severity": policy.severity}
    )
    return policy

def update_policy(db: Session, policy_id: str, data: PolicyUpdate, actor: str = "analyst") -> Policy:
    policy = get_policy(db, policy_id)
    update_dict = data.model_dump(exclude_unset=True)

    for field, val in update_dict.items():
        setattr(policy, field, val)

    db.commit()
    db.refresh(policy)

    log_audit_event(
        db=db,
        event_type="POLICY_UPDATED",
        actor=actor,
        details={"rule_id": policy.rule_id, "updated_fields": list(update_dict.keys())}
    )
    return policy

def delete_policy(db: Session, policy_id: str, actor: str = "analyst") -> None:
    policy = get_policy(db, policy_id)
    if policy.is_baseline:
        raise BayoraException(
            f"Baseline rule '{policy.rule_id}' cannot be deleted. You can disable it instead.",
            status_code=400
        )

    rule_id = policy.rule_id
    db.delete(policy)
    db.commit()

    log_audit_event(
        db=db,
        event_type="POLICY_DELETED",
        actor=actor,
        details={"rule_id": rule_id}
    )
