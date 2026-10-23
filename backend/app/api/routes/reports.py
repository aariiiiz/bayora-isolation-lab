from typing import Dict, Any
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.report_service import get_report_data

router = APIRouter(tags=["Reports"])

@router.get("/experiments/{run_id}/report", response_model=Dict[str, Any])
def export_experiment_report(run_id: str, db: Session = Depends(get_db)):
    """
    Generates a structured, evidence-backed JSON security evaluation report.
    Logs the export event in the tamper-evident audit trail.
    """
    report_dict = get_report_data(db=db, experiment_id=run_id, actor="analyst")
    return report_dict
