from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class AuditEventResponse(BaseModel):
    id: str
    event_type: str
    experiment_id: Optional[str] = None
    actor: str
    timestamp: datetime
    details: Dict[str, Any]
    prev_hash: str
    record_hash: str

    class Config:
        from_attributes = True

class AuditChainVerifyResponse(BaseModel):
    valid: bool
    break_detected: bool
    total_verified: int
    latest_hash: Optional[str] = None
    broken_index: Optional[int] = None
    event_id: Optional[str] = None
    reason: Optional[str] = None
    message: str
