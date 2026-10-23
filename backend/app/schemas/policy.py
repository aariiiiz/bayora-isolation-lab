from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class PolicyBase(BaseModel):
    rule_id: str = Field(..., min_length=3, max_length=100)
    name: str = Field(..., min_length=2, max_length=255)
    category: str = Field(..., description="isolation, audit, prompt, config")
    severity: str = Field(default="HIGH", description="CRITICAL, HIGH, MEDIUM, LOW, INFO")
    is_enabled: bool = True
    description: str
    explanation: str
    remediation: str
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_baseline: bool = False

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    is_enabled: Optional[bool] = None
    description: Optional[str] = None
    explanation: Optional[str] = None
    remediation: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class PolicyResponse(PolicyBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
