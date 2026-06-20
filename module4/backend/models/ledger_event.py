"""
ledger_events table.

This IS the "blockchain" — an append-only, hash-chained ledger.
Each row's current_hash is derived from its own event_data PLUS the
previous row's hash, so any tampering with historical rows breaks
the chain and is detectable on verification.

NOTE: This is intentionally NOT a real distributed blockchain
(no Ethereum/Hyperledger). It's a tamper-evident hash chain stored
in Postgres, which is the correct scope for a 24-48hr hackathon
per the architecture doc.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from module4.backend.core.database import Base


class LedgerEvent(Base):
    __tablename__ = "ledger_events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sequence_number = Column(Integer, nullable=False, unique=True, index=True)

    event_data = Column(Text, nullable=False)  # JSON string of the event payload
    event_type = Column(String, nullable=False, index=True)  # CONSENT | ACCESS | OVERRIDE | COMPLAINT

    previous_hash = Column(String, nullable=False)
    current_hash = Column(String, nullable=False, unique=True, index=True)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<LedgerEvent #{self.sequence_number} {self.event_type}>"
