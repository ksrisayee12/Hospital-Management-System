"""
Analytics Service.
Calculates medication compliance and appointment compliance metrics.
Outputs data for Module 3 and Module 4 consumption.
"""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import AppointmentRepository, PrescriptionRepository
from app.schemas import ComplianceResponse, ComplianceMetric


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.appointment_repo = AppointmentRepository(session)
        self.prescription_repo = PrescriptionRepository(session)

    async def get_compliance_metrics(self, patient_id: str, period_days: int = 30) -> ComplianceResponse:
        """
        Calculate compliance metrics over a given period.
        """
        # 1. Appointment Compliance
        # Metric: (Completed Appointments) / (Completed + Cancelled(by patient) + No-Shows)
        appointments, _ = await self.appointment_repo.get_by_patient_id(
            patient_id, 
            from_date=datetime.utcnow() - timedelta(days=period_days),
            limit=1000
        )
        
        apt_total = 0
        apt_completed = 0
        for apt in appointments:
            if apt.status in ["completed", "cancelled"]: # Simplification for demo
                apt_total += 1
                if apt.status == "completed":
                    apt_completed += 1
                    
        apt_score = (apt_completed / apt_total * 100) if apt_total > 0 else 100.0
        
        # 2. Medication Compliance
        # Real-world: Based on refill rates, self-reporting, or smart pill bottles.
        # Here we mock it based on ratio of active vs stopped prescriptions + mock logic.
        prescriptions, _ = await self.prescription_repo.get_by_patient_id(patient_id, limit=100)
        
        med_total = len(prescriptions)
        # Mock logic: assume 85% base compliance, subtract 5% for each inactive
        base = 85.0
        for p in prescriptions:
             if not p.is_active and p.status != "completed":
                 base -= 5.0
        
        med_score = max(0.0, min(100.0, base if med_total > 0 else 100.0))
        med_completed = int((med_score / 100.0) * med_total) if med_total > 0 else 1
        med_total = med_total if med_total > 0 else 1

        overall_score = (apt_score * 0.4) + (med_score * 0.6)

        return ComplianceResponse(
            patient_id=patient_id,
            period_days=period_days,
            medication_compliance=ComplianceMetric(
                metric="medication_adherence",
                value=round(med_score, 1),
                numerator=med_completed,
                denominator=med_total,
                period_days=period_days
            ),
            appointment_compliance=ComplianceMetric(
                metric="appointment_attendance",
                value=round(apt_score, 1),
                numerator=apt_completed,
                denominator=apt_total,
                period_days=period_days
            ),
            overall_compliance_score=round(overall_score, 1),
            calculated_at=datetime.utcnow()
        )
