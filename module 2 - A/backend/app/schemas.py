"""
Pydantic schemas for API request/response validation — Module 2 complete.
Includes existing schemas + new OCR, Safety, AI, Analytics, Insights schemas.
All outputs structured for inter-module consumption (Module 3, Module 4).
"""

from datetime import datetime, date
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, EmailStr, validator, computed_field
from enum import Enum


# ============================================================================
# COMMON SCHEMAS
# ============================================================================

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: List[Any]
    has_next: bool
    has_previous: bool


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Any] = None


class TimestampSchema(BaseModel):
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None


# ============================================================================
# PATIENT SCHEMAS
# ============================================================================

class PatientCreateRequest(BaseModel):
    user_id: str
    email: EmailStr
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    height_cm: Optional[float] = Field(None, gt=0, le=250)
    weight_kg: Optional[float] = Field(None, gt=0, le=500)
    known_allergies: Optional[List[str]] = None


class PatientUpdateRequest(BaseModel):
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    known_allergies: Optional[List[str]] = None


class PatientResponse(BaseModel):
    id: str
    user_id: str
    email: str
    phone: Optional[str]
    first_name: str
    last_name: str
    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    date_of_birth: Optional[date]
    gender: Optional[str]
    blood_group: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    zip_code: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relation: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    bmi: Optional[float]
    known_allergies: Optional[List[str]]
    vault_initialized: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class DashboardHealthStatus(BaseModel):
    total_conditions: int = 0
    critical_conditions: int = 0
    medications_active: int = 0
    allergies: int = 0
    last_checkup: Optional[date] = None


class DashboardUpcomingAppointment(BaseModel):
    id: str
    doctor_name: str
    specialty: Optional[str]
    appointment_date: datetime
    visit_type: Optional[str]


class DashboardResponse(BaseModel):
    patient_id: str
    welcome_message: str
    reports_count: int = 0
    prescriptions_count: int = 0
    appointments_count: int = 0
    allergies_count: int = 0
    health_status: DashboardHealthStatus
    upcoming_appointments: List[DashboardUpcomingAppointment]
    next_appointment: Optional[DashboardUpcomingAppointment]
    active_doctor_id: Optional[str]
    active_doctor_name: Optional[str]
    latest_insight: Optional[str] = None           # Latest AI insight summary
    pending_safety_alerts: int = 0                 # Count of HIGH/CRITICAL safety alerts


# ============================================================================
# MEDICAL RECORD SCHEMAS
# ============================================================================

class LabResult(BaseModel):
    test_name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    status: Optional[str] = None


class MedicalRecordCreateRequest(BaseModel):
    record_type: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    record_date: date
    provider_id: Optional[str] = None
    provider_name: str
    provider_facility: Optional[str] = None
    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None
    is_critical: bool = False
    requires_follow_up: bool = False
    follow_up_date: Optional[date] = None
    lab_results: Optional[List[LabResult]] = None
    file_id: Optional[str] = None


class MedicalRecordUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None
    is_critical: Optional[bool] = None
    is_archived: Optional[bool] = None
    requires_follow_up: Optional[bool] = None
    follow_up_date: Optional[date] = None
    lab_results: Optional[List[LabResult]] = None


class MedicalRecordResponse(BaseModel):
    id: str
    patient_id: str
    record_type: str
    title: str
    description: Optional[str]
    record_date: date
    provider_id: Optional[str]
    provider_name: str
    provider_facility: Optional[str]
    diagnosis: Optional[str]
    symptoms: Optional[str]
    treatment: Optional[str]
    notes: Optional[str]
    is_critical: bool
    is_archived: bool = False
    requires_follow_up: bool
    follow_up_date: Optional[date]
    lab_results: Optional[List[LabResult]]
    file_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# APPOINTMENT SCHEMAS
# ============================================================================

class AppointmentCreateRequest(BaseModel):
    doctor_id: str
    doctor_name: str
    doctor_specialty: Optional[str] = None
    facility_name: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    appointment_date: datetime
    duration_minutes: int = Field(default=30, ge=15, le=480)
    visit_type: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None


class AppointmentUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    visit_type: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None
    completed_date: Optional[datetime] = None
    next_appointment_date: Optional[datetime] = None


class AppointmentRescheduleRequest(BaseModel):
    requested_reschedule_date: datetime
    reschedule_reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    doctor_name: str
    doctor_specialty: Optional[str]
    facility_name: Optional[str]
    title: str
    description: Optional[str]
    appointment_date: datetime
    duration_minutes: int
    status: str
    visit_type: Optional[str]
    location: Optional[str]
    meeting_link: Optional[str]
    requested_reschedule_date: Optional[datetime]
    reschedule_reason: Optional[str]
    completed_date: Optional[datetime]
    notes: Optional[str]
    next_appointment_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# TIMELINE SCHEMAS
# ============================================================================

class TimelineEventResponse(BaseModel):
    id: str
    patient_id: str
    title: str
    description: Optional[str]
    event_date: date
    event_year: int
    event_month: Optional[int]
    event_type: Optional[str]
    severity: Optional[str]
    impact: Optional[str]
    action_taken: Optional[str]
    related_medical_record_id: Optional[str]
    related_appointment_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TimelineListResponse(BaseModel):
    year: int
    events: List[TimelineEventResponse]


# ============================================================================
# FAMILY ACCESS SCHEMAS
# ============================================================================

class FamilyAccessCreateRequest(BaseModel):
    family_member_email: EmailStr
    family_member_name: str
    relationship: str
    permission_level: str = "view_only"
    allowed_record_types: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    is_emergency_contact: bool = False


class FamilyAccessUpdateRequest(BaseModel):
    permission_level: Optional[str] = None
    allowed_record_types: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class FamilyAccessApprovalRequest(BaseModel):
    status: str
    rejection_reason: Optional[str] = None


class FamilyAccessResponse(BaseModel):
    id: str
    patient_id: str
    family_member_user_id: str
    family_member_email: str
    family_member_name: str
    relationship: str
    permission_level: str
    status: str
    is_emergency_contact: bool = False
    allowed_record_types: Optional[List[str]]
    requested_at: datetime
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]
    rejection_reason: Optional[str]
    revoked_at: Optional[datetime]
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class FamilyDashboardResponse(BaseModel):
    patient_id: str
    patient_name: str
    relationship: str
    permission_level: str
    health_status: Optional[DashboardHealthStatus]
    recent_records: List[MedicalRecordResponse]
    upcoming_appointments: List[AppointmentResponse]
    last_accessed: Optional[datetime]


# ============================================================================
# VAULT SCHEMAS
# ============================================================================

class VaultFileCreateRequest(BaseModel):
    file_name: str = Field(..., max_length=255)
    file_type: str
    category: Optional[str] = None
    description: Optional[str] = None
    is_shared_with_providers: bool = False
    shared_with_provider_ids: Optional[List[str]] = None


class VaultFileResponse(BaseModel):
    id: str
    patient_id: str
    original_filename: str
    file_type: str
    file_size_bytes: int
    category: Optional[str]
    description: Optional[str]
    upload_date: datetime
    encryption_algorithm: str
    encryption_key_version: str
    file_hash: Optional[str]
    ocr_processed: bool
    extraction_status: Optional[str]
    extraction_date: Optional[datetime]
    is_shared_with_providers: bool
    shared_with_provider_ids: Optional[List[str]]

    class Config:
        from_attributes = True


class VaultStorageStatsResponse(BaseModel):
    patient_id: str
    total_files: int
    total_size_bytes: int
    total_size_mb: float
    max_size_mb: int
    usage_percent: float
    files_by_type: dict
    files_by_category: dict
    ocr_processed_count: int
    ocr_pending_count: int


# ============================================================================
# WEARABLE SCHEMAS
# ============================================================================

class WearableMetricCreateRequest(BaseModel):
    metric_type: str
    metric_date: date
    metric_timestamp: datetime
    value: float = Field(..., gt=0)
    unit: str
    value_min: Optional[float] = None
    value_max: Optional[float] = None
    value_avg: Optional[float] = None
    source_device: Optional[str] = None
    source_app: Optional[str] = None
    notes: Optional[str] = None
    is_manual_entry: bool = False


class WearableMetricResponse(BaseModel):
    id: str
    patient_id: str
    metric_type: str
    metric_date: date
    metric_timestamp: datetime
    value: float
    unit: str
    value_min: Optional[float]
    value_max: Optional[float]
    value_avg: Optional[float]
    source_device: Optional[str]
    source_app: Optional[str]
    notes: Optional[str]
    is_manual_entry: bool
    data_integrity_verified: bool
    confidence_score: Optional[float]
    extracted_from_screenshot: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class WearableMetricsStatsResponse(BaseModel):
    patient_id: str
    date_range: dict
    metrics_by_type: dict
    total_records: int
    manual_entries: int
    auto_synced: int


class WearableBatchUploadRequest(BaseModel):
    source_device: str
    source_app: str
    metrics: List[WearableMetricCreateRequest]


class WearableGoalCreateRequest(BaseModel):
    metric_type: str
    target_value: float
    unit: str
    target_min: Optional[float] = None
    target_max: Optional[float] = None
    description: Optional[str] = None


class WearableGoalResponse(BaseModel):
    id: str
    patient_id: str
    metric_type: str
    target_value: float
    unit: str
    target_min: Optional[float]
    target_max: Optional[float]
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# PRESCRIPTION SCHEMAS
# ============================================================================

class PrescriptionCreateRequest(BaseModel):
    medicine_name: str
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None
    instructions: Optional[str] = None
    prescribing_doctor: Optional[str] = None
    prescribing_doctor_id: Optional[str] = None
    prescription_date: Optional[date] = None
    medical_record_id: Optional[str] = None
    notes: Optional[str] = None


class PrescriptionResponse(BaseModel):
    id: str
    patient_id: str
    medicine_name: str
    generic_name: Optional[str]
    dosage: Optional[str]
    frequency: Optional[str]
    duration: Optional[str]
    route: Optional[str]
    instructions: Optional[str]
    prescribing_doctor: Optional[str]
    prescription_date: Optional[date]
    status: str
    is_active: bool
    ocr_extraction_id: Optional[str]
    safety_analyzed: bool
    safety_record_id: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# OCR SCHEMAS
# ============================================================================

class OCRExtractedFields(BaseModel):
    """Fields extracted from a prescription/wearable image via PaddleOCR."""
    medicine_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    prescribing_doctor: Optional[str] = None
    prescription_date: Optional[str] = None
    notes: Optional[str] = None
    # Wearable-specific
    heart_rate: Optional[float] = None
    steps: Optional[int] = None
    sleep_hours: Optional[float] = None
    calories: Optional[float] = None
    blood_oxygen: Optional[float] = None
    raw_text: Optional[str] = None


class OCRExtractionResponse(BaseModel):
    """Response from OCR extraction pipeline."""
    extraction_id: str            # VaultFile ID of the uploaded image
    patient_id: str
    extraction_type: str          # prescription | wearable_screenshot
    status: str                   # completed | failed | partial
    extracted_fields: OCRExtractedFields
    confidence_score: float       # 0.0-1.0 overall confidence
    raw_text: str                 # Full OCR text
    # If prescription: ID of created Prescription record
    prescription_id: Optional[str] = None
    # If wearable: list of created WearableMetric IDs
    wearable_metric_ids: Optional[List[str]] = None
    safety_analysis: Optional["PrescriptionSafetyResponse"] = None
    processed_at: datetime


# ============================================================================
# PRESCRIPTION SAFETY SCHEMAS
# ============================================================================

class DrugWarning(BaseModel):
    """Individual drug warning."""
    warning_type: str               # INTERACTION | ALLERGY | DUPLICATE | DOSAGE | DANGEROUS_COMBO
    drugs_involved: List[str]
    description: str
    severity: str                   # low | medium | high | critical


class PrescriptionSafetyResponse(BaseModel):
    """Full safety analysis result — consumed by Module 3 (Doctor) and Module 4 (Governance)."""
    safety_id: str
    patient_id: str
    prescription_id: Optional[str]
    medicine_name: str

    risk_score: float               # 0-100
    risk_level: str                 # LOW | MEDIUM | HIGH | CRITICAL
    warnings: List[DrugWarning]
    interactions: List[Dict[str, Any]]
    allergy_conflicts: List[Dict[str, Any]]
    duplicate_ingredients: List[str]
    dosage_outliers: List[Dict[str, Any]]
    recommendations: List[str]
    auto_flagged: bool

    # Module 4 governance hook
    governance_alert_created: bool = False
    governance_alert_id: Optional[str] = None

    analyzed_at: datetime
    analysis_source: str

    class Config:
        from_attributes = True


# ============================================================================
# AI ASSISTANT SCHEMAS
# ============================================================================

class CitedSource(BaseModel):
    """Source citation for RAG responses."""
    record_id: str
    record_type: str
    record_title: str
    record_date: Optional[date]
    relevance_score: float


class AIChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    include_wearable_context: bool = True
    top_k: int = Field(default=5, ge=1, le=20)


class AIChatResponse(BaseModel):
    """RAG-backed AI chat response — includes citations for Module 3 audit."""
    question: str
    answer: str
    cited_sources: List[CitedSource]
    model_used: str
    is_medical_advice: bool = False   # Always False — disclaimer enforcement
    disclaimer: str = (
        "This is medical information only. It is not a diagnosis or prescription. "
        "Always consult a qualified healthcare provider."
    )
    generated_at: datetime
    model_config = {"protected_namespaces": ()}


class AIExplainResponse(BaseModel):
    """Plain-language explanation of a medical record or prescription."""
    record_id: str
    record_type: str
    explanation: str
    key_points: List[str]
    side_effects: Optional[List[str]] = None     # For prescriptions
    follow_up_suggestions: Optional[List[str]] = None
    model_used: str
    disclaimer: str = (
        "This explanation is AI-generated from your existing records only. "
        "It is not a diagnosis or medical advice."
    )
    generated_at: datetime
    model_config = {"protected_namespaces": ()}


# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class ComplianceMetric(BaseModel):
    metric: str
    value: float           # Percentage 0-100
    numerator: int
    denominator: int
    period_days: int


class ComplianceResponse(BaseModel):
    """Compliance data — consumed by Module 3 (Doctor portal) and Module 4 (Analytics)."""
    patient_id: str
    period_days: int
    medication_compliance: ComplianceMetric
    appointment_compliance: ComplianceMetric
    overall_compliance_score: float
    calculated_at: datetime


class TrendDataPoint(BaseModel):
    date: date
    value: float
    is_anomaly: bool = False
    anomaly_direction: Optional[str] = None   # "high" | "low"


class TrendResponse(BaseModel):
    """Wearable metric trend — consumed by Module 3 (Doctor) for clinical context."""
    patient_id: str
    metric_type: str
    unit: str
    period_days: int
    data_points: List[TrendDataPoint]
    moving_avg_7d: Optional[float]
    moving_avg_30d: Optional[float]
    moving_avg_90d: Optional[float]
    baseline_mean: Optional[float]
    baseline_std: Optional[float]
    anomaly_count: int
    trend_direction: str                  # "improving" | "declining" | "stable"
    calculated_at: datetime


class WearableAnalyticsSummary(BaseModel):
    """Wearable analytics summary — full picture for Module 3 clinical view."""
    patient_id: str
    period_days: int
    sleep_avg_hours: Optional[float]
    sleep_quality_score: Optional[float]
    heart_rate_avg: Optional[float]
    heart_rate_trend: Optional[str]
    blood_oxygen_avg: Optional[float]
    low_spo2_alert: bool = False
    low_spo2_count: int = 0
    steps_avg: Optional[float]
    steps_goal_achievement_pct: Optional[float]
    calories_avg: Optional[float]
    calculated_at: datetime


class AnalyticsSummaryResponse(BaseModel):
    """Full analytics dashboard — primary output for Module 3 & Module 4 consumption."""
    patient_id: str
    compliance: ComplianceResponse
    wearable_summary: WearableAnalyticsSummary
    risk_flags: List[str]                 # High-priority flags for Module 4
    generated_at: datetime


# ============================================================================
# SCREENSHOT ANALYSIS SCHEMAS
# ============================================================================

class ScreenshotAnalysisResponse(BaseModel):
    """Result of smartwatch screenshot analysis."""
    extraction_id: str
    patient_id: str
    device_detected: Optional[str]        # DaFit | Apple Watch | generic
    metrics_extracted: List[WearableMetricResponse]
    raw_ocr_text: str
    confidence_score: float
    analytics_triggered: bool
    wearable_analytics: Optional[WearableAnalyticsSummary] = None
    processed_at: datetime


# ============================================================================
# HEALTH INSIGHT SCHEMAS
# ============================================================================

class HealthInsightResponse(BaseModel):
    """AI-generated health insight — consumed by Module 3 and patient dashboard."""
    id: str
    patient_id: str
    insights: List[str]
    action_recommendations: List[str]
    wearable_summary: Optional[Dict[str, Any]]
    compliance_summary: Optional[Dict[str, Any]]
    generated_at: datetime
    model_used: Optional[str]
    generation_period_days: int
    is_read: bool

    class Config:
        from_attributes = True
        protected_namespaces = ()


class HealthInsightListResponse(BaseModel):
    patient_id: str
    total_insights: int
    unread_count: int
    insights: List[HealthInsightResponse]


# ============================================================================
# PAGINATION HELPERS
# ============================================================================

def create_paginated_response(
    items: List[Any],
    page: int,
    page_size: int,
    total_items: int
) -> PaginatedResponse:
    total_pages = (total_items + page_size - 1) // page_size
    return PaginatedResponse(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        items=items,
        has_next=page < total_pages,
        has_previous=page > 1
    )


# Update forward references
OCRExtractionResponse.model_rebuild()
