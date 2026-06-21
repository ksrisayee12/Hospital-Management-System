"""
Insight Service.
Generates weekly health insights combining wearable, compliance, and record data.
"""

from datetime import datetime
import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import HealthInsightRepository
from app.models import HealthInsight
from app.services.analytics_service import AnalyticsService
from app.services.wearable_analytics_service import WearableAnalyticsService
from app.services.ai_service import ai_service


class InsightService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.insight_repo = HealthInsightRepository(session)
        self.analytics_service = AnalyticsService(session)
        self.wearable_service = WearableAnalyticsService(session)

    async def generate_weekly_insights(self, patient_id: str) -> HealthInsight:
        """
        Generate comprehensive health insights for the patient.
        1. Gather analytics & wearable data
        2. Prompt AI
        3. Save and return
        """
        period_days = 7
        
        # Gather context
        compliance = await self.analytics_service.get_compliance_metrics(patient_id, period_days)
        wearable_summary = await self.wearable_service.get_summary(patient_id, period_days)
        
        context_str = (
            f"Medication Adherence: {compliance.medication_compliance.value}%\n"
            f"Average Sleep: {wearable_summary.sleep_avg_hours or 'N/A'} hours\n"
            f"Average Steps: {wearable_summary.steps_avg or 'N/A'}\n"
            f"Average SpO2: {wearable_summary.blood_oxygen_avg or 'N/A'}%\n"
        )
        
        prompt = (
            "You are a helpful health assistant. Review the following weekly health metrics for a patient:\n\n"
            f"{context_str}\n\n"
            "Provide 3 brief, encouraging health insights based on this data. "
            "Also provide 2 specific, actionable recommendations. "
            "Format your response EXACTLY as a JSON object with two lists of strings: "
            '{"insights": ["..."], "action_recommendations": ["..."]}. '
            "Do not include any other text."
        )
        
        # In a real implementation we would enforce JSON output using outlines/guidance or regex extraction.
        # For this prototype, we'll try to extract the JSON.
        result_text, model_used = ai_service._generate(prompt)
        
        insights = ["Data suggests a stable week."]
        actions = ["Continue monitoring metrics."]
        
        try:
            # Simple JSON extraction heuristic
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                insights = data.get("insights", insights)
                actions = data.get("action_recommendations", actions)
        except Exception:
            pass # Fallback to default if generation parsing fails

        insight = HealthInsight(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            insights=insights,
            action_recommendations=actions,
            wearable_summary=wearable_summary.model_dump(mode="json"),
            compliance_summary=compliance.model_dump(mode="json"),
            generated_at=datetime.utcnow(),
            model_used=model_used,
            generation_period_days=period_days,
            created_by="ai_system"
        )
        
        insight = await self.insight_repo.create(insight)
        await self.session.commit()
        return insight
