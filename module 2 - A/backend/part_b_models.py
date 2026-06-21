"""
MODULE 2 — PART B: SQLAlchemy Models
Extends Part A without modification.
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    DateTime, JSON, ForeignKey, Enum as SAEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
import enum

# Import Base from Part A's database module
from app.database import Base  # adjust path to your Part A base


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class OCRDocumentType(str, enum.Enum):
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    MEDICAL_DOCUMENT = "medical_document"
    WEARABLE_SCREENSHOT = "wearable_screenshot"

class OCRStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ChatMode(str, enum.Enum):
    MINI = "mini"
    FULL = "full"

class EmbeddingStatus(str, enum.Enum):
    PENDING = "pending"
    EMBEDDED = "embedded"
    FAILED = "failed"

class AnalyticsPeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class InsightType(str, enum.Enum):
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    VITALS = "vitals"
    SLEEP = "sleep"
    ACTIVITY = "activity"
    GENERAL = "general"


# ─────────────────────────────────────────────
# OCR JOBS
# ─────────────────────────────────────────────

class OCRJob(Base):
    __tablename__ = "ocr_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    document_type = Column(SAEnum(OCRDocumentType), nullable=False)
    status = Column(SAEnum(OCRStatus), default=OCRStatus.PENDING, nullable=False)
    original_file_url = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=True)
    raw_extracted_text = Column(Text, nullable=True)
    structured_data = Column(JSONB, nullable=True)      # parsed fields
    confidence_score = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    ocr_engine_version = Column(String(50), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="ocr_jobs")
    extracted_prescriptions = relationship("ExtractedPrescription", back_populates="ocr_job")
    extracted_lab_values = relationship("ExtractedLabValue", back_populates="ocr_job")

    __table_args__ = (
        Index("ix_ocr_jobs_patient_id", "patient_id"),
        Index("ix_ocr_jobs_status", "status"),
    )


class ExtractedPrescription(Base):
    """Structured prescription data from OCR."""
    __tablename__ = "extracted_prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ocr_job_id = Column(UUID(as_uuid=True), ForeignKey("ocr_jobs.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    prescription_id = Column(UUID(as_uuid=True), ForeignKey("prescriptions.id"), nullable=True)

    medicine_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    duration = Column(String(100), nullable=True)
    doctor_name = Column(String(255), nullable=True)
    hospital_clinic = Column(String(255), nullable=True)
    prescription_date = Column(DateTime, nullable=True)
    instructions = Column(Text, nullable=True)
    refills = Column(Integer, nullable=True)
    raw_confidence = Column(Float, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    ocr_job = relationship("OCRJob", back_populates="extracted_prescriptions")

    __table_args__ = (
        Index("ix_extracted_prescriptions_patient_id", "patient_id"),
    )


class ExtractedLabValue(Base):
    """Structured lab values from OCR."""
    __tablename__ = "extracted_lab_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ocr_job_id = Column(UUID(as_uuid=True), ForeignKey("ocr_jobs.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    report_id = Column(UUID(as_uuid=True), ForeignKey("reports.id"), nullable=True)

    test_name = Column(String(255), nullable=False)
    value = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    reference_range = Column(String(100), nullable=True)
    is_abnormal = Column(Boolean, nullable=True)
    lab_date = Column(DateTime, nullable=True)
    ordering_doctor = Column(String(255), nullable=True)
    lab_name = Column(String(255), nullable=True)
    raw_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ocr_job = relationship("OCRJob", back_populates="extracted_lab_values")

    __table_args__ = (
        Index("ix_extracted_lab_values_patient_id", "patient_id"),
        Index("ix_extracted_lab_values_test_name", "test_name"),
    )


# ─────────────────────────────────────────────
# RAG / EMBEDDINGS
# ─────────────────────────────────────────────

class DocumentEmbedding(Base):
    """Tracks which documents have been embedded in ChromaDB."""
    __tablename__ = "document_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    source_type = Column(String(50), nullable=False)    # medical_record, prescription, report, etc.
    source_id = Column(UUID(as_uuid=True), nullable=False)
    chroma_document_id = Column(String(255), nullable=False, unique=True)
    chunk_index = Column(Integer, default=0)
    chunk_text = Column(Text, nullable=True)
    status = Column(SAEnum(EmbeddingStatus), default=EmbeddingStatus.PENDING)
    model_name = Column(String(100), nullable=True)
    embedded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_document_embeddings_patient_source", "patient_id", "source_type", "source_id"),
        Index("ix_document_embeddings_chroma_id", "chroma_document_id"),
    )


# ─────────────────────────────────────────────
# CHAT SESSIONS
# ─────────────────────────────────────────────

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    mode = Column(SAEnum(ChatMode), nullable=False, default=ChatMode.FULL)
    title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, nullable=True)

    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")

    __table_args__ = (
        Index("ix_chat_sessions_patient_id", "patient_id"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    role = Column(String(20), nullable=False)            # user | assistant
    content = Column(Text, nullable=False)
    retrieved_sources = Column(JSONB, nullable=True)     # which records were used
    retrieval_count = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        Index("ix_chat_messages_session_id", "session_id"),
    )


# ─────────────────────────────────────────────
# ANALYTICS SNAPSHOTS
# ─────────────────────────────────────────────

class HealthAnalyticsSnapshot(Base):
    """Pre-computed analytics snapshots per patient per period."""
    __tablename__ = "health_analytics_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    period = Column(SAEnum(AnalyticsPeriod), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    medication_adherence_pct = Column(Float, nullable=True)
    appointment_completion_pct = Column(Float, nullable=True)
    total_medications = Column(Integer, nullable=True)
    missed_doses = Column(Integer, nullable=True)
    total_appointments = Column(Integer, nullable=True)
    missed_appointments = Column(Integer, nullable=True)

    avg_heart_rate = Column(Float, nullable=True)
    avg_blood_pressure_systolic = Column(Float, nullable=True)
    avg_blood_pressure_diastolic = Column(Float, nullable=True)
    avg_blood_sugar = Column(Float, nullable=True)
    avg_weight = Column(Float, nullable=True)

    computed_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_analytics_patient_period", "patient_id", "period", "period_start"),
    )


# ─────────────────────────────────────────────
# WEARABLE OCR JOBS
# ─────────────────────────────────────────────

class WearableOCRJob(Base):
    """Tracks screenshot-to-wearable-metrics pipeline jobs."""
    __tablename__ = "wearable_ocr_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    screenshot_url = Column(Text, nullable=False)
    source_app = Column(String(100), nullable=True)     # DaFit, Fitbit, etc.
    status = Column(SAEnum(OCRStatus), default=OCRStatus.PENDING)
    raw_text = Column(Text, nullable=True)
    extracted_metrics = Column(JSONB, nullable=True)
    stored_metric_ids = Column(JSONB, nullable=True)    # list of wearable_metrics IDs created
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_wearable_ocr_jobs_patient_id", "patient_id"),
    )


# ─────────────────────────────────────────────
# AI HEALTH INSIGHTS
# ─────────────────────────────────────────────

class AIHealthInsight(Base):
    __tablename__ = "ai_health_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    insight_type = Column(SAEnum(InsightType), nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    detail = Column(Text, nullable=True)
    metric_delta = Column(Float, nullable=True)         # e.g. +12 for 12% increase
    metric_unit = Column(String(50), nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    is_read = Column(Boolean, default=False)
    model_used = Column(String(100), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_ai_health_insights_patient_id", "patient_id"),
        Index("ix_ai_health_insights_type", "insight_type"),
    )
