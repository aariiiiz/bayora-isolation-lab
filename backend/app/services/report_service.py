from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models.experiment import Experiment
from app.db.models.finding import Finding
from app.db.models.policy import Policy
from app.db.models.audit import AuditEvent
from app.engine.report_generator import generate_experiment_report
from app.services.experiment_service import get_experiment_by_id, get_experiment_findings
from app.services.audit_service import log_audit_event, check_chain_integrity
from app.core.errors import ResourceNotFoundError

def get_dashboard_summary(db: Session, tenant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Computes all statistics directly from the database, strictly scoped to the tenant domain.
    Never returns hardcoded or fabricated security metrics.
    """
    exp_query = db.query(Experiment)
    if tenant_id:
        exp_query = exp_query.filter(Experiment.tenant_id == tenant_id)

    total_experiments = exp_query.count()

    finding_query = db.query(Finding).join(Experiment, Finding.experiment_id == Experiment.id)
    if tenant_id:
        finding_query = finding_query.filter(Experiment.tenant_id == tenant_id)
    total_findings = finding_query.count()

    # Findings by severity
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    sev_rows_query = db.query(Finding.severity, func.count(Finding.id)).join(Experiment, Finding.experiment_id == Experiment.id)
    if tenant_id:
        sev_rows_query = sev_rows_query.filter(Experiment.tenant_id == tenant_id)
    severity_rows = sev_rows_query.group_by(Finding.severity).all()

    for sev, count in severity_rows:
        sev_upper = str(sev).upper()
        if sev_upper in severity_counts:
            severity_counts[sev_upper] = count

    # Status counts
    status_counts = {"completed": 0, "running": 0, "failed": 0, "queued": 0}
    st_rows_query = db.query(Experiment.status, func.count(Experiment.id))
    if tenant_id:
        st_rows_query = st_rows_query.filter(Experiment.tenant_id == tenant_id)
    status_rows = st_rows_query.group_by(Experiment.status).all()

    for st, count in status_rows:
        if st in status_counts:
            status_counts[st] = count

    # Avg risk score
    avg_score_query = db.query(func.avg(Experiment.risk_score)).filter(Experiment.status == "completed")
    if tenant_id:
        avg_score_query = avg_score_query.filter(Experiment.tenant_id == tenant_id)
    avg_score = avg_score_query.scalar() or 0.0

    # Recent experiments
    recent_exp_query = db.query(Experiment)
    if tenant_id:
        recent_exp_query = recent_exp_query.filter(Experiment.tenant_id == tenant_id)
    recent_exp = recent_exp_query.order_by(Experiment.created_at.desc()).limit(5).all()

    # Recent audit events
    recent_audit_query = db.query(AuditEvent)
    if tenant_id:
        recent_audit_query = recent_audit_query.filter((AuditEvent.tenant_id == tenant_id) | (AuditEvent.tenant_id.is_(None)))
    recent_audit = recent_audit_query.order_by(AuditEvent.timestamp.desc()).limit(6).all()

    recent_audit_dicts = [
        {
            "id": a.id,
            "event_type": a.event_type,
            "experiment_id": a.experiment_id,
            "actor": a.actor,
            "timestamp": a.timestamp.isoformat() if hasattr(a.timestamp, "isoformat") else str(a.timestamp),
            "record_hash": a.record_hash[:16] + "..." if a.record_hash else ""
        }
        for a in recent_audit
    ]

    active_policies_count = db.query(Policy).filter(Policy.is_enabled == True).count()

    return {
        "total_experiments": total_experiments,
        "total_findings": total_findings,
        "findings_by_severity": severity_counts,
        "experiments_by_status": status_counts,
        "avg_risk_score": round(float(avg_score), 1),
        "recent_experiments": recent_exp,
        "recent_audit_events": recent_audit_dicts,
        "active_policies_count": active_policies_count
    }

def get_report_data(
    db: Session,
    experiment_id: str,
    actor: str = "analyst",
    tenant_id: Optional[str] = None
) -> Dict[str, Any]:
    experiment = get_experiment_by_id(db, experiment_id, tenant_id=tenant_id)
    findings = get_experiment_findings(db, experiment_id, tenant_id=tenant_id)

    # Check audit chain validity
    chain_check = check_chain_integrity(db, tenant_id=tenant_id)
    chain_status = "CRYPTOGRAPHICALLY_VERIFIED" if chain_check.get("valid") else "TAMPER_BREAK_DETECTED"

    exp_dict = {
        "id": experiment.id,
        "name": experiment.name,
        "environment": experiment.environment,
        "operation": experiment.operation,
        "profile": experiment.profile,
        "description": experiment.description,
        "artifact_filename": experiment.artifact_filename,
        "artifact_type": experiment.artifact_type,
        "status": experiment.status,
        "risk_score": experiment.risk_score,
        "risk_level": experiment.risk_level,
        "summary": experiment.summary or {},
        "ai_analysis": experiment.ai_analysis,
        "tenant_id": experiment.tenant_id,
        "parent_experiment_id": getattr(experiment, "parent_experiment_id", None),
        "created_at": experiment.created_at,
        "updated_at": experiment.updated_at
    }

    findings_list = [
        {
            "id": f.id,
            "rule_id": f.rule_id,
            "title": f.title,
            "severity": f.severity,
            "description": f.description,
            "evidence": f.evidence,
            "remediation": f.remediation,
            "detection_method": f.detection_method,
            "confidence": f.confidence,
            "limitations": f.limitations,
            "created_at": f.created_at.isoformat()
        }
        for f in findings
    ]

    report = generate_experiment_report(
        experiment_data=exp_dict,
        findings_data=findings_list,
        audit_chain_status=chain_status
    )

    log_audit_event(
        db=db,
        event_type="REPORT_EXPORTED",
        actor=actor,
        experiment_id=experiment_id,
        tenant_id=tenant_id or experiment.tenant_id,
        details={"report_id": report["report_id"], "findings_included": len(findings_list)}
    )

    return report
