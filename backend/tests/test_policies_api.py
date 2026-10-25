def test_list_policies(client, admin_headers):
    response = client.get("/api/policies", headers=admin_headers)
    assert response.status_code == 200
    policies = response.json()
    assert len(policies) > 0
    rule_ids = [p["rule_id"] for p in policies]
    assert "ISO-001" in rule_ids

def test_create_custom_policy(client, admin_headers):
    new_policy = {
        "rule_id": "CUST-001",
        "name": "Custom Isolation Rule",
        "category": "isolation",
        "severity": "HIGH",
        "is_enabled": True,
        "description": "Test custom policy rule.",
        "explanation": "Custom isolation explanation.",
        "remediation": "Custom remediation advice.",
        "parameters": {}
    }
    response = client.post("/api/policies", json=new_policy, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["rule_id"] == "CUST-001"

def test_cannot_delete_baseline_policy(client, admin_headers):
    response = client.delete("/api/policies/ISO-001", headers=admin_headers)
    assert response.status_code == 400
    assert "Baseline rule" in response.json()["message"]
