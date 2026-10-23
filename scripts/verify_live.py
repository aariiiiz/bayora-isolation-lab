import httpx

def main():
    client = httpx.Client(base_url="http://127.0.0.1:8000")
    
    # 1. Health
    h = client.get("/api/health")
    print("Health:", h.status_code, h.json())

    # 2. Upload and run experiment
    sample_content = b'{"tenant_id": "*", "permissions": ["admin:*"], "isolate_sessions": false}'
    files = {"file": ("test_multi_tenant.json", sample_content, "application/json")}
    data = {
        "name": "Live Test Run from Verifier",
        "operation": "isolation_access",
        "environment": "staging",
        "profile": "strict"
    }
    exp = client.post("/api/experiments", data=data, files=files)
    print("Experiment:", exp.status_code, exp.json().get("risk_level"), "Score:", exp.json().get("risk_score"))
    run_id = exp.json()["id"]

    # 3. Findings
    findings = client.get(f"/api/experiments/{run_id}/findings")
    print("Findings count:", len(findings.json()))

    # 4. Audit Verify Chain
    chain = client.get("/api/audit-events/verify-chain")
    print("Audit Chain Valid:", chain.json().get("valid"), "Verified events:", chain.json().get("total_verified"))

    # 5. Synthetic Sandbox
    synth = client.post("/api/synthetic/run")
    print("Synthetic Sandbox Enforced:", synth.json().get("all_enforced"), f"{synth.json().get('passed_scenarios')}/{synth.json().get('total_scenarios')}")

    # 6. Report Export
    report = client.get(f"/api/experiments/{run_id}/report")
    print("Report Export:", report.status_code, report.json().get("report_id"))

if __name__ == "__main__":
    main()
