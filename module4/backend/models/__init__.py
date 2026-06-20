"""
Import all models here so Alembic's `target_metadata = Base.metadata`
picks up every table when autogenerating migrations.
"""

from module4.backend.core.database import Base  # noqa: F401
from module4.backend.models.audit_log import AuditLog  # noqa: F401
from module4.backend.models.ledger_event import LedgerEvent  # noqa: F401
from module4.backend.models.complaint import Complaint, ComplaintCategory, ComplaintPriority, ComplaintStatus  # noqa: F401
from module4.backend.models.security_alert import SecurityAlert, AlertType, AlertStatus  # noqa: F401
from module4.backend.models.trust_score import TrustScore, RiskLevel  # noqa: F401
from module4.backend.models.hospital_metrics import HospitalMetrics  # noqa: F401
from module4.backend.models.emergency_override import EmergencyOverride, OverrideStatus  # noqa: F401

__all__ = [
    "Base",
    "AuditLog",
    "LedgerEvent",
    "Complaint",
    "ComplaintCategory",
    "ComplaintPriority",
    "ComplaintStatus",
    "SecurityAlert",
    "AlertType",
    "AlertStatus",
    "TrustScore",
    "RiskLevel",
    "HospitalMetrics",
    "EmergencyOverride",
    "OverrideStatus",
]
