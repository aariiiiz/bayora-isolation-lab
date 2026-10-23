import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON
from app.db.session import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)
    experiment_id = Column(String(36), nullable=True, index=True)
    actor = Column(String(100), default="analyst", nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    details = Column(JSON, default=dict)
    
    # Cryptographic tamper-evident hash chain fields
    prev_hash = Column(String(64), nullable=False, default="GENESIS")
    record_hash = Column(String(64), nullable=False)
