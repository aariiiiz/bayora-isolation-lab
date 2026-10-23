from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models.audit import AuditEvent
from app.utils.crypto import compute_record_hash, verify_audit_chain

def log_audit_event(
    db: Session,
    event_type: str,
    actor: str = "analyst",
    details: Dict[str, Any] = None,
    experiment_id: Optional[str] = None
) -> AuditEvent:
    """
    Persists an audit event with cryptographic SHA-256 hash chaining to ensure tamper evidence.
    """
    details = details or {}
    ts = datetime.utcnow()
    
    # Get last event in chronological order
    last_event = db.query(AuditEvent).order_by(desc(AuditEvent.timestamp)).first()
    prev_hash = last_event.record_hash if last_event else "GENESIS"

    record_hash = compute_record_hash(
        prev_hash=prev_hash,
        event_type=event_type,
        timestamp_str=ts.isoformat(),
        actor=actor,
        details=details
    )

    audit_entry = AuditEvent(
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
    return audit_entry

from typing import Optional, Dict, Any, List, Tuple

def get_audit_trail(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    event_type: Optional[str] = None,
    experiment_id: Optional[str] = None
) -> Tuple[List[AuditEvent], int]:
    query = db.query(AuditEvent)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    if experiment_id:
        query = query.filter(AuditEvent.experiment_id == experiment_id)

    total = query.count()
    events = query.order_by(desc(AuditEvent.timestamp)).offset(offset).limit(limit).all()
    return events, total

def check_chain_integrity(db: Session) -> Dict[str, Any]:
    # Query in ascending order to follow chain from genesis
    events = db.query(AuditEvent).order_by(AuditEvent.timestamp.asc()).all()
    return verify_audit_chain(events)

