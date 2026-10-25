import io
import json
import pytest

def test_complete_e2e_security_workflow(client, analyst_headers, beta_headers, viewer_headers):
    """
    Priority 4 End-to-End Workflow Verification:
    1. Authenticate as an authorized user.
    2. Receive clear validation errors for unsupported or oversized files.
    3. Upload supported artifact and start analysis.
    4. Retrieve persisted findings with evidence and remediation.
    5. Create a distinct retest run linked to the baseline experiment.
    6. Compare original run and retest results.
    7. Verify relevant audit events and chain integrity.
    8. Export and verify report matching persisted findings.
    9. Confirm unauthorized cross-tenant and role-restricted access are securely denied.
    """
    # 1. Authenticate via login endpoint
    login_res = client.post("/api/auth/login", json={
        "email": "analyst@alpha.io",
        "password": "Bayora@Analyst2026!"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    auth_data = login_res.json()
    token = auth_data["access_token"]
    user_headers = {"Authorization": f"Bearer {token}"}
    assert auth_data["user"]["email"] == "analyst@alpha.io"
    assert auth_data["active_tenant"]["role"] == "analyst"

    # 2. Validation error for unsupported file extension
    bad_file = ("test.exe", io.BytesIO(b"malicious payload"), "application/octet-stream")
    res_bad = client.post(
        "/api/experiments",
        files={"file": bad_file},
        data={"name": "Bad File", "operation": "isolation_access"},
        headers=user_headers
    )
    assert res_bad.status_code == 400
    assert "Unsupported file format" in res_bad.text

    # 3. Validation error for oversized file (> 10MB)
    huge_data = io.BytesIO(b"0" * (10 * 1024 * 1024 + 1024))
    res_huge = client.post(
        "/api/experiments",
        files={"file": ("huge.json", huge_data, "application/json")},
        data={"name": "Oversized File", "operation": "isolation_access"},
        headers=user_headers
    )
    assert res_huge.status_code == 400
    assert "exceeds maximum allowable limit" in res_huge.text

    # 4. Upload supported baseline artifact and run analysis
    baseline_payload = json.dumps({
        "tenant_id": "*",
        "permissions": ["admin:*"],
        "isolate_sessions": False
    }).encode("utf-8")

    res_baseline = client.post(
        "/api/experiments",
        files={"file": ("baseline_policy.json", io.BytesIO(baseline_payload), "application/json")},
        data={
            "name": "Baseline Isolation Audit",
            "operation": "isolation_access",
            "environment": "staging",
            "profile": "strict",
            "description": "Baseline safety test run",
            "enable_ai_advisor": "false"
        },
        headers=user_headers
    )
    assert res_baseline.status_code == 201, f"Experiment creation failed: {res_baseline.text}"
    baseline_run = res_baseline.json()
    baseline_id = baseline_run["id"]
    assert baseline_run["status"] == "completed"
    assert baseline_run["tenant_id"] == "tenant-alpha"
    assert baseline_run["parent_experiment_id"] is None

    # 5. Retrieve persisted experiment detail & findings
    res_detail = client.get(f"/api/experiments/{baseline_id}", headers=user_headers)
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert len(detail_data["findings"]) >= 2
    first_finding = detail_data["findings"][0]
    assert "rule_id" in first_finding
    assert "severity" in first_finding
    assert "evidence" in first_finding
    assert "remediation" in first_finding

    # 6. Create a distinct retest run with parent linkage
    retest_payload = json.dumps({
        "tenant_id": "tenant-alpha",
        "permissions": ["experiments:read", "experiments:run"],
        "isolate_sessions": True
    }).encode("utf-8")

    res_retest = client.post(
        "/api/experiments",
        files={"file": ("retest_policy.json", io.BytesIO(retest_payload), "application/json")},
        data={
            "name": "Retest: Baseline Isolation Audit",
            "operation": "isolation_access",
            "environment": "staging",
            "profile": "strict",
            "parent_experiment_id": baseline_id,
            "enable_ai_advisor": "false"
        },
        headers=user_headers
    )
    assert res_retest.status_code == 201
    retest_run = res_retest.json()
    retest_id = retest_run["id"]
    assert retest_id != baseline_id
    assert retest_run["parent_experiment_id"] == baseline_id

    # 7. Verify baseline experiment remained immutable
    res_baseline_check = client.get(f"/api/experiments/{baseline_id}", headers=user_headers)
    assert res_baseline_check.status_code == 200
    assert res_baseline_check.json()["parent_experiment_id"] is None
    assert res_baseline_check.json()["risk_score"] == baseline_run["risk_score"]

    # 8. Compare findings between baseline and retest
    res_retest_detail = client.get(f"/api/experiments/{retest_id}", headers=user_headers)
    assert res_retest_detail.status_code == 200
    # Cleaned retest payload has 0 cross-tenant anomalies
    assert res_retest_detail.json()["risk_score"] < baseline_run["risk_score"]

    # 9. Verify audit chain verification endpoint reflects unbroken chain
    res_audit_verify = client.get("/api/audit-events/verify-chain", headers=user_headers)
    assert res_audit_verify.status_code == 200
    audit_report = res_audit_verify.json()
    assert audit_report["valid"] is True
    assert audit_report["break_detected"] is False
    assert audit_report["total_verified"] >= 2
    assert audit_report["failure_category"] is None

    # 10. Export JSON report and confirm it matches stored results
    res_report = client.get(f"/api/experiments/{baseline_id}/report", headers=user_headers)
    assert res_report.status_code == 200
    report_data = res_report.json()
    assert report_data["experiment"]["id"] == baseline_id
    assert report_data["experiment"]["name"] == baseline_run["name"]
    assert len(report_data["findings"]) == len(detail_data["findings"])

    # 11. Cross-Tenant IDOR Protection: Tenant Beta cannot access Tenant Alpha's experiment
    res_beta_get = client.get(f"/api/experiments/{baseline_id}", headers=beta_headers)
    assert res_beta_get.status_code == 404, "Cross-tenant experiment read should return 404"

    # 12. Cross-Tenant Report Download Denial: Tenant Beta cannot download Tenant Alpha's report
    res_beta_report = client.get(f"/api/experiments/{baseline_id}/report", headers=beta_headers)
    assert res_beta_report.status_code == 404, "Cross-tenant report download should return 404"

    # 13. Cross-Tenant Audit Event Access Denial
    res_beta_audit = client.get("/api/audit-events?tenant_id=tenant-alpha", headers=beta_headers)
    assert res_beta_audit.status_code == 200
    # Returned events must only be scoped to caller's tenant (tenant-beta) or system, never tenant-alpha
    for event in res_beta_audit.json()["items"]:
        assert event["tenant_id"] in ("tenant-beta", None)
        assert event["tenant_id"] != "tenant-alpha"

    # 14. Role Violation: Viewer cannot create new experiments
    res_viewer_post = client.post(
        "/api/experiments",
        files={"file": ("test.json", io.BytesIO(baseline_payload), "application/json")},
        data={"name": "Unauthorized Run", "operation": "isolation_access"},
        headers=viewer_headers
    )
    assert res_viewer_post.status_code == 403
    assert "Forbidden" in res_viewer_post.json()["detail"]

    # 15. Header Spoofing Resistance: Cannot override server tenant context via X-Tenant-ID header
    spoof_headers = {**user_headers, "X-Tenant-ID": "tenant-beta"}
    res_spoof = client.get(f"/api/experiments/{baseline_id}", headers=spoof_headers)
    assert res_spoof.status_code == 403
    assert "not an authorized member of tenant" in res_spoof.json()["detail"]
