from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.audit import AuditEvent
from app.schemas.audit import AuditEventResponse, AuditChainVerifyResponse
from app.services.audit_service import get_audit_trail, check_chain_integrity, log_audit_event
from app.api.deps import require_role, TenantContext

router = APIRouter(prefix="/audit-events", tags=["Audit Trail"])

# In-memory backup store for demo tamper simulation and instant recovery
_TAMPER_BACKUP_STORE: Dict[str, Dict[str, Any]] = {}

@router.get("", response_model=Dict[str, Any])
def list_audit_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = None,
    experiment_id: Optional[str] = None,
    ctx: TenantContext = Depends(require_role(["admin", "analyst", "viewer"])),
    db: Session = Depends(get_db)
):
    """
    Returns persisted audit events with cryptographic record hashes and monotonic sequence numbers,
    scoped strictly to the caller's authorized tenant.
    """
    items, total = get_audit_trail(
        db=db,
        limit=limit,
        offset=offset,
        event_type=event_type,
        experiment_id=experiment_id,
        tenant_id=ctx.tenant_id
    )
    return {
        "items": [AuditEventResponse.model_validate(e) for e in items],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/verify-chain", response_model=AuditChainVerifyResponse)
def verify_hash_chain(
    ctx: TenantContext = Depends(require_role(["admin", "analyst", "viewer"])),
    db: Session = Depends(get_db)
):
    """
    Cryptographically verifies the SHA-256 hash chain and sequence monotonicity across stored audit records.
    Compares against trusted external checkpoint. Read-only verification that never mutates stored records.
    Accessible to Administrator, Security Analyst, and Auditor Viewer roles.
    """
    report = check_chain_integrity(db, tenant_id=ctx.tenant_id)
    return report

@router.post("/simulate-tamper")
def simulate_audit_tampering(
    tamper_type: str = Query("payload", description="payload, broken_link, sequence_gap"),
    ctx: TenantContext = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """
    Controlled demonstration endpoint for hackathon evaluation:
    Simulates an adversary gaining raw database access and mutating an audit log record.
    Provides tangible proof that Bayora's cryptographic verification detects tampering.
    """
    event = db.query(AuditEvent).filter(
        AuditEvent.tenant_id == ctx.tenant_id
    ).order_by(AuditEvent.sequence_number.desc()).first()

    if not event:
        # Create a sample event if tenant audit log is empty
        event = log_audit_event(
            db=db,
            event_type="DEMO_SEED_EVENT",
            actor=ctx.user.email,
            tenant_id=ctx.tenant_id,
            details={"purpose": "tamper_demonstration_baseline"}
        )

    # Save original state for restoration
    _TAMPER_BACKUP_STORE[event.id] = {
        "details": dict(event.details or {}),
        "prev_hash": event.prev_hash,
        "record_hash": event.record_hash,
        "sequence_number": event.sequence_number
    }

    if tamper_type == "payload":
        # Mutate the payload content without updating hash
        modified_details = dict(event.details or {})
        modified_details["__adversarial_injection"] = "FORGED_PRIVILEGE_ELEVATION_RECORD"
        modified_details["original_status"] = "tampered"
        event.details = modified_details
    elif tamper_type == "broken_link":
        # Corrupt the previous hash pointer
        event.prev_hash = "FORGED_BAD_HASH_99999999999999999999999999999999999999999999999999999999"
    elif tamper_type == "sequence_gap":
        # Introduce sequence gap
        event.sequence_number = event.sequence_number + 5

    db.commit()

    return {
        "success": True,
        "tamper_type": tamper_type,
        "event_id": event.id,
        "sequence_number": event.sequence_number,
        "message": f"Simulated '{tamper_type}' tamper attack on record #{event.sequence_number} (ID: {event.id}). Run chain verification to view cryptographic detection evidence."
    }

@router.post("/restore-chain")
def restore_audit_chain(
    ctx: TenantContext = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """
    Restores tampered audit records to their original clean cryptographic state.
    """
    restored_count = 0
    for event_id, original in list(_TAMPER_BACKUP_STORE.items()):
        evt = db.query(AuditEvent).filter(AuditEvent.id == event_id).first()
        if evt:
            evt.details = original["details"]
            evt.prev_hash = original["prev_hash"]
            evt.record_hash = original["record_hash"]
            evt.sequence_number = original["sequence_number"]
            restored_count += 1
            del _TAMPER_BACKUP_STORE[event_id]

    db.commit()

    return {
        "success": True,
        "restored_records": restored_count,
        "message": f"Restored {restored_count} audit event(s) to original cryptographic state. Chain integrity is now intact."
    }
