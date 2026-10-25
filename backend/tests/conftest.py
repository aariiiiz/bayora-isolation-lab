import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base, get_db
from app.main import app
from app.services.policy_service import seed_baseline_policies
from app.cli.bootstrap import bootstrap_system
from app.core.security import create_access_token
from app.utils.crypto import clear_audit_checkpoint
from app.db.models.user import User

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    clear_audit_checkpoint()
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_baseline_policies(db)
    bootstrap_system(db)
    db.close()
    yield
    clear_audit_checkpoint()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_tokens(db_session):
    admin_user = db_session.query(User).filter(User.email == "admin@alpha.io").first()
    analyst_user = db_session.query(User).filter(User.email == "analyst@alpha.io").first()
    viewer_user = db_session.query(User).filter(User.email == "viewer@alpha.io").first()
    beta_analyst_user = db_session.query(User).filter(User.email == "analyst@beta.io").first()

    return {
        "admin": create_access_token({
            "sub": admin_user.id if admin_user else "admin-id",
            "email": "admin@alpha.io",
            "tenant_id": "tenant-alpha",
            "role": "admin"
        }),
        "analyst": create_access_token({
            "sub": analyst_user.id if analyst_user else "analyst-id",
            "email": "analyst@alpha.io",
            "tenant_id": "tenant-alpha",
            "role": "analyst"
        }),
        "viewer": create_access_token({
            "sub": viewer_user.id if viewer_user else "viewer-id",
            "email": "viewer@alpha.io",
            "tenant_id": "tenant-alpha",
            "role": "viewer"
        }),
        "beta_analyst": create_access_token({
            "sub": beta_analyst_user.id if beta_analyst_user else "beta-id",
            "email": "analyst@beta.io",
            "tenant_id": "tenant-beta",
            "role": "analyst"
        }),
    }

@pytest.fixture
def admin_headers(auth_tokens):
    return {"Authorization": f"Bearer {auth_tokens['admin']}"}

@pytest.fixture
def analyst_headers(auth_tokens):
    return {"Authorization": f"Bearer {auth_tokens['analyst']}"}

@pytest.fixture
def viewer_headers(auth_tokens):
    return {"Authorization": f"Bearer {auth_tokens['viewer']}"}

@pytest.fixture
def beta_headers(auth_tokens):
    return {"Authorization": f"Bearer {auth_tokens['beta_analyst']}"}
