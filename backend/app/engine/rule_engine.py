from typing import List, Dict, Any, Tuple
from app.engine.artifact_parser import ParsedArtifact
from app.engine.isolation_checks import check_isolation_and_access
from app.engine.audit_integrity_checks import check_audit_log_integrity
from app.engine.prompt_security_checks import check_prompt_security
from app.engine.configuration_checks import check_configuration_risks
from app.engine.risk_scorer import calculate_risk_score
from app.core.errors import BayoraException

VALID_OPERATIONS = {
    "isolation_access": ("Isolation & Access-Control Review", check_isolation_and_access),
    "audit_integrity": ("Audit Log Integrity Review", check_audit_log_integrity),
    "prompt_injection": ("Prompt-Injection & Adversarial Input Review", check_prompt_security),
    "config_risk": ("Configuration Risk Review", check_configuration_risks)
}

def execute_analysis(
    parsed: ParsedArtifact,
    operation: str,
    profile: str = "strict",
    parameters: Dict[str, Any] = None,
    active_policies: Dict[str, Any] = None
) -> Tuple[List[Dict[str, Any]], float, str, Dict[str, Any]]:
    """
    Coordinates execution of security checks for the selected operation.
    Returns:
    - findings: List of evidence-based finding objects
    - risk_score: 0.0 to 100.0
    - risk_level: CLEAN, LOW, MEDIUM, HIGH, CRITICAL
    - summary: counts by severity and execution metadata
    """
    if operation not in VALID_OPERATIONS:
        raise BayoraException(
            f"Unsupported operation '{operation}'. Supported operations: {list(VALID_OPERATIONS.keys())}",
            status_code=400
        )

    op_name, check_func = VALID_OPERATIONS[operation]
    
    # Execute deterministic rule inspection
    findings = check_func(parsed=parsed, profile=profile, active_policies=active_policies)

    # Calculate risk score
    risk_score, risk_level, counts = calculate_risk_score(findings)

    summary = {
        "operation": operation,
        "operation_name": op_name,
        "profile": profile,
        "total_findings": len(findings),
        "critical": counts["CRITICAL"],
        "high": counts["HIGH"],
        "medium": counts["MEDIUM"],
        "low": counts["LOW"],
        "info": counts["INFO"],
        "artifact_type": parsed.artifact_type,
        "raw_lines_analyzed": len(parsed.raw_lines)
    }

    return findings, risk_score, risk_level, summary
