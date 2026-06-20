from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from module4.backend.models.security_alert import AlertStatus, AlertType


class SecurityAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: UUID
    user_id: str
    hospital_id: str | None = None
    alert_type: AlertType
    risk_score: float
    description: str | None = None
    status: AlertStatus
    created_at: datetime
    resolved_at: datetime | None = None


class SecurityAlertUpdateStatus(BaseModel):
    status: AlertStatus
