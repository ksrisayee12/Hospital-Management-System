"""
Wearable Analytics Service.
Calculates trends, moving averages, and detects anomalies in wearable data.
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import statistics
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import WearableMetricRepository, WearableGoalRepository
from app.schemas import (
    TrendResponse, TrendDataPoint, WearableAnalyticsSummary, WearableGoalResponse
)
from app.config import settings


class WearableAnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.metric_repo = WearableMetricRepository(session)
        self.goal_repo = WearableGoalRepository(session)

    def _calculate_moving_average(self, data: List[float], window: int) -> Optional[float]:
        if not data or len(data) < window:
             return None if not data else sum(data) / len(data)
        return sum(data[-window:]) / window

    async def get_metric_trend(self, patient_id: str, metric_type: str, period_days: int = 30) -> TrendResponse:
        """Calculate trends, moving averages, and anomalies for a specific metric."""
        metrics, _ = await self.metric_repo.get_by_patient_id(
            patient_id, metric_type=metric_type,
            from_date=datetime.utcnow().date() - timedelta(days=period_days),
            limit=1000
        )
        
        # Sort chronologically
        metrics.sort(key=lambda x: x.metric_date)
        
        if not metrics:
            return TrendResponse(
                patient_id=patient_id, metric_type=metric_type, unit="unknown",
                period_days=period_days, data_points=[],
                moving_avg_7d=None, moving_avg_30d=None, moving_avg_90d=None,
                baseline_mean=None, baseline_std=None, anomaly_count=0,
                trend_direction="stable", calculated_at=datetime.utcnow()
            )
            
        unit = metrics[0].unit
        values = [m.value for m in metrics]
        
        # Baseline (all data in period)
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        
        # Anomalies
        data_points = []
        anomaly_count = 0
        for m in metrics:
            is_anomaly = False
            direction = None
            if std_dev > 0 and abs(m.value - mean) > (std_dev * settings.WEARABLE_ANOMALY_SIGMA):
                is_anomaly = True
                anomaly_count += 1
                direction = "high" if m.value > mean else "low"
                
            data_points.append(TrendDataPoint(
                date=m.metric_date,
                value=m.value,
                is_anomaly=is_anomaly,
                anomaly_direction=direction
            ))
            
        # Moving Averages
        ma_7d = self._calculate_moving_average(values, 7)
        ma_30d = self._calculate_moving_average(values, 30)
        
        # Trend Direction (simple slope of first half vs second half)
        trend_direction = "stable"
        if len(values) >= 4:
            half = len(values) // 2
            h1_avg = sum(values[:half]) / half
            h2_avg = sum(values[half:]) / len(values[half:])
            
            diff = h2_avg - h1_avg
            threshold = std_dev * 0.2 if std_dev > 0 else mean * 0.05
            
            if diff > threshold:
                trend_direction = "increasing"
            elif diff < -threshold:
                trend_direction = "decreasing"
                
            # Map increasing/decreasing to improving/declining based on metric
            if metric_type in ["heart_rate", "blood_pressure_sys", "blood_pressure_dia"]:
                 trend_direction = "declining" if trend_direction == "increasing" else "improving"
            else: # steps, sleep, spo2
                 trend_direction = "improving" if trend_direction == "increasing" else "declining"

        return TrendResponse(
            patient_id=patient_id,
            metric_type=metric_type,
            unit=unit,
            period_days=period_days,
            data_points=data_points,
            moving_avg_7d=ma_7d,
            moving_avg_30d=ma_30d,
            moving_avg_90d=None, # Need 90 days of data
            baseline_mean=mean,
            baseline_std=std_dev,
            anomaly_count=anomaly_count,
            trend_direction=trend_direction,
            calculated_at=datetime.utcnow()
        )

    async def get_summary(self, patient_id: str, period_days: int = 30) -> WearableAnalyticsSummary:
        """Comprehensive summary across all metrics for clinical view."""
        metrics = await self.metric_repo.get_all_for_patient_period(patient_id, days=period_days)
        goals = await self.goal_repo.get_by_patient_id(patient_id)
        goal_map = {g.metric_type: g.target_value for g in goals}
        
        grouped = {}
        for m in metrics:
            if m.metric_type not in grouped:
                grouped[m.metric_type] = []
            grouped[m.metric_type].append(m.value)
            
        def avg(l): return sum(l)/len(l) if l else None
        
        sleep_avg = avg(grouped.get("sleep_hours", []))
        hr_avg = avg(grouped.get("heart_rate", []))
        spo2_avg = avg(grouped.get("blood_oxygen", []))
        steps_avg = avg(grouped.get("steps", []))
        calories_avg = avg(grouped.get("calories", []))
        
        spo2_list = grouped.get("blood_oxygen", [])
        low_spo2 = [v for v in spo2_list if v < settings.BLOOD_OXYGEN_ALERT_THRESHOLD]
        
        steps_goal = goal_map.get("steps", 10000)
        steps_pct = (steps_avg / steps_goal * 100) if steps_avg else None
        
        # Sleep quality mock (based on hours)
        sleep_q = min(100.0, (sleep_avg / 8.0 * 100)) if sleep_avg else None
        
        return WearableAnalyticsSummary(
            patient_id=patient_id,
            period_days=period_days,
            sleep_avg_hours=sleep_avg,
            sleep_quality_score=sleep_q,
            heart_rate_avg=hr_avg,
            heart_rate_trend="stable", # Needs full trend analysis
            blood_oxygen_avg=spo2_avg,
            low_spo2_alert=len(low_spo2) > 0,
            low_spo2_count=len(low_spo2),
            steps_avg=steps_avg,
            steps_goal_achievement_pct=steps_pct,
            calories_avg=calories_avg,
            calculated_at=datetime.utcnow()
        )
