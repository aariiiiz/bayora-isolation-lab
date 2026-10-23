from datetime import datetime
from app.db.models.audit import AuditEvent
from app.utils.crypto import compute_record_hash, verify_audit_chain
from app.services.audit_service import log_audit_event, check_chain_integrity

def test_audit_hash_chain_verification_clean(db_session):
    # Log 3 events
    e1 = log_audit_event(db_session, "EVENT_A", "analyst", {"note": "first"})
    e2 = log_audit_event(db_session, "EVENT_B", "analyst", {"note": "second"})
    e3 = log_audit_event(db_session, "EVENT_C", "analyst", {"note": "third"})

    assert e1.prev_hash is not None
    assert e2.prev_hash == e1.record_hash
    assert e3.prev_hash == e2.record_hash

    # Verify chain
    result = check_chain_integrity(db_session)
    assert result["valid"] is True
    assert result["break_detected"] is False
    assert result["total_verified"] >= 3

def test_audit_hash_chain_detects_tampering(db_session):
    e1 = log_audit_event(db_session, "INIT", "system", {"val": 1})
    e2 = log_audit_event(db_session, "ACTION", "system", {"val": 2})

    # Tamper with e2's record_hash directly in DB
    e2.record_hash = "FORGED_HASH_ATTACKER_OVERWRITE_0000000000000000000000000000"
    db_session.commit()

    result = check_chain_integrity(db_session)
    assert result["valid"] is False
    assert result["break_detected"] is True
