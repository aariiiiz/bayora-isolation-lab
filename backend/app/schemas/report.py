from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.schemas.experiment import ExperimentResponse
from app.schemas.finding import FindingResponse

class DashboardSummaryResponse(BaseModel):
    total_experiments: int
    total_findings: int
    findings_by_severity: Dict[str, int]
    experiments_by_status: Dict[str, int]
    avg_risk_score: float
    recent_experiments: List[ExperimentResponse]
    recent_audit_events: List[Dict[str, Any]]
    active_policies_count: int

class ReportResponse(BaseModel):
    generated_at: datetime
    platform: str = "Bayora Isolation Lab"
    version: str
    experiment: ExperimentResponse
    findings: List[FindingResponse]
    risk_summary: Dict[str, Any]
    limitations_and_residual_risks: List[str]
    compliance_notes: str
    audit_chain_status: Optional[str] = None
