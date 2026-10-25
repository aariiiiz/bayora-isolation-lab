import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import UploadFile

from app.db.models.experiment import Experiment
from app.db.models.finding import Finding
from app.db.models.policy import Policy
from app.schemas.experiment import ExperimentCreate
from app.engine.file_validator import validate_uploaded_file
from app.engine.artifact_parser import parse_artifact
from app.engine.rule_engine import execute_analysis
from app.services.audit_service import log_audit_event
from app.services.ai_advisor_service import generate_ai_threat_advisory
from app.core.config import settings
from app.core.errors import ResourceNotFoundError, BayoraException

async def create_and_run_experiment(
    db: Session,
    file: UploadFile,
    name: str,
    operation: str,
    environment: str = "staging",
    profile: str = "strict",
    description: Optional[str] = None,
    parameters: Dict[str, Any] = None,
    enable_ai_advisor: bool = False,
    actor: str = "analyst",
    tenant_id: str = "tenant-alpha",
    user_id: Optional[str] = None,
    parent_experiment_id: Optional[str] = None
) -> Experiment:
    """
    Complete end-to-end multi-step workflow:
    1. Read and validate uploaded file (strict mime, size, filename sanitize)
    2. Persist experiment scoped to the caller's authorized tenant
    3. Safely parse artifact (never executes code)
    4. Fetch active policies from DB
    5. Execute deterministic security rule engine
    6. Persist findings to database
    7. Optionally call Groq AI advisor for threat modeling summary
    8. Record audit events with SHA-256 hash chaining and tenant scoping
    """
    parameters = parameters or {}
    
    # 1. Read file bytes safely into memory
    content = await file.read()
    file_size = len(content)

    # Validate file
    clean_filename, artifact_type = validate_uploaded_file(
        filename=file.filename or "artifact.txt",
        file_size=file_size,
        mime_type=file.content_type
    )

    # Create Experiment Record
    exp_id = str(uuid.uuid4())
    experiment = Experiment(
        id=exp_id,
        name=name,
        environment=environment,
        operation=operation,
        profile=profile,
        description=description,
        artifact_filename=clean_filename,
        artifact_type=artifact_type,
        artifact_size_bytes=file_size,
        parameters=parameters,
        status="running",
        risk_score=0.0,
        risk_level="PENDING",
        summary={},
        tenant_id=tenant_id,
        user_id=user_id,
        parent_experiment_id=parent_experiment_id
    )
    db.add(experiment)
    db.commit()

    log_audit_event(
        db=db,
        event_type="EXPERIMENT_CREATED",
        actor=actor,
        experiment_id=exp_id,
        tenant_id=tenant_id,
        user_id=user_id,
        details={
            "name": name,
            "operation": operation,
            "environment": environment,
            "filename": clean_filename,
            "size_bytes": file_size,
            "parent_experiment_id": parent_experiment_id
        }
    )

    log_audit_event(
        db=db,
        event_type="FILE_VALIDATED",
        actor=actor,
        experiment_id=exp_id,
        tenant_id=tenant_id,
        user_id=user_id,
        details={"filename": clean_filename, "artifact_type": artifact_type, "status": "PASSED"}
    )

    log_audit_event(
        db=db,
        event_type="ANALYSIS_STARTED",
        actor=actor,
        experiment_id=exp_id,
        tenant_id=tenant_id,
        user_id=user_id,
        details={"operation": operation, "profile": profile}
    )

    try:
        # 3. Safely parse artifact
        parsed = parse_artifact(raw_bytes=content, artifact_type=artifact_type)

        # 4. Fetch active policies from DB for this operation
        policies = db.query(Policy).all()
        active_policies = {p.rule_id: {"is_enabled": p.is_enabled, "parameters": p.parameters} for p in policies}

        # 5. Execute rule engine
        raw_findings, risk_score, risk_level, summary = execute_analysis(
            parsed=parsed,
            operation=operation,
            profile=profile,
            parameters=parameters,
            active_policies=active_policies
        )

        # 6. Save findings
        for f_data in raw_findings:
            finding = Finding(
                id=str(uuid.uuid4()),
                experiment_id=exp_id,
                rule_id=f_data["rule_id"],
                title=f_data["title"],
                severity=f_data["severity"],
                description=f_data["description"],
                evidence=f_data["evidence"],
                remediation=f_data["remediation"],
                detection_method=f_data["detection_method"],
                confidence=f_data.get("confidence", "HIGH"),
                limitations=f_data.get("limitations")
            )
            db.add(finding)

        # 7. AI Threat Advisor (Groq) if enabled
        ai_summary = None
        if enable_ai_advisor or settings.GROQ_API_KEY:
            ai_summary = await generate_ai_threat_advisory(
                experiment_name=name,
                operation=operation,
                risk_level=risk_level,
                risk_score=risk_score,
                findings=raw_findings
            )

        # Update experiment status
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        experiment.status = "completed"
        experiment.risk_score = risk_score
        experiment.risk_level = risk_level
        experiment.summary = summary
        experiment.ai_analysis = ai_summary
        experiment.updated_at = now_utc

        db.commit()
        db.refresh(experiment)

        log_audit_event(
            db=db,
            event_type="ANALYSIS_COMPLETED",
            actor=actor,
            experiment_id=exp_id,
            tenant_id=tenant_id,
            user_id=user_id,
            details={
                "risk_score": risk_score,
                "risk_level": risk_level,
                "total_findings": len(raw_findings),
                "critical": summary.get("critical", 0)
            }
        )

        return experiment

    except Exception as e:
        db.rollback()
        experiment.status = "failed"
        experiment.error_message = str(e)
        experiment.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

        log_audit_event(
            db=db,
            event_type="ANALYSIS_FAILED",
            actor=actor,
            experiment_id=exp_id,
            tenant_id=tenant_id,
            user_id=user_id,
            details={"error": str(e)}
        )
        raise e

def get_experiments(
    db: Session,
    limit: int = 50,
    offset: int = 0,
    operation: Optional[str] = None,
    status: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> Tuple[List[Experiment], int]:
    query = db.query(Experiment)
    if tenant_id:
        query = query.filter(Experiment.tenant_id == tenant_id)
    if operation:
        query = query.filter(Experiment.operation == operation)
    if status:
        query = query.filter(Experiment.status == status)

    total = query.count()
    items = query.order_by(desc(Experiment.created_at)).offset(offset).limit(limit).all()
    return items, total

def get_experiment_by_id(
    db: Session,
    experiment_id: str,
    tenant_id: Optional[str] = None
) -> Experiment:
    query = db.query(Experiment).filter(Experiment.id == experiment_id)
    if tenant_id:
        query = query.filter(Experiment.tenant_id == tenant_id)
    exp = query.first()
    if not exp:
        raise ResourceNotFoundError(f"Experiment '{experiment_id}' was not found.")
    return exp

def get_experiment_findings(
    db: Session,
    experiment_id: str,
    tenant_id: Optional[str] = None
) -> List[Finding]:
    get_experiment_by_id(db, experiment_id, tenant_id=tenant_id)
    return db.query(Finding).filter(Finding.experiment_id == experiment_id).order_by(Finding.severity).all()

def update_experiment_metadata(
    db: Session,
    experiment_id: str,
    tenant_id: str,
    data: Dict[str, Any],
    actor: str,
    user_id: Optional[str] = None
) -> Experiment:
    experiment = get_experiment_by_id(db=db, experiment_id=experiment_id, tenant_id=tenant_id)
    allowed_fields = ["name", "description", "environment", "profile"]
    modified = {}
    for f in allowed_fields:
        if f in data and data[f] is not None:
            setattr(experiment, f, data[f])
            modified[f] = data[f]

    experiment.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(experiment)

    log_audit_event(
        db=db,
        event_type="EXPERIMENT_UPDATED",
        actor=actor,
        experiment_id=experiment.id,
        tenant_id=tenant_id,
        user_id=user_id,
        details={"updated_fields": list(modified.keys()), "experiment_name": experiment.name}
    )
    return experiment

def delete_experiment(
    db: Session,
    experiment_id: str,
    tenant_id: str,
    actor: str,
    user_id: Optional[str] = None
) -> None:
    experiment = get_experiment_by_id(db=db, experiment_id=experiment_id, tenant_id=tenant_id)
    exp_name = experiment.name
    db.delete(experiment)
    db.commit()

    log_audit_event(
        db=db,
        event_type="EXPERIMENT_DELETED",
        actor=actor,
        experiment_id=experiment_id,
        tenant_id=tenant_id,
        user_id=user_id,
        details={"deleted_experiment_name": exp_name}
    )

