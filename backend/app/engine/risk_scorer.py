from typing import List, Dict, Any, Tuple

SEVERITY_WEIGHTS = {
    "CRITICAL": 35.0,
    "HIGH": 18.0,
    "MEDIUM": 8.0,
    "LOW": 3.0,
    "INFO": 0.0
}

def calculate_risk_score(findings: List[Dict[str, Any]]) -> Tuple[float, str, Dict[str, int]]:
    """
    Computes deterministic risk score (0-100), risk level category,
    and severity counts from a list of findings.
    """
    counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
        "INFO": 0
    }

    raw_score = 0.0
    for finding in findings:
        sev = str(finding.get("severity", "LOW")).upper()
        if sev not in counts:
            sev = "LOW"
        counts[sev] += 1
        raw_score += SEVERITY_WEIGHTS.get(sev, 0.0)

    # Normalized score clamped to 100.0
    normalized_score = min(100.0, round(raw_score, 1))

    # Categorize Risk Level
    if counts["CRITICAL"] > 0 or normalized_score >= 80.0:
        risk_level = "CRITICAL"
    elif counts["HIGH"] > 0 or normalized_score >= 50.0:
        risk_level = "HIGH"
    elif counts["MEDIUM"] > 0 or normalized_score >= 25.0:
        risk_level = "MEDIUM"
    elif counts["LOW"] > 0 or normalized_score > 0.0:
        risk_level = "LOW"
    else:
        risk_level = "CLEAN"

    return normalized_score, risk_level, counts
