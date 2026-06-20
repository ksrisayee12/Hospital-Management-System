"""
trust_scores table.

Every doctor starts at 100. Score decreases on complaints, access
abuse, security alerts, and override misuse. Drives the doctor-level
trust badge and feeds into hospital-level risk aggregation.
"""

import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String

from module4.backend.core.database import Base


class RiskLevel(str, enum.Enum):
    LOW = "LOW"           # 80-100
    MODERATE = "MODERATE"  # 60-79
    HIGH = "HIGH"          # 40-59
    CRITICAL = "CRITICAL"  # 0-39


class TrustScore(Base):
    __tablename__ = "trust_scores"

    doctor_id = Column(String, primary_key=True)
    hospital_id = Column(String, nullable=True, index=True)

    score = Column(Integer, default=100, nullable=False)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<TrustScore doctor={self.doctor_id} score={self.score}>"


def score_to_risk_level(score: int) -> RiskLevel:
    if score >= 80:
        return RiskLevel.LOW
    if score >= 60:
        return RiskLevel.MODERATE
    if score >= 40:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL
