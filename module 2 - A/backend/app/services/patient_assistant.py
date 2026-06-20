"""
Patient Health Assistant.
A RAG-backed chatbot strictly scoped to the patient's context.
Enforces strict filtering of raw reports and sensitive data.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

from app.schemas import AIChatResponse, CitedSource
from app.services.ai_service import ai_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

# System prompt emphasizing safety and no raw data dumping.
PATIENT_CHAT_SYSTEM_PROMPT = (
    "You are the Patient Health Assistant for a secure health vault application. "
    "Your objective is to provide simple, clear explanations of health trends, medications, and appointments. "
    "CRITICAL SECURITY RULE: You must NEVER reveal the raw content of medical reports, doctor notes, or raw laboratory values. "
    "If a user asks to see a report or explicit lab values, respond EXACTLY with: "
    "'Your recent report appears stable. For detailed laboratory values, please view the report through the secure reports section.' "
    "Do not provide medical advice. Do not diagnose conditions."
)

class PatientHealthAssistant:
    """Chatbot specifically for patients."""

    # Explicitly allowed RAG categories for patients.
    ALLOWED_RECORD_TYPES = [
        "analytics", 
        "prescription", 
        "appointment", 
        "timeline_event", 
        "wearable_metric",
        "wearable_trends"
    ]

    async def chat(
        self,
        patient_id: str,
        question: str,
        top_k: int = 5
    ) -> AIChatResponse:
        """
        Retrieves filtered patient records and generates a safe response.
        """
        # 1. Retrieve explicitly allowed records via RAG
        chunks = await rag_service.query(
            patient_id=patient_id, 
            query_text=question, 
            top_k=top_k,
            allowed_record_types=self.ALLOWED_RECORD_TYPES
        )
        
        # 2. Sanitize user input
        sanitized_question = ai_service._sanitize_input(question)
        
        # 3. Build context
        context_parts = []
        cited_sources = []
        for chunk in chunks[:top_k]:
            context_parts.append(f"[{chunk.get('record_type', 'record')}] {chunk.get('text', '')[:400]}")
            cited_sources.append(CitedSource(
                record_id=chunk.get("record_id", ""),
                record_type=chunk.get("record_type", ""),
                record_title=chunk.get("record_title", ""),
                record_date=chunk.get("record_date"),
                relevance_score=chunk.get("score", 0.0)
            ))
            
        context = "\n---\n".join(context_parts) if context_parts else "No relevant records found."
        
        # 4. Construct prompt
        prompt = (
            f"{PATIENT_CHAT_SYSTEM_PROMPT}\n\n"
            f"Relevant Health Context (Sanitized):\n{context}\n\n"
            f"Patient Question: {sanitized_question}\n\n"
            "Answer the question based only on the provided context while obeying the security rules."
        )
        
        # 5. Generate response using the existing AI pipeline
        answer, model_used = ai_service._generate(prompt)
        
        return AIChatResponse(
            question=sanitized_question,
            answer=answer,
            cited_sources=cited_sources,
            model_used=model_used,
            is_medical_advice=False,
            generated_at=datetime.utcnow()
        )

patient_assistant = PatientHealthAssistant()
