"""
hospital_metrics table.

Aggregated per-hospital counters used by the Super Admin dashboard
to compute a hospital-wide risk score (Hospital Security Analytics).
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from module4.backend.core.database import Base


class HospitalMetrics(Base):
    __tablename__ = "hospital_metrics"

    hospital_id = Column(String, primary_key=True)
    hospital_name = Column(String, nullable=True)

    total_doctors = Column(Integer, default=0)
    total_patients = Column(Integer, default=0)

    total_complaints = Column(Integer, default=0)
    open_complaints = Column(Integer, default=0)

    total_alerts = Column(Integer, default=0)
    active_alerts = Column(Integer, default=0)

    total_overrides = Column(Integer, default=0)

    avg_trust_score = Column(Float, default=100.0)
    risk_score = Column(Float, default=0.0)  # 0 (safe) - 100 (high risk)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<HospitalMetrics {self.hospital_id} risk={self.risk_score}>"
