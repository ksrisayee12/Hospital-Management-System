"""
complaints table.

Patient-initiated complaints against doctors. Status lifecycle:
OPEN -> UNDER_REVIEW -> RESOLVED / ESCALATED
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID

from module4.backend.core.database import Base


class ComplaintCategory(str, enum.Enum):
    MEDICAL_ERROR = "MEDICAL_ERROR"
    PRIVACY_ISSUE = "PRIVACY_ISSUE"
    BEHAVIORAL_ISSUE = "BEHAVIORAL_ISSUE"
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    INCORRECT_UPDATE = "INCORRECT_UPDATE"
    OTHER = "OTHER"


class ComplaintStatus(str, enum.Enum):
    OPEN = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"


class ComplaintPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(String, nullable=False, index=True)
    doctor_id = Column(String, nullable=False, index=True)
    hospital_id = Column(String, nullable=True, index=True)

    category = Column(Enum(ComplaintCategory), nullable=False)
    description = Column(Text, nullable=False)

    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.OPEN, index=True)
    priority = Column(Enum(ComplaintPriority), nullable=True)  # set by AI classifier

    admin_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Complaint {self.complaint_id} status={self.status}>"
