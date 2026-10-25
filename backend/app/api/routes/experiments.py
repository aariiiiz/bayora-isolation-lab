import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.experiment import ExperimentResponse, ExperimentDetailResponse
from app.schemas.finding import FindingResponse
from app.services.experiment_service import (
    create_and_run_experiment,
    get_experiments,
    get_experiment_by_id,
    get_experiment_findings
)
from app.services.ai_advisor_service import generate_ai_threat_advisory
from app.api.deps import require_role, TenantContext

router = APIRouter(prefix="/experiments", tags=["Experiments"])

@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
async def create_experiment_run(
    file: UploadFile = File(..., description="Uploaded security artifact (JSON, JSONL, CSV, TXT, YAML)"),
    name: str = Form(..., min_length=2, max_length=255),
    operation: str = Form(..., description="isolation_access, audit_integrity, prompt_injection, config_risk"),
    environment: str = Form("staging"),
    profile: str = Form("strict"),
    description: Optional[str] = Form(None),
    parameters: Optional[str] = Form("{}"),
    enable_ai_advisor: bool = Form(False),
    parent_experiment_id: Optional[str] = Form(None),
    ctx: TenantContext = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """
    Step 1-4: Uploads artifact, validates type and size, executes selected security operation,
    stores findings and audit trail scoped strictly to the authenticated caller's tenant.
    """
    try:
        parsed_params = json.loads(parameters) if parameters else {}
    except Exception:
        parsed_params = {}

    # If retesting, verify parent belongs to this tenant
    if parent_experiment_id:
        get_experiment_by_id(db=db, experiment_id=parent_experiment_id, tenant_id=ctx.tenant_id)

    experiment = await create_and_run_experiment(
        db=db,
        file=file,
        name=name,
        operation=operation,
        environment=environment,
        profile=profile,
        description=description,
        parameters=parsed_params,
        enable_ai_advisor=enable_ai_advisor,
        actor=ctx.user.email,
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        parent_experiment_id=parent_experiment_id
    )
    return experiment

@router.get("", response_model=Dict[str, Any])
def list_experiments(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    operation: Optional[str] = None,
    status: Optional[str] = None,
    ctx: TenantContext = Depends(require_role(["admin", "analyst", "viewer"])),
    db: Session = Depends(get_db)
):
    """
    Lists historical validation runs with pagination and filtering, scoped strictly
    to the authenticated caller's tenant domain.
    """
    items, total = get_experiments(
        db=db,
        limit=limit,
        offset=offset,
        operation=operation,
        status=status,
        tenant_id=ctx.tenant_id
    )
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{run_id}", response_model=ExperimentDetailResponse)
def get_experiment_details(
    run_id: str,
    ctx: TenantContext = Depends(require_role(["admin", "analyst", "viewer"])),
    db: Session = Depends(get_db)
):
    """
    Retrieves full details of a specific experiment run including all findings,
    preventing IDOR by enforcing tenant ownership.
    """
    experiment = get_experiment_by_id(db=db, experiment_id=run_id, tenant_id=ctx.tenant_id)
    findings = get_experiment_findings(db=db, experiment_id=run_id, tenant_id=ctx.tenant_id)
    
    exp_data = ExperimentResponse.model_validate(experiment).model_dump()
    exp_data["findings"] = [FindingResponse.model_validate(f) for f in findings]
    return exp_data

@router.get("/{run_id}/findings", response_model=List[FindingResponse])
def get_findings_for_run(
    run_id: str,
    ctx: TenantContext = Depends(require_role(["admin", "analyst", "viewer"])),
    db: Session = Depends(get_db)
):
    """
    Retrieves findings for a specific experiment run within authorized tenant boundaries.
    """
    return get_experiment_findings(db=db, experiment_id=run_id, tenant_id=ctx.tenant_id)

@router.post("/{run_id}/ai-advise")
async def request_ai_advisory(
    run_id: str,
    ctx: TenantContext = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db)
):
    """
    Triggers on-demand Groq AI threat modeling and mitigation synthesis for an existing run.
    """
    experiment = get_experiment_by_id(db=db, experiment_id=run_id, tenant_id=ctx.tenant_id)
    findings = get_experiment_findings(db=db, experiment_id=run_id, tenant_id=ctx.tenant_id)
    findings_dicts = [
        {"severity": f.severity, "rule_id": f.rule_id, "title": f.title, "evidence": f.evidence}
        for f in findings
    ]
    
    advisory = await generate_ai_threat_advisory(
        experiment_name=experiment.name,
        operation=experiment.operation,
        risk_level=experiment.risk_level,
        risk_score=experiment.risk_score,
        findings=findings_dicts
    )

    experiment.ai_analysis = advisory
    db.commit()
    db.refresh(experiment)

    return {"experiment_id": run_id, "ai_analysis": advisory}
