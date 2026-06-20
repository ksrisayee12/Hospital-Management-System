"""
audit_logs table.

Passive record of every action taken in the system. This is the raw
feed that the Audit Intelligence System and AI Security Engine analyze.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from module4.backend.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # doctor | patient | admin | super_admin
    action = Column(String, nullable=False, index=True)  # e.g. VIEW_REPORT, UPDATE_RECORD
    resource = Column(String, nullable=True)  # e.g. patient_id, report_id
    hospital_id = Column(String, nullable=True, index=True)
    metadata_json = Column(String, nullable=True)  # JSON-serialized extra context
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.user_id} at {self.timestamp}>"
