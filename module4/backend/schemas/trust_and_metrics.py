from datetime import datetime

from pydantic import BaseModel, ConfigDict

from module4.backend.models.trust_score import RiskLevel


class TrustScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doctor_id: str
    hospital_id: str | None = None
    score: int
    risk_level: RiskLevel
    updated_at: datetime


class HospitalMetricsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hospital_id: str
    hospital_name: str | None = None
    total_doctors: int
    total_patients: int
    total_complaints: int
    open_complaints: int
    total_alerts: int
    active_alerts: int
    total_overrides: int
    avg_trust_score: float
    risk_score: float
    updated_at: datetime
