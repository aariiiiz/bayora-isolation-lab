from app.services.synthetic_service import run_synthetic_isolation_suite, LocalSyntheticSandbox

def test_synthetic_sandbox_logic():
    sandbox = LocalSyntheticSandbox()
    
    # 1. Authorized access succeeds
    res1 = sandbox.access_resource("tenant-alpha", "key-alpha-998811", "tenant-alpha", "res-eval-01")
    assert res1["status_code"] == 200
    assert res1["allowed"] is True

    # 2. Cross-tenant access is rejected with 403
    res2 = sandbox.access_resource("tenant-alpha", "key-alpha-998811", "tenant-beta", "res-eval-99")
    assert res2["status_code"] == 403
    assert res2["allowed"] is False
    assert res2["error"] == "CROSS_TENANT_ACCESS_DENIED"

    # 3. Cross-session access is rejected with 403
    res3 = sandbox.access_session_scratchpad("tenant-alpha", "sess-alpha-02", "sess-alpha-01")
    assert res3["status_code"] == 403
    assert res3["allowed"] is False
    assert res3["error"] == "CROSS_SESSION_ISOLATION_ENFORCED"

    # 4. Unauthenticated access is rejected with 401
    res4 = sandbox.access_resource("", "", "tenant-alpha", "res-eval-01")
    assert res4["status_code"] == 401
    assert res4["allowed"] is False

def test_synthetic_api_suite_run(client, analyst_headers):
    response = client.post("/api/synthetic/run", headers=analyst_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["all_enforced"] is True
    assert data["total_tests"] == 10
    assert data["passed_tests"] == 10
    assert data["audit_events_recorded"] == 10
