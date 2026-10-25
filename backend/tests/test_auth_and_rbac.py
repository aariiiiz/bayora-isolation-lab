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

def test_14_viewer_can_read_and_verify_audit_trail(client, viewer_headers):
    # Auditor Viewer role must be allowed read-only access to audit events
    res_list = client.get("/api/audit-events", headers=viewer_headers)
    assert res_list.status_code == 200
    assert "items" in res_list.json()

    # Auditor Viewer can also invoke read-only cryptographic chain verification
    res_verify = client.get("/api/audit-events/verify-chain", headers=viewer_headers)
    assert res_verify.status_code == 200
    assert "valid" in res_verify.json()

def test_15_viewer_cannot_modify_or_delete_experiments(client, viewer_headers, analyst_headers, db_session):
    exp = Experiment(name="Alpha Test Run", operation="isolation_access", tenant_id="tenant-alpha", artifact_filename="a.json", artifact_type="json", artifact_size_bytes=100)
    db_session.add(exp)
    db_session.commit()

    # Viewer attempts modification
    res_patch = client.patch(f"/api/experiments/{exp.id}", json={"name": "Hacked Name"}, headers=viewer_headers)
    assert res_patch.status_code == 403
    assert "Forbidden" in res_patch.json()["detail"]

    # Viewer attempts deletion
    res_del = client.delete(f"/api/experiments/{exp.id}", headers=viewer_headers)
    assert res_del.status_code == 403
    assert "Forbidden" in res_del.json()["detail"]

def test_16_analyst_cannot_delete_experiment_admin_only(client, analyst_headers, db_session):
    exp = Experiment(name="Alpha Critical Baseline", operation="isolation_access", tenant_id="tenant-alpha", artifact_filename="a.json", artifact_type="json", artifact_size_bytes=100)
    db_session.add(exp)
    db_session.commit()

    # Security Analyst role cannot delete experiments (admin only)
    res_del = client.delete(f"/api/experiments/{exp.id}", headers=analyst_headers)
    assert res_del.status_code == 403
    assert "Forbidden" in res_del.json()["detail"]

def test_17_cross_tenant_admin_cannot_delete_another_tenant_experiment(client, admin_headers, beta_headers, db_session):
    beta_exp = Experiment(name="Beta Defense Artifact", operation="isolation_access", tenant_id="tenant-beta", artifact_filename="beta.json", artifact_type="json", artifact_size_bytes=100)
    db_session.add(beta_exp)
    db_session.commit()

    # Tenant Alpha admin attempts to delete Tenant Beta experiment
    res_del = client.delete(f"/api/experiments/{beta_exp.id}", headers=admin_headers)
    assert res_del.status_code == 404  # Non-disclosing 404

    # Ensure Beta experiment is still intact
    assert db_session.query(Experiment).filter(Experiment.id == beta_exp.id).first() is not None

def test_18_authorized_admin_can_delete_experiment_with_audit_trail(client, admin_headers, db_session):
    exp = Experiment(name="Disposable Alpha Run", operation="isolation_access", tenant_id="tenant-alpha", artifact_filename="a.json", artifact_type="json", artifact_size_bytes=100)
    db_session.add(exp)
    db_session.commit()

    res_del = client.delete(f"/api/experiments/{exp.id}", headers=admin_headers)
    assert res_del.status_code == 200
    assert "permanently deleted" in res_del.json()["message"]

    # Verify deleted from DB
    assert db_session.query(Experiment).filter(Experiment.id == exp.id).first() is None

    # Verify EXPERIMENT_DELETED event logged in audit trail
    audit_res = client.get("/api/audit-events?event_type=EXPERIMENT_DELETED", headers=admin_headers)
    assert audit_res.status_code == 200
    events = audit_res.json()["items"]
    assert any(e["experiment_id"] == exp.id for e in events)

def test_19_retest_comparison_endpoint_computes_deltas(client, analyst_headers, db_session):
    base_exp = Experiment(name="Baseline Run", operation="isolation_access", tenant_id="tenant-alpha", artifact_filename="base.json", artifact_type="json", artifact_size_bytes=100, risk_score=85.0, risk_level="HIGH")
    db_session.add(base_exp)
    db_session.commit()

    f1 = Finding(experiment_id=base_exp.id, rule_id="ISO-001", title="Wildcard Tenant", severity="CRITICAL", description="d", evidence={}, remediation="r", detection_method="schema_rule")
    f2 = Finding(experiment_id=base_exp.id, rule_id="ISO-002", title="Shared Session", severity="HIGH", description="d", evidence={}, remediation="r", detection_method="schema_rule")
    db_session.add_all([f1, f2])

    retest_exp = Experiment(name="Retest Run", operation="isolation_access", tenant_id="tenant-alpha", artifact_filename="fixed.json", artifact_type="json", artifact_size_bytes=100, risk_score=0.0, risk_level="CLEAN", parent_experiment_id=base_exp.id)
    db_session.add(retest_exp)
    db_session.commit()

    res = client.get(f"/api/experiments/{retest_exp.id}/compare", headers=analyst_headers)
    assert res.status_code == 200
    comp_data = res.json()
    assert comp_data["comparison"]["status"] == "IMPROVED"
    assert comp_data["comparison"]["score_delta"] == 85.0
    assert comp_data["comparison"]["resolved_count"] == 2
    assert len(comp_data["comparison"]["resolved_findings"]) == 2

def test_20_simulated_tamper_attack_and_restoration_lifecycle(client, analyst_headers):
    # 1. Verify chain is currently intact
    v1 = client.get("/api/audit-events/verify-chain", headers=analyst_headers)
    assert v1.status_code == 200
    assert v1.json()["valid"] is True

    # 2. Simulate adversarial tamper attack
    tamper_res = client.post("/api/audit-events/simulate-tamper?tamper_type=payload", headers=analyst_headers)
    assert tamper_res.status_code == 200
    assert tamper_res.json()["success"] is True

    # 3. Chain verification detects tamper with rich evidence
    v2 = client.get("/api/audit-events/verify-chain", headers=analyst_headers)
    assert v2.status_code == 200
    report = v2.json()
    assert report["valid"] is False
    assert report["break_detected"] is True
    assert report["failure_category"] == "PAYLOAD_TAMPERED"
    assert report["expected_hash"] is not None
    assert report["calculated_hash"] is not None
    assert "Integrity Failure" in report["message"]

    # 4. Restore chain integrity
    restore_res = client.post("/api/audit-events/restore-chain", headers=analyst_headers)
    assert restore_res.status_code == 200
    assert restore_res.json()["success"] is True

    # 5. Chain verification passes again
    v3 = client.get("/api/audit-events/verify-chain", headers=analyst_headers)
    assert v3.status_code == 200
    assert v3.json()["valid"] is True

