from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from module4.backend.models.complaint import ComplaintCategory, ComplaintPriority, ComplaintStatus


class ComplaintCreate(BaseModel):
    patient_id: str
    doctor_id: str
    hospital_id: str | None = None
    category: ComplaintCategory
    description: str


class ComplaintUpdateStatus(BaseModel):
    status: ComplaintStatus
    admin_notes: str | None = None


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: UUID
    patient_id: str
    doctor_id: str
    hospital_id: str | None = None
    category: ComplaintCategory
    description: str
    status: ComplaintStatus
    priority: ComplaintPriority | None = None
    admin_notes: str | None = None
    created_at: datetime
    updated_at: datetime
