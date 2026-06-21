"""
MODULE 2 — PART B: OCR Service
PaddleOCR-based extraction for prescriptions, lab reports, medical documents.
"""

from __future__ import annotations

import io
import re
import time
from typing import Any, Optional
from uuid import UUID

import httpx
from PIL import Image
from paddleocr import PaddleOCR

from core.config import get_settings
from core.exceptions import (
    OCRFileTooLargeError, OCRProcessingError, OCRLowConfidenceError, OCRUnsupportedFormatError
)
from core.logging_config import get_logger
from models.part_b_models import OCRDocumentType

settings = get_settings()
logger = get_logger(__name__)

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff", "image/bmp"}
MAX_FILE_BYTES = settings.ocr_max_file_size_mb * 1024 * 1024


class OCRService:
    """Singleton wrapper around PaddleOCR with structured extraction."""

    _instance: Optional["OCRService"] = None
    _ocr: Optional[PaddleOCR] = None

    def __new__(cls) -> "OCRService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_engine(self) -> PaddleOCR:
        if self._ocr is None:
            logger.info("Initializing PaddleOCR engine")
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang=settings.paddleocr_lang,
                show_log=False,
                use_gpu=False,
            )
        return self._ocr

    # ── Public API ──────────────────────────────

    async def process_image_bytes(
        self,
        image_bytes: bytes,
        mime_type: str,
        document_type: OCRDocumentType,
    ) -> dict[str, Any]:
        """
        Run OCR on raw bytes.
        Returns: {raw_text, structured_data, confidence_score, processing_time_ms}
        """
        if mime_type not in ALLOWED_MIME_TYPES:
            raise OCRUnsupportedFormatError(f"MIME type {mime_type} not supported")
        if len(image_bytes) > MAX_FILE_BYTES:
            raise OCRFileTooLargeError(f"File exceeds {settings.ocr_max_file_size_mb} MB")

        t0 = time.perf_counter()
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            result = self._get_engine().ocr(image, cls=True)
        except Exception as exc:
            logger.error("PaddleOCR engine error", exc_info=True)
            raise OCRProcessingError(str(exc)) from exc

        lines, confidences = self._parse_paddle_result(result)
        raw_text = "\n".join(lines)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
        ms = int((time.perf_counter() - t0) * 1000)

        if avg_conf < settings.ocr_confidence_threshold and len(lines) > 3:
            logger.warning("Low OCR confidence: %.2f", avg_conf)
            raise OCRLowConfidenceError(f"Confidence {avg_conf:.2f} below threshold")

        structured = self._structure(raw_text, document_type)
        logger.info(
            "OCR complete",
            extra={"doc_type": document_type, "lines": len(lines), "conf": avg_conf, "ms": ms},
        )
        return {
            "raw_text": raw_text,
            "structured_data": structured,
            "confidence_score": round(avg_conf, 4),
            "processing_time_ms": ms,
        }

    # ── Internal helpers ────────────────────────

    def _parse_paddle_result(self, result: list) -> tuple[list[str], list[float]]:
        lines, confs = [], []
        if not result:
            return lines, confs
        for page in result:
            if not page:
                continue
            for line in page:
                # line = [[bbox], [text, confidence]]
                if len(line) >= 2 and len(line[1]) >= 2:
                    text = line[1][0].strip()
                    conf = float(line[1][1])
                    if text:
                        lines.append(text)
                        confs.append(conf)
        return lines, confs

    def _structure(self, raw_text: str, doc_type: OCRDocumentType) -> dict[str, Any]:
        if doc_type == OCRDocumentType.PRESCRIPTION:
            return self._extract_prescription_fields(raw_text)
        elif doc_type == OCRDocumentType.LAB_REPORT:
            return self._extract_lab_fields(raw_text)
        elif doc_type == OCRDocumentType.WEARABLE_SCREENSHOT:
            return self._extract_wearable_fields(raw_text)
        return {"raw": raw_text}

    def _extract_prescription_fields(self, text: str) -> dict[str, Any]:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return {
            "medicine_names": self._find_medicines(lines),
            "dosages": self._find_pattern(text, r"(\d+\s*mg|\d+\s*ml|\d+\s*mcg|\d+\s*IU)", "dosage"),
            "frequencies": self._find_pattern(
                text,
                r"(once|twice|thrice|OD|BD|TDS|QID|every\s+\d+\s+hours?|daily|weekly)",
                "frequency",
                flags=re.IGNORECASE,
            ),
            "duration": self._find_pattern(
                text, r"for\s+(\d+\s+days?|\d+\s+weeks?|\d+\s+months?)", "duration", flags=re.IGNORECASE
            ),
            "doctor_name": self._find_pattern(text, r"(?:Dr\.?|Doctor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", "doctor"),
            "date": self._find_date(text),
        }

    def _extract_lab_fields(self, text: str) -> dict[str, Any]:
        lab_values = []
        # Common pattern: TestName  Value  Unit  Reference
        pattern = re.compile(
            r"([A-Za-z][A-Za-z\s\/\(\)]+?)\s+"
            r"(\d+\.?\d*)\s*"
            r"([a-zA-Z\/μ%]+)?\s*"
            r"(\d+\.?\d*\s*[-–]\s*\d+\.?\d*)?",
        )
        for match in pattern.finditer(text):
            test, value, unit, ref = match.groups()
            if test and value:
                lab_values.append({
                    "test_name": test.strip(),
                    "value": value.strip(),
                    "unit": (unit or "").strip(),
                    "reference_range": (ref or "").strip(),
                })
        return {
            "lab_values": lab_values,
            "doctor_name": self._find_pattern(text, r"(?:Dr\.?|Doctor)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", "doctor"),
            "date": self._find_date(text),
            "lab_name": self._find_lab_name(text),
        }

    def _extract_wearable_fields(self, text: str) -> dict[str, Any]:
        metrics: dict[str, Any] = {}
        patterns = {
            "heart_rate": r"(\d+)\s*(?:bpm|BPM|heart rate)",
            "steps": r"(\d[\d,]*)\s*(?:steps?|STEPS)",
            "calories": r"(\d+\.?\d*)\s*(?:kcal|cal|calories?)",
            "sleep_hours": r"(\d+\.?\d*)\s*(?:hrs?|hours?)\s*(?:sleep|asleep)?",
            "blood_oxygen": r"(\d+\.?\d*)\s*%?\s*(?:SpO2|blood oxygen|spo2)",
            "weight_kg": r"(\d+\.?\d*)\s*(?:kg|KG)",
        }
        for metric, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    metrics[metric] = float(match.group(1).replace(",", ""))
                except ValueError:
                    pass
        return metrics

    # ── Regex helpers ───────────────────────────

    def _find_pattern(self, text: str, pattern: str, key: str, flags: int = 0) -> Optional[str]:
        match = re.search(pattern, text, flags)
        return match.group(1).strip() if match else None

    def _find_date(self, text: str) -> Optional[str]:
        match = re.search(
            r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-]\d{2}[\/\-]\d{2})", text
        )
        return match.group(1) if match else None

    def _find_medicines(self, lines: list[str]) -> list[str]:
        """
        Heuristic: capitalised words not matching known labels are likely medicine names.
        """
        exclude = {"Dr", "Date", "Patient", "Name", "Rx", "Hospital", "Clinic", "Report"}
        medicines = []
        for line in lines:
            words = line.split()
            if words and words[0][0].isupper() and words[0] not in exclude:
                if re.search(r"\d+\s*mg|\d+\s*ml", line, re.IGNORECASE):
                    medicines.append(line)
        return medicines[:10]

    def _find_lab_name(self, text: str) -> Optional[str]:
        match = re.search(r"(?:Laboratory|Lab|Diagnostics|Pathology)[\s:]+([A-Za-z\s]+)", text, re.IGNORECASE)
        return match.group(1).strip() if match else None
