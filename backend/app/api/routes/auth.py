from typing import Dict, Any
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
    TenantMembershipResponse,
    ActiveTenantResponse
)
from app.services.auth_service import authenticate_user
from app.api.deps import get_current_user, get_tenant_context, TenantContext
from app.db.models.user import User
from app.db.models.tenant import Tenant, TenantMembership
from app.core.security import create_access_token
from app.services.audit_service import log_audit_event
from app.core.errors import BayoraException

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticates user credentials and issues a cryptographically signed HMAC-SHA256 JWT access token.
    Never stores or logs passwords. Rejects invalid credentials with HTTP 401.
    """
    preferred_tenant = request.headers.get("X-Tenant-ID")
    return authenticate_user(
        db=db,
        email=data.email,
        password=data.password,
        preferred_tenant_id=preferred_tenant
    )

@router.get("/me", response_model=UserProfileResponse)
def get_authenticated_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the server-verified identity and authorized tenant memberships of the current caller.
    """
    memberships = db.query(TenantMembership).filter(
        TenantMembership.user_id == current_user.id
    ).all()

    mem_list = []
    for m in memberships:
        t = db.query(Tenant).filter(Tenant.id == m.tenant_id).first()
        mem_list.append(
            TenantMembershipResponse(
                tenant_id=m.tenant_id,
                tenant_name=t.name if t else m.tenant_id,
                role=m.role
            )
        )

    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        memberships=mem_list
    )

@router.post("/switch-tenant/{tenant_id}", response_model=TokenResponse)
def switch_active_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Issues a new access token scoped to the specified tenant, verifying the caller has active membership.
    Rejects unauthorized tenant switching with HTTP 403.
    """
    membership = db.query(TenantMembership).filter(
        TenantMembership.user_id == current_user.id,
        TenantMembership.tenant_id == tenant_id
    ).first()

    if not membership:
        raise BayoraException(
            f"Access denied: You are not an authorized member of tenant '{tenant_id}'.",
            status_code=403
        )

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    token_claims = {
        "sub": current_user.id,
        "email": current_user.email,
        "tenant_id": tenant_id,
        "role": membership.role
    }
    new_token = create_access_token(token_claims)

    memberships = db.query(TenantMembership).filter(
        TenantMembership.user_id == current_user.id
    ).all()
    mem_list = []
    for m in memberships:
        t = db.query(Tenant).filter(Tenant.id == m.tenant_id).first()
        mem_list.append(
            TenantMembershipResponse(
                tenant_id=m.tenant_id,
                tenant_name=t.name if t else m.tenant_id,
                role=m.role
            )
        )

    log_audit_event(
        db=db,
        event_type="TENANT_SWITCHED",
        actor=current_user.email,
        tenant_id=tenant_id,
        user_id=current_user.id,
        details={"new_tenant_id": tenant_id, "role": membership.role}
    )

    return TokenResponse(
        access_token=new_token,
        token_type="bearer",
        user=UserProfileResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            is_active=current_user.is_active,
            memberships=mem_list
        ),
        active_tenant=ActiveTenantResponse(
            id=tenant_id,
            name=tenant.name if tenant else tenant_id,
            role=membership.role
        )
    )

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logs out the current session and records an audit event.
    """
    log_audit_event(
        db=db,
        event_type="USER_LOGGED_OUT",
        actor=current_user.email,
        user_id=current_user.id,
        details={"status": "session_terminated"}
    )
    return {"success": True, "message": "Successfully logged out."}
