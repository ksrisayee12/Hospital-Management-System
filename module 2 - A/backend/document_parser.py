"""
MODULE 2 — PART B: Document Parser & Validation Layer
Converts raw OCR structured data into validated DB records.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.logging_config import get_logger
from models.part_b_models import ExtractedPrescription, ExtractedLabValue, OCRJob

logger = get_logger(__name__)

DATE_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y"]


def _parse_date(raw: Optional[str]) -> Optional[datetime]:
    if not raw:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None


class DocumentParser:
    """Converts OCR structured_data dict into ORM objects and persists them."""

    async def parse_and_persist(
        self,
        db: AsyncSession,
        ocr_job: OCRJob,
        structured_data: dict[str, Any],
        confidence: float,
    ) -> dict[str, Any]:
        from models.part_b_models import OCRDocumentType

        counts: dict[str, int] = {}

        if ocr_job.document_type == OCRDocumentType.PRESCRIPTION:
            prescriptions = await self._persist_prescriptions(db, ocr_job, structured_data, confidence)
            counts["prescriptions"] = len(prescriptions)

        elif ocr_job.document_type == OCRDocumentType.LAB_REPORT:
            labs = await self._persist_lab_values(db, ocr_job, structured_data, confidence)
            counts["lab_values"] = len(labs)

        return counts

    async def _persist_prescriptions(
        self,
        db: AsyncSession,
        ocr_job: OCRJob,
        data: dict[str, Any],
        confidence: float,
    ) -> list[ExtractedPrescription]:
        medicines = data.get("medicine_names", [])
        dosages = data.get("dosages", [])
        frequencies = data.get("frequencies", [])
        records = []

        for i, med_line in enumerate(medicines):
            # Extract medicine name and dosage from the line
            name_match = re.match(r"([A-Za-z\s]+)", med_line)
            name = name_match.group(1).strip() if name_match else med_line

            ep = ExtractedPrescription(
                ocr_job_id=ocr_job.id,
                patient_id=ocr_job.patient_id,
                medicine_name=name,
                dosage=dosages[i] if i < len(dosages) else data.get("dosages"),
                frequency=frequencies[i] if i < len(frequencies) else data.get("frequencies"),
                duration=data.get("duration"),
                doctor_name=data.get("doctor_name"),
                prescription_date=_parse_date(data.get("date")),
                raw_confidence=confidence,
            )
            db.add(ep)
            records.append(ep)

        if not medicines and data.get("doctor_name"):
            # At least one blank record to capture doctor + date
            ep = ExtractedPrescription(
                ocr_job_id=ocr_job.id,
                patient_id=ocr_job.patient_id,
                medicine_name="UNDETECTED",
                doctor_name=data.get("doctor_name"),
                prescription_date=_parse_date(data.get("date")),
                raw_confidence=confidence,
            )
            db.add(ep)
            records.append(ep)

        await db.flush()
        return records

    async def _persist_lab_values(
        self,
        db: AsyncSession,
        ocr_job: OCRJob,
        data: dict[str, Any],
        confidence: float,
    ) -> list[ExtractedLabValue]:
        records = []
        for item in data.get("lab_values", []):
            lv = ExtractedLabValue(
                ocr_job_id=ocr_job.id,
                patient_id=ocr_job.patient_id,
                test_name=item.get("test_name", "UNKNOWN"),
                value=item.get("value"),
                unit=item.get("unit"),
                reference_range=item.get("reference_range"),
                is_abnormal=self._check_abnormal(item.get("value"), item.get("reference_range")),
                lab_date=_parse_date(data.get("date")),
                ordering_doctor=data.get("doctor_name"),
                lab_name=data.get("lab_name"),
                raw_confidence=confidence,
            )
            db.add(lv)
            records.append(lv)

        await db.flush()
        return records

    def _check_abnormal(self, value_str: Optional[str], ref_range: Optional[str]) -> Optional[bool]:
        if not value_str or not ref_range:
            return None
        try:
            value = float(value_str.replace(",", ""))
            # ref_range like "70 - 110" or "70-110"
            parts = re.split(r"\s*[-–]\s*", ref_range)
            if len(parts) == 2:
                lo, hi = float(parts[0]), float(parts[1])
                return not (lo <= value <= hi)
        except (ValueError, AttributeError):
            pass
        return None
