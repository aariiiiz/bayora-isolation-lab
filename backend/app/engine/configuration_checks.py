import re
from typing import List, Dict, Any
from app.engine.artifact_parser import ParsedArtifact

SECRET_KEY_PATTERNS = [
    (r"(sk-[a-zA-Z0-9]{20,})", "OpenAI / Anthropic Secret Key"),
    (r"(gsk_[a-zA-Z0-9]{30,})", "Groq API Key"),
    (r"(AIza[0-9A-Za-z-_]{35})", "Google Cloud API Key"),
    (r"(AKIA[0-9A-Z]{16})", "AWS Access Key ID"),
    (r"password\s*[:=]\s*[\"']([^\"']+)[\"']", "Plaintext Password Assignment"),
    (r"secret\s*[:=]\s*[\"']([^\"']+)[\"']", "Plaintext Secret Assignment")
]

def check_configuration_risks(parsed: ParsedArtifact, profile: str = "strict", active_policies: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Operation D: Configuration risk review.
    Checks supported configuration fields against explicit security rules and reports misconfigurations.
    """
    findings = []
    active_policies = active_policies or {}

    def is_rule_enabled(rule_id: str) -> bool:
        if rule_id in active_policies:
            return active_policies[rule_id].get("is_enabled", True)
        return True

    data = parsed.structured_data
    raw_lines = parsed.raw_lines

    # 1. CFG-001: Hardcoded Secrets & API Keys
    if is_rule_enabled("CFG-001"):
        for idx, line in enumerate(raw_lines, 1):
            for pattern, pattern_label in SECRET_KEY_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    val = match.group(0)
                    masked = val[:6] + "..." + val[-4:] if len(val) > 10 else "***"
                    findings.append({
                        "rule_id": "CFG-001",
                        "title": f"Hardcoded Secret Detected ({pattern_label})",
                        "severity": "CRITICAL",
                        "description": f"A plaintext secret or API credential was identified on line {idx}. Committing secrets into test configurations risks credential compromise.",
                        "evidence": {
                            "line_number": idx,
                            "secret_type": pattern_label,
                            "masked_excerpt": line.replace(val, masked).strip()
                        },
                        "remediation": "Remove hardcoded credentials. Store secrets in environment variables or a dedicated vault (e.g. AWS Secrets Manager, HashiCorp Vault).",
                        "detection_method": "regex_entropy_signature",
                        "confidence": "HIGH",
                        "limitations": "Flags credentials matching recognized provider token patterns."
                    })

    # 2. CFG-002: Insecure Host Binding & Debug Modes
    if is_rule_enabled("CFG-002"):
        def inspect_network_config(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if k.lower() in ("host", "bind_address", "listen") and v in ("0.0.0.0", "::"):
                        line_no = None
                        for idx, line in enumerate(raw_lines, 1):
                            if k in line and str(v) in line:
                                line_no = idx
                                break
                        findings.append({
                            "rule_id": "CFG-002",
                            "title": "Insecure Global Network Interface Binding (0.0.0.0)",
                            "severity": "HIGH",
                            "description": f"Field '{current_path}' binds the service to 0.0.0.0, exposing internal testing services to all network interfaces.",
                            "evidence": {
                                "field_path": current_path,
                                "value": str(v),
                                "line_number": line_no
                            },
                            "remediation": "Bind testing services to loopback interface (127.0.0.1 or localhost) or a private subnet.",
                            "detection_method": "network_declaration_audit",
                            "confidence": "HIGH",
                            "limitations": "Evaluates declared binding parameter."
                        })
                    elif k.lower() in ("debug", "development_mode", "reload") and v is True:
                        line_no = None
                        for idx, line in enumerate(raw_lines, 1):
                            if k in line:
                                line_no = idx
                                break
                        findings.append({
                            "rule_id": "CFG-002",
                            "title": "Debug Mode Enabled in Configuration",
                            "severity": "MEDIUM",
                            "description": f"Debug mode flag '{current_path}' is set to true, which may expose stack traces, interactive debuggers, or unauthenticated reload endpoints.",
                            "evidence": {
                                "field_path": current_path,
                                "value": str(v),
                                "line_number": line_no
                            },
                            "remediation": "Set debug to false in non-development test deployments.",
                            "detection_method": "static_flag_detection",
                            "confidence": "HIGH",
                            "limitations": "Assumes standard boolean flag semantics."
                        })
                    else:
                        inspect_network_config(v, current_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    inspect_network_config(item, f"{path}[{idx}]")

        inspect_network_config(data)

    # 3. CFG-003: Insecure TLS / SSL Verification Disabled
    if is_rule_enabled("CFG-003"):
        def inspect_tls(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if (k.lower() in ("verify_ssl", "ssl_verify", "tls_verify", "check_cert") and v is False) or \
                       (k.lower() in ("insecure_skip_verify", "allow_insecure_http") and v is True):
                        line_no = None
                        for idx, line in enumerate(raw_lines, 1):
                            if k in line:
                                line_no = idx
                                break
                        findings.append({
                            "rule_id": "CFG-003",
                            "title": "TLS Certificate Verification Disabled",
                            "severity": "CRITICAL",
                            "description": f"Field '{current_path}' disables TLS/SSL certificate verification, exposing testing traffic to Man-in-the-Middle (MitM) attacks.",
                            "evidence": {
                                "field_path": current_path,
                                "value": str(v),
                                "line_number": line_no
                            },
                            "remediation": "Enable strict TLS certificate verification and supply custom CA certificates when testing private endpoints.",
                            "detection_method": "static_flag_detection",
                            "confidence": "HIGH",
                            "limitations": "Verifies configuration flags."
                        })
                    elif isinstance(v, str) and v.startswith("http://") and "localhost" not in v and "127.0.0.1" not in v:
                        line_no = None
                        for idx, line in enumerate(raw_lines, 1):
                            if v in line:
                                line_no = idx
                                break
                        findings.append({
                            "rule_id": "CFG-003",
                            "title": "Unencrypted HTTP Endpoint in Configuration",
                            "severity": "MEDIUM",
                            "description": f"Endpoint '{v}' in field '{current_path}' uses plaintext HTTP instead of encrypted HTTPS.",
                            "evidence": {
                                "field_path": current_path,
                                "endpoint": v,
                                "line_number": line_no
                            },
                            "remediation": "Upgrade remote communication endpoints to use HTTPS.",
                            "detection_method": "uri_scheme_audit",
                            "confidence": "HIGH",
                            "limitations": "Checks remote URI schemes."
                        })
                    else:
                        inspect_tls(v, current_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    inspect_tls(item, f"{path}[{idx}]")

        inspect_tls(data)

    # 4. CFG-004: Resource Exhaustion & Missing Rate Limits
    if is_rule_enabled("CFG-004"):
        def inspect_limits(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if k.lower() in ("rate_limiting", "rate_limit_enabled") and v is False:
                        line_no = None
                        for idx, line in enumerate(raw_lines, 1):
                            if k in line:
                                line_no = idx
                                break
                        findings.append({
                            "rule_id": "CFG-004",
                            "title": "Rate Limiting Explicitly Disabled",
                            "severity": "HIGH",
                            "description": f"Rate limiting configuration '{current_path}' is disabled, exposing safety testing infrastructure to denial of service or resource exhaustion.",
                            "evidence": {
                                "field_path": current_path,
                                "value": str(v),
                                "line_number": line_no
                            },
                            "remediation": "Enable rate limiting and concurrency throttling on test orchestrator endpoints.",
                            "detection_method": "configuration_audit",
                            "confidence": "HIGH",
                            "limitations": "Static inspection of rate limit flags."
                        })
                    elif k.lower() in ("max_tokens", "max_output_tokens") and isinstance(v, (int, float)) and v > 128000:
                        line_no = None
                        for idx, line in enumerate(raw_lines, 1):
                            if k in line:
                                line_no = idx
                                break
                        findings.append({
                            "rule_id": "CFG-004",
                            "title": "Excessive Token Limit Allocation",
                            "severity": "MEDIUM",
                            "description": f"Token limit '{current_path}' is set to {v}, which poses memory exhaustion risk during adversarial prompt evaluations.",
                            "evidence": {
                                "field_path": current_path,
                                "max_tokens": v,
                                "line_number": line_no
                            },
                            "remediation": "Constrain max_tokens to appropriate bounded limits per test run.",
                            "detection_method": "threshold_validation",
                            "confidence": "HIGH",
                            "limitations": "Flags tokens exceeding 128,000 threshold."
                        })
                    else:
                        inspect_limits(v, current_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    inspect_limits(item, f"{path}[{idx}]")

        inspect_limits(data)

    # 5. CFG-005: Prompt & Response Data Logging Risks
    if is_rule_enabled("CFG-005"):
        def inspect_prompt_logging(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    current_path = f"{path}.{k}" if path else k
                    if k.lower() in ("log_full_prompts", "log_raw_payloads", "store_unmasked_prompts") and v is True:
                        line_no = None
                        for idx, line in enumerate(raw_lines, 1):
                            if k in line:
                                line_no = idx
                                break
                        findings.append({
                            "rule_id": "CFG-005",
                            "title": "Unmasked Raw Prompt Logging Enabled",
                            "severity": "MEDIUM",
                            "description": f"Parameter '{current_path}' logs unmasked raw prompt payloads. This can inadvertently leak private test assets or proprietary instructions to general logging sinks.",
                            "evidence": {
                                "field_path": current_path,
                                "value": str(v),
                                "line_number": line_no
                            },
                            "remediation": "Mask sensitive tokens and prompt content prior to persisting debug logs.",
                            "detection_method": "privacy_leak_audit",
                            "confidence": "HIGH",
                            "limitations": "Verifies configuration flags."
                        })
                    else:
                        inspect_prompt_logging(v, current_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    inspect_prompt_logging(item, f"{path}[{idx}]")

        inspect_prompt_logging(data)

    return findings
