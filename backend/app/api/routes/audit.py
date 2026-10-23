from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.audit import AuditEventResponse, AuditChainVerifyResponse
from app.services.audit_service import get_audit_trail, check_chain_integrity

router = APIRouter(prefix="/audit-events", tags=["Audit Trail"])

@router.get("", response_model=Dict[str, Any])
def list_audit_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = None,
    experiment_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns persisted audit events with cryptographic record hashes.
    """
    items, total = get_audit_trail(
        db=db,
        limit=limit,
        offset=offset,
        event_type=event_type,
        experiment_id=experiment_id
    )
    return {
        "items": [AuditEventResponse.model_validate(e) for e in items],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/verify-chain", response_model=AuditChainVerifyResponse)
def verify_hash_chain(db: Session = Depends(get_db)):
    """
    Cryptographically verifies the SHA-256 hash chain across all stored audit records.
    Reports any detected break, missing link, or tampered record.
    """
    report = check_chain_integrity(db)
    return report
