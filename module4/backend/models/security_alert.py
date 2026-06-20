"""
security_alerts table.

Output of the AI Security Engine / Fraud Detection Agent. Admins
triage these: DISMISS, REVIEW, or ESCALATE.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID

from module4.backend.core.database import Base


class AlertType(str, enum.Enum):
    REPEATED_ACCESS = "REPEATED_ACCESS"
    ABNORMAL_DOWNLOAD = "ABNORMAL_DOWNLOAD"
    EXCESSIVE_VIEWS = "EXCESSIVE_VIEWS"
    OVERRIDE_ABUSE = "OVERRIDE_ABUSE"
    OTHER_ANOMALY = "OTHER_ANOMALY"


class AlertStatus(str, enum.Enum):
    NEW = "NEW"
    DISMISSED = "DISMISSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ESCALATED = "ESCALATED"


class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)  # the doctor/user flagged
    hospital_id = Column(String, nullable=True, index=True)

    alert_type = Column(Enum(AlertType), nullable=False)
    risk_score = Column(Float, nullable=False)  # 0-100
    description = Column(Text, nullable=True)
    evidence_json = Column(Text, nullable=True)  # JSON blob: counts, window, resource ids

    status = Column(Enum(AlertStatus), default=AlertStatus.NEW, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<SecurityAlert {self.alert_type} risk={self.risk_score}>"
