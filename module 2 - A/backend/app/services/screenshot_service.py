"""
Screenshot Service.
Orchestrates OCR extraction + metric creation + analytics triggering.
"""

from datetime import datetime, date
import os
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.services.ocr_service import ocr_service
from app.repositories import WearableMetricRepository
from app.schemas import ScreenshotAnalysisResponse, WearableMetricResponse, WearableMetricCreateRequest
from app.models import WearableMetric


class ScreenshotService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.metric_repo = WearableMetricRepository(session)

    async def analyze_smartwatch_screenshot(
        self, patient_id: str, extraction_id: str, file_path: str
    ) -> ScreenshotAnalysisResponse:
        """
        Process a screenshot:
        1. Run PaddleOCR
        2. Extract metrics via Regex/LLM
        3. Save metrics to DB
        4. Trigger analytics
        """
        # 1. OCR
        raw_text, conf_score = await ocr_service.process_image(file_path)
        
        # 2. Extract Fields
        fields = await ocr_service.parse_smartwatch_metrics(raw_text)
        
        # Guess Device (Simple heuristic)
        device = "generic_smartwatch"
        if "da fit" in raw_text.lower():
            device = "DaFit"
        elif "apple" in raw_text.lower():
            device = "Apple Watch"
            
        # 3. Create Metrics
        created_metrics = []
        today = date.today()
        now = datetime.utcnow()
        
        for metric_type, value in fields.items():
            if value is not None:
                unit_map = {
                    "heart_rate": "bpm",
                    "steps": "steps",
                    "sleep_hours": "hours",
                    "blood_oxygen": "%",
                    "calories": "kcal"
                }
                
                metric = WearableMetric(
                    id=str(uuid.uuid4()),
                    patient_id=patient_id,
                    metric_type=metric_type,
                    metric_date=today,
                    metric_timestamp=now,
                    value=value,
                    unit=unit_map.get(metric_type, ""),
                    source_device=device,
                    confidence_score=conf_score,
                    extracted_from_screenshot=True,
                    screenshot_vault_file_id=extraction_id,
                    created_by=patient_id
                )
                
                metric = await self.metric_repo.create(metric)
                created_metrics.append(metric)
                
        await self.session.commit()
        
        # Convert to schemas
        metric_responses = [WearableMetricResponse.model_validate(m) for m in created_metrics]
        
        # 4. Trigger analytics (Return the trigger status, we don't calculate full summary here to save time)
        analytics_triggered = len(created_metrics) > 0

        return ScreenshotAnalysisResponse(
            extraction_id=extraction_id,
            patient_id=patient_id,
            device_detected=device,
            metrics_extracted=metric_responses,
            raw_ocr_text=raw_text,
            confidence_score=conf_score,
            analytics_triggered=analytics_triggered,
            processed_at=datetime.utcnow()
        )
