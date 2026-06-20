"""
Pydantic schemas for API request/response validation.
Includes nested schemas for all entities.
"""

from datetime import datetime, date
from typing import Optional, List, Any
from pydantic import BaseModel, Field, EmailStr, validator, conlist
from enum import Enum


# ============================================================================
# COMMON SCHEMAS
# ============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number starting from 1")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    items: List[Any]
    has_next: bool
    has_previous: bool


class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Any] = None


class TimestampSchema(BaseModel):
    """Audit timestamp fields."""
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None


# ============================================================================
# PATIENT SCHEMAS
# ============================================================================

class PatientCreateRequest(BaseModel):
    """Request schema for creating a new patient."""
    user_id: str = Field(..., description="User ID from authentication module")
    email: EmailStr
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(Male|Female|Other|Prefer not to say)$")
    blood_group: Optional[str] = Field(None, pattern="^(A|B|AB|O)[+-]$")
    
    # Address
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    
    # Health Metrics
    height_cm: Optional[float] = Field(None, gt=0, le=250)
    weight_kg: Optional[float] = Field(None, gt=0, le=500)


class PatientUpdateRequest(BaseModel):
    """Request schema for updating patient information."""
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

    @validator('height_cm', 'weight_kg')
    def validate_health_metrics(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Must be greater than 0')
        return v


class PatientResponse(BaseModel):
    """Response schema for patient data."""
    id: str
    user_id: str
    email: str
    phone: Optional[str]
    first_name: str
    last_name: str
    full_name: str = Field(...)  # Computed field
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
    
    vault_initialized: bool
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD SCHEMAS
# ============================================================================

class DashboardHealthStatus(BaseModel):
    """Health status summary for dashboard."""
    total_conditions: int = 0
    critical_conditions: int = 0
    medications_active: int = 0
    allergies: int = 0
    last_checkup: Optional[date] = None


class DashboardUpcomingAppointment(BaseModel):
    """Upcoming appointment summary."""
    id: str
    doctor_name: str
    specialty: Optional[str]
    appointment_date: datetime
    visit_type: Optional[str]


class DashboardResponse(BaseModel):
    """Patient dashboard overview."""
    patient_id: str
    welcome_message: str
    
    # Counts
    reports_count: int = 0
    prescriptions_count: int = 0
    appointments_count: int = 0
    allergies_count: int = 0
    
    # Status
    health_status: DashboardHealthStatus
    
    # Upcoming
    upcoming_appointments: List[DashboardUpcomingAppointment]
    next_appointment: Optional[DashboardUpcomingAppointment]
    
    # Active Doctor
    active_doctor_id: Optional[str]
    active_doctor_name: Optional[str]


# ============================================================================
# MEDICAL RECORD SCHEMAS
# ============================================================================

class LabResult(BaseModel):
    """Individual lab test result."""
    test_name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    status: Optional[str] = None  # normal, high, low, critical


class MedicalRecordCreateRequest(BaseModel):
    """Request schema for creating medical record."""
    record_type: str = Field(..., description="Type of medical record")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    record_date: date
    
    provider_id: Optional[str] = None
    provider_name: str = Field(..., max_length=255)
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
    """Request schema for updating medical record."""
    title: Optional[str] = None
    description: Optional[str] = None
    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None
    is_critical: Optional[bool] = None
    requires_follow_up: Optional[bool] = None
    follow_up_date: Optional[date] = None
    lab_results: Optional[List[LabResult]] = None


class MedicalRecordResponse(BaseModel):
    """Response schema for medical record."""
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
    """Request schema for creating appointment."""
    doctor_id: str
    doctor_name: str
    doctor_specialty: Optional[str] = None
    facility_name: Optional[str] = None
    
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    appointment_date: datetime
    duration_minutes: int = Field(default=30, ge=15, le=480)
    
    visit_type: Optional[str] = None  # in-person, telehealth
    location: Optional[str] = None
    meeting_link: Optional[str] = None


class AppointmentUpdateRequest(BaseModel):
    """Request schema for updating appointment."""
    title: Optional[str] = None
    description: Optional[str] = None
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    visit_type: Optional[str] = None
    location: Optional[str] = None
    meeting_link: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    """Request schema for updating appointment status."""
    status: str = Field(..., description="New status (pending, approved, completed, cancelled, rescheduled)")
    notes: Optional[str] = None
    completed_date: Optional[datetime] = None
    next_appointment_date: Optional[datetime] = None


class AppointmentRescheduleRequest(BaseModel):
    """Request schema for rescheduling appointment."""
    requested_reschedule_date: datetime
    reschedule_reason: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Response schema for appointment."""
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
    """Response schema for timeline event."""
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
    """Timeline grouped by year."""
    year: int
    events: List[TimelineEventResponse]


# ============================================================================
# FAMILY ACCESS SCHEMAS
# ============================================================================

class FamilyAccessCreateRequest(BaseModel):
    """Request schema for granting family access."""
    family_member_email: EmailStr
    family_member_name: str
    relationship: str = Field(..., description="Relationship: spouse, parent, child, sibling, other")
    permission_level: str = Field(default="view_only", description="view_only, edit, full_access")
    allowed_record_types: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class FamilyAccessUpdateRequest(BaseModel):
    """Request schema for updating family access."""
    permission_level: Optional[str] = None
    allowed_record_types: Optional[List[str]] = None
    expires_at: Optional[datetime] = None


class FamilyAccessApprovalRequest(BaseModel):
    """Request schema for approving/rejecting family access."""
    status: str = Field(..., description="approved or rejected")
    rejection_reason: Optional[str] = None


class FamilyAccessResponse(BaseModel):
    """Response schema for family access."""
    id: str
    patient_id: str
    family_member_user_id: str
    family_member_email: str
    family_member_name: str
    relationship: str
    permission_level: str
    status: str
    
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
    """Family member's view of patient dashboard."""
    patient_id: str
    patient_name: str
    relationship: str
    permission_level: str
    
    # Only visible data based on permissions
    health_status: Optional[DashboardHealthStatus]
    recent_records: List[MedicalRecordResponse]
    upcoming_appointments: List[AppointmentResponse]
    
    last_accessed: Optional[datetime]


# ============================================================================
# VAULT SCHEMAS
# ============================================================================

class VaultFileCreateRequest(BaseModel):
    """Request schema for uploading file to vault."""
    file_name: str = Field(..., max_length=255)
    file_type: str = Field(..., description="pdf, jpg, png, doc, docx, etc.")
    category: Optional[str] = None  # prescription, lab_report, imaging, etc.
    description: Optional[str] = None
    is_shared_with_providers: bool = False
    shared_with_provider_ids: Optional[List[str]] = None


class VaultFileResponse(BaseModel):
    """Response schema for vault file."""
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
    
    ocr_processed: bool
    extraction_status: Optional[str]
    extraction_date: Optional[datetime]
    
    is_shared_with_providers: bool
    shared_with_provider_ids: Optional[List[str]]

    class Config:
        from_attributes = True


class VaultStorageStatsResponse(BaseModel):
    """Vault storage statistics."""
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
    """Request schema for creating wearable metric."""
    metric_type: str = Field(..., description="heart_rate, steps, sleep, calories, blood_oxygen, etc.")
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
    """Response schema for wearable metric."""
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
    
    created_at: datetime

    class Config:
        from_attributes = True


class WearableMetricsStatsResponse(BaseModel):
    """Statistics for wearable metrics."""
    patient_id: str
    date_range: dict  # {from: date, to: date}
    
    metrics_by_type: dict  # {metric_type: {count, avg_value, min_value, max_value}}
    
    total_records: int
    manual_entries: int
    auto_synced: int


class WearableBatchUploadRequest(BaseModel):
    """Request schema for batch wearable data upload."""
    source_device: str
    source_app: str
    metrics: List[WearableMetricCreateRequest]


# ============================================================================
# PAGINATION HELPERS
# ============================================================================

def create_paginated_response(
    items: List[Any],
    page: int,
    page_size: int,
    total_items: int
) -> PaginatedResponse:
    """Create a paginated response object."""
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
