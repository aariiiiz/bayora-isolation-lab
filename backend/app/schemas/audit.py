from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

class AuditEventResponse(BaseModel):
    id: str
    sequence_number: int = 1
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    event_type: str
    experiment_id: Optional[str] = None
    actor: str
    timestamp: datetime
    details: Dict[str, Any]
    prev_hash: str
    record_hash: str

    model_config = ConfigDict(from_attributes=True)

class AuditChainVerifyResponse(BaseModel):
    valid: bool
    break_detected: bool
    total_verified: int
    latest_hash: Optional[str] = None
    latest_sequence: Optional[int] = None
    broken_index: Optional[int] = None
    event_id: Optional[str] = None
    failure_category: Optional[str] = None
    reason: Optional[str] = None
    verification_timestamp: Optional[str] = None
    checkpoint_status: Optional[Dict[str, Any]] = None
    message: str

    model_config = ConfigDict(from_attributes=True)
