import json
import httpx
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("bayora")

async def generate_ai_threat_advisory(
    experiment_name: str,
    operation: str,
    risk_level: str,
    risk_score: float,
    findings: List[Dict[str, Any]]
) -> str:
    """
    Leverages Groq fast LLM inference (using user's configured Groq API key)
    to generate an in-depth security threat model and mitigation advisory.
    Gracefully falls back to deterministic local synthesis if offline or key is unset.
    """
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.strip() == "":
        return generate_local_threat_advisory(operation, risk_level, findings)

    # Format findings summary for prompt
    findings_summary = []
    for f in findings[:10]: # limit to top 10 to keep prompt concise
        findings_summary.append(
            f"- [{f.get('severity')}] {f.get('rule_id')}: {f.get('title')} - Evidence: {json.dumps(f.get('evidence', {}))}"
        )
    findings_text = "\n".join(findings_summary) if findings_summary else "No security violations detected."

    prompt = f"""You are a Principal AI Safety and Security Engineer at Bayora Isolation Lab.
Review the following security assessment findings from an adversarial AI testing infrastructure:

Experiment: {experiment_name}
Operation: {operation}
Overall Risk Level: {risk_level} (Score: {risk_score}/100)

Findings List:
{findings_text}

Provide a concise, expert security advisory formatted in clean markdown:
1. Threat Model & Attacker Perspective (STRIDE / exploit scenario)
2. Isolation & Safety Impact (Cross-tenant blast radius, data leakage, model compromise)
3. Actionable Hardening Recommendations (Exact config fixes or architectural defenses)
Keep it direct, professional, and evidence-grounded. Do not invent findings not present in the list."""

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are Bayora Isolation Lab's Senior AI Safety & Infrastructure Security Advisor."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1024
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                logger.warning(f"Groq API returned status {response.status_code}: {response.text}")
                return generate_local_threat_advisory(operation, risk_level, findings)
    except Exception as e:
        logger.warning(f"Failed to query Groq API: {str(e)}. Falling back to deterministic local analysis.")
        return generate_local_threat_advisory(operation, risk_level, findings)

def generate_local_threat_advisory(operation: str, risk_level: str, findings: List[Dict[str, Any]]) -> str:
    """
    Deterministic offline synthesis of threat intel and mitigation plan.
    """
    total = len(findings)
    critical_count = sum(1 for f in findings if f.get("severity") == "CRITICAL")
    high_count = sum(1 for f in findings if f.get("severity") == "HIGH")

    return f"""### Bayora Threat Model & Remediation Advisory (Deterministic Engine)

**Operational Review:** `{operation}` | **Assessment:** `{risk_level}`
**Evaluated Findings:** {total} total ({critical_count} Critical, {high_count} High)

#### 1. Threat Modeling & Blast Radius
- **Tenant Isolation Boundaries:** {'Identified severe gaps in tenant partitioning and access boundaries.' if critical_count > 0 else 'Baseline tenant boundaries are intact, with secondary configuration risks identified.'}
- **Adversarial Exploitation Vectors:** Testing harnesses exposed to unauthenticated impersonation or wildcard permissions risk enabling cross-tenant data exfiltration or state poisoning during multi-tenant red-team drills.

#### 2. Defense-in-Depth Mitigation Strategy
1. **Enforce Cryptographic Scoping:** Bind all session tokens and workspace paths to explicit tenant UUIDs rather than shared filesystem mountpoints.
2. **Harden Audit Pipeline:** Ensure continuous cryptographic SHA-256 hash chaining on all audit streams to guarantee tamper-evidence under forensic scrutiny.
3. **Strict Least Privilege:** Deprecate all wildcard (`*`) role definitions and enforce explicit capability-based security tokens.
"""
