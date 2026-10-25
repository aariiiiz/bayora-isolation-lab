from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.audit import AuditEventResponse, AuditChainVerifyResponse
from app.services.audit_service import get_audit_trail, check_chain_integrity
from app.api.deps import require_role, TenantContext

router = APIRouter(prefix="/audit-events", tags=["Audit Trail"])

@router.get("", response_model=Dict[str, Any])
def list_audit_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = None,
    experiment_id: Optional[str] = None,
    ctx: TenantContext = Depends(require_role(["admin", "analyst"])),
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
    ctx: TenantContext = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """
    Cryptographically verifies the SHA-256 hash chain and sequence monotonicity across stored audit records.
    Compares against trusted external checkpoint. Read-only verification that never mutates stored records.
    """
    report = check_chain_integrity(db, tenant_id=ctx.tenant_id)
    return report
