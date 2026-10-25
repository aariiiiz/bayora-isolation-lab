from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class LoginRequest(BaseModel):
    email: str
    password: str

class TenantMembershipResponse(BaseModel):
    tenant_id: str
    tenant_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    memberships: List[TenantMembershipResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ActiveTenantResponse(BaseModel):
    id: str
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse
    active_tenant: ActiveTenantResponse
