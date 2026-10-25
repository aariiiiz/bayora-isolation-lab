import uuid
from sqlalchemy import Column, String, Integer, Text, DateTime, JSON
from app.db.session import Base, utcnow

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence_number = Column(Integer, nullable=False, default=1, index=True)
    tenant_id = Column(String(36), nullable=True, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    experiment_id = Column(String(36), nullable=True, index=True)
    actor = Column(String(100), default="analyst", nullable=False)
    timestamp = Column(DateTime, default=utcnow, nullable=False, index=True)
    details = Column(JSON, default=dict)
    
    # Cryptographic tamper-evident hash chain fields
    prev_hash = Column(String(64), nullable=False, default="GENESIS")
    record_hash = Column(String(64), nullable=False)

