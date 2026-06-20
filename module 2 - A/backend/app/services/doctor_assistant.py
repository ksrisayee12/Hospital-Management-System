"""
Doctor Patient Assistant.
A RAG-backed chatbot strictly scoped to assist a doctor querying a specific patient's dataset.
Allows comprehensive access to the patient's history including raw reports and OCR data.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

from app.schemas import AIChatResponse, CitedSource
from app.services.ai_service import ai_service
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

# System prompt emphasizing clinical context.
DOCTOR_CHAT_SYSTEM_PROMPT = (
    "You are the Doctor Patient Assistant for a secure health vault application. "
    "You are directly assisting a qualified healthcare provider. "
    "Your objective is to provide comprehensive clinical summaries, summarize OCR results, "
    "and identify relevant trends across the patient's entire medical history. "
    "You may reference detailed clinical values and reports, as the user is an authorized medical professional. "
    "Always rely strictly on the provided patient context. Do not invent details."
)

class DoctorPatientAssistant:
    """Chatbot specifically for doctors querying a patient's records."""

    async def chat(
        self,
        patient_id: str,
        question: str,
        top_k: int = 10
    ) -> AIChatResponse:
        """
        Retrieves all relevant patient records and generates a clinical summary response.
        Note: The doctor has full access to the patient's RAG index (no type filtering).
        """
        # 1. Retrieve records via RAG (no record type restrictions for doctor)
        chunks = await rag_service.query(
            patient_id=patient_id, 
            query_text=question, 
            top_k=top_k,
            allowed_record_types=None # Allows raw_report, ocr_dump, clinical_notes, etc.
        )
        
        # 2. Sanitize user input
        sanitized_question = ai_service._sanitize_input(question)
        
        # 3. Build context
        context_parts = []
        cited_sources = []
        for chunk in chunks[:top_k]:
            context_parts.append(f"[{chunk.get('record_type', 'record')}] {chunk.get('text', '')[:600]}")
            cited_sources.append(CitedSource(
                record_id=chunk.get("record_id", ""),
                record_type=chunk.get("record_type", ""),
                record_title=chunk.get("record_title", ""),
                record_date=chunk.get("record_date"),
                relevance_score=chunk.get("score", 0.0)
            ))
            
        context = "\n---\n".join(context_parts) if context_parts else "No relevant records found in this patient's vault."
        
        # 4. Construct prompt
        prompt = (
            f"{DOCTOR_CHAT_SYSTEM_PROMPT}\n\n"
            f"Patient Context Dataset:\n{context}\n\n"
            f"Provider Query: {sanitized_question}\n\n"
            "Provide a clinical summary answering the provider's query based ONLY on the dataset above."
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

doctor_assistant = DoctorPatientAssistant()
