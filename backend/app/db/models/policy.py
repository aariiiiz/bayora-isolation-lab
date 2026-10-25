import uuid
from sqlalchemy import Column, String, Boolean, Text, DateTime, JSON
from app.db.session import Base, utcnow

class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)  # isolation, audit, prompt, config
    severity = Column(String(50), default="HIGH", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    is_enabled = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    remediation = Column(Text, nullable=False)
    parameters = Column(JSON, default=dict)
    is_baseline = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

