"""
SQLAlchemy ORM models for healthcare vault backend — Module 2 complete.
Includes all existing models + 6 new models for AI/safety/analytics layer.
"""

from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Date, Boolean,
    ForeignKey, Text, Enum, Index, UniqueConstraint, DECIMAL,
    JSON, LargeBinary
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship as sa_relationship
import enum


Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class MedicalRecordType(str, enum.Enum):
    """Types of medical records."""
    LAB_REPORT = "lab_report"
    MRI_REPORT = "mri_report"
    CT_SCAN_REPORT = "ct_scan_report"
    PRESCRIPTION = "prescription"
    CLINICAL_NOTE = "clinical_note"
    ALLERGY = "allergy"
    VACCINATION = "vaccination"
    OTHER = "other"


class AppointmentStatus(str, enum.Enum):
    """Appointment lifecycle states."""
    REQUESTED = "requested"
    PENDING = "pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class AccessPermission(str, enum.Enum):
    """Family member access levels."""
    VIEW_ONLY = "view_only"
    EDIT = "edit"
    FULL_ACCESS = "full_access"


class AccessStatus(str, enum.Enum):
    """Status of family access."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"


class RiskLevel(str, enum.Enum):
    """Prescription safety risk levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RAGIndexStatusEnum(str, enum.Enum):
    """ChromaDB indexing status."""
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"
    REMOVED = "removed"


# ============================================================================
# BASE MODEL
# ============================================================================

class BaseModel(Base):
    """Abstract base model with common audit fields."""
    __abstract__ = True

    id = Column(String(36), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(36), nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)


# ============================================================================
# PATIENT MODEL
# ============================================================================

class Patient(BaseModel):
    """Patient profile and core health information."""
    __tablename__ = "patients"
    __table_args__ = (
        Index('idx_patient_email', 'email', unique=True),
        Index('idx_patient_user_id', 'user_id', unique=True),
        Index('idx_patient_phone', 'phone'),
    )

    user_id = Column(String(36), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)

    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)

    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(50), nullable=True)

    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)

    vault_initialized = Column(Boolean, default=False)
    vault_encryption_key_id = Column(String(100), nullable=True)

    # Known allergies stored as JSON list for safety analysis
    known_allergies = Column(JSON, nullable=True)  # ["penicillin", "sulfa", ...]

    # Relationships
    medical_records = sa_relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
    appointments = sa_relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    timeline_events = sa_relationship("TimelineEvent", back_populates="patient", cascade="all, delete-orphan")
    family_accesses = sa_relationship("FamilyAccess", back_populates="patient", cascade="all, delete-orphan")
    vault_files = sa_relationship("VaultFile", back_populates="patient", cascade="all, delete-orphan")
    wearable_metrics = sa_relationship("WearableMetric", back_populates="patient", cascade="all, delete-orphan")
    prescriptions = sa_relationship("Prescription", back_populates="patient", cascade="all, delete-orphan")
    wearable_goals = sa_relationship("WearableGoal", back_populates="patient", cascade="all, delete-orphan")
    health_insights = sa_relationship("HealthInsight", back_populates="patient", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Patient(id={self.id}, email={self.email})>"


# ============================================================================
# MEDICAL RECORDS MODEL
# ============================================================================

class MedicalRecord(BaseModel):
    """Patient medical records including reports, prescriptions, clinical notes."""
    __tablename__ = "medical_records"
    __table_args__ = (
        Index('idx_medical_record_patient', 'patient_id'),
        Index('idx_medical_record_type', 'record_type'),
        Index('idx_medical_record_date', 'record_date'),
        Index('idx_medical_record_provider', 'provider_id'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    record_type = Column(Enum(MedicalRecordType), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    record_date = Column(Date, nullable=False, index=True)

    provider_id = Column(String(36), nullable=True)
    provider_name = Column(String(255), nullable=False)
    provider_facility = Column(String(255), nullable=True)

    diagnosis = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)
    treatment = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    file_id = Column(String(36), ForeignKey('vault_files.id', ondelete='SET NULL'), nullable=True)
    file_url = Column(Text, nullable=True)

    is_critical = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)  # Module 2 spec: use is_archived, not hard-delete
    requires_follow_up = Column(Boolean, default=False)
    follow_up_date = Column(Date, nullable=True)

    lab_results = Column(JSON, nullable=True)

    patient = sa_relationship("Patient", back_populates="medical_records")
    vault_file = sa_relationship("VaultFile", uselist=False, foreign_keys=[file_id])

    def __repr__(self):
        return f"<MedicalRecord(id={self.id}, type={self.record_type}, date={self.record_date})>"


# ============================================================================
# APPOINTMENT MODEL
# ============================================================================

class Appointment(BaseModel):
    """Patient appointments with doctors/healthcare providers."""
    __tablename__ = "appointments"
    __table_args__ = (
        Index('idx_appointment_patient', 'patient_id'),
        Index('idx_appointment_doctor', 'doctor_id'),
        Index('idx_appointment_status', 'status'),
        Index('idx_appointment_date', 'appointment_date'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    doctor_id = Column(String(36), nullable=False, index=True)
    doctor_name = Column(String(255), nullable=False)
    doctor_specialty = Column(String(100), nullable=True)
    facility_name = Column(String(255), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    appointment_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=30)

    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.REQUESTED, index=True)

    requested_reschedule_date = Column(DateTime, nullable=True)
    reschedule_reason = Column(Text, nullable=True)

    visit_type = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    meeting_link = Column(Text, nullable=True)

    completed_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    next_appointment_date = Column(DateTime, nullable=True)

    # Compliance tracking
    reminder_timestamps = Column(JSON, nullable=True)  # List of scheduled reminder datetimes
    was_reminded = Column(Boolean, default=False)

    patient = sa_relationship("Patient", back_populates="appointments")

    def __repr__(self):
        return f"<Appointment(id={self.id}, patient={self.patient_id}, status={self.status})>"


# ============================================================================
# TIMELINE EVENT MODEL
# ============================================================================

class TimelineEvent(BaseModel):
    """Chronological timeline of patient health events."""
    __tablename__ = "timeline_events"
    __table_args__ = (
        Index('idx_timeline_patient', 'patient_id'),
        Index('idx_timeline_date', 'event_date'),
        Index('idx_timeline_year', 'event_year'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(Date, nullable=False, index=True)
    event_year = Column(Integer, nullable=False, index=True)
    event_month = Column(Integer, nullable=True)

    event_type = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=True)

    related_medical_record_id = Column(String(36), ForeignKey('medical_records.id'), nullable=True)
    related_appointment_id = Column(String(36), ForeignKey('appointments.id'), nullable=True)

    impact = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)

    patient = sa_relationship("Patient", back_populates="timeline_events")

    def __repr__(self):
        return f"<TimelineEvent(id={self.id}, date={self.event_date}, type={self.event_type})>"


# ============================================================================
# FAMILY ACCESS MODEL
# ============================================================================

class FamilyAccess(BaseModel):
    """Manage family member access to patient records."""
    __tablename__ = "family_access"
    __table_args__ = (
        Index('idx_family_patient', 'patient_id'),
        Index('idx_family_member', 'family_member_user_id'),
        Index('idx_family_status', 'status'),
        UniqueConstraint('patient_id', 'family_member_user_id', name='uq_patient_family_member'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    family_member_user_id = Column(String(36), nullable=False, index=True)
    family_member_email = Column(String(255), nullable=False)
    family_member_name = Column(String(255), nullable=False)
    relationship = Column(String(50), nullable=False)

    permission_level = Column(Enum(AccessPermission), default=AccessPermission.VIEW_ONLY)
    status = Column(Enum(AccessStatus), default=AccessStatus.PENDING, index=True)

    # Emergency-only tier — can override VIEW_ONLY for emergency data
    is_emergency_contact = Column(Boolean, default=False)

    allowed_record_types = Column(JSON, nullable=True)

    requested_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(36), nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    expires_at = Column(DateTime, nullable=True)

    patient = sa_relationship("Patient", back_populates="family_accesses")

    def __repr__(self):
        return f"<FamilyAccess(id={self.id}, patient={self.patient_id}, status={self.status})>"


# ============================================================================
# VAULT FILE MODEL
# ============================================================================

class VaultFile(BaseModel):
    """Encrypted file storage metadata in health vault."""
    __tablename__ = "vault_files"
    __table_args__ = (
        Index('idx_vault_patient', 'patient_id'),
        Index('idx_vault_upload_date', 'upload_date'),
        Index('idx_vault_file_type', 'file_type'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)

    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=True)

    storage_path = Column(String(500), nullable=False)
    storage_bucket = Column(String(100), default="health-vault")

    encryption_algorithm = Column(String(50), default="AES-256")
    encryption_key_version = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=True)  # SHA-256

    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow, index=True)

    ocr_processed = Column(Boolean, default=False)
    ocr_text = Column(Text, nullable=True)
    extraction_status = Column(String(50), nullable=True)
    extraction_date = Column(DateTime, nullable=True)

    is_shared_with_providers = Column(Boolean, default=False)
    shared_with_provider_ids = Column(JSON, nullable=True)

    patient = sa_relationship("Patient", back_populates="vault_files")

    def __repr__(self):
        return f"<VaultFile(id={self.id}, filename={self.original_filename})>"


# ============================================================================
# WEARABLE METRICS MODEL
# ============================================================================

class WearableMetric(BaseModel):
    """Health metrics from wearable devices and manual uploads."""
    __tablename__ = "wearable_metrics"
    __table_args__ = (
        Index('idx_wearable_patient', 'patient_id'),
        Index('idx_wearable_date', 'metric_date'),
        Index('idx_wearable_type', 'metric_type'),
        Index('idx_wearable_composite', 'patient_id', 'metric_date'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)

    metric_type = Column(String(50), nullable=False)
    metric_date = Column(Date, nullable=False, index=True)
    metric_timestamp = Column(DateTime, nullable=False)

    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)

    value_min = Column(Float, nullable=True)
    value_max = Column(Float, nullable=True)
    value_avg = Column(Float, nullable=True)

    source_device = Column(String(100), nullable=True)  # DaFit, smartwatch, fitness_app
    source_app = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    confidence_score = Column(Float, nullable=True)
    is_manual_entry = Column(Boolean, default=False)
    data_integrity_verified = Column(Boolean, default=False)

    # Source: screenshot extraction or direct sync
    extracted_from_screenshot = Column(Boolean, default=False)
    screenshot_vault_file_id = Column(String(36), nullable=True)

    patient = sa_relationship("Patient", back_populates="wearable_metrics")

    def __repr__(self):
        return f"<WearableMetric(id={self.id}, type={self.metric_type}, date={self.metric_date})>"


# ============================================================================
# NEW MODEL: PRESCRIPTION
# ============================================================================

class Prescription(BaseModel):
    """Structured prescription data — extracted from OCR or entered manually."""
    __tablename__ = "prescriptions"
    __table_args__ = (
        Index('idx_prescription_patient', 'patient_id'),
        Index('idx_prescription_date', 'prescription_date'),
        Index('idx_prescription_status', 'status'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)

    # Extracted fields
    medicine_name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=True)
    dosage = Column(String(100), nullable=True)         # e.g. "500mg"
    frequency = Column(String(100), nullable=True)      # e.g. "twice daily"
    duration = Column(String(100), nullable=True)       # e.g. "7 days"
    route = Column(String(50), nullable=True)           # oral, topical, IV, etc.
    instructions = Column(Text, nullable=True)          # "Take with food"

    # Provider
    prescribing_doctor = Column(String(255), nullable=True)
    prescribing_doctor_id = Column(String(36), nullable=True)
    prescription_date = Column(Date, nullable=True)

    # Status
    status = Column(String(50), default="active")  # active, completed, stopped, recalled
    is_active = Column(Boolean, default=True, index=True)

    # Source reference
    ocr_extraction_id = Column(String(36), nullable=True)  # VaultFile ID of original image
    medical_record_id = Column(String(36), ForeignKey('medical_records.id'), nullable=True)

    # AI/Safety tracking
    safety_analyzed = Column(Boolean, default=False)
    safety_record_id = Column(String(36), nullable=True)

    notes = Column(Text, nullable=True)

    patient = sa_relationship("Patient", back_populates="prescriptions")

    def __repr__(self):
        return f"<Prescription(id={self.id}, medicine={self.medicine_name}, patient={self.patient_id})>"


# ============================================================================
# NEW MODEL: PRESCRIPTION SAFETY
# ============================================================================

class PrescriptionSafety(BaseModel):
    """Prescription safety analysis results."""
    __tablename__ = "prescription_safety"
    __table_args__ = (
        Index('idx_safety_patient', 'patient_id'),
        Index('idx_safety_prescription', 'prescription_id'),
        Index('idx_safety_risk_level', 'risk_level'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    prescription_id = Column(String(36), ForeignKey('prescriptions.id'), nullable=True)

    # Risk assessment
    risk_score = Column(Float, nullable=False, default=0.0)  # 0–100
    risk_level = Column(Enum(RiskLevel), nullable=False, default=RiskLevel.LOW)

    # Detailed findings (JSON arrays)
    warnings = Column(JSON, nullable=True)          # [{type, drugs, description}, ...]
    interactions = Column(JSON, nullable=True)      # [{drug_a, drug_b, severity, description}, ...]
    allergy_conflicts = Column(JSON, nullable=True) # [{allergen, medicine, description}, ...]
    duplicate_ingredients = Column(JSON, nullable=True)
    dosage_outliers = Column(JSON, nullable=True)

    # Recommendations
    recommendations = Column(JSON, nullable=True)   # ["Consult physician before combining X and Y", ...]

    auto_flagged = Column(Boolean, default=False)
    flagged_reason = Column(Text, nullable=True)

    # Governance hook: alert created in Module 4
    governance_alert_created = Column(Boolean, default=False)
    governance_alert_id = Column(String(36), nullable=True)

    # Analysis metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    analysis_source = Column(String(50), default="openfda")  # openfda | local_matrix

    def __repr__(self):
        return f"<PrescriptionSafety(id={self.id}, risk={self.risk_level}, score={self.risk_score})>"


# ============================================================================
# NEW MODEL: WEARABLE GOAL
# ============================================================================

class WearableGoal(BaseModel):
    """Patient-set wearable metric targets."""
    __tablename__ = "wearable_goals"
    __table_args__ = (
        Index('idx_wearable_goal_patient', 'patient_id'),
        UniqueConstraint('patient_id', 'metric_type', name='uq_patient_metric_goal'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)

    metric_type = Column(String(50), nullable=False)  # steps, sleep_hours, heart_rate, etc.
    target_value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)

    target_min = Column(Float, nullable=True)   # Optional range
    target_max = Column(Float, nullable=True)

    description = Column(String(255), nullable=True)  # "Walk 10,000 steps daily"
    is_active = Column(Boolean, default=True)

    patient = sa_relationship("Patient", back_populates="wearable_goals")

    def __repr__(self):
        return f"<WearableGoal(id={self.id}, metric={self.metric_type}, target={self.target_value})>"


# ============================================================================
# NEW MODEL: HEALTH INSIGHT
# ============================================================================

class HealthInsight(BaseModel):
    """AI-generated health insights per patient."""
    __tablename__ = "health_insights"
    __table_args__ = (
        Index('idx_insight_patient', 'patient_id'),
        Index('idx_insight_generated_at', 'generated_at'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)

    # Generated content
    insights = Column(JSON, nullable=False)             # ["Insight 1 text", "Insight 2 text", ...]
    action_recommendations = Column(JSON, nullable=True) # ["Action 1", "Action 2"]

    # Context used for generation
    wearable_summary = Column(JSON, nullable=True)      # Summary stats used as input
    compliance_summary = Column(JSON, nullable=True)
    recent_records_summary = Column(JSON, nullable=True)

    # Generation metadata
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)
    model_used = Column(String(100), nullable=True)     # biomistral | medgemma
    generation_period_days = Column(Integer, default=7)
    is_read = Column(Boolean, default=False)

    patient = sa_relationship("Patient", back_populates="health_insights")

    def __repr__(self):
        return f"<HealthInsight(id={self.id}, patient={self.patient_id}, generated={self.generated_at})>"


# ============================================================================
# NEW MODEL: RAG INDEX STATUS
# ============================================================================

class RAGIndexStatus(BaseModel):
    """ChromaDB sync state per patient record."""
    __tablename__ = "rag_index_status"
    __table_args__ = (
        Index('idx_rag_patient', 'patient_id'),
        Index('idx_rag_record', 'record_id'),
        UniqueConstraint('patient_id', 'record_id', 'record_type', name='uq_rag_record'),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    record_id = Column(String(36), nullable=False, index=True)
    record_type = Column(String(50), nullable=False)  # medical_record | prescription | wearable_summary | insight

    # ChromaDB state
    chroma_collection = Column(String(255), nullable=True)
    chroma_document_ids = Column(JSON, nullable=True)  # List of ChromaDB doc IDs for this record
    chunk_count = Column(Integer, default=0)

    status = Column(Enum(RAGIndexStatusEnum), default=RAGIndexStatusEnum.PENDING, index=True)
    indexed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self):
        return f"<RAGIndexStatus(id={self.id}, record={self.record_id}, status={self.status})>"


# ============================================================================
# NEW MODEL: RECORD ACCESS LOG
# ============================================================================

class RecordAccessLog(Base):
    """Audit trail for every record view — no soft-delete, immutable."""
    __tablename__ = "record_access_log"
    __table_args__ = (
        Index('idx_access_log_patient', 'patient_id'),
        Index('idx_access_log_record', 'record_id'),
        Index('idx_access_log_user', 'accessed_by_user_id'),
        Index('idx_access_log_time', 'accessed_at'),
    )

    id = Column(String(36), primary_key=True, index=True)
    patient_id = Column(String(36), nullable=False, index=True)
    record_id = Column(String(36), nullable=False, index=True)
    record_type = Column(String(50), nullable=False)

    accessed_by_user_id = Column(String(36), nullable=False)
    accessed_by_role = Column(String(50), nullable=True)  # patient | doctor | family | system
    access_module = Column(String(50), nullable=True)     # module_2 | module_3 | module_4

    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String(50), nullable=True)
    action = Column(String(50), default="view")           # view | download | share

    def __repr__(self):
        return f"<RecordAccessLog(record={self.record_id}, user={self.accessed_by_user_id})>"


# ============================================================================
# COMPOSITE INDEXES
# ============================================================================

Index('idx_medical_record_patient_date', MedicalRecord.patient_id, MedicalRecord.record_date)
Index('idx_appointment_patient_date', Appointment.patient_id, Appointment.appointment_date)
Index('idx_family_access_patient_status', FamilyAccess.patient_id, FamilyAccess.status)
Index('idx_wearable_patient_type_date', WearableMetric.patient_id, WearableMetric.metric_type, WearableMetric.metric_date)
Index('idx_prescription_patient_active', Prescription.patient_id, Prescription.is_active)
Index('idx_safety_patient_risk', PrescriptionSafety.patient_id, PrescriptionSafety.risk_level)
