"""
Immutable Consent & Audit Ledger — hash-chain implementation.

This is the "blockchain" referenced throughout the docs. It is a
deliberately simple, tamper-evident append-only chain stored in
Postgres (ledger_events table):

    current_hash = SHA256(event_data + previous_hash + timestamp)

Each new event includes the previous event's hash, so altering any
historical row changes its hash and breaks the chain for every
subsequent row — this is what verify_chain() detects.

NOTE: This is intentionally NOT a real distributed blockchain
(no Ethereum/Hyperledger). It's a tamper-evident hash chain stored
in Postgres, which is the correct scope for a 24-48hr hackathon
per the architecture doc.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from module4.backend.models.ledger_event import LedgerEvent

logger = logging.getLogger(__name__)

GENESIS_HASH = "0" * 64  # hash of the first block's "previous_hash"


def _compute_hash(event_data: str, previous_hash: str, timestamp: str) -> str:
    """Compute SHA-256 hash of the concatenation of event_data, previous_hash, and timestamp."""
    payload = f"{event_data}{previous_hash}{timestamp}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def get_latest_event(db: Session) -> LedgerEvent | None:
    """Return the most recently appended ledger event, or None if chain is empty."""
    return (
        db.query(LedgerEvent)
        .order_by(LedgerEvent.sequence_number.desc())
        .first()
    )


def append_event(db: Session, event_type: str, event_payload: dict[str, Any]) -> LedgerEvent:
    """
    Append a new event to the ledger. This is the ONLY way events
    should be written — never update/delete existing ledger_events rows.

    The new event's current_hash is derived from:
      SHA256(event_data_json + previous_hash + timestamp_iso)
    This links every event to its predecessor, making the chain
    tamper-evident: altering any past event breaks all subsequent hashes.

    Args:
        db:            SQLAlchemy session.
        event_type:    Category string (e.g. "CONSENT_APPROVED").
        event_payload: Dict to serialize as the event's data.

    Returns:
        The newly persisted LedgerEvent row.
    """
    latest = get_latest_event(db)
    previous_hash = latest.current_hash if latest else GENESIS_HASH
    next_sequence = (latest.sequence_number + 1) if latest else 1

    timestamp = datetime.utcnow()
    timestamp_str = timestamp.isoformat()
    event_data_str = json.dumps(event_payload, sort_keys=True, default=str)

    current_hash = _compute_hash(event_data_str, previous_hash, timestamp_str)

    ledger_event = LedgerEvent(
        sequence_number=next_sequence,
        event_data=event_data_str,
        event_type=event_type,
        previous_hash=previous_hash,
        current_hash=current_hash,
        timestamp=timestamp,
    )
    db.add(ledger_event)
    db.commit()
    db.refresh(ledger_event)

    logger.info(
        json.dumps({
            "timestamp": timestamp_str,
            "action": "LEDGER_APPEND",
            "user_id": event_payload.get("user_id", "system"),
            "event_type": event_type,
            "sequence_number": next_sequence,
            "outcome": "appended",
        })
    )
    return ledger_event


def verify_chain(db: Session) -> dict[str, Any]:
    """
    Walk the entire chain in sequence order and recompute each hash.

    Detects two distinct failure modes:
      1. previous_hash mismatch — the chain link between two events is broken
         (e.g. a row was deleted or sequence was manipulated).
      2. current_hash mismatch — the event_data or timestamp of a specific
         event was tampered with after it was written.

    Returns:
        Dict with keys:
          - valid (bool): True iff the entire chain is intact.
          - total_events (int | None): count of events if valid.
          - broken_at_sequence (int | None): sequence number of first broken link.
          - reason (str | None): human-readable explanation of the failure.
    """
    events = db.query(LedgerEvent).order_by(LedgerEvent.sequence_number.asc()).all()

    expected_previous = GENESIS_HASH
    for event in events:
        # Failure mode 1: previous_hash chain link broken
        if event.previous_hash != expected_previous:
            result = {
                "valid": False,
                "broken_at_sequence": event.sequence_number,
                "reason": "previous_hash mismatch — chain link broken",
            }
            logger.warning(json.dumps({"action": "LEDGER_VERIFY", "outcome": "tampered", **result}))
            return result

        # Failure mode 2: current_hash / event_data tampered
        recomputed = _compute_hash(
            event.event_data,
            event.previous_hash,
            event.timestamp.isoformat(),
        )
        if recomputed != event.current_hash:
            result = {
                "valid": False,
                "broken_at_sequence": event.sequence_number,
                "reason": "current_hash mismatch — event data tampered",
            }
            logger.warning(json.dumps({"action": "LEDGER_VERIFY", "outcome": "tampered", **result}))
            return result

        expected_previous = event.current_hash

    result = {"valid": True, "total_events": len(events)}
    logger.info(json.dumps({"action": "LEDGER_VERIFY", "outcome": "intact", **result}))
    return result
