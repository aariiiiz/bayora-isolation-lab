import io

def test_create_and_run_experiment_flow(client):
    file_content = b'''{
        "tenant_id": "*",
        "permissions": ["admin:*"],
        "isolate_sessions": false
    }'''
    files = {
        "file": ("test_policy.json", io.BytesIO(file_content), "application/json")
    }
    data = {
        "name": "Integration Test Run",
        "operation": "isolation_access",
        "environment": "staging",
        "profile": "strict"
    }

    response = client.post("/api/experiments", data=data, files=files)
    assert response.status_code == 201
    exp_data = response.json()
    run_id = exp_data["id"]
    assert exp_data["status"] == "completed"
    assert exp_data["risk_level"] == "CRITICAL"
    assert exp_data["summary"]["critical"] >= 2

    # Verify retrieval
    detail_res = client.get(f"/api/experiments/{run_id}")
    assert detail_res.status_code == 200
    assert len(detail_res.json()["findings"]) >= 2

    # Verify report export
    report_res = client.get(f"/api/experiments/{run_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    assert report_data["experiment"]["id"] == run_id
    assert report_data["audit_chain_status"] == "CRYPTOGRAPHICALLY_VERIFIED"
