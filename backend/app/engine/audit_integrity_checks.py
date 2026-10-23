import json
import re
from datetime import datetime
from typing import List, Dict, Any
from app.engine.artifact_parser import ParsedArtifact
from app.utils.crypto import compute_record_hash

REQUIRED_AUDIT_FIELDS = ["event_id", "timestamp", "event_type", "actor"]
ALIAS_FIELDS = {
    "event_id": ["id", "event_id", "record_id", "uuid"],
    "timestamp": ["timestamp", "time", "created_at", "ts"],
    "event_type": ["event_type", "action", "operation", "type"],
    "actor": ["actor", "user", "user_id", "principal", "subject"]
}

def check_audit_log_integrity(parsed: ParsedArtifact, profile: str = "strict", active_policies: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Operation B: Audit log integrity review.
    Validates the structure of supplied audit records, detects missing required fields,
    malformed timestamps, duplicate event identifiers, and broken hash-chain links.
    """
    findings = []
    active_policies = active_policies or {}

    def is_rule_enabled(rule_id: str) -> bool:
        if rule_id in active_policies:
            return active_policies[rule_id].get("is_enabled", True)
        return True

    # Extract records list
    raw_data = parsed.structured_data
    records = []
    if isinstance(raw_data, list):
        for idx, item in enumerate(raw_data):
            if isinstance(item, dict) and "data" in item and "line_number" in item:
                # jsonl structure
                records.append((item["line_number"], item["data"]))
            elif isinstance(item, dict) and "data" in item and "row_number" in item:
                # csv structure
                records.append((item["row_number"], item["data"]))
            elif isinstance(item, dict):
                records.append((idx + 1, item))
    elif isinstance(raw_data, dict):
        # Could be { "events": [...] } or { "logs": [...] }
        for key in ("events", "logs", "records", "audit_trail"):
            if key in raw_data and isinstance(raw_data[key], list):
                for idx, item in enumerate(raw_data[key]):
                    records.append((idx + 1, item))
                break
        if not records:
            # Single object audit record
            records.append((1, raw_data))

    if not records:
        findings.append({
            "rule_id": "AUD-000",
            "title": "No Parseable Audit Records Found",
            "severity": "HIGH",
            "description": "Artifact was parsed but no recognizable list of audit records or events was identified.",
            "evidence": {"raw_lines_count": len(parsed.raw_lines)},
            "remediation": "Provide an audit artifact formatted as a JSON list of objects, JSONL lines, or CSV rows.",
            "detection_method": "structure_inspection",
            "confidence": "HIGH",
            "limitations": "Requires standard event object collections."
        })
        return findings

    seen_event_ids = {}
    prev_chain_hash = "GENESIS"
    has_hash_chain = False

    for line_or_row, rec in records:
        if not isinstance(rec, dict):
            continue

        # 1. AUD-001: Missing Required Audit Fields
        if is_rule_enabled("AUD-001"):
            missing = []
            for field, aliases in ALIAS_FIELDS.items():
                if not any(a in rec and rec[a] not in (None, "") for a in aliases):
                    missing.append(field)
            if missing:
                findings.append({
                    "rule_id": "AUD-001",
                    "title": "Audit Record Missing Mandatory Audit Fields",
                    "severity": "HIGH",
                    "description": f"Record at entry {line_or_row} is missing required audit attributes: {', '.join(missing)}.",
                    "evidence": {
                        "entry": line_or_row,
                        "record_snippet": str(rec)[:200],
                        "missing_fields": missing
                    },
                    "remediation": f"Ensure all audit logs record {', '.join(REQUIRED_AUDIT_FIELDS)} for complete non-repudiation.",
                    "detection_method": "schema_completeness_validation",
                    "confidence": "HIGH",
                    "limitations": "Evaluates schema fields against baseline audit taxonomy."
                })

        # 2. AUD-002: Malformed or Non-Chronological Timestamps
        if is_rule_enabled("AUD-002"):
            ts_val = None
            for alias in ALIAS_FIELDS["timestamp"]:
                if alias in rec and rec[alias]:
                    ts_val = str(rec[alias])
                    break
            if ts_val:
                try:
                    # Try ISO 8601 parse
                    cleaned_ts = ts_val.replace("Z", "+00:00")
                    parsed_dt = datetime.fromisoformat(cleaned_ts)
                    # Check future timestamp
                    if parsed_dt.year > 2035:
                        findings.append({
                            "rule_id": "AUD-002",
                            "title": "Anomalous Future Timestamp in Audit Record",
                            "severity": "MEDIUM",
                            "description": f"Record at entry {line_or_row} has anomalous timestamp '{ts_val}' set far in the future.",
                            "evidence": {"entry": line_or_row, "timestamp": ts_val},
                            "remediation": "Sync host clock via NTP and enforce server-generated UTC timestamps.",
                            "detection_method": "timestamp_heuristic_validation",
                            "confidence": "HIGH",
                            "limitations": "Only flags future timestamps beyond reasonable threshold."
                        })
                except ValueError:
                    findings.append({
                        "rule_id": "AUD-002",
                        "title": "Malformed Non-ISO8601 Timestamp Detected",
                        "severity": "MEDIUM",
                        "description": f"Record at entry {line_or_row} has unparseable timestamp format: '{ts_val}'.",
                        "evidence": {"entry": line_or_row, "timestamp": ts_val},
                        "remediation": "Format all audit timestamps in standard ISO 8601 (YYYY-MM-DDTHH:MM:SSZ).",
                        "detection_method": "format_validation",
                        "confidence": "HIGH",
                        "limitations": "Attempts standard ISO 8601 format verification."
                    })

        # 3. AUD-003: Duplicate Event Identifiers
        if is_rule_enabled("AUD-003"):
            eid = None
            for alias in ALIAS_FIELDS["event_id"]:
                if alias in rec and rec[alias]:
                    eid = str(rec[alias])
                    break
            if eid:
                if eid in seen_event_ids:
                    findings.append({
                        "rule_id": "AUD-003",
                        "title": "Duplicate Audit Event Identifier Detected",
                        "severity": "HIGH",
                        "description": f"Event ID '{eid}' at entry {line_or_row} was previously observed at entry {seen_event_ids[eid]}. Indicates log replay or collision.",
                        "evidence": {
                            "duplicate_event_id": eid,
                            "first_seen_entry": seen_event_ids[eid],
                            "duplicate_entry": line_or_row
                        },
                        "remediation": "Use universally unique identifiers (UUIDv4) for all audit records.",
                        "detection_method": "collision_analysis",
                        "confidence": "HIGH",
                        "limitations": "Checks for ID uniqueness within the supplied artifact scope."
                    })
                else:
                    seen_event_ids[eid] = line_or_row

        # 4. AUD-004: Hash-Chain Integrity Verification (if present)
        if "prev_hash" in rec or "record_hash" in rec or "hash" in rec:
            has_hash_chain = True
            rec_prev = rec.get("prev_hash")
            rec_hash = rec.get("record_hash") or rec.get("hash")

            if is_rule_enabled("AUD-004"):
                if rec_prev is not None and rec_prev != prev_chain_hash:
                    findings.append({
                        "rule_id": "AUD-004",
                        "title": "Broken Cryptographic Hash Chain Link Detected",
                        "severity": "CRITICAL",
                        "description": f"Tamper evidence: Record at entry {line_or_row} references prev_hash '{rec_prev}', but expected '{prev_chain_hash}'. The log history was broken or modified.",
                        "evidence": {
                            "entry": line_or_row,
                            "expected_prev_hash": prev_chain_hash,
                            "actual_prev_hash": rec_prev,
                            "record_hash": rec_hash
                        },
                        "remediation": "Investigate potential audit record truncation, deletion, or tampering. Re-establish chain verification from secure cold storage.",
                        "detection_method": "cryptographic_chain_verification",
                        "confidence": "HIGH",
                        "limitations": "Verifies cryptographic chain against previous record hash."
                    })
                if rec_hash:
                    prev_chain_hash = rec_hash

        # 5. AUD-005: Anonymous or Unauthenticated Privilege Operation
        if is_rule_enabled("AUD-005"):
            actor = None
            for alias in ALIAS_FIELDS["actor"]:
                if alias in rec:
                    actor = str(rec[alias]).strip().lower()
                    break
            action = str(rec.get("action") or rec.get("event_type") or "").lower()
            if actor in ("anonymous", "null", "undefined", "unknown", "") and any(term in action for term in ("modify", "delete", "create", "grant", "exec")):
                findings.append({
                    "rule_id": "AUD-005",
                    "title": "Anonymous Actor Performed Sensitive Security Operation",
                    "severity": "HIGH",
                    "description": f"Sensitive action '{action}' at entry {line_or_row} was logged without a verified actor identity.",
                    "evidence": {"entry": line_or_row, "actor": actor, "action": action},
                    "remediation": "Enforce authenticated identity context on all state-modifying endpoints before generating audit events.",
                    "detection_method": "heuristic_privilege_correlation",
                    "confidence": "HIGH",
                    "limitations": "Relies on declared event action naming."
                })

    return findings
