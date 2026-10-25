import io
import pytest
from datetime import timedelta
from app.core.security import create_access_token
from app.db.models.experiment import Experiment
from app.db.models.finding import Finding
from app.db.models.audit import AuditEvent

def test_01_request_without_credentials_is_rejected(client):
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 401
    assert "missing credentials" in res.json()["detail"].lower()

def test_02_invalid_token_is_rejected(client):
    headers = {"Authorization": "Bearer evil.invalid.signature"}
    res = client.get("/api/dashboard/summary", headers=headers)
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower() or "malformed" in res.json()["detail"].lower()

def test_03_expired_token_is_rejected(client):
    expired = create_access_token({
        "sub": "user-uuid",
        "email": "analyst@alpha.io",
        "tenant_id": "tenant-alpha",
        "role": "analyst"
    }, expires_delta=timedelta(seconds=-60))
    headers = {"Authorization": f"Bearer {expired}"}
    res = client.get("/api/dashboard/summary", headers=headers)
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()

def test_04_valid_analyst_can_access_authorized_resources(client, analyst_headers):
    res = client.get("/api/dashboard/summary", headers=analyst_headers)
    assert res.status_code == 200
    assert "total_experiments" in res.json()

def test_05_viewer_cannot_perform_restricted_administrative_actions(client, viewer_headers):
    # Viewer tries to create a custom policy
    new_policy = {
        "rule_id": "VIEWER-FORBIDDEN-01",
        "name": "Unauthorized Policy",
        "category": "isolation",
        "severity": "HIGH",
        "is_enabled": True,
        "description": "Exploit attempt",
        "explanation": "Should fail",
        "remediation": "Deny"
    }
    res = client.post("/api/policies", json=new_policy, headers=viewer_headers)
    assert res.status_code == 403
    assert "Forbidden" in res.json()["detail"]

def test_06_user_cannot_access_another_tenants_experiment(client, analyst_headers, beta_headers, db_session):
    # Create private experiment for Tenant Beta
    beta_exp = Experiment(
        name="Beta Secret AI Project",
        operation="isolation_access",
        tenant_id="tenant-beta",
        artifact_filename="beta_secret.json",
        artifact_type="json",
        artifact_size_bytes=1024,
        status="completed"
    )
    db_session.add(beta_exp)
    db_session.commit()
    db_session.refresh(beta_exp)

    # Tenant Alpha analyst attempts to access Tenant Beta's experiment
    res = client.get(f"/api/experiments/{beta_exp.id}", headers=analyst_headers)
    assert res.status_code == 404  # Non-disclosing 404

    # Tenant Beta analyst can access it
    beta_res = client.get(f"/api/experiments/{beta_exp.id}", headers=beta_headers)
    assert beta_res.status_code == 200
    assert beta_res.json()["name"] == "Beta Secret AI Project"

def test_07_user_cannot_access_another_tenants_findings(client, analyst_headers, db_session):
    beta_exp = Experiment(
        name="Beta Findings Project",
        operation="isolation_access",
        tenant_id="tenant-beta",
        artifact_filename="beta.json",
        artifact_type="json",
        artifact_size_bytes=512,
        status="completed"
    )
    db_session.add(beta_exp)
    db_session.commit()

    finding = Finding(
        experiment_id=beta_exp.id,
        rule_id="ISO-001",
        title="Beta Leak",
        severity="CRITICAL",
        description="Private beta vulnerability",
        evidence={"leak": "data"},
        remediation="Fix it",
        detection_method="schema_rule"
    )
    db_session.add(finding)
    db_session.commit()

    # Tenant Alpha analyst requests findings
    res = client.get(f"/api/experiments/{beta_exp.id}/findings", headers=analyst_headers)
    assert res.status_code == 404

def test_08_user_cannot_download_another_tenants_report(client, analyst_headers, db_session):
    beta_exp = Experiment(
        name="Beta Sensitive Report Experiment",
        operation="isolation_access",
        tenant_id="tenant-beta",
        artifact_filename="beta.json",
        artifact_type="json",
        artifact_size_bytes=512,
        status="completed"
    )
    db_session.add(beta_exp)
    db_session.commit()

    res = client.get(f"/api/experiments/{beta_exp.id}/report", headers=analyst_headers)
    assert res.status_code == 404

def test_09_user_cannot_read_another_tenants_audit_events(client, analyst_headers, beta_headers, db_session):
    # Create private audit event for Tenant Beta
    beta_audit = AuditEvent(
        tenant_id="tenant-beta",
        event_type="BETA_CLASSIFIED_EVALUATION",
        actor="bob@beta.io",
        sequence_number=999,
        details={"confidential": "true"},
        prev_hash="GENESIS",
        record_hash="d4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35"
    )
    db_session.add(beta_audit)
    db_session.commit()

    # Alpha analyst queries audit trail
    res = client.get("/api/audit-events", headers=analyst_headers)
    assert res.status_code == 200
    event_types = [e["event_type"] for e in res.json()["items"]]
    assert "BETA_CLASSIFIED_EVALUATION" not in event_types

    # Beta analyst queries audit trail
    beta_res = client.get("/api/audit-events", headers=beta_headers)
    assert beta_res.status_code == 200
    beta_event_types = [e["event_type"] for e in beta_res.json()["items"]]
    assert "BETA_CLASSIFIED_EVALUATION" in beta_event_types

def test_10_user_cannot_bypass_authorization_using_guessed_id(client, analyst_headers):
    random_uuid = "00000000-0000-0000-0000-000000000000"
    res = client.get(f"/api/experiments/{random_uuid}", headers=analyst_headers)
    assert res.status_code == 404

def test_11_request_cannot_override_tenant_via_header_if_not_member(client, analyst_headers):
    # Alpha analyst attempts to spoof tenant header to tenant-beta
    spoofed_headers = dict(analyst_headers)
    spoofed_headers["X-Tenant-ID"] = "tenant-beta"

    res = client.get("/api/dashboard/summary", headers=spoofed_headers)
    assert res.status_code == 403
    assert "not an authorized member" in res.json()["detail"]

def test_12_tenant_scoped_dashboard_counts_do_not_leak_cross_tenant_totals(client, analyst_headers, db_session):
    # Add 2 experiments to Tenant Beta
    b1 = Experiment(name="B1", operation="isolation_access", tenant_id="tenant-beta", artifact_filename="b.json", artifact_type="json", artifact_size_bytes=100)
    b2 = Experiment(name="B2", operation="isolation_access", tenant_id="tenant-beta", artifact_filename="b.json", artifact_type="json", artifact_size_bytes=100)
    db_session.add_all([b1, b2])
    db_session.commit()

    # Alpha analyst checks summary
    res = client.get("/api/dashboard/summary", headers=analyst_headers)
    assert res.status_code == 200
    alpha_exp_count = res.json()["total_experiments"]

    # Beta experiment IDs must not be in Alpha recent experiments
    recent_names = [e["name"] for e in res.json()["recent_experiments"]]
    assert "B1" not in recent_names
    assert "B2" not in recent_names

def test_13_cross_tenant_parent_retest_linkage_is_rejected(client, analyst_headers, db_session):
    # Try to retest a Beta parent using Alpha credentials
    beta_exp = Experiment(name="Beta Parent", operation="isolation_access", tenant_id="tenant-beta", artifact_filename="b.json", artifact_type="json", artifact_size_bytes=100)
    db_session.add(beta_exp)
    db_session.commit()

    files = {"file": ("test.json", io.BytesIO(b'{"key": "val"}'), "application/json")}
    data = {
        "name": "Malicious Retest Cross-Tenant Link",
        "operation": "isolation_access",
        "parent_experiment_id": beta_exp.id
    }
    res = client.post("/api/experiments", data=data, files=files, headers=analyst_headers)
    assert res.status_code == 404
