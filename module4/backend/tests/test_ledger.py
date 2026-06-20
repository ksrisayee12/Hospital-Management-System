"""
Tests for blockchain/ledger.py — verify_chain both tamper failure modes.
"""

import hashlib
import json
from datetime import datetime

import pytest

from module4.backend.blockchain.ledger import GENESIS_HASH, _compute_hash, append_event, verify_chain
from module4.backend.models.ledger_event import LedgerEvent


def _seed_events(db_session, n: int = 3) -> list[LedgerEvent]:
    """Append n legitimate events to the ledger."""
    events = []
    for i in range(n):
        e = append_event(db_session, "TEST_EVENT", {"index": i, "user_id": "doctor-x"})
        events.append(e)
    return events


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_verify_chain_empty(db_session):
    result = verify_chain(db_session)
    assert result["valid"] is True
    assert result["total_events"] == 0


def test_verify_chain_intact(db_session):
    _seed_events(db_session, 5)
    result = verify_chain(db_session)
    assert result["valid"] is True
    assert result["total_events"] == 5


# ---------------------------------------------------------------------------
# Tamper detection — FAILURE MODE 1: previous_hash mismatch
# ---------------------------------------------------------------------------

def test_verify_chain_detects_previous_hash_tampering(db_session):
    """
    Directly corrupt the previous_hash of the second ledger event.
    This breaks the chain link between events 1 and 2.
    verify_chain() must return valid=False with the correct broken_at_sequence.
    """
    events = _seed_events(db_session, 3)

    # Tamper: overwrite the second event's previous_hash with garbage
    event2 = db_session.query(LedgerEvent).filter_by(sequence_number=2).first()
    event2.previous_hash = "deadbeef" * 8  # 64 chars, but wrong
    db_session.commit()

    result = verify_chain(db_session)
    assert result["valid"] is False
    assert result["broken_at_sequence"] == 2
    assert "previous_hash mismatch" in result["reason"]


# ---------------------------------------------------------------------------
# Tamper detection — FAILURE MODE 2: event_data tampered
# ---------------------------------------------------------------------------

def test_verify_chain_detects_event_data_tampering(db_session):
    """
    Directly corrupt the event_data of an existing ledger event without
    updating its current_hash. This simulates a direct DB-level edit
    (the most likely attack vector against the hash chain).
    verify_chain() must recompute the hash and detect the mismatch.
    """
    events = _seed_events(db_session, 3)

    # Tamper: change event_data of the first event without fixing current_hash
    event1 = db_session.query(LedgerEvent).filter_by(sequence_number=1).first()
    original_data = json.loads(event1.event_data)
    original_data["TAMPERED"] = True
    event1.event_data = json.dumps(original_data, sort_keys=True)
    db_session.commit()

    result = verify_chain(db_session)
    assert result["valid"] is False
    assert result["broken_at_sequence"] == 1
    assert "current_hash mismatch" in result["reason"]


def test_verify_chain_detects_both_modes_independently(db_session):
    """
    Confirm the two failure modes are truly independent:
    event_data tampering triggers failure mode 2, not failure mode 1.
    """
    _seed_events(db_session, 2)
    event2 = db_session.query(LedgerEvent).filter_by(sequence_number=2).first()
    # Tamper only event_data, leave previous_hash alone
    event2.event_data = json.dumps({"INJECTED": "malicious_data"})
    db_session.commit()

    result = verify_chain(db_session)
    assert result["valid"] is False
    assert result["reason"] == "current_hash mismatch — event data tampered"


def test_append_event_links_correctly(db_session):
    """Each new event's previous_hash must equal the prior event's current_hash."""
    e1 = append_event(db_session, "A", {"x": 1})
    e2 = append_event(db_session, "B", {"x": 2})
    e3 = append_event(db_session, "C", {"x": 3})

    assert e1.previous_hash == GENESIS_HASH
    assert e2.previous_hash == e1.current_hash
    assert e3.previous_hash == e2.current_hash
