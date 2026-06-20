"""
MODULE 2 — PART B: Health Analytics Service
Medication Compliance, Appointment Compliance, Vitals Trends.
"""

from __future__ import annotations

import statistics
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.exceptions import InsufficientDataError
from core.logging_config import get_logger
from schemas.part_b_schemas import (
    MedicationAdherenceResponse,
    AppointmentComplianceResponse,
    VitalTrendResponse,
    VitalTrendPoint,
    HealthSummaryResponse,
)

settings = get_settings()
logger = get_logger(__name__)


class HealthAnalyticsService:

    # ── Medication Adherence ─────────────────────

    async def medication_adherence(
        self,
        db: AsyncSession,
        patient_id: UUID,
        period: str = "monthly",
        days: int = 30,
    ) -> MedicationAdherenceResponse:
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        result = await db.execute(
            text("""
                SELECT
                    p.id,
                    p.medicine_name,
                    p.dosage,
                    p.frequency,
                    p.start_date,
                    p.end_date,
                    COUNT(te.id) FILTER (WHERE te.event_type = 'medication_taken') AS taken_count,
                    COUNT(te.id) FILTER (WHERE te.event_type = 'medication_missed') AS missed_count
                FROM prescriptions p
                LEFT JOIN timeline_events te
                    ON te.reference_id = p.id::text
                    AND te.event_date BETWEEN :start AND :end
                WHERE p.patient_id = :pid
                  AND (p.end_date IS NULL OR p.end_date >= :start)
                GROUP BY p.id, p.medicine_name, p.dosage, p.frequency, p.start_date, p.end_date
            """),
            {"pid": str(patient_id), "start": start, "end": end},
        )
        rows = result.fetchall()

        total_meds = len(rows)
        total_missed = sum(r.missed_count or 0 for r in rows)
        total_taken = sum(r.taken_count or 0 for r in rows)
        total_doses = total_taken + total_missed
        adherence_pct = (total_taken / total_doses * 100) if total_doses > 0 else 100.0

        detail = [
            {
                "medicine": r.medicine_name,
                "dosage": r.dosage,
                "taken": r.taken_count or 0,
                "missed": r.missed_count or 0,
            }
            for r in rows
        ]

        return MedicationAdherenceResponse(
            patient_id=patient_id,
            period=period,
            period_start=start,
            period_end=end,
            total_medications=total_meds,
            missed_doses=total_missed,
            adherence_percentage=round(adherence_pct, 2),
            medications_detail=detail,
        )

    # ── Appointment Compliance ───────────────────

    async def appointment_compliance(
        self,
        db: AsyncSession,
        patient_id: UUID,
        period: str = "monthly",
        days: int = 30,
    ) -> AppointmentComplianceResponse:
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        result = await db.execute(
            text("""
                SELECT
                    id,
                    appointment_date,
                    doctor_name,
                    status
                FROM appointments
                WHERE patient_id = :pid
                  AND appointment_date BETWEEN :start AND :end
            """),
            {"pid": str(patient_id), "start": start, "end": end},
        )
        rows = result.fetchall()

        total = len(rows)
        missed = sum(1 for r in rows if r.status in ("missed", "no_show"))
        completed = sum(1 for r in rows if r.status == "completed")
        completion_pct = (completed / total * 100) if total > 0 else 100.0

        return AppointmentComplianceResponse(
            patient_id=patient_id,
            period=period,
            period_start=start,
            period_end=end,
            total_appointments=total,
            missed_appointments=missed,
            completion_percentage=round(completion_pct, 2),
            appointments_detail=[
                {"id": str(r.id), "date": r.appointment_date.isoformat(), "doctor": r.doctor_name, "status": r.status}
                for r in rows
            ],
        )

    # ── Vitals Trends ────────────────────────────

    async def vitals_trend(
        self,
        db: AsyncSession,
        patient_id: UUID,
        metric: str,              # blood_sugar | blood_pressure | weight | heart_rate
        period: str = "monthly",
        days: int = 30,
    ) -> VitalTrendResponse:
        """
        Pulls vital readings from medical_records (Part A) and computes trend.
        Expects medical_records to have a `vitals` JSONB column with the metric.
        """
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        result = await db.execute(
            text("""
                SELECT
                    record_date,
                    vitals->:metric AS value
                FROM medical_records
                WHERE patient_id = :pid
                  AND record_date BETWEEN :start AND :end
                  AND vitals ? :metric
                ORDER BY record_date ASC
            """),
            {"pid": str(patient_id), "metric": metric, "start": start, "end": end},
        )
        rows = result.fetchall()

        if not rows:
            raise InsufficientDataError(f"No {metric} data in the last {days} days")

        points = []
        values = []
        for r in rows:
            try:
                val = float(r.value)
                points.append(VitalTrendPoint(date=r.record_date, value=val))
                values.append(val)
            except (TypeError, ValueError):
                continue

        avg = round(statistics.mean(values), 2) if values else None
        direction = self._trend_direction(values)

        return VitalTrendResponse(
            patient_id=patient_id,
            metric=metric,
            period=period,
            trend=points,
            average=avg,
            min_value=round(min(values), 2) if values else None,
            max_value=round(max(values), 2) if values else None,
            trend_direction=direction,
        )

    # ── Health Summary ────────────────────────────

    async def health_summary(
        self,
        db: AsyncSession,
        patient_id: UUID,
        days: int = 30,
    ) -> HealthSummaryResponse:
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        period = "monthly" if days >= 28 else ("weekly" if days >= 7 else "daily")

        med_adh = await self.medication_adherence(db, patient_id, period, days)
        appt_comp = await self.appointment_compliance(db, patient_id, period, days)

        # Pull averages from wearable_metrics (Part A table)
        vitals_result = await db.execute(
            text("""
                SELECT
                    AVG(CASE WHEN metric_type = 'heart_rate' THEN value END) AS avg_hr,
                    AVG(CASE WHEN metric_type = 'blood_pressure_systolic' THEN value END) AS avg_bps,
                    AVG(CASE WHEN metric_type = 'blood_pressure_diastolic' THEN value END) AS avg_bpd,
                    AVG(CASE WHEN metric_type = 'blood_sugar' THEN value END) AS avg_bs,
                    AVG(CASE WHEN metric_type = 'weight' THEN value END) AS avg_wt
                FROM wearable_metrics
                WHERE patient_id = :pid AND recorded_at BETWEEN :start AND :end
            """),
            {"pid": str(patient_id), "start": start, "end": end},
        )
        v = vitals_result.fetchone()

        return HealthSummaryResponse(
            patient_id=patient_id,
            period=period,
            period_start=start,
            period_end=end,
            medication_adherence_pct=med_adh.adherence_percentage,
            appointment_completion_pct=appt_comp.completion_percentage,
            avg_heart_rate=round(v.avg_hr, 1) if v.avg_hr else None,
            avg_blood_pressure_systolic=round(v.avg_bps, 1) if v.avg_bps else None,
            avg_blood_pressure_diastolic=round(v.avg_bpd, 1) if v.avg_bpd else None,
            avg_blood_sugar=round(v.avg_bs, 1) if v.avg_bs else None,
            avg_weight=round(v.avg_wt, 1) if v.avg_wt else None,
        )

    # ── Historical Changes ────────────────────────

    async def historical_health_changes(
        self, db: AsyncSession, patient_id: UUID
    ) -> list[dict[str, Any]]:
        """Compare current month vs previous month for key metrics."""
        now = datetime.utcnow()
        periods = [
            ("current", now - timedelta(days=30), now),
            ("previous", now - timedelta(days=60), now - timedelta(days=30)),
        ]
        results = {}
        for label, start, end in periods:
            r = await db.execute(
                text("""
                    SELECT
                        metric_type,
                        AVG(value) AS avg_value
                    FROM wearable_metrics
                    WHERE patient_id = :pid AND recorded_at BETWEEN :start AND :end
                    GROUP BY metric_type
                """),
                {"pid": str(patient_id), "start": start, "end": end},
            )
            results[label] = {row.metric_type: row.avg_value for row in r.fetchall()}

        changes = []
        for metric, curr_val in results["current"].items():
            prev_val = results["previous"].get(metric)
            if prev_val and curr_val:
                delta_pct = ((curr_val - prev_val) / prev_val) * 100
                changes.append({
                    "metric": metric,
                    "current_avg": round(curr_val, 2),
                    "previous_avg": round(prev_val, 2),
                    "change_pct": round(delta_pct, 2),
                    "direction": "up" if delta_pct > 0 else "down",
                })
        return sorted(changes, key=lambda x: abs(x["change_pct"]), reverse=True)

    # ── Utilities ─────────────────────────────────

    def _trend_direction(self, values: list[float], window: int = 3) -> str:
        if len(values) < window * 2:
            return "stable"
        first_half = statistics.mean(values[: len(values) // 2])
        second_half = statistics.mean(values[len(values) // 2 :])
        delta = second_half - first_half
        if abs(delta) < 0.02 * first_half:
            return "stable"
        return "increasing" if delta > 0 else "decreasing"
