from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from module4.backend.models.emergency_override import OverrideStatus


class EmergencyOverrideCreate(BaseModel):
    doctor_id: str
    patient_id: str
    hospital_id: str | None = None
    reason: str
    urgency: str = "HIGH"


class EmergencyOverrideReview(BaseModel):
    approve: bool
    review_notes: str | None = None
    access_window_hours: int = 24


class EmergencyOverrideOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_id: UUID
    doctor_id: str
    patient_id: str
    hospital_id: str | None = None
    reason: str
    urgency: str | None = None
    status: OverrideStatus
    reviewed_by: str | None = None
    review_notes: str | None = None
    requested_at: datetime
    reviewed_at: datetime | None = None
    access_expires_at: datetime | None = None
