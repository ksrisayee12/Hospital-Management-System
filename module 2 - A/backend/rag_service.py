"""
MODULE 2 — PART B: RAG Service
Full retrieval-augmented generation pipeline:
  Question → ChromaDB Search → Context Builder → BioMistral/MedGemma → Answer
"""

from __future__ import annotations

import time
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.exceptions import NoRelevantContextError, AIModelError
from core.logging_config import get_logger
from services.rag.embedding_service import EmbeddingService
from services.rag.ai_model_service import AIModelService

settings = get_settings()
logger = get_logger(__name__)


class ContextBuilder:
    """Assembles retrieved chunks into a structured prompt context."""

    MAX_CONTEXT_CHARS = 3500

    def build(self, retrieved: list[dict[str, Any]], patient_name: str = "the patient") -> str:
        if not retrieved:
            return ""

        sections: dict[str, list[str]] = {}
        for item in retrieved:
            src = item.get("source_type", "record")
            sections.setdefault(src, []).append(item["chunk_text"])

        parts = [f"PATIENT MEDICAL RECORDS (patient: {patient_name})\n{'='*50}"]
        total = 0
        for src_type, chunks in sections.items():
            header = f"\n[{src_type.upper().replace('_', ' ')}]\n"
            parts.append(header)
            for chunk in chunks:
                if total + len(chunk) > self.MAX_CONTEXT_CHARS:
                    break
                parts.append(chunk)
                total += len(chunk)

        return "\n".join(parts)

    def build_sources_list(self, retrieved: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "source_type": r.get("source_type"),
                "source_id": r.get("source_id"),
                "relevance_score": r.get("relevance_score"),
            }
            for r in retrieved
        ]


class RAGService:
    """Orchestrates the full RAG pipeline."""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.ai_service = AIModelService()
        self.context_builder = ContextBuilder()

    async def answer(
        self,
        patient_id: str,
        patient_name: str,
        question: str,
        conversation_history: Optional[list[dict[str, str]]] = None,
        source_type_filter: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Full RAG turn:
        1. Embed the question and retrieve relevant chunks from patient's collection.
        2. Build structured context.
        3. Generate answer via BioMistral / MedGemma.
        Returns answer + sources + timing metadata.
        """
        t0 = time.perf_counter()

        # Step 1 — Retrieve
        retrieved = await self.embedding_service.query(
            patient_id=patient_id,
            query_text=question,
            top_k=settings.rag_top_k,
            source_type_filter=source_type_filter,
        )

        if not retrieved:
            # Graceful: answer without context rather than hard error
            context = ""
            answer = (
                "I couldn't find relevant records to answer your question. "
                "Please ensure your health records have been uploaded and processed."
            )
            sources = []
        else:
            # Step 2 — Build context
            context = self.context_builder.build(retrieved, patient_name)
            sources = self.context_builder.build_sources_list(retrieved)

            # Step 3 — Generate
            answer = await self.ai_service.generate(
                question=question,
                context=context,
                conversation_history=conversation_history or [],
            )

        latency_ms = int((time.perf_counter() - t0) * 1000)
        logger.info(
            "RAG answer generated",
            extra={
                "patient_id": patient_id,
                "retrieved": len(retrieved),
                "latency_ms": latency_ms,
            },
        )
        return {
            "answer": answer,
            "sources": sources,
            "retrieval_count": len(retrieved),
            "latency_ms": latency_ms,
            "model_used": self.ai_service.active_model,
        }

    async def index_patient_record(
        self,
        patient_id: str,
        source_type: str,
        source_id: str,
        text: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> list[str]:
        """Embed a new or updated patient record into their ChromaDB collection."""
        return await self.embedding_service.embed_document(
            patient_id=patient_id,
            source_type=source_type,
            source_id=source_id,
            text=text,
            metadata=metadata,
        )

    async def remove_patient_record(
        self, patient_id: str, source_type: str, source_id: str
    ) -> int:
        return await self.embedding_service.delete_document(patient_id, source_type, source_id)
