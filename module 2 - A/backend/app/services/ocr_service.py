"""
OCR Service using PaddleOCR.
Extracts structured text from prescription images and smartwatch screenshots.
CPU-bound, runs in thread pool.
"""

import os
import re
import logging
from typing import Dict, Any, Optional, Tuple
import asyncio

from app.config import settings

logger = logging.getLogger(__name__)


class OCRService:
    """
    PaddleOCR integration for text extraction from medical images.
    Loaded lazily on first use.
    """
    
    _ocr_model = None
    _initialized = False
    
    @classmethod
    def _initialize(cls):
        if cls._initialized:
            return
            
        try:
            from paddleocr import PaddleOCR
            # Using CPU, en language. Disable debug logs.
            cls._ocr_model = PaddleOCR(
                use_angle_cls=settings.PADDLE_USE_ANGLE_CLS,
                lang=settings.PADDLE_OCR_LANG
            )
            cls._initialized = True
            logger.info("PaddleOCR loaded successfully")
        except ImportError:
            logger.error("PaddleOCR not installed. OCR will fail.")
            
    @classmethod
    def _run_ocr_sync(cls, image_path: str) -> Tuple[str, float]:
        """Synchronous OCR processing."""
        cls._initialize()
        if not cls._ocr_model:
            raise Exception("OCR model not available")
            
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")
            
        result = cls._ocr_model.ocr(image_path)
        
        if not result or not result[0]:
            return "", 0.0
            
        text_lines = []
        confidences = []
        
        for line in result[0]:
            # line is like: [[[x,y],...], ("text", confidence)]
            box, (text, confidence) = line
            text_lines.append(text)
            confidences.append(confidence)
            
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        full_text = "\n".join(text_lines)
        
        return full_text, avg_confidence

    async def process_image(self, image_path: str) -> Tuple[str, float]:
        """Async wrapper for OCR processing."""
        loop = asyncio.get_running_loop()
        # Run CPU-bound task in executor
        return await loop.run_in_executor(None, self._run_ocr_sync, image_path)

    async def parse_prescription(self, full_text: str) -> Dict[str, Any]:
        """Parse raw OCR text into prescription fields using Regex + LLM (or pure regex for now)."""
        # In a full implementation, we'd pass this to the LLM to structure.
        # For this demo, we'll use regex to find common patterns.
        fields = {
            "medicine_name": None,
            "dosage": None,
            "frequency": None,
            "duration": None,
            "prescribing_doctor": None
        }
        
        # Simple heuristics
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            l = line.lower()
            if "dr." in l or "doctor" in l or "md" in l.split():
                fields["prescribing_doctor"] = line.strip()
            elif re.search(r'\b\d+\s*(mg|ml|mcg|g)\b', l):
                # Found dosage, likely medicine name is nearby (or same line)
                fields["dosage"] = re.search(r'\d+\s*(mg|ml|mcg|g)', l, re.I).group(0)
                # Medicine name heuristic: word before dosage or previous line
                match = re.search(r'([A-Za-z]+)\s+\d+\s*(mg|ml)', line, re.I)
                if match:
                    fields["medicine_name"] = match.group(1)
                elif i > 0 and len(lines[i-1].split()) <= 2:
                    fields["medicine_name"] = lines[i-1]
            elif any(w in l for w in ["daily", "twice", "thrice", "bd", "tid", "od", "hs", "hours"]):
                fields["frequency"] = line.strip()
            elif any(w in l for w in ["days", "weeks", "month", "continue for"]):
                fields["duration"] = line.strip()
                
        # Fallback for medicine name if not found but we have text
        if not fields["medicine_name"] and lines:
             # Often the largest/first prominent text
             non_empty = [x for x in lines if len(x) > 3]
             if non_empty:
                 fields["medicine_name"] = non_empty[0]
                 
        return fields
        
    async def parse_smartwatch_metrics(self, full_text: str) -> Dict[str, Any]:
        """Extract smartwatch metrics from screenshot text."""
        fields = {}
        
        # Look for heart rate: e.g. "72 bpm"
        hr_match = re.search(r'(\d{2,3})\s*(bpm|beats)', full_text, re.I)
        if hr_match:
            fields["heart_rate"] = float(hr_match.group(1))
            
        # Look for steps: e.g. "10,432 steps" or just big number near "steps"
        steps_match = re.search(r'([\d,]+)\s*steps', full_text, re.I)
        if steps_match:
            fields["steps"] = int(steps_match.group(1).replace(',', ''))
            
        # Look for sleep: e.g. "7h 30m" or "7 hrs 30 mins" sleep
        sleep_h_match = re.search(r'(\d+)\s*h(?:ou)?r?s?', full_text, re.I)
        sleep_m_match = re.search(r'(\d+)\s*m(?:in)?s?', full_text, re.I)
        
        if "sleep" in full_text.lower() and (sleep_h_match or sleep_m_match):
            h = int(sleep_h_match.group(1)) if sleep_h_match else 0
            m = int(sleep_m_match.group(1)) if sleep_m_match else 0
            if h < 24: # Sanity check
                fields["sleep_hours"] = h + (m / 60.0)
                
        # Look for SpO2: "98%"
        spo2_match = re.search(r'(?:spo2|blood oxygen|o2).*?(\d{2,3})\s*%', full_text, re.I)
        if not spo2_match: # try just percentage
             spo2_match = re.search(r'(\d{2,3})\s*%', full_text)
        if spo2_match:
             val = float(spo2_match.group(1))
             if 70 <= val <= 100:
                 fields["blood_oxygen"] = val
                 
        return fields

ocr_service = OCRService()
