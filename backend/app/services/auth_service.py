from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models.user import User
from app.db.models.tenant import Tenant, TenantMembership
from app.core.security import verify_password, create_access_token
from app.schemas.auth import (
    TokenResponse,
    UserProfileResponse,
    TenantMembershipResponse,
    ActiveTenantResponse
)
from app.services.audit_service import log_audit_event
from app.core.errors import BayoraException

def authenticate_user(
    db: Session,
    email: str,
    password: str,
    preferred_tenant_id: Optional[str] = None
) -> TokenResponse:
    """
    Verifies user credentials, checks tenant membership, logs audit event,
    and returns signed JWT access token.
    """
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user or not user.is_active:
        raise BayoraException(
            "Invalid email or password.",
            status_code=401
        )

    if not verify_password(password, user.hashed_password):
        raise BayoraException(
            "Invalid email or password.",
            status_code=401
        )

    # Resolve memberships
    memberships = db.query(TenantMembership).filter(TenantMembership.user_id == user.id).all()
    if not memberships:
        raise BayoraException(
            "User is not assigned to any active tenant domain.",
            status_code=403
        )

    # Determine active tenant
    membership_dict = {m.tenant_id: m for m in memberships}
    if preferred_tenant_id and preferred_tenant_id in membership_dict:
        active_mem = membership_dict[preferred_tenant_id]
    else:
        active_mem = memberships[0]

    tenant = db.query(Tenant).filter(Tenant.id == active_mem.tenant_id).first()
    tenant_name = tenant.name if tenant else active_mem.tenant_id

    # Create JWT
    token_claims = {
        "sub": user.id,
        "email": user.email,
        "tenant_id": active_mem.tenant_id,
        "role": active_mem.role
    }
    access_token = create_access_token(token_claims)

    # Audit login
    log_audit_event(
        db=db,
        event_type="USER_AUTHENTICATED",
        actor=user.email,
        tenant_id=active_mem.tenant_id,
        user_id=user.id,
        details={
            "tenant_id": active_mem.tenant_id,
            "role": active_mem.role,
            "login_time": datetime.now(timezone.utc).isoformat()
        }
    )

    membership_responses = []
    for m in memberships:
        t = db.query(Tenant).filter(Tenant.id == m.tenant_id).first()
        membership_responses.append(
            TenantMembershipResponse(
                tenant_id=m.tenant_id,
                tenant_name=t.name if t else m.tenant_id,
                role=m.role
            )
        )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserProfileResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            memberships=membership_responses
        ),
        active_tenant=ActiveTenantResponse(
            id=active_mem.tenant_id,
            name=tenant_name,
            role=active_mem.role
        )
    )
