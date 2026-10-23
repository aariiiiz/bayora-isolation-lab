import json
import hashlib
from typing import Any, Dict

def canonical_json(data: Dict[str, Any]) -> str:
    """
    Deterministically serializes a dictionary into canonical JSON format:
    - Keys sorted alphabetically
    - No unnecessary whitespace
    - UTF-8 encoding
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def compute_record_hash(prev_hash: str, event_type: str, timestamp_str: str, actor: str, details: Dict[str, Any]) -> str:
    """
    Computes a cryptographic SHA-256 hash chaining this audit event to the previous event.
    """
    payload = {
        "prev_hash": prev_hash,
        "event_type": event_type,
        "timestamp": timestamp_str,
        "actor": actor,
        "details": details
    }
    serialized = canonical_json(payload)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def verify_audit_chain(events: list) -> Dict[str, Any]:
    """
    Iterates through audit events and verifies that:
    1. Each event's record_hash matches the re-computed hash.
    2. Each event's prev_hash matches the previous event's record_hash (first event starts with GENESIS).
    Returns a verification report indicating validity and any broken link found.
    """
    if not events:
        return {"valid": True, "total_verified": 0, "break_detected": False, "message": "Audit chain is empty."}

    prev_hash = "GENESIS"
    for idx, event in enumerate(events):
        expected_prev = prev_hash
        actual_prev = getattr(event, "prev_hash", "")
        if actual_prev != expected_prev:
            return {
                "valid": False,
                "break_detected": True,
                "broken_index": idx,
                "event_id": getattr(event, "id", str(idx)),
                "reason": f"Mismatched prev_hash at event {idx}. Expected {expected_prev}, found {actual_prev}",
                "total_verified": idx
            }
        
        # Verify current record hash
        ts = event.timestamp.isoformat() if hasattr(event.timestamp, "isoformat") else str(event.timestamp)
        details = getattr(event, "details", {})
        computed = compute_record_hash(
            prev_hash=actual_prev,
            event_type=getattr(event, "event_type", ""),
            timestamp_str=ts,
            actor=getattr(event, "actor", ""),
            details=details
        )
        actual_hash = getattr(event, "record_hash", "")
        if computed != actual_hash:
            return {
                "valid": False,
                "break_detected": True,
                "broken_index": idx,
                "event_id": getattr(event, "id", str(idx)),
                "reason": f"Tampered record payload at event {idx}. Hash mismatch.",
                "total_verified": idx
            }
        
        prev_hash = actual_hash

    return {
        "valid": True,
        "break_detected": False,
        "total_verified": len(events),
        "latest_hash": prev_hash,
        "message": f"Cryptographic integrity verified across all {len(events)} events."
    }
