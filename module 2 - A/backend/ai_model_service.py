"""
MODULE 2 — PART B: AI Model Service
Wraps BioMistral / MedGemma with healthcare-specific prompt templates.
Models are loaded lazily; only one is active at a time to conserve VRAM.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from core.config import get_settings
from core.exceptions import AIModelError, AIModelUnavailableError
from core.logging_config import get_logger

settings = get_settings()
logger = get_logger(__name__)


SYSTEM_PROMPT = """You are a compassionate and accurate AI health assistant integrated into a \
patient-owned health platform. You ONLY answer questions based on the patient's own medical \
records provided in the context below. You NEVER share or reference any other patient's data. \
If the answer is not in the records, say so honestly. Always recommend consulting a healthcare \
provider for medical decisions. Do not diagnose or prescribe."""

CONTEXT_PROMPT_TEMPLATE = """{system_prompt}

---
PATIENT RECORDS CONTEXT:
{context}
---

CONVERSATION HISTORY:
{history}

PATIENT QUESTION: {question}

ASSISTANT ANSWER:"""


class AIModelService:
    """
    Lazy-loaded BioMistral / MedGemma wrapper.
    Uses transformers pipeline in a thread pool to avoid blocking the event loop.
    """

    _pipeline: Any = None
    _loaded_model: Optional[str] = None

    @property
    def active_model(self) -> str:
        return self._loaded_model or settings.default_ai_model

    def _load_model(self) -> Any:
        """Lazy-load the selected model. Called in a thread pool."""
        if self._pipeline is not None:
            return self._pipeline

        model_name = settings.default_ai_model
        logger.info("Loading AI model: %s", model_name)

        try:
            from transformers import pipeline as hf_pipeline

            if model_name == "biomistral":
                model_path = settings.biomistral_model_path
            else:
                model_path = settings.medgemma_model_path

            self._pipeline = hf_pipeline(
                "text-generation",
                model=model_path,
                max_new_tokens=settings.ai_max_tokens,
                temperature=settings.ai_temperature,
                do_sample=True,
                return_full_text=False,
                device_map="auto",
            )
            self._loaded_model = model_name
            logger.info("AI model loaded: %s", model_name)
            return self._pipeline

        except Exception as exc:
            logger.error("AI model load failed", exc_info=True)
            raise AIModelUnavailableError(str(exc)) from exc

    def _run_inference(self, prompt: str) -> str:
        pipe = self._load_model()
        try:
            result = pipe(prompt)
            return result[0]["generated_text"].strip()
        except Exception as exc:
            raise AIModelError(f"Inference failed: {exc}") from exc

    async def generate(
        self,
        question: str,
        context: str,
        conversation_history: list[dict[str, str]] = None,
    ) -> str:
        """Async wrapper — runs blocking inference in a thread pool."""
        history_text = self._format_history(conversation_history or [])
        prompt = CONTEXT_PROMPT_TEMPLATE.format(
            system_prompt=SYSTEM_PROMPT,
            context=context or "No records available.",
            history=history_text or "None",
            question=question,
        )
        loop = asyncio.get_event_loop()
        try:
            answer = await loop.run_in_executor(None, self._run_inference, prompt)
        except AIModelUnavailableError:
            raise
        except Exception as exc:
            raise AIModelError(str(exc)) from exc
        return answer

    def _format_history(self, history: list[dict[str, str]]) -> str:
        if not history:
            return ""
        lines = []
        for turn in history[-6:]:  # last 3 turns
            role = turn.get("role", "user").capitalize()
            content = turn.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)
