from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.report_service import get_report_data
from app.api.deps import require_role, TenantContext

router = APIRouter(tags=["Reports"])

@router.get("/experiments/{run_id}/report", response_model=Dict[str, Any])
def export_experiment_report(
    run_id: str,
    ctx: TenantContext = Depends(require_role(["admin", "analyst", "viewer"])),
    db: Session = Depends(get_db)
):
    """
    Generates a structured, evidence-backed JSON security evaluation report,
    enforcing that the caller belongs to the tenant that owns the experiment run.
    Logs the export event in the tamper-evident audit trail.
    """
    report_dict = get_report_data(
        db=db,
        experiment_id=run_id,
        actor=ctx.user.email,
        tenant_id=ctx.tenant_id
    )
    return report_dict
