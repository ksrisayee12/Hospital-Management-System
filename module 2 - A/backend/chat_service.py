"""
MODULE 2 — PART B: Chat Service
Manages Mini Assistant (dashboard widget) and Full Health Assistant (chat system).
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.logging_config import get_logger
from models.part_b_models import ChatSession, ChatMessage, ChatMode
from services.rag.rag_service import RAGService
from schemas.part_b_schemas import MiniAssistantResponse

logger = get_logger(__name__)


class ChatService:

    def __init__(self):
        self.rag = RAGService()

    # ── Session Management ───────────────────────

    async def create_session(
        self, db: AsyncSession, patient_id: UUID, mode: str = "full", title: Optional[str] = None
    ) -> ChatSession:
        session = ChatSession(
            patient_id=patient_id,
            mode=ChatMode(mode),
            title=title or f"Chat {datetime.utcnow().strftime('%b %d, %Y')}",
        )
        db.add(session)
        await db.flush()
        return session

    async def get_session(
        self, db: AsyncSession, session_id: UUID, patient_id: UUID
    ) -> Optional[ChatSession]:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.id == session_id,
                ChatSession.patient_id == patient_id,  # enforce patient isolation
                ChatSession.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def list_sessions(
        self, db: AsyncSession, patient_id: UUID, limit: int = 20
    ) -> list[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.patient_id == patient_id, ChatSession.is_active == True)
            .order_by(desc(ChatSession.last_message_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def close_session(self, db: AsyncSession, session: ChatSession) -> None:
        session.is_active = False
        await db.flush()

    # ── Full Assistant ────────────────────────────

    async def chat_turn(
        self,
        db: AsyncSession,
        session: ChatSession,
        patient_name: str,
        user_content: str,
    ) -> dict[str, Any]:
        """Process one full-assistant turn: user message → RAG → assistant reply."""
        # 1. Persist user message
        user_msg = ChatMessage(
            session_id=session.id,
            patient_id=session.patient_id,
            role="user",
            content=user_content,
        )
        db.add(user_msg)
        await db.flush()

        # 2. Load recent history for context
        history = await self._load_history(db, session.id, last_n=6)

        # 3. RAG pipeline
        rag_result = await self.rag.answer(
            patient_id=str(session.patient_id),
            patient_name=patient_name,
            question=user_content,
            conversation_history=history,
        )

        # 4. Persist assistant reply
        assistant_msg = ChatMessage(
            session_id=session.id,
            patient_id=session.patient_id,
            role="assistant",
            content=rag_result["answer"],
            retrieved_sources=rag_result["sources"],
            retrieval_count=rag_result["retrieval_count"],
            model_used=rag_result["model_used"],
            latency_ms=rag_result["latency_ms"],
        )
        db.add(assistant_msg)

        # 5. Update session timestamp
        session.last_message_at = datetime.utcnow()
        await db.flush()

        return {
            "user_message": user_msg,
            "assistant_message": assistant_msg,
            "sources_used": rag_result["retrieval_count"],
        }

    # ── Mini Assistant ────────────────────────────

    async def get_mini_assistant_data(
        self,
        db: AsyncSession,
        patient_id: UUID,
    ) -> MiniAssistantResponse:
        """
        Dashboard widget: returns structured data without RAG LLM call.
        Queries the existing Part A tables directly for speed.
        """
        now = datetime.utcnow()
        upcoming_appts = await self._get_upcoming_appointments(db, patient_id, now)
        current_doctor = await self._get_current_doctor(db, patient_id)
        med_reminders = await self._get_medication_reminders(db, patient_id)
        recent_reports = await self._get_recent_reports(db, patient_id)

        return MiniAssistantResponse(
            upcoming_appointments=upcoming_appts,
            current_doctor=current_doctor,
            medication_reminders=med_reminders,
            recent_reports=recent_reports,
            summary=self._build_summary(upcoming_appts, med_reminders, current_doctor),
        )

    # ── Private helpers ──────────────────────────

    async def _load_history(
        self, db: AsyncSession, session_id: UUID, last_n: int = 6
    ) -> list[dict[str, str]]:
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(last_n)
        )
        messages = list(reversed(result.scalars().all()))
        return [{"role": m.role, "content": m.content} for m in messages]

    async def _get_upcoming_appointments(
        self, db: AsyncSession, patient_id: UUID, since: datetime
    ) -> list[dict[str, Any]]:
        from sqlalchemy import text
        # Use Part A's appointments table
        result = await db.execute(
            text("""
                SELECT id, appointment_date, doctor_name, department, status
                FROM appointments
                WHERE patient_id = :pid
                  AND appointment_date >= :now
                  AND status NOT IN ('cancelled', 'completed')
                ORDER BY appointment_date ASC
                LIMIT 5
            """),
            {"pid": str(patient_id), "now": since},
        )
        rows = result.fetchall()
        return [
            {
                "id": str(r.id),
                "date": r.appointment_date.isoformat(),
                "doctor": r.doctor_name,
                "department": r.department,
                "status": r.status,
            }
            for r in rows
        ]

    async def _get_current_doctor(self, db: AsyncSession, patient_id: UUID) -> Optional[str]:
        from sqlalchemy import text
        result = await db.execute(
            text("""
                SELECT doctor_name FROM appointments
                WHERE patient_id = :pid AND status = 'completed'
                ORDER BY appointment_date DESC LIMIT 1
            """),
            {"pid": str(patient_id)},
        )
        row = result.fetchone()
        return row.doctor_name if row else None

    async def _get_medication_reminders(
        self, db: AsyncSession, patient_id: UUID
    ) -> list[dict[str, Any]]:
        from sqlalchemy import text
        result = await db.execute(
            text("""
                SELECT id, medicine_name, dosage, frequency, end_date
                FROM prescriptions
                WHERE patient_id = :pid
                  AND (end_date IS NULL OR end_date >= CURRENT_DATE)
                ORDER BY created_at DESC LIMIT 10
            """),
            {"pid": str(patient_id)},
        )
        return [
            {
                "id": str(r.id),
                "medicine": r.medicine_name,
                "dosage": r.dosage,
                "frequency": r.frequency,
                "end_date": r.end_date.isoformat() if r.end_date else None,
            }
            for r in result.fetchall()
        ]

    async def _get_recent_reports(
        self, db: AsyncSession, patient_id: UUID
    ) -> list[dict[str, Any]]:
        from sqlalchemy import text
        result = await db.execute(
            text("""
                SELECT id, report_type, report_date, doctor_name
                FROM reports
                WHERE patient_id = :pid
                ORDER BY report_date DESC LIMIT 5
            """),
            {"pid": str(patient_id)},
        )
        return [
            {
                "id": str(r.id),
                "type": r.report_type,
                "date": r.report_date.isoformat() if r.report_date else None,
                "doctor": r.doctor_name,
            }
            for r in result.fetchall()
        ]

    def _build_summary(
        self, appointments: list, reminders: list, doctor: Optional[str]
    ) -> str:
        parts = []
        if appointments:
            next_appt = appointments[0]
            parts.append(f"Next appointment: {next_appt['date'][:10]} with {next_appt['doctor']}")
        if doctor:
            parts.append(f"Current doctor: {doctor}")
        if reminders:
            parts.append(f"{len(reminders)} active medication(s)")
        return " · ".join(parts) if parts else "No immediate health activities."
