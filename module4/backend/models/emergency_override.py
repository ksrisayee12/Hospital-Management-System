"""
emergency_overrides table.

Backs the Emergency Override Management workflow (Module 4 Part 1,
section 4) and the /emergency + /emergency/approve API endpoints
(Module 4 Part 2 API Design). Not explicitly listed in the original
table list, but required by the documented API surface, so it's
included here for completeness.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID

from module4.backend.core.database import Base


class OverrideStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class EmergencyOverride(Base):
    __tablename__ = "emergency_overrides"

    request_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(String, nullable=False, index=True)
    patient_id = Column(String, nullable=False, index=True)
    hospital_id = Column(String, nullable=True, index=True)

    reason = Column(Text, nullable=False)  # e.g. "Emergency Surgery", "ICU Admission"
    urgency = Column(String, nullable=True)  # LOW | MEDIUM | HIGH | CRITICAL

    status = Column(Enum(OverrideStatus), default=OverrideStatus.PENDING, index=True)
    reviewed_by = Column(String, nullable=True)  # admin user_id
    review_notes = Column(Text, nullable=True)

    requested_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    access_expires_at = Column(DateTime, nullable=True)  # temporary access window if approved

    def __repr__(self) -> str:
        return f"<EmergencyOverride {self.request_id} status={self.status}>"
