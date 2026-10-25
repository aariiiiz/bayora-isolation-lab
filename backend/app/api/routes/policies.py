from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.policy import PolicyResponse, PolicyCreate, PolicyUpdate
from app.services.policy_service import (
    get_policies,
    get_policy,
    create_policy,
    update_policy,
    delete_policy
)
from app.api.deps import require_role, TenantContext

router = APIRouter(prefix="/policies", tags=["Policies"])

@router.get("", response_model=List[PolicyResponse])
def list_policies(
    category: Optional[str] = Query(None, description="isolation, audit, prompt, config"),
    is_enabled: Optional[bool] = None,
    ctx: TenantContext = Depends(require_role(["admin", "analyst", "viewer"])),
    db: Session = Depends(get_db)
):
    """
    Lists security policies and baseline rules for authorized identities.
    """
    return get_policies(db=db, category=category, is_enabled=is_enabled)

@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy_detail(
    policy_id: str,
    ctx: TenantContext = Depends(require_role(["admin", "analyst", "viewer"])),
    db: Session = Depends(get_db)
):
    """
    Gets details of a specific policy by ID or rule_id.
    """
    return get_policy(db=db, policy_id=policy_id)

@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_new_policy(
    data: PolicyCreate,
    ctx: TenantContext = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Creates a new custom security validation rule. Restricted to Admin role.
    """
    return create_policy(db=db, data=data, actor=ctx.user.email)

@router.patch("/{policy_id}", response_model=PolicyResponse)
def update_existing_policy(
    policy_id: str,
    data: PolicyUpdate,
    ctx: TenantContext = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Updates policy fields (e.g. enable/disable toggle or severity adjustment). Restricted to Admin role.
    """
    return update_policy(db=db, policy_id=policy_id, data=data, actor=ctx.user.email)

@router.delete("/{policy_id}", status_code=status.HTTP_200_OK)
def remove_policy(
    policy_id: str,
    ctx: TenantContext = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """
    Deletes a user-defined policy. Restricted to Admin role. Baseline policies are protected from deletion.
    """
    delete_policy(db=db, policy_id=policy_id, actor=ctx.user.email)
    return {"success": True, "message": f"Policy '{policy_id}' successfully removed."}
