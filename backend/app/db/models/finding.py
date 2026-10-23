import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base

class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False)  # structured evidence: excerpt, line_number, field, matched_pattern
    remediation = Column(Text, nullable=False)
    detection_method = Column(String(100), nullable=False)  # static_ast, schema_rule, heuristic, cryptographic_hash
    confidence = Column(String(50), default="HIGH", nullable=False)
    limitations = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    experiment = relationship("Experiment", back_populates="findings")
