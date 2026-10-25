from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from app.db.models.audit import AuditEvent
from app.utils.crypto import (
    compute_record_hash,
    verify_audit_chain,
    save_audit_checkpoint,
    load_audit_checkpoint
)

def log_audit_event(
    db: Session,
    event_type: str,
    actor: str = "analyst",
    details: Dict[str, Any] = None,
    experiment_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None
) -> AuditEvent:
    """
    Persists an audit event with sequential ordering, cryptographic SHA-256 hash chaining,
    tenant scoping, and external trusted checkpoint updates.
    """
    details = details or {}
    ts = datetime.now(timezone.utc)

    # Determine last event for sequential linkage
    query = db.query(AuditEvent)
    if tenant_id:
        # Check if tenant-scoped or global chain
        last_event = query.filter(AuditEvent.tenant_id == tenant_id).order_by(desc(AuditEvent.sequence_number)).first()
        if not last_event:
            # Fallback to last global event if tenant chain is starting
            last_event = query.order_by(desc(AuditEvent.sequence_number)).first()
    else:
        last_event = query.order_by(desc(AuditEvent.sequence_number)).first()

    if not last_event:
        # Also check by timestamp as fallback
        last_event = query.order_by(desc(AuditEvent.timestamp)).first()

    prev_hash = last_event.record_hash if last_event else "GENESIS"
    sequence_number = (last_event.sequence_number + 1) if (last_event and last_event.sequence_number) else 1

    record_hash = compute_record_hash(
        prev_hash=prev_hash,
        event_type=event_type,
        timestamp_str=ts.isoformat(),
        actor=actor,
        details=details,
        sequence_number=sequence_number,
        tenant_id=tenant_id
    )

    audit_entry = AuditEvent(
        sequence_number=sequence_number,
        tenant_id=tenant_id,
        user_id=user_id,
        event_type=event_type,
        experiment_id=experiment_id,
        actor=actor,
        timestamp=ts,
        details=details,
        prev_hash=prev_hash,
        record_hash=record_hash
    )

    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)

    # Update trusted external checkpoint anchor
    save_audit_checkpoint(sequence_number=sequence_number, record_hash=record_hash, tenant_id=tenant_id)

    return audit_entry

def get_audit_trail(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    event_type: Optional[str] = None,
    experiment_id: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> Tuple[List[AuditEvent], int]:
    query = db.query(AuditEvent)
    if tenant_id:
        query = query.filter((AuditEvent.tenant_id == tenant_id) | (AuditEvent.tenant_id.is_(None)))
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if experiment_id:
        query = query.filter(AuditEvent.experiment_id == experiment_id)

    total = query.count()
    events = query.order_by(desc(AuditEvent.sequence_number), desc(AuditEvent.timestamp)).offset(offset).limit(limit).all()
    return events, total

def check_chain_integrity(db: Session, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Read-only cryptographic verification of the audit hash chain.
    Loads events strictly in ascending sequence order and compares against external checkpoint.
    Never mutates or regenerates stored records.
    """
    query = db.query(AuditEvent)
    if tenant_id:
        # Check tenant events or global
        events = query.filter((AuditEvent.tenant_id == tenant_id) | (AuditEvent.tenant_id.is_(None))).order_by(asc(AuditEvent.sequence_number), asc(AuditEvent.timestamp)).all()
    else:
        events = query.order_by(asc(AuditEvent.sequence_number), asc(AuditEvent.timestamp)).all()

    checkpoint = load_audit_checkpoint()
    return verify_audit_chain(events, checkpoint=checkpoint)
