from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.report_service import get_dashboard_summary
from app.api.deps import require_role, TenantContext

router = APIRouter()

@router.get("/dashboard/summary", tags=["Dashboard"])
def get_dashboard_metrics(
    ctx: TenantContext = Depends(require_role(["admin", "analyst", "viewer"])),
    db: Session = Depends(get_db)
):
    """
    Returns live metrics aggregated dynamically from the database, strictly scoped
    to the authenticated caller's tenant domain.
    """
    return get_dashboard_summary(db=db, tenant_id=ctx.tenant_id)
