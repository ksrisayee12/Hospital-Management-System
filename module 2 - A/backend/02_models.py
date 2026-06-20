"""
SQLAlchemy ORM models for healthcare vault backend.
Includes patients, medical records, appointments, timeline, family access, vault storage, and wearable metrics.
"""

from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Date, Boolean, 
    ForeignKey, Text, Enum, Index, UniqueConstraint, DECIMAL,
    JSON, LargeBinary
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
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


# ============================================================================
# BASE MODEL
# ============================================================================

class BaseModel(Base):
    """Abstract base model with common audit fields."""
    __abstract__ = True

    id = Column(String(36), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(36), nullable=True)  # User ID from auth system
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

    user_id = Column(String(36), nullable=False, index=True)  # From auth module
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)
    
    # Contact Information
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)

    # Emergency Contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(50), nullable=True)

    # Health Information
    height_cm = Column(Float, nullable=True)  # Height in centimeters
    weight_kg = Column(Float, nullable=True)  # Weight in kilograms
    bmi = Column(Float, nullable=True)  # Calculated BMI
    
    # Vault Metadata
    vault_initialized = Column(Boolean, default=False)
    vault_encryption_key_id = Column(String(100), nullable=True)  # Reference to encryption key version

    # Relationships
    medical_records = relationship("MedicalRecord", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="patient", cascade="all, delete-orphan")
    family_accesses = relationship("FamilyAccess", back_populates="patient", cascade="all, delete-orphan")
    vault_files = relationship("VaultFile", back_populates="patient", cascade="all, delete-orphan")
    wearable_metrics = relationship("WearableMetric", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient(id={self.id}, email={self.email}, name={self.first_name} {self.last_name})>"


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
    
    # Record Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    record_date = Column(Date, nullable=False, index=True)
    
    # Provider Information
    provider_id = Column(String(36), nullable=True)  # Healthcare provider ID
    provider_name = Column(String(255), nullable=False)
    provider_facility = Column(String(255), nullable=True)
    
    # Medical Details
    diagnosis = Column(Text, nullable=True)  # Primary diagnosis
    symptoms = Column(Text, nullable=True)  # Comma-separated symptoms
    treatment = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # File References
    file_id = Column(String(36), nullable=True)  # Reference to vault file
    file_url = Column(Text, nullable=True)  # Encrypted URL to storage
    
    # Additional Metadata
    is_critical = Column(Boolean, default=False)
    requires_follow_up = Column(Boolean, default=False)
    follow_up_date = Column(Date, nullable=True)
    
    # Lab Results (for lab reports)
    lab_results = Column(JSON, nullable=True)  # Structured lab test results
    
    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    vault_file = relationship("VaultFile", uselist=False, foreign_keys="MedicalRecord.file_id")

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
    doctor_id = Column(String(36), nullable=False, index=True)  # Healthcare provider ID
    doctor_name = Column(String(255), nullable=False)
    doctor_specialty = Column(String(100), nullable=True)
    facility_name = Column(String(255), nullable=True)
    
    # Appointment Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    appointment_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=30)
    
    # Status & Workflow
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.REQUESTED, index=True)
    
    # Rescheduling
    requested_reschedule_date = Column(DateTime, nullable=True)
    reschedule_reason = Column(Text, nullable=True)
    
    # Visit Info
    visit_type = Column(String(50), nullable=True)  # in-person, telehealth, etc.
    location = Column(String(255), nullable=True)
    meeting_link = Column(Text, nullable=True)
    
    # Outcomes
    completed_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    next_appointment_date = Column(DateTime, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")

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
    
    # Event Details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(Date, nullable=False, index=True)
    event_year = Column(Integer, nullable=False, index=True)
    event_month = Column(Integer, nullable=True)
    
    # Event Classification
    event_type = Column(String(100), nullable=True)  # diagnosis, medication_change, procedure, lab_result, etc.
    severity = Column(String(20), nullable=True)  # critical, high, medium, low
    
    # Linked Records
    related_medical_record_id = Column(String(36), ForeignKey('medical_records.id'), nullable=True)
    related_appointment_id = Column(String(36), ForeignKey('appointments.id'), nullable=True)
    
    # Content
    impact = Column(Text, nullable=True)  # Health impact description
    action_taken = Column(Text, nullable=True)  # Actions or treatments applied
    
    # Relationships
    patient = relationship("Patient", back_populates="timeline_events")

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
    relationship = Column(String(50), nullable=False)  # spouse, parent, child, sibling, etc.
    
    # Access Control
    permission_level = Column(Enum(AccessPermission), default=AccessPermission.VIEW_ONLY)
    status = Column(Enum(AccessStatus), default=AccessStatus.PENDING, index=True)
    
    # Record Type Restrictions (if needed)
    allowed_record_types = Column(JSON, nullable=True)  # List of MedicalRecordType values they can access
    
    # Approval Workflow
    requested_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String(36), nullable=True)  # Patient ID who approved
    rejected_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    
    # Expiry
    expires_at = Column(DateTime, nullable=True)  # Access expiry date
    
    # Relationships
    patient = relationship("Patient", back_populates="family_accesses")

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
    
    # File Metadata
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, jpg, png, doc, etc.
    file_size_bytes = Column(Integer, nullable=False)
    
    # Storage References
    storage_path = Column(String(500), nullable=False)  # Path in Supabase Storage
    storage_bucket = Column(String(100), default="health-vault")
    
    # Encryption
    encryption_algorithm = Column(String(50), default="AES-256")
    encryption_key_version = Column(String(100), nullable=False)
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash for integrity
    
    # Classification
    category = Column(String(100), nullable=True)  # prescription, lab_report, imaging, etc.
    description = Column(Text, nullable=True)
    upload_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Document Processing Status
    ocr_processed = Column(Boolean, default=False)
    ocr_text = Column(Text, nullable=True)  # Extracted text from OCR (Module 3)
    extraction_status = Column(String(50), nullable=True)  # pending, processing, completed, failed
    extraction_date = Column(DateTime, nullable=True)
    
    # Access & Sharing
    is_shared_with_providers = Column(Boolean, default=False)
    shared_with_provider_ids = Column(JSON, nullable=True)  # List of provider IDs
    
    # Relationships
    patient = relationship("Patient", back_populates="vault_files")

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
        Index('idx_wearable_composite', ['patient_id', 'metric_date']),
    )

    patient_id = Column(String(36), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Metric Information
    metric_type = Column(String(50), nullable=False)  # heart_rate, steps, sleep, calories, blood_oxygen, etc.
    metric_date = Column(Date, nullable=False, index=True)
    metric_timestamp = Column(DateTime, nullable=False)  # Precise timestamp
    
    # Metric Values (flexible for different metric types)
    value = Column(Float, nullable=False)  # Primary value
    unit = Column(String(20), nullable=False)  # bpm, steps, hours, kcal, %, etc.
    
    # Additional Details
    value_min = Column(Float, nullable=True)  # For ranges
    value_max = Column(Float, nullable=True)  # For ranges
    value_avg = Column(Float, nullable=True)  # For daily aggregates
    
    # Metadata
    source_device = Column(String(100), nullable=True)  # Apple Watch, Fitbit, Manual, etc.
    source_app = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Data Quality
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    is_manual_entry = Column(Boolean, default=False)
    data_integrity_verified = Column(Boolean, default=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="wearable_metrics")

    def __repr__(self):
        return f"<WearableMetric(id={self.id}, type={self.metric_type}, date={self.metric_date})>"


# ============================================================================
# INDEXES FOR COMMON QUERIES
# ============================================================================

# Additional composite indexes for common query patterns
Index('idx_medical_record_patient_date', MedicalRecord.patient_id, MedicalRecord.record_date)
Index('idx_appointment_patient_date', Appointment.patient_id, Appointment.appointment_date)
Index('idx_family_access_patient_status', FamilyAccess.patient_id, FamilyAccess.status)
Index('idx_wearable_patient_type_date', WearableMetric.patient_id, WearableMetric.metric_type, WearableMetric.metric_date)
