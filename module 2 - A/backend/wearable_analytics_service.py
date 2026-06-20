"""
MODULE 2 — PART B: Wearable Analytics Service
Trend Detection, Anomaly Detection, Activity Scoring.
Uses existing wearable_metrics table from Part A.
"""

from __future__ import annotations

import math
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
    WearableTrendResponse,
    WearableTrendPoint,
    WearableAnomalyResponse,
    ActivityScoreResponse,
)

settings = get_settings()
logger = get_logger(__name__)

# Normal ranges for anomaly detection
METRIC_NORMAL_RANGES = {
    "heart_rate": (50.0, 100.0),
    "blood_oxygen": (95.0, 100.0),
    "steps": (0.0, 60000.0),
    "calories": (0.0, 4000.0),
    "sleep_hours": (5.0, 10.0),
}


class WearableAnalyticsService:

    # ── Trend Detection ──────────────────────────

    async def metric_trend(
        self,
        db: AsyncSession,
        patient_id: UUID,
        metric_type: str,
        period_days: int = 30,
    ) -> WearableTrendResponse:
        end = datetime.utcnow()
        start = end - timedelta(days=period_days)

        result = await db.execute(
            text("""
                SELECT recorded_at, value
                FROM wearable_metrics
                WHERE patient_id = :pid
                  AND metric_type = :metric
                  AND recorded_at BETWEEN :start AND :end
                ORDER BY recorded_at ASC
            """),
            {"pid": str(patient_id), "metric": metric_type, "start": start, "end": end},
        )
        rows = result.fetchall()

        if not rows:
            raise InsufficientDataError(f"No {metric_type} data found")

        points = [WearableTrendPoint(timestamp=r.recorded_at, value=r.value, metric_type=metric_type) for r in rows]
        values = [r.value for r in rows]

        return WearableTrendResponse(
            patient_id=patient_id,
            metric_type=metric_type,
            period_days=period_days,
            data_points=points,
            average=round(statistics.mean(values), 2),
            min_value=round(min(values), 2),
            max_value=round(max(values), 2),
            trend_direction=self._trend_direction(values),
        )

    async def weekly_step_trends(
        self, db: AsyncSession, patient_id: UUID, weeks: int = 4
    ) -> list[dict[str, Any]]:
        end = datetime.utcnow()
        start = end - timedelta(weeks=weeks)

        result = await db.execute(
            text("""
                SELECT
                    DATE_TRUNC('week', recorded_at) AS week_start,
                    SUM(value) AS total_steps,
                    AVG(value) AS avg_daily_steps,
                    COUNT(*) AS day_count
                FROM wearable_metrics
                WHERE patient_id = :pid
                  AND metric_type = 'steps'
                  AND recorded_at BETWEEN :start AND :end
                GROUP BY DATE_TRUNC('week', recorded_at)
                ORDER BY week_start ASC
            """),
            {"pid": str(patient_id), "start": start, "end": end},
        )
        return [
            {
                "week_start": r.week_start.isoformat(),
                "total_steps": int(r.total_steps or 0),
                "avg_daily_steps": round(r.avg_daily_steps or 0, 0),
                "days_tracked": r.day_count,
            }
            for r in result.fetchall()
        ]

    async def sleep_quality_trend(
        self, db: AsyncSession, patient_id: UUID, days: int = 30
    ) -> dict[str, Any]:
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        result = await db.execute(
            text("""
                SELECT
                    recorded_at::date AS sleep_date,
                    value AS hours
                FROM wearable_metrics
                WHERE patient_id = :pid
                  AND metric_type = 'sleep_hours'
                  AND recorded_at BETWEEN :start AND :end
                ORDER BY sleep_date ASC
            """),
            {"pid": str(patient_id), "start": start, "end": end},
        )
        rows = result.fetchall()
        if not rows:
            raise InsufficientDataError("No sleep data")

        values = [r.hours for r in rows]
        avg = statistics.mean(values)
        quality = self._sleep_quality_label(avg)

        return {
            "patient_id": str(patient_id),
            "period_days": days,
            "avg_sleep_hours": round(avg, 2),
            "min_sleep_hours": round(min(values), 2),
            "max_sleep_hours": round(max(values), 2),
            "quality_label": quality,
            "daily_breakdown": [
                {"date": r.sleep_date.isoformat(), "hours": r.hours} for r in rows
            ],
        }

    # ── Anomaly Detection ────────────────────────

    async def detect_anomalies(
        self, db: AsyncSession, patient_id: UUID, days: int = 7
    ) -> list[WearableAnomalyResponse]:
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        result = await db.execute(
            text("""
                SELECT metric_type, value, recorded_at
                FROM wearable_metrics
                WHERE patient_id = :pid AND recorded_at BETWEEN :start AND :end
                ORDER BY recorded_at DESC
            """),
            {"pid": str(patient_id), "start": start, "end": end},
        )
        rows = result.fetchall()

        # Build per-metric baselines (last 30 days, excluding recent 7)
        baselines = await self._get_baselines(db, patient_id, end - timedelta(days=37), start)
        anomalies = []

        for r in rows:
            metric = r.metric_type
            value = r.value

            # Static range check
            if metric in METRIC_NORMAL_RANGES:
                lo, hi = METRIC_NORMAL_RANGES[metric]
                if not (lo <= value <= hi):
                    severity = self._severity(value, lo, hi)
                    anomalies.append(
                        WearableAnomalyResponse(
                            patient_id=patient_id,
                            metric_type=metric,
                            anomaly_timestamp=r.recorded_at,
                            observed_value=value,
                            expected_range_low=lo,
                            expected_range_high=hi,
                            severity=severity,
                            description=f"{metric.replace('_', ' ').title()} of {value} is outside normal range ({lo}–{hi})",
                        )
                    )
                    continue

            # Z-score check against personal baseline
            if metric in baselines:
                mean_val, std_val = baselines[metric]
                if std_val > 0:
                    z = abs((value - mean_val) / std_val)
                    if z > settings.anomaly_z_score_threshold:
                        anomalies.append(
                            WearableAnomalyResponse(
                                patient_id=patient_id,
                                metric_type=metric,
                                anomaly_timestamp=r.recorded_at,
                                observed_value=value,
                                expected_range_low=round(mean_val - 2 * std_val, 2),
                                expected_range_high=round(mean_val + 2 * std_val, 2),
                                severity="medium" if z < 3.5 else "high",
                                description=f"{metric.replace('_', ' ').title()} deviated {z:.1f} standard deviations from your personal baseline",
                            )
                        )

        return anomalies[:20]  # cap response size

    async def _get_baselines(
        self,
        db: AsyncSession,
        patient_id: UUID,
        start: datetime,
        end: datetime,
    ) -> dict[str, tuple[float, float]]:
        result = await db.execute(
            text("""
                SELECT
                    metric_type,
                    AVG(value) AS mean_val,
                    STDDEV(value) AS std_val
                FROM wearable_metrics
                WHERE patient_id = :pid AND recorded_at BETWEEN :start AND :end
                GROUP BY metric_type
                HAVING COUNT(*) > 5
            """),
            {"pid": str(patient_id), "start": start, "end": end},
        )
        return {
            r.metric_type: (r.mean_val or 0.0, r.std_val or 0.0)
            for r in result.fetchall()
        }

    # ── Activity Score ────────────────────────────

    async def activity_score(
        self, db: AsyncSession, patient_id: UUID, days: int = 7
    ) -> ActivityScoreResponse:
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        result = await db.execute(
            text("""
                SELECT metric_type, SUM(value) AS total, AVG(value) AS avg_val
                FROM wearable_metrics
                WHERE patient_id = :pid AND recorded_at BETWEEN :start AND :end
                GROUP BY metric_type
            """),
            {"pid": str(patient_id), "start": start, "end": end},
        )
        metrics = {r.metric_type: {"total": r.total, "avg": r.avg_val} for r in result.fetchall()}

        avg_steps = metrics.get("steps", {}).get("avg", 0) or 0
        total_steps = int(metrics.get("steps", {}).get("total", 0) or 0)
        total_calories = metrics.get("calories", {}).get("total", 0) or 0
        avg_sleep = metrics.get("sleep_hours", {}).get("avg", 0) or 0
        avg_spo2 = metrics.get("blood_oxygen", {}).get("avg", None)

        # Score components (0–100)
        step_score = min(avg_steps / 10000 * 100, 100)
        sleep_score = 100 if 7 <= avg_sleep <= 9 else max(0, 100 - abs(avg_sleep - 8) * 20)
        spo2_score = 100 if (avg_spo2 and avg_spo2 >= 97) else (80 if avg_spo2 and avg_spo2 >= 95 else 50)

        score = round((step_score * 0.5 + sleep_score * 0.3 + spo2_score * 0.2), 1)
        label = (
            "Excellent" if score >= 80 else
            "Good" if score >= 60 else
            "Fair" if score >= 40 else "Poor"
        )

        return ActivityScoreResponse(
            patient_id=patient_id,
            period_days=days,
            total_steps=total_steps,
            avg_daily_steps=round(avg_steps, 0),
            total_calories=round(total_calories, 1),
            avg_sleep_hours=round(avg_sleep, 2),
            avg_blood_oxygen=round(avg_spo2, 1) if avg_spo2 else None,
            activity_score=score,
            score_label=label,
        )

    # ── Utilities ─────────────────────────────────

    def _trend_direction(self, values: list[float]) -> str:
        if len(values) < 4:
            return "stable"
        half = len(values) // 2
        delta = statistics.mean(values[half:]) - statistics.mean(values[:half])
        if abs(delta) < 0.02 * max(statistics.mean(values), 1):
            return "stable"
        return "increasing" if delta > 0 else "decreasing"

    def _sleep_quality_label(self, avg_hours: float) -> str:
        if avg_hours >= 7:
            return "Good"
        elif avg_hours >= 6:
            return "Fair"
        return "Poor"

    def _severity(self, value: float, lo: float, hi: float) -> str:
        deviation = max(lo - value, value - hi, 0)
        range_size = hi - lo
        ratio = deviation / max(range_size, 1)
        if ratio > 0.5:
            return "high"
        elif ratio > 0.2:
            return "medium"
        return "low"
