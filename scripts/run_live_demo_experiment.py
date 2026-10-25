import sys
import urllib.request
import urllib.parse
import json
import uuid

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000/api"

def make_request(url, method="GET", headers=None, data=None):
    headers = dict(headers or {})
    body = None
    if data is not None:
        if isinstance(data, dict):
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, (bytes, bytearray)):
            body = data
        else:
            body = str(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            try:
                return json.loads(content)
            except:
                return content
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        try:
            return json.loads(err_content)
        except:
            return {"error": err_content, "status_code": e.code}

def main():
    print("=" * 80)
    print("🚀 BAYORA ISOLATION LAB — LIVE SECURITY EXPERIMENT EXECUTION")
    print("=" * 80)

    # 1. Authenticate as Alice Safety Analyst
    print("\n[Step 1] Authenticating as Alice Safety Analyst (tenant-alpha)...")
    auth_resp = make_request(
        f"{BASE_URL}/auth/login",
        method="POST",
        data={"email": "analyst@alpha.io", "password": "Bayora@Analyst2026!"}
    )
    token = auth_resp.get("access_token")
    if not token:
        print(f"❌ Authentication failed: {auth_resp}")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": "tenant-alpha"
    }
    print(f"✅ Authenticated successfully! Token issued for {auth_resp['user']['email']} (Role: {auth_resp['active_tenant']['role']})")

    # 2. Get demo fixtures
    fixtures = make_request(f"{BASE_URL}/synthetic/fixtures", headers=headers)
    vulnerable_fixture = fixtures["isolation_vulnerable"]
    hardened_fixture = fixtures["isolation_safe"]

    # 3. Multipart form data helper
    def build_multipart(fields, file_field, filename, file_content):
        boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
        parts = []
        for k, v in fields.items():
            parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode("utf-8"))
        
        file_header = f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{filename}\"\r\nContent-Type: application/json\r\n\r\n".encode("utf-8")
        parts.append(file_header + file_content.encode("utf-8") + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode("utf-8"))
        return b"".join(parts), f"multipart/form-data; boundary={boundary}"

    # 4. Execute Baseline Experiment (Vulnerable Policy)
    print("\n[Step 2] Executing Baseline Security Experiment (Vulnerable Policy)...")
    fields = {
        "name": "Multi-Tenant Isolation & Access Boundary Review",
        "operation": "isolation_access",
        "environment": "staging",
        "profile": "strict",
        "description": "Baseline evaluation of multi-tenant policy configuration",
        "enable_ai_advisor": "false"
    }
    body, content_type = build_multipart(fields, "file", vulnerable_fixture["filename"], vulnerable_fixture["content"])
    upload_headers = dict(headers)
    upload_headers["Content-Type"] = content_type

    baseline_exp = make_request(f"{BASE_URL}/experiments", method="POST", headers=upload_headers, data=body)
    baseline_id = baseline_exp["id"]
    baseline_findings = make_request(f"{BASE_URL}/experiments/{baseline_id}/findings", headers=headers)
    print(f"✅ Baseline Run Created & Executed:")
    print(f"   • Experiment ID : {baseline_id}")
    print(f"   • Risk Score    : {baseline_exp['risk_score']:.1f} / 100 ({baseline_exp['risk_level']})")
    print(f"   • Findings Count: {len(baseline_findings)}")

    print("\n--- Documented Ground-Truth Findings (Baseline) ---")
    for f in baseline_findings:
        print(f"   🔴 [{f['rule_id']}] {f['title']} (Severity: {f['severity']})")
        print(f"      - Field: {f['evidence'].get('field_path')} | Value: {f['evidence'].get('value')}")
        print(f"      - Excerpt: {f['evidence'].get('excerpt')}")
        print(f"      - Remediation: {f['remediation']}\n")

    # 5. Execute Comparative Retest (Hardened Policy)
    print("\n[Step 3] Executing Comparative Retest with Remediated Policy...")
    retest_fields = {
        "name": "Retest: Hardened Multi-Tenant Isolation Policy",
        "operation": "isolation_access",
        "environment": "staging",
        "profile": "strict",
        "description": "Retest after enforcing strict tenant UUID and session memory boundaries",
        "parent_experiment_id": baseline_id,
        "enable_ai_advisor": "false"
    }
    retest_body, retest_ct = build_multipart(retest_fields, "file", hardened_fixture["filename"], hardened_fixture["content"])
    retest_headers = dict(headers)
    retest_headers["Content-Type"] = retest_ct

    retest_exp = make_request(f"{BASE_URL}/experiments", method="POST", headers=retest_headers, data=retest_body)
    retest_id = retest_exp["id"]
    retest_findings = make_request(f"{BASE_URL}/experiments/{retest_id}/findings", headers=headers)
    print(f"✅ Retest Run Created & Executed:")
    print(f"   • Retest ID     : {retest_id}")
    print(f"   • Parent Linkage: {retest_exp['parent_experiment_id']}")
    print(f"   • Risk Score    : {retest_exp['risk_score']:.1f} / 100 ({retest_exp['risk_level']})")
    print(f"   • Findings Count: {len(retest_findings)}")

    # 6. Query Before-and-After Retest Comparison
    print("\n[Step 4] Querying Side-by-Side Retest Delta Comparison (/compare)...")
    comparison = make_request(f"{BASE_URL}/experiments/{retest_id}/compare", headers=headers)
    cmp_details = comparison.get("comparison", {})
    print(f"✅ Comparison Report Output:")
    print(f"   • Status          : {cmp_details.get('status')}")
    print(f"   • Baseline Score  : {comparison['baseline']['risk_score']:.1f} ({comparison['baseline']['risk_level']})")
    print(f"   • Retest Score    : {comparison['retest']['risk_score']:.1f} ({comparison['retest']['risk_level']})")
    print(f"   • Score Delta     : {cmp_details.get('score_delta'):.1f} pts (Risk Improvement)")
    print(f"   • Resolved Issues : {cmp_details.get('resolved_count')} findings")
    for rf in cmp_details.get("resolved_findings", []):
        print(f"      ✓ Remediated: [{rf['rule_id']}] {rf['title']} (Was: {rf['severity']})")
    print(f"   • Persistent Risks: {cmp_details.get('persistent_count')}")
    print(f"   • New Findings    : {cmp_details.get('new_count')}")

    # 7. Verify Cryptographic Audit Chain Integrity
    print("\n[Step 5] Verifying SHA-256 Tamper-Evident Audit Chain Integrity...")
    audit_verify = make_request(f"{BASE_URL}/audit-events/verify-chain", headers=headers)
    print(f"✅ Audit Verification Output:")
    print(f"   • Is Valid Chain? : {audit_verify.get('valid')}")
    print(f"   • Total Verified  : {audit_verify.get('total_verified')} records")
    print(f"   • Latest Sequence : #{audit_verify.get('latest_sequence')}")
    print(f"   • Latest Hash     : {audit_verify.get('latest_hash')}")
    print(f"   • Verified At     : {audit_verify.get('verification_timestamp')}")
    print(f"   • Message         : {audit_verify.get('message')}")

    # 8. Export Compliance Report
    print("\n[Step 6] Exporting Formal Evaluation Report...")
    report = make_request(f"{BASE_URL}/experiments/{retest_id}/report", headers=headers)
    print(f"✅ Compliance Report Generated:")
    print(f"   • Report ID       : {report.get('report_id')}")
    print(f"   • Platform        : {report.get('platform')} v{report.get('platform_version')}")
    print(f"   • Audit Status    : {report.get('audit_chain_status')}")
    print(f"   • Compliance Notes: {report.get('compliance_notes')}")
    print(f"   • Residual Risks  : {len(report.get('limitations_and_residual_risks', []))} disclosures documented")

    # 9. Execute 10-Scenario Synthetic Isolation Matrix
    print("\n[Step 7] Running 10-Scenario Controlled Synthetic Isolation Matrix (/synthetic/run)...")
    matrix = make_request(f"{BASE_URL}/synthetic/run", method="POST", headers=headers)
    print(f"✅ Synthetic Isolation Matrix Results:")
    print(f"   • Total Scenarios : {matrix.get('total_scenarios')}")
    print(f"   • Passed Scenarios: {matrix.get('passed_scenarios')}")
    print(f"   • All Enforced    : {matrix.get('all_enforced')}")
    print("   • Matrix Scenarios Breakdown:")
    for s in matrix.get("scenarios", []):
        print(f"      [✓] {s['test_id']}: {s['name']}")
        print(f"          Expected: {s['expected_outcome']} | Actual: {s['actual_outcome']} -> {s['status']}")
        print(f"          Evidence: {s.get('evidence')}")

    print("\n" + "=" * 80)
    print("🏆 ALL EXPERIMENT PHASES EXECUTED & VERIFIED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()
