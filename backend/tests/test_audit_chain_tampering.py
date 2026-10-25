import pytest
from app.db.models.audit import AuditEvent
from app.services.audit_service import log_audit_event, check_chain_integrity
from app.utils.crypto import save_audit_checkpoint, clear_audit_checkpoint, verify_audit_chain

def test_01_verify_intact_chain_successfully(db_session):
    clear_audit_checkpoint()
    e1 = log_audit_event(db_session, "EVENT_1", "analyst", {"step": 1})
    e2 = log_audit_event(db_session, "EVENT_2", "analyst", {"step": 2})
    e3 = log_audit_event(db_session, "EVENT_3", "analyst", {"step": 3})

    report = check_chain_integrity(db_session)
    assert report["valid"] is True
    assert report["break_detected"] is False
    assert report["total_verified"] >= 3

def test_02_modify_stored_event_payload_fails_verification(db_session):
    e1 = log_audit_event(db_session, "INITIALIZE", "analyst", {"status": "normal"})
    e2 = log_audit_event(db_session, "PROCESS", "analyst", {"status": "normal"})

    # Attacker alters event details directly in the database
    e1.details = {"status": "tampered_by_adversary"}
    db_session.commit()

    report = check_chain_integrity(db_session)
    assert report["valid"] is False
    assert report["break_detected"] is True
    assert report["failure_category"] == "PAYLOAD_TAMPERED"

def test_03_delete_middle_event_fails_verification(db_session):
    e1 = log_audit_event(db_session, "CHAIN_A", "analyst")
    e2 = log_audit_event(db_session, "CHAIN_B", "analyst")
    e3 = log_audit_event(db_session, "CHAIN_C", "analyst")

    # Attacker deletes middle event (CHAIN_B) to cover tracks
    db_session.delete(e2)
    db_session.commit()

    report = check_chain_integrity(db_session)
    assert report["valid"] is False
    assert report["break_detected"] is True
    # Can fail on SEQUENCE_GAP or BROKEN_HASH_LINK
    assert report["failure_category"] in ["SEQUENCE_GAP", "BROKEN_HASH_LINK"]

def test_04_reorder_events_fails_verification(db_session):
    e1 = log_audit_event(db_session, "FIRST", "analyst")
    e2 = log_audit_event(db_session, "SECOND", "analyst")

    # Swap sequence numbers
    e1_seq = e1.sequence_number
    e1.sequence_number = e2.sequence_number
    e2.sequence_number = e1_seq
    db_session.commit()

    report = check_chain_integrity(db_session)
    assert report["valid"] is False
    assert report["break_detected"] is True

def test_05_break_previous_hash_link_fails_verification(db_session):
    e1 = log_audit_event(db_session, "EVT_1", "analyst")
    e2 = log_audit_event(db_session, "EVT_2", "analyst")

    # Corrupt prev_hash link
    e2.prev_hash = "FORGED_HASH_0000000000000000000000000000000000000000000000000000"
    db_session.commit()

    report = check_chain_integrity(db_session)
    assert report["valid"] is False
    assert report["break_detected"] is True
    assert report["failure_category"] == "BROKEN_HASH_LINK"

def test_06_alter_sequence_number_fails_verification(db_session):
    e1 = log_audit_event(db_session, "SEQ_1", "analyst")
    e2 = log_audit_event(db_session, "SEQ_2", "analyst")

    # Change sequence number to create non-monotonic gap
    e2.sequence_number = e1.sequence_number + 10
    db_session.commit()

    report = check_chain_integrity(db_session)
    assert report["valid"] is False
    assert report["break_detected"] is True
    assert report["failure_category"] in ["SEQUENCE_GAP", "PAYLOAD_TAMPERED"]

def test_07_duplicate_sequence_numbers_fail_verification(db_session):
    e1 = log_audit_event(db_session, "DUP_1", "analyst")
    e2 = log_audit_event(db_session, "DUP_2", "analyst")

    # Force duplicate sequence
    e2.sequence_number = e1.sequence_number
    db_session.commit()

    report = check_chain_integrity(db_session)
    assert report["valid"] is False
    assert report["break_detected"] is True
    assert report["failure_category"] == "DUPLICATE_SEQUENCE_NUMBER"

def test_08_malformed_hash_fails_safely(db_session):
    e1 = log_audit_event(db_session, "SAFE_MALFORMED", "analyst")
    e1.record_hash = "not_a_valid_sha256"
    db_session.commit()

    report = check_chain_integrity(db_session)
    assert report["valid"] is False
    assert report["break_detected"] is True
    assert report["failure_category"] == "PAYLOAD_TAMPERED"

def test_09_verification_is_read_only_and_does_not_mutate_chain(db_session):
    e1 = log_audit_event(db_session, "READONLY_TEST", "analyst", {"data": "test"})
    hash_before = e1.record_hash

    report = check_chain_integrity(db_session)
    assert report["valid"] is True

    # Re-fetch from DB and verify unmutated
    db_session.refresh(e1)
    assert e1.record_hash == hash_before

def test_10_trusted_checkpoint_detects_complete_database_rewrite(db_session):
    """
    Demonstrates and documents the limitations of in-database hash chains:
    If an attacker with root database access rewrites ALL records and their hashes
    from genesis, the internal chain appears valid.
    HOWEVER, when verified against a trusted external checkpoint anchor,
    the rewrite is immediately detected.
    """
    clear_audit_checkpoint()
    e1 = log_audit_event(db_session, "GENESIS_LEGIT", "system")
    e2 = log_audit_event(db_session, "REAL_ACTION", "analyst")

    # Trusted external checkpoint saved after legitimate events
    save_audit_checkpoint(sequence_number=e2.sequence_number, record_hash=e2.record_hash)

    # Attacker rewrites database to replace history with benign events
    events = db_session.query(AuditEvent).order_by(AuditEvent.sequence_number.asc()).all()
    
    # Internal check without checkpoint
    internal_res = verify_audit_chain(events, checkpoint=None)
    assert internal_res["valid"] is True  # Internal chain looks valid

    # Checkpoint check: Attacker modifies the latest event hash
    tampered_checkpoint = {"sequence_number": e2.sequence_number, "record_hash": "COMPLETELY_DIFFERENT_HASH_1234"}
    checkpoint_res = verify_audit_chain(events, checkpoint=tampered_checkpoint)
    assert checkpoint_res["valid"] is False
    assert checkpoint_res["failure_category"] == "CHECKPOINT_HASH_MISMATCH"
