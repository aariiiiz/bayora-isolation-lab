import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    environment = Column(String(100), default="staging", nullable=False)
    operation = Column(String(100), nullable=False)  # isolation_access, audit_integrity, prompt_injection, config_risk
    profile = Column(String(50), default="strict", nullable=False)
    description = Column(Text, nullable=True)
    
    artifact_filename = Column(String(255), nullable=False)
    artifact_type = Column(String(50), nullable=False)
    artifact_size_bytes = Column(Integer, nullable=False)
    parameters = Column(JSON, default=dict)
    
    status = Column(String(50), default="queued", nullable=False)  # queued, running, completed, failed
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(50), default="CLEAN")  # CLEAN, LOW, MEDIUM, HIGH, CRITICAL
    summary = Column(JSON, default=dict)  # counts of severities, rules executed
    error_message = Column(Text, nullable=True)
    ai_analysis = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    findings = relationship("Finding", back_populates="experiment", cascade="all, delete-orphan", order_by="Finding.severity")
