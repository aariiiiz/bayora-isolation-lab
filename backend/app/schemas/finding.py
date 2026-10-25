from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class EvidenceDetail(BaseModel):
    excerpt: Optional[str] = None
    line_number: Optional[int] = None
    field_path: Optional[str] = None
    matched_pattern: Optional[str] = None
    sample_context: Optional[str] = None

class FindingBase(BaseModel):
    rule_id: str
    title: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    description: str
    evidence: Dict[str, Any]
    remediation: str
    detection_method: str
    confidence: str = "HIGH"
    limitations: Optional[str] = None

class FindingCreate(FindingBase):
    experiment_id: str

class FindingResponse(FindingBase):
    id: str
    experiment_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
