"""
AI Service — HuggingFace BioMistral (primary) + MedGemma (fallback/specialty).
Provides: record explanation, prescription explanation, trend explanation, RAG chat.
All outputs include model_used field for audit trail (Module 3 / Module 4 consumption).
"""

import logging
import re
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.config import settings
from app.schemas import AIChatResponse, AIExplainResponse, CitedSource

logger = logging.getLogger(__name__)

MEDICAL_SYSTEM_PROMPT = (
    "You are a medical information assistant for a patient health vault application. "
    "You ONLY explain existing patient records in plain, clear language. "
    "You do NOT diagnose conditions. You do NOT prescribe medications. "
    "You do NOT recommend changing any ongoing treatment. "
    "You explain what is written in the patient's own health records. "
    "Always end with a reminder to consult a qualified healthcare provider."
)


class AIService:
    """
    HuggingFace-based AI assistant using BioMistral (primary) and MedGemma (fallback).
    Detects available models at startup and logs which backend is active.
    """

    _pipeline_biomistral = None
    _pipeline_medgemma = None
    _image_pipeline = None
    _active_model: str = "none"
    _initialized: bool = False

    @classmethod
    def initialize(cls):
        """Load models at app startup. Logs which backend is active."""
        if cls._initialized:
            return

        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
            import torch

            device = 0 if torch.cuda.is_available() else -1
            device_name = "GPU" if device == 0 else "CPU"
            logger.info(f"AI Service: Loading models on {device_name}")

            # Try BioMistral first
            try:
                logger.info(f"Loading BioMistral: {settings.HUGGINGFACE_BIOMISTRAL_MODEL}")
                cls._pipeline_biomistral = pipeline(
                    "text-generation",
                    model=settings.HUGGINGFACE_BIOMISTRAL_MODEL,
                    token=settings.HUGGINGFACE_API_TOKEN or None,
                    device=device,
                    max_new_tokens=settings.AI_MAX_NEW_TOKENS,
                    temperature=settings.AI_TEMPERATURE,
                    do_sample=True,
                    pad_token_id=2,
                )
                cls._active_model = "biomistral"
                logger.info("✓ BioMistral loaded successfully (primary)")
            except Exception as e:
                logger.warning(f"BioMistral load failed: {e}. Trying MedGemma...")

            # Try MedGemma
            try:
                logger.info(f"Loading MedGemma: {settings.HUGGINGFACE_MEDGEMMA_MODEL}")
                cls._pipeline_medgemma = pipeline(
                    "text-generation",
                    model=settings.HUGGINGFACE_MEDGEMMA_MODEL,
                    token=settings.HUGGINGFACE_API_TOKEN or None,
                    device=device,
                    max_new_tokens=settings.AI_MAX_NEW_TOKENS,
                    temperature=settings.AI_TEMPERATURE,
                    do_sample=True,
                )
                if cls._active_model == "none":
                    cls._active_model = "medgemma"
                logger.info("✓ MedGemma loaded successfully (fallback)")
            except Exception as e:
                logger.warning(f"MedGemma load failed: {e}")

            # Try loading Image-to-Text capability if MedGemma is configured
            try:
                logger.info(f"Loading MedGemma Image Pipeline: {settings.HUGGINGFACE_MEDGEMMA_MODEL}")
                cls._image_pipeline = pipeline(
                    "image-text-to-text",
                    model=settings.HUGGINGFACE_MEDGEMMA_MODEL,
                    token=settings.HUGGINGFACE_API_TOKEN or None,
                    device=device,
                    torch_dtype=torch.bfloat16
                )
                logger.info("✓ MedGemma Image Pipeline loaded successfully")
            except Exception as e:
                logger.warning(f"MedGemma Image Pipeline load failed: {e}")

            if cls._active_model == "none":
                logger.error("No AI model loaded. AI endpoints will return stub responses.")
            else:
                logger.info(f"AI Service active — primary model: {cls._active_model}")

        except ImportError:
            logger.warning("transformers/torch not installed. AI service will use stub mode.")

        cls._initialized = True

    def _get_active_pipeline(self):
        """Return the best available pipeline."""
        if self._pipeline_biomistral is not None:
            return self._pipeline_biomistral, "biomistral"
        if self._pipeline_medgemma is not None:
            return self._pipeline_medgemma, "medgemma"
        return None, "stub"

    def _generate(self, prompt: str) -> tuple:
        """Generate text from the active model. Returns (text, model_name)."""
        pipe, model_name = self._get_active_pipeline()
        if pipe is None:
            return (
                "AI model not available. Please ensure transformers and torch are installed "
                "and a HuggingFace model is configured. Always consult a healthcare provider.",
                "stub"
            )
        try:
            result = pipe(prompt, return_full_text=False)
            return result[0]["generated_text"].strip(), model_name
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return f"Unable to generate explanation at this time. Error: {str(e)}", model_name

    def analyze_image(self, image_path: str, prompt: str) -> str:
        """Analyze an image (like an X-Ray or screenshot) using MedGemma."""
        if self._image_pipeline is None:
            return "Image analysis model not available. Ensure MedGemma image pipeline is loaded."
        try:
            from PIL import Image
            image = Image.open(image_path)
            messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are an expert radiologist and medical assistant."}]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "image": image}
                    ]
                }
            ]
            # Some pipelines require model max token settings
            output = self._image_pipeline(text=messages, max_new_tokens=settings.AI_MAX_NEW_TOKENS)
            return output[0]["generated_text"][-1]["content"]
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return f"Error analyzing image: {str(e)}"

    def _sanitize_input(self, text: str) -> str:
        """Sanitize user input before passing to LLM."""
        # Remove potential injection patterns
        text = re.sub(r"(ignore|forget|disregard)\s+(previous|all|the\s+above)", "", text, flags=re.IGNORECASE)
        text = text.strip()[:1000]  # Limit length
        return text

    async def explain_report(
        self, record_id: str, record_type: str, record_content: Dict[str, Any]
    ) -> AIExplainResponse:
        """Explain a medical record / lab report in plain language."""
        sanitized_content = {k: str(v)[:500] for k, v in record_content.items() if v}

        prompt = (
            f"{MEDICAL_SYSTEM_PROMPT}\n\n"
            f"Patient Record Type: {record_type}\n"
            f"Record Details: {sanitized_content}\n\n"
            "Explain this record in simple, clear language the patient can understand. "
            "List 3-5 key points. If it is a lab report, explain what each value means "
            "and whether it is in normal range based on the record data only."
        )

        explanation, model_used = self._generate(prompt)

        # Extract key points
        key_points = [
            line.strip().lstrip("•-*1234567890. ")
            for line in explanation.split("\n")
            if line.strip() and len(line.strip()) > 10
        ][:5]

        return AIExplainResponse(
            record_id=record_id,
            record_type=record_type,
            explanation=explanation,
            key_points=key_points if key_points else [explanation[:200]],
            model_used=model_used,
            generated_at=datetime.utcnow()
        )

    async def explain_prescription(
        self, prescription_id: str, prescription_data: Dict[str, Any]
    ) -> AIExplainResponse:
        """Explain a prescription — what it is, how to take it, side effects."""
        sanitized = {k: str(v)[:300] for k, v in prescription_data.items() if v}

        prompt = (
            f"{MEDICAL_SYSTEM_PROMPT}\n\n"
            f"Prescription Details: {sanitized}\n\n"
            "Explain this prescription to the patient in plain language:\n"
            "1. What this medicine is commonly used for\n"
            "2. How to take it (based on the dosage and frequency in the record)\n"
            "3. Common side effects to be aware of\n"
            "4. Important instructions\n"
            "Remember: Only explain based on the prescription record. Do not add instructions "
            "beyond what is written. Remind the patient to follow their doctor's specific instructions."
        )

        explanation, model_used = self._generate(prompt)

        lines = [l.strip() for l in explanation.split("\n") if l.strip()]
        key_points = [l for l in lines if len(l) > 10][:4]

        # Extract side effects section if present
        side_effects = []
        in_side_effects = False
        for line in lines:
            if "side effect" in line.lower():
                in_side_effects = True
            elif in_side_effects and line.startswith(("-", "•", "*")):
                side_effects.append(line.lstrip("-•* "))
            elif in_side_effects and len(side_effects) > 3:
                break

        return AIExplainResponse(
            record_id=prescription_id,
            record_type="prescription",
            explanation=explanation,
            key_points=key_points,
            side_effects=side_effects if side_effects else None,
            model_used=model_used,
            generated_at=datetime.utcnow()
        )

    async def explain_trends(
        self, patient_id: str, trend_data: Dict[str, Any]
    ) -> AIExplainResponse:
        """Explain wearable health metric trends in plain language."""
        sanitized = str(trend_data)[:800]

        prompt = (
            f"{MEDICAL_SYSTEM_PROMPT}\n\n"
            f"Patient Health Metric Trends (last 30 days): {sanitized}\n\n"
            "Explain these health trends to the patient in simple terms:\n"
            "1. What the trends show overall\n"
            "2. Which metrics are improving and which need attention\n"
            "3. Any notable patterns\n"
            "Base your explanation ONLY on the data provided above."
        )

        explanation, model_used = self._generate(prompt)
        key_points = [l.strip() for l in explanation.split("\n") if l.strip() and len(l.strip()) > 15][:4]

        return AIExplainResponse(
            record_id=patient_id,
            record_type="wearable_trends",
            explanation=explanation,
            key_points=key_points,
            model_used=model_used,
            generated_at=datetime.utcnow()
        )

    async def chat(
        self,
        question: str,
        patient_context: str,
        retrieved_chunks: List[Dict[str, Any]],
        top_k: int = 5
    ) -> AIChatResponse:
        """
        RAG-backed health Q&A.
        retrieved_chunks: list of {text, record_id, record_type, record_title, record_date, score}
        """
        sanitized_question = self._sanitize_input(question)

        # Build context from retrieved chunks
        context_parts = []
        cited_sources = []
        for chunk in retrieved_chunks[:top_k]:
            context_parts.append(f"[{chunk.get('record_type', 'record')}] {chunk.get('text', '')[:400]}")
            cited_sources.append(CitedSource(
                record_id=chunk.get("record_id", ""),
                record_type=chunk.get("record_type", ""),
                record_title=chunk.get("record_title", ""),
                record_date=chunk.get("record_date"),
                relevance_score=chunk.get("score", 0.0)
            ))

        context = "\n---\n".join(context_parts) if context_parts else "No relevant records found."
        patient_ctx = str(patient_context)[:400] if patient_context else ""

        prompt = (
            f"{MEDICAL_SYSTEM_PROMPT}\n\n"
            f"Patient Profile Summary: {patient_ctx}\n\n"
            f"Relevant Health Records:\n{context}\n\n"
            f"Patient Question: {sanitized_question}\n\n"
            "Answer the patient's question based ONLY on their health records shown above. "
            "If the answer is not in their records, say so clearly. "
            "Do not provide medical advice beyond explaining what is in the records."
        )

        answer, model_used = self._generate(prompt)

        return AIChatResponse(
            question=sanitized_question,
            answer=answer,
            cited_sources=cited_sources,
            model_used=model_used,
            is_medical_advice=False,
            generated_at=datetime.utcnow()
        )


# Singleton instance
ai_service = AIService()
