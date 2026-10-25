from typing import Optional, List, Tuple
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.tenant import Tenant, TenantMembership
from app.core.security import decode_access_token

security_bearer = HTTPBearer(auto_error=False)

class TenantContext:
    def __init__(self, tenant: Tenant, role: str, user: User):
        self.tenant = tenant
        self.role = role
        self.user = user

    @property
    def tenant_id(self) -> str:
        return self.tenant.id

    @property
    def user_id(self) -> str:
        return self.user.id

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    """
    Extracts and cryptographically validates the Bearer token.
    Enforces active user verification against the database.
    Returns HTTP 401 on missing, malformed, expired, or invalid credentials.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: missing credentials.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        error_msg = str(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {error_msg}",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: token missing subject identifier.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: user does not exist or has been disabled.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user

def get_tenant_context(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TenantContext:
    """
    Resolves the server-verified tenant identity and membership role.
    Checks:
    1. If client sent 'X-Tenant-ID' header, validates that current_user is an authorized member.
    2. Otherwise, uses the user's primary/first active tenant membership.
    Rejects any request attempting to access a tenant where membership does not exist (403 Forbidden).
    """
    requested_tenant_id = request.headers.get("X-Tenant-ID")

    # Fetch user memberships
    memberships = db.query(TenantMembership).filter(
        TenantMembership.user_id == current_user.id
    ).all()

    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: user has no authorized tenant memberships."
        )

    membership_map = {m.tenant_id: m for m in memberships}

    if requested_tenant_id:
        if requested_tenant_id not in membership_map:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: caller is not an authorized member of tenant '{requested_tenant_id}'."
            )
        active_membership = membership_map[requested_tenant_id]
    else:
        active_membership = memberships[0]

    tenant = db.query(Tenant).filter(
        Tenant.id == active_membership.tenant_id,
        Tenant.is_active == True
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authorized tenant is inactive or not found."
        )

    return TenantContext(
        tenant=tenant,
        role=active_membership.role,
        user=current_user
    )

def require_role(allowed_roles: List[str]):
    """
    Role-based authorization dependency factory.
    Verifies that the caller's role within their active tenant is permitted.
    """
    def role_checker(ctx: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if ctx.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of roles: {allowed_roles}. Current role: '{ctx.role}'."
            )
        return ctx
    return role_checker
