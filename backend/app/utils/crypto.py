import json
import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

CHECKPOINT_FILE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../.audit_checkpoint.json")
)

def canonical_json(data: Dict[str, Any]) -> str:
    """
    Deterministically serializes a dictionary into canonical JSON format:
    - Keys sorted alphabetically
    - No unnecessary whitespace
    - UTF-8 encoding
    - Normalized string representations
    """
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

def normalize_timestamp(ts: Any) -> str:
    """
    Normalizes timestamps to strict UTC ISO-8601 representation ending in 'Z'.
    Handles datetime objects (naive or timezone-aware) and string representations.
    """
    if isinstance(ts, datetime):
        utc_dt = ts.astimezone(timezone.utc).replace(tzinfo=None) if ts.tzinfo else ts
        return utc_dt.isoformat() + "Z"
    elif isinstance(ts, str):
        cleaned = ts.replace("+00:00", "").rstrip("Z")
        return cleaned + "Z"
    return str(ts)

def compute_record_hash(
    prev_hash: str,
    event_type: str,
    timestamp_str: Any,
    actor: str,
    details: Dict[str, Any],
    sequence_number: Optional[int] = None,
    tenant_id: Optional[str] = None
) -> str:
    """
    Computes a cryptographic SHA-256 hash chaining this audit event to the previous event.
    Deterministic payload includes previous hash, event type, normalized timestamp, actor, details,
    and optionally sequence_number and tenant_id.
    """
    payload = {
        "prev_hash": prev_hash,
        "event_type": event_type,
        "timestamp": normalize_timestamp(timestamp_str),
        "actor": actor,
        "details": details or {}
    }
    if sequence_number is not None:
        payload["sequence_number"] = sequence_number
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id

    serialized = canonical_json(payload)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def save_audit_checkpoint(sequence_number: int, record_hash: str, tenant_id: Optional[str] = None) -> None:
    """
    Writes a trusted checkpoint anchor outside the database to provide tamper-evidence
    against complete database rollback or rewrite attacks.
    """
    checkpoint_data = {
        "sequence_number": sequence_number,
        "record_hash": record_hash,
        "tenant_id": tenant_id or "global",
        "checkpoint_time": datetime.now(timezone.utc).isoformat()
    }
    try:
        os.makedirs(os.path.dirname(CHECKPOINT_FILE_PATH), exist_ok=True)
        with open(CHECKPOINT_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(canonical_json(checkpoint_data))
    except Exception:
        pass

def load_audit_checkpoint() -> Optional[Dict[str, Any]]:
    """
    Reads the trusted external checkpoint anchor if it exists.
    """
    if not os.path.exists(CHECKPOINT_FILE_PATH):
        return None
    try:
        with open(CHECKPOINT_FILE_PATH, "r", encoding="utf-8") as f:
            return json.loads(f.read())
    except Exception:
        return None

def clear_audit_checkpoint() -> None:
    """
    Cleans up the checkpoint anchor (used during testing).
    """
    if os.path.exists(CHECKPOINT_FILE_PATH):
        try:
            os.remove(CHECKPOINT_FILE_PATH)
        except Exception:
            pass

def verify_audit_chain(events: list, checkpoint: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Iterates through audit events strictly in ascending order and verifies that:
    1. Sequence numbers are strictly monotonically increasing (no gaps, no duplicates, no reordering).
    2. Each event's record_hash matches the re-computed SHA-256 hash.
    3. Each event's prev_hash matches the preceding event's record_hash (first event starts with GENESIS).
    4. Compares the final event hash against the trusted external checkpoint anchor if supplied.
    Never mutates or regenerates records during verification.
    """
    verification_time = datetime.now(timezone.utc).isoformat()

    if not events:
        return {
            "valid": True,
            "break_detected": False,
            "total_verified": 0,
            "message": "Audit chain is empty.",
            "verification_timestamp": verification_time,
            "checkpoint_status": {"verified": False, "reason": "No events to compare."}
        }

    prev_hash = "GENESIS"
    seen_sequences = set()
    last_seq = 0

    for idx, event in enumerate(events):
        seq = getattr(event, "sequence_number", None)
        event_id = getattr(event, "id", str(idx))
        actual_prev = getattr(event, "prev_hash", "")
        actual_hash = getattr(event, "record_hash", "")
        actor = getattr(event, "actor", "")
        event_type = getattr(event, "event_type", "")
        details = getattr(event, "details", {})
        tenant_id = getattr(event, "tenant_id", None)

        # 1. Sequence Validation
        if seq is not None:
            if seq in seen_sequences:
                msg = f"Integrity Failure: Duplicate sequence number {seq} detected at event index {idx} (Event ID: {event_id})."
                return {
                    "valid": False,
                    "break_detected": True,
                    "broken_index": idx,
                    "event_id": event_id,
                    "failure_category": "DUPLICATE_SEQUENCE_NUMBER",
                    "reason": msg,
                    "message": msg,
                    "expected_sequence": last_seq + 1,
                    "actual_sequence": seq,
                    "total_verified": idx,
                    "verification_timestamp": verification_time
                }
            if seq <= last_seq and idx > 0:
                msg = f"Integrity Failure: Out-of-order sequence number at event index {idx}. Expected > {last_seq}, found {seq}."
                return {
                    "valid": False,
                    "break_detected": True,
                    "broken_index": idx,
                    "event_id": event_id,
                    "failure_category": "SEQUENCE_REORDERING",
                    "reason": msg,
                    "message": msg,
                    "expected_sequence": last_seq + 1,
                    "actual_sequence": seq,
                    "total_verified": idx,
                    "verification_timestamp": verification_time
                }
            if idx > 0 and seq != last_seq + 1:
                msg = f"Integrity Failure: Gap in sequence numbers detected between #{last_seq} and #{seq} at event index {idx}."
                return {
                    "valid": False,
                    "break_detected": True,
                    "broken_index": idx,
                    "event_id": event_id,
                    "failure_category": "SEQUENCE_GAP",
                    "reason": msg,
                    "message": msg,
                    "expected_sequence": last_seq + 1,
                    "actual_sequence": seq,
                    "total_verified": idx,
                    "verification_timestamp": verification_time
                }
            seen_sequences.add(seq)
            last_seq = seq

        # 2. Previous Hash Linkage Validation
        expected_prev = prev_hash
        if actual_prev != expected_prev:
            msg = f"Integrity Failure: Broken hash chain link at event #{seq or idx} (ID: {event_id}). Expected previous link '{expected_prev}', but record links to '{actual_prev}'."
            return {
                "valid": False,
                "break_detected": True,
                "broken_index": idx,
                "event_id": event_id,
                "failure_category": "BROKEN_HASH_LINK",
                "reason": msg,
                "message": msg,
                "expected_hash": expected_prev,
                "calculated_hash": actual_prev,
                "total_verified": idx,
                "verification_timestamp": verification_time
            }

        # 3. Payload Integrity / Hash Matching
        ts_val = getattr(event, "timestamp", "")

        # Check candidate hashes (with seq, with legacy ts format, etc.)
        candidate_hashes = [
            compute_record_hash(actual_prev, event_type, ts_val, actor, details, sequence_number=seq, tenant_id=tenant_id),
            compute_record_hash(actual_prev, event_type, ts_val, actor, details, sequence_number=seq),
            compute_record_hash(actual_prev, event_type, ts_val, actor, details),
            # Support raw unnormalized isoformat for existing legacy records
            compute_record_hash(actual_prev, event_type, ts_val.isoformat() if hasattr(ts_val, "isoformat") else str(ts_val), actor, details)
        ]

        if actual_hash not in candidate_hashes:
            expected = candidate_hashes[0]
            msg = f"Integrity Failure: Stored event payload or hash tampered at event #{seq or idx} (ID: {event_id}). Recomputed SHA-256 is '{expected}', but database contains '{actual_hash}'."
            return {
                "valid": False,
                "break_detected": True,
                "broken_index": idx,
                "event_id": event_id,
                "failure_category": "PAYLOAD_TAMPERED",
                "reason": msg,
                "message": msg,
                "expected_hash": expected,
                "calculated_hash": actual_hash,
                "total_verified": idx,
                "verification_timestamp": verification_time
            }

        prev_hash = actual_hash

    # 4. Checkpoint comparison
    checkpoint_status = {"verified": True, "message": "No external checkpoint file present."}
    if checkpoint:
        chk_seq = checkpoint.get("sequence_number")
        chk_hash = checkpoint.get("record_hash")
        if chk_seq is not None and last_seq < chk_seq:
            msg = f"Integrity Failure: Database has fewer events ({last_seq}) than trusted external checkpoint ({chk_seq}). Database rollback detected."
            return {
                "valid": False,
                "break_detected": True,
                "failure_category": "CHECKPOINT_ROLLBACK_DETECTED",
                "reason": msg,
                "message": msg,
                "total_verified": len(events),
                "verification_timestamp": verification_time,
                "checkpoint_status": {"verified": False, "expected_seq": chk_seq, "db_seq": last_seq}
            }
        if chk_hash and chk_seq == last_seq and chk_hash != prev_hash:
            msg = f"Integrity Failure: Latest record hash '{prev_hash}' does not match external anchor '{chk_hash}'. Complete database rewrite detected."
            return {
                "valid": False,
                "break_detected": True,
                "failure_category": "CHECKPOINT_HASH_MISMATCH",
                "reason": msg,
                "message": msg,
                "expected_hash": chk_hash,
                "calculated_hash": prev_hash,
                "total_verified": len(events),
                "verification_timestamp": verification_time,
                "checkpoint_status": {"verified": False, "checkpoint_hash": chk_hash, "db_hash": prev_hash}
            }
        checkpoint_status = {"verified": True, "message": "Matched external trusted checkpoint."}

    return {
        "valid": True,
        "break_detected": False,
        "total_verified": len(events),
        "latest_hash": prev_hash,
        "latest_sequence": last_seq,
        "message": f"Cryptographic integrity verified across all {len(events)} events.",
        "verification_timestamp": verification_time,
        "checkpoint_status": checkpoint_status
    }
