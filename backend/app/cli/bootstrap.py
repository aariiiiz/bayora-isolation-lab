import os
import sys
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.migrate import run_db_migrations
from app.db.models.tenant import Tenant, TenantMembership
from app.db.models.user import User
from app.core.security import hash_password
from app.services.audit_service import log_audit_event
from app.services.policy_service import seed_baseline_policies

DEFAULT_USERS = [
    {
        "email": "admin@alpha.io",
        "full_name": "Alpha Security Admin",
        "role": "admin",
        "tenant_id": "tenant-alpha",
        "env_var": "BAYORA_ADMIN_PASSWORD",
        "default_pass": "Bayora@Admin2026!"
    },
    {
        "email": "analyst@alpha.io",
        "full_name": "Alice Safety Analyst",
        "role": "analyst",
        "tenant_id": "tenant-alpha",
        "env_var": "BAYORA_ANALYST_PASSWORD",
        "default_pass": "Bayora@Analyst2026!"
    },
    {
        "email": "viewer@alpha.io",
        "full_name": "Auditor Viewer",
        "role": "viewer",
        "tenant_id": "tenant-alpha",
        "env_var": "BAYORA_VIEWER_PASSWORD",
        "default_pass": "Bayora@Viewer2026!"
    },
    {
        "email": "admin@beta.io",
        "full_name": "Beta Security Lead",
        "role": "admin",
        "tenant_id": "tenant-beta",
        "env_var": "BAYORA_ADMIN_PASSWORD",
        "default_pass": "Bayora@Admin2026!"
    },
    {
        "email": "analyst@beta.io",
        "full_name": "Bob Red Teamer",
        "role": "analyst",
        "tenant_id": "tenant-beta",
        "env_var": "BAYORA_ANALYST_PASSWORD",
        "default_pass": "Bayora@Analyst2026!"
    }
]

DEFAULT_TENANTS = [
    {
        "id": "tenant-alpha",
        "name": "Alpha AI Safety Lab",
        "description": "Primary safety evaluation and isolation testing domain."
    },
    {
        "id": "tenant-beta",
        "name": "Beta Defense AI Labs",
        "description": "Secondary red-team isolation testing domain."
    }
]

def bootstrap_system(db: Session) -> Dict[str, Any]:
    """
    Bootstraps the initial tenants and authenticated user accounts.
    Idempotent: does not overwrite existing passwords or duplicate records.
    Never exposes passwords in audit logs.
    """
    created_tenants = 0
    created_users = 0
    created_memberships = 0

    # 1. Tenants
    for t_data in DEFAULT_TENANTS:
        existing = db.query(Tenant).filter(Tenant.id == t_data["id"]).first()
        if not existing:
            tenant = Tenant(
                id=t_data["id"],
                name=t_data["name"],
                description=t_data["description"]
            )
            db.add(tenant)
            created_tenants += 1

    db.commit()

    # 2. Users and Memberships
    for u_data in DEFAULT_USERS:
        email = u_data["email"].lower().strip()
        existing_user = db.query(User).filter(User.email == email).first()
        
        password = os.environ.get(u_data["env_var"], u_data["default_pass"])
        hashed = hash_password(password)

        if not existing_user:
            user = User(
                email=email,
                full_name=u_data["full_name"],
                hashed_password=hashed,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created_users += 1
        else:
            user = existing_user

        # Ensure membership
        membership = db.query(TenantMembership).filter(
            TenantMembership.user_id == user.id,
            TenantMembership.tenant_id == u_data["tenant_id"]
        ).first()

        if not membership:
            mem = TenantMembership(
                user_id=user.id,
                tenant_id=u_data["tenant_id"],
                role=u_data["role"]
            )
            db.add(mem)
            created_memberships += 1

    db.commit()

    if created_users > 0 or created_tenants > 0:
        log_audit_event(
            db=db,
            event_type="SYSTEM_BOOTSTRAPPED",
            actor="bootstrap_cli",
            details={
                "tenants_created": created_tenants,
                "users_created": created_users,
                "memberships_created": created_memberships
            }
        )

    return {
        "tenants_created": created_tenants,
        "users_created": created_users,
        "memberships_created": created_memberships
    }

def main():
    print("Running Bayora Isolation Lab database bootstrap...")
    run_db_migrations(engine)
    db = SessionLocal()
    try:
        seed_baseline_policies(db)
        result = bootstrap_system(db)
        print("Bootstrap complete:")
        print(f"  Tenants created: {result['tenants_created']}")
        print(f"  Users created:   {result['users_created']}")
        print(f"  Memberships:     {result['memberships_created']}")
        print("\nDefault Demo Credentials (for local testing):")
        print("  - Admin:   admin@alpha.io   / Bayora@Admin2026!   (tenant-alpha)")
        print("  - Analyst: analyst@alpha.io / Bayora@Analyst2026! (tenant-alpha)")
        print("  - Viewer:  viewer@alpha.io  / Bayora@Viewer2026!  (tenant-alpha)")
        print("  - Admin:   admin@beta.io    / Bayora@Admin2026!   (tenant-beta)")
        print("  - Analyst: analyst@beta.io  / Bayora@Analyst2026! (tenant-beta)")
    finally:
        db.close()

if __name__ == "__main__":
    main()
