from datetime import datetime, timezone
from typing import Dict, Any, List
from app.core.config import settings

def build_compliance_notes(operation: str) -> str:
    mapping = {
        "isolation_access": "Evaluated against ISO/IEC 27001:2022 A.8.2 (Privileged Access Rights), A.8.3 (Information Access Restriction) and NIST SP 800-53 AC-3 (Access Enforcement).",
        "audit_integrity": "Evaluated against NIST SP 800-53 AU-9 (Protection of Audit Information) and SOC 2 Trust Services Criteria CC6.8 / CC7.2.",
        "prompt_injection": "Evaluated against OWASP Top 10 for LLM Applications (LLM01: Prompt Injection) and NIST AI Risk Management Framework (AI RMF 1.0).",
        "config_risk": "Evaluated against CIS Critical Security Controls v8 Control 4 (Secure Configuration of Enterprise Assets and Software)."
    }
    return mapping.get(operation, "Standard baseline security evaluation.")

def generate_experiment_report(experiment_data: Dict[str, Any], findings_data: List[Dict[str, Any]], audit_chain_status: str = "VERIFIED") -> Dict[str, Any]:
    """
    Generates a formal, downloadable JSON security validation report.
    """
    operation = experiment_data.get("operation", "isolation_access")
    
    limitations = [
        "Static configuration and rule-based inspection validates declared settings and known signature patterns.",
        "Deterministic local screening does not simulate dynamic runtime execution or arbitrary third-party cloud provider RBAC engines.",
        "Adversarial prompt screening identifies known heuristic override constructs; novel adaptive evasion techniques require continuous red-teaming.",
        "Evidence gathered reflects state at analysis time. Any subsequent artifact or environment modification invalidates this assessment."
    ]

    report = {
        "report_id": f"REP-{experiment_data.get('id', 'unknown')[:8]}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": settings.PROJECT_NAME,
        "platform_version": settings.VERSION,
        "experiment": {
            "id": experiment_data.get("id"),
            "name": experiment_data.get("name"),
            "environment": experiment_data.get("environment"),
            "operation": operation,
            "profile": experiment_data.get("profile"),
            "description": experiment_data.get("description"),
            "artifact_filename": experiment_data.get("artifact_filename"),
            "artifact_type": experiment_data.get("artifact_type"),
            "status": experiment_data.get("status"),
            "risk_score": experiment_data.get("risk_score"),
            "risk_level": experiment_data.get("risk_level"),
            "created_at": str(experiment_data.get("created_at")),
            "completed_at": str(experiment_data.get("updated_at"))
        },
        "risk_summary": experiment_data.get("summary", {}),
        "findings_count": len(findings_data),
        "findings": findings_data,
        "ai_analysis": experiment_data.get("ai_analysis"),
        "compliance_notes": build_compliance_notes(operation),
        "audit_chain_status": audit_chain_status,
        "limitations_and_residual_risks": limitations
    }

    return report
