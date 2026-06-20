"""
MODULE 2 — PART B: Pydantic Schemas
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────
# OCR SCHEMAS
# ─────────────────────────────────────────────

class OCRJobCreate(BaseModel):
    document_type: str = Field(..., description="prescription | lab_report | medical_document")

class OCRJobResponse(BaseModel):
    id: UUID
    patient_id: UUID
    document_type: str
    status: str
    confidence_score: Optional[float] = None
    structured_data: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ExtractedPrescriptionResponse(BaseModel):
    id: UUID
    ocr_job_id: UUID
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    doctor_name: Optional[str] = None
    hospital_clinic: Optional[str] = None
    prescription_date: Optional[datetime] = None
    instructions: Optional[str] = None
    refills: Optional[int] = None
    raw_confidence: Optional[float] = None
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ExtractedLabValueResponse(BaseModel):
    id: UUID
    ocr_job_id: UUID
    test_name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: Optional[bool] = None
    lab_date: Optional[datetime] = None
    ordering_doctor: Optional[str] = None
    lab_name: Optional[str] = None
    raw_confidence: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OCRResultResponse(BaseModel):
    job: OCRJobResponse
    prescriptions: list[ExtractedPrescriptionResponse] = []
    lab_values: list[ExtractedLabValueResponse] = []


# ─────────────────────────────────────────────
# CHAT / AI ASSISTANT SCHEMAS
# ─────────────────────────────────────────────

class ChatSessionCreate(BaseModel):
    mode: str = Field(default="full", description="mini | full")
    title: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: UUID
    patient_id: UUID
    mode: str
    title: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_message_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)

class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    retrieved_sources: Optional[list[dict[str, Any]]] = None
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class ChatTurnResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    sources_used: int = 0


class MiniAssistantResponse(BaseModel):
    upcoming_appointments: list[dict[str, Any]] = []
    current_doctor: Optional[str] = None
    medication_reminders: list[dict[str, Any]] = []
    recent_reports: list[dict[str, Any]] = []
    summary: str = ""


# ─────────────────────────────────────────────
# RAG SCHEMAS
# ─────────────────────────────────────────────

class EmbedDocumentRequest(BaseModel):
    source_type: str
    source_id: UUID

class EmbedDocumentResponse(BaseModel):
    source_type: str
    source_id: UUID
    chunks_embedded: int
    chroma_ids: list[str]
    status: str

class RetrievalResult(BaseModel):
    chroma_document_id: str
    source_type: str
    source_id: str
    chunk_text: str
    relevance_score: float
    metadata: dict[str, Any] = {}


# ─────────────────────────────────────────────
# ANALYTICS SCHEMAS
# ─────────────────────────────────────────────

class MedicationAdherenceResponse(BaseModel):
    patient_id: UUID
    period: str
    period_start: datetime
    period_end: datetime
    total_medications: int
    missed_doses: int
    adherence_percentage: float
    medications_detail: list[dict[str, Any]] = []

class AppointmentComplianceResponse(BaseModel):
    patient_id: UUID
    period: str
    period_start: datetime
    period_end: datetime
    total_appointments: int
    missed_appointments: int
    completion_percentage: float
    appointments_detail: list[dict[str, Any]] = []

class VitalTrendPoint(BaseModel):
    date: datetime
    value: float
    unit: Optional[str] = None

class VitalTrendResponse(BaseModel):
    patient_id: UUID
    metric: str
    period: str
    trend: list[VitalTrendPoint]
    average: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    trend_direction: Optional[str] = None  # increasing | decreasing | stable

class HealthSummaryResponse(BaseModel):
    patient_id: UUID
    period: str
    period_start: datetime
    period_end: datetime
    medication_adherence_pct: Optional[float] = None
    appointment_completion_pct: Optional[float] = None
    avg_heart_rate: Optional[float] = None
    avg_blood_pressure_systolic: Optional[float] = None
    avg_blood_pressure_diastolic: Optional[float] = None
    avg_blood_sugar: Optional[float] = None
    avg_weight: Optional[float] = None


# ─────────────────────────────────────────────
# WEARABLE ANALYTICS SCHEMAS
# ─────────────────────────────────────────────

class WearableOCRCreate(BaseModel):
    source_app: Optional[str] = Field(None, description="DaFit | Fitbit | Apple Health | etc.")

class WearableOCRResponse(BaseModel):
    id: UUID
    patient_id: UUID
    source_app: Optional[str]
    status: str
    extracted_metrics: Optional[dict[str, Any]] = None
    stored_metric_ids: Optional[list[str]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WearableTrendPoint(BaseModel):
    timestamp: datetime
    value: float
    metric_type: str

class WearableTrendResponse(BaseModel):
    patient_id: UUID
    metric_type: str
    period_days: int
    data_points: list[WearableTrendPoint]
    average: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    trend_direction: Optional[str] = None

class WearableAnomalyResponse(BaseModel):
    patient_id: UUID
    metric_type: str
    anomaly_timestamp: datetime
    observed_value: float
    expected_range_low: float
    expected_range_high: float
    severity: str   # low | medium | high
    description: str

class ActivityScoreResponse(BaseModel):
    patient_id: UUID
    period_days: int
    total_steps: int
    avg_daily_steps: float
    total_calories: float
    avg_sleep_hours: float
    avg_blood_oxygen: Optional[float] = None
    activity_score: float           # 0–100
    score_label: str                # Poor | Fair | Good | Excellent


# ─────────────────────────────────────────────
# AI HEALTH INSIGHTS SCHEMAS
# ─────────────────────────────────────────────

class AIInsightResponse(BaseModel):
    id: UUID
    insight_type: str
    title: str
    summary: str
    detail: Optional[str] = None
    metric_delta: Optional[float] = None
    metric_unit: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    is_read: bool
    generated_at: datetime

    model_config = {"from_attributes": True}

class InsightListResponse(BaseModel):
    patient_id: UUID
    total: int
    unread: int
    insights: list[AIInsightResponse]


# ─────────────────────────────────────────────
# COMMON
# ─────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
