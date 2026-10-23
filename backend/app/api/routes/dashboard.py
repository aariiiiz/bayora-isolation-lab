from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.report_service import get_dashboard_summary

router = APIRouter()

@router.get("/dashboard/summary", tags=["Dashboard"])
def get_dashboard_metrics(db: Session = Depends(get_db)):
    """
    Returns live metrics aggregated dynamically from the database.
    Zero values are returned if no experiments exist.
    """
    return get_dashboard_summary(db)
