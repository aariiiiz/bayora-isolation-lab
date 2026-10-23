from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.finding import FindingResponse

class ExperimentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    environment: str = Field(default="staging", max_length=100)
    operation: str = Field(..., description="One of: isolation_access, audit_integrity, prompt_injection, config_risk")
    profile: str = Field(default="strict", description="One of: strict, standard, permissive")
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    enable_ai_advisor: Optional[bool] = Field(default=False, description="Enable Groq-powered AI threat modeling and remediation summary")

class ExperimentSummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    total: int = 0
    rules_evaluated: int = 0

class ExperimentResponse(BaseModel):
    id: str
    name: str
    environment: str
    operation: str
    profile: str
    description: Optional[str] = None
    artifact_filename: str
    artifact_type: str
    artifact_size_bytes: int
    parameters: Dict[str, Any]
    status: str
    risk_score: float
    risk_level: str
    summary: Dict[str, Any]
    error_message: Optional[str] = None
    ai_analysis: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExperimentDetailResponse(ExperimentResponse):
    findings: List[FindingResponse] = []
