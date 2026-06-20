"""
Service layer containing business logic, validations, and orchestration.
Services use repositories for data access.
"""

import uuid
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Patient, MedicalRecord, Appointment, TimelineEvent,
    FamilyAccess, VaultFile, WearableMetric,
    MedicalRecordType, AppointmentStatus, AccessStatus
)
from app.repositories import (
    PatientRepository, MedicalRecordRepository, AppointmentRepository,
    TimelineRepository, FamilyAccessRepository, VaultFileRepository,
    WearableMetricRepository
)
from app.schemas import (
    PatientResponse, DashboardResponse, DashboardHealthStatus,
    DashboardUpcomingAppointment, MedicalRecordResponse, AppointmentResponse,
    TimelineEventResponse, TimelineListResponse
)


# ============================================================================
# PATIENT SERVICE
# ============================================================================

class PatientService:
    """Business logic for patient operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.patient_repo = PatientRepository(session)

    async def create_patient(
        self,
        user_id: str,
        email: str,
        first_name: str,
        last_name: str,
        **kwargs
    ) -> Patient:
        """Create new patient and initialize vault."""
        patient = Patient(
            id=str(uuid.uuid4()),
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            created_by=user_id,
            vault_initialized=True,
            **kwargs
        )
        patient = await self.patient_repo.create(patient)
        await self.session.commit()
        return patient

    async def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get patient by ID."""
        return await self.patient_repo.get_by_id(patient_id)

    async def get_patient_by_email(self, email: str) -> Optional[Patient]:
        """Get patient by email."""
        return await self.patient_repo.get_by_email(email)

    async def get_patient_by_user_id(self, user_id: str) -> Optional[Patient]:
        """Get patient by auth user ID."""
        return await self.patient_repo.get_by_user_id(user_id)

    async def update_patient(
        self,
        patient_id: str,
        **updates
    ) -> Optional[Patient]:
        """Update patient information."""
        # Calculate BMI if height and weight provided
        if "height_cm" in updates or "weight_kg" in updates:
            patient = await self.patient_repo.get_by_id(patient_id)
            height_cm = updates.get("height_cm", patient.height_cm)
            weight_kg = updates.get("weight_kg", patient.weight_kg)
            
            if height_cm and weight_kg:
                height_m = height_cm / 100
                bmi = weight_kg / (height_m ** 2)
                updates["bmi"] = round(bmi, 2)

        patient = await self.patient_repo.update(patient_id, **updates)
        await self.session.commit()
        return patient

    async def calculate_age(self, patient_id: str) -> Optional[int]:
        """Calculate patient age from DOB."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient or not patient.date_of_birth:
            return None
        
        today = date.today()
        age = today.year - patient.date_of_birth.year
        if (today.month, today.day) < (patient.date_of_birth.month, patient.date_of_birth.day):
            age -= 1
        return age


# ============================================================================
# DASHBOARD SERVICE
# ============================================================================

class DashboardService:
    """Aggregates data for patient dashboard."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.patient_repo = PatientRepository(session)
        self.medical_repo = MedicalRecordRepository(session)
        self.appointment_repo = AppointmentRepository(session)

    async def get_dashboard(self, patient_id: str) -> Optional[DashboardResponse]:
        """Get complete dashboard data."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            return None

        # Get counts
        medical_records, _ = await self.medical_repo.get_by_patient_id(
            patient_id, limit=1000
        )
        appointments, _ = await self.appointment_repo.get_by_patient_id(
            patient_id, limit=1000
        )

        record_counts = await self.medical_repo.count_by_type(patient_id)
        
        # Get upcoming appointments
        upcoming = await self.appointment_repo.get_upcoming(patient_id)
        upcoming_dtos = [
            DashboardUpcomingAppointment(
                id=apt.id,
                doctor_name=apt.doctor_name,
                specialty=apt.doctor_specialty,
                appointment_date=apt.appointment_date,
                visit_type=apt.visit_type
            )
            for apt in upcoming
        ]

        # Find active doctor (most recent appointment)
        active_doctor_id = None
        active_doctor_name = None
        if appointments:
            latest = sorted(
                appointments,
                key=lambda x: x.appointment_date,
                reverse=True
            )[0]
            active_doctor_id = latest.doctor_id
            active_doctor_name = latest.doctor_name

        # Health status
        health_status = DashboardHealthStatus(
            total_conditions=len([r for r in medical_records if r.diagnosis]),
            critical_conditions=len([r for r in medical_records if r.is_critical]),
            medications_active=record_counts.get("prescription", 0),
            allergies=record_counts.get("allergy", 0),
            last_checkup=max(
                [r.record_date for r in medical_records],
                default=None
            )
        )

        return DashboardResponse(
            patient_id=patient_id,
            welcome_message=f"Welcome back, {patient.first_name}!",
            reports_count=record_counts.get("lab_report", 0) + record_counts.get("mri_report", 0) + record_counts.get("ct_scan_report", 0),
            prescriptions_count=record_counts.get("prescription", 0),
            appointments_count=len(appointments),
            allergies_count=record_counts.get("allergy", 0),
            health_status=health_status,
            upcoming_appointments=upcoming_dtos[:5],
            next_appointment=upcoming_dtos[0] if upcoming_dtos else None,
            active_doctor_id=active_doctor_id,
            active_doctor_name=active_doctor_name
        )


# ============================================================================
# MEDICAL RECORD SERVICE
# ============================================================================

class MedicalRecordService:
    """Business logic for medical records."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.medical_repo = MedicalRecordRepository(session)
        self.timeline_repo = TimelineRepository(session)

    async def create_medical_record(
        self,
        patient_id: str,
        record_type: str,
        title: str,
        record_date: date,
        provider_name: str,
        **kwargs
    ) -> MedicalRecord:
        """Create medical record and update timeline."""
        record = MedicalRecord(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            record_type=record_type,
            title=title,
            record_date=record_date,
            provider_name=provider_name,
            created_by=patient_id,
            **kwargs
        )
        record = await self.medical_repo.create(record)

        # Create timeline event for significant records
        if record.diagnosis or record.is_critical:
            await self._create_timeline_event_for_record(record)

        await self.session.commit()
        return record

    async def update_medical_record(
        self,
        record_id: str,
        **updates
    ) -> Optional[MedicalRecord]:
        """Update medical record."""
        record = await self.medical_repo.update(record_id, **updates)
        await self.session.commit()
        return record

    async def get_medical_record(self, record_id: str) -> Optional[MedicalRecord]:
        """Get medical record by ID."""
        return await self.medical_repo.get_by_id(record_id)

    async def get_patient_medical_records(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20,
        record_type: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Tuple[List[MedicalRecord], int]:
        """Get patient's medical records with filters."""
        return await self.medical_repo.get_by_patient_id(
            patient_id, skip, limit, record_type, from_date, to_date
        )

    async def get_critical_records(
        self,
        patient_id: str
    ) -> List[MedicalRecord]:
        """Get patient's critical records."""
        return await self.medical_repo.get_critical_records(patient_id)

    async def _create_timeline_event_for_record(
        self,
        record: MedicalRecord
    ) -> TimelineEvent:
        """Create timeline event from medical record."""
        event = TimelineEvent(
            id=str(uuid.uuid4()),
            patient_id=record.patient_id,
            title=record.title,
            description=record.diagnosis,
            event_date=record.record_date,
            event_year=record.record_date.year,
            event_month=record.record_date.month,
            event_type=record.record_type,
            severity="critical" if record.is_critical else "medium",
            related_medical_record_id=record.id,
            created_by=record.patient_id
        )
        await self.timeline_repo.create(event)


# ============================================================================
# APPOINTMENT SERVICE
# ============================================================================

class AppointmentService:
    """Business logic for appointments."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.appointment_repo = AppointmentRepository(session)
        self.timeline_repo = TimelineRepository(session)

    async def request_appointment(
        self,
        patient_id: str,
        doctor_id: str,
        doctor_name: str,
        title: str,
        appointment_date: datetime,
        **kwargs
    ) -> Appointment:
        """Request appointment from doctor."""
        appointment = Appointment(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            title=title,
            appointment_date=appointment_date,
            status=AppointmentStatus.REQUESTED,
            created_by=patient_id,
            **kwargs
        )
        appointment = await self.appointment_repo.create(appointment)
        await self.session.commit()
        return appointment

    async def approve_appointment(
        self,
        appointment_id: str,
        approved_by_id: str
    ) -> Optional[Appointment]:
        """Doctor approves appointment."""
        appointment = await self.appointment_repo.update(
            appointment_id,
            status=AppointmentStatus.APPROVED
        )
        await self.session.commit()
        return appointment

    async def reject_appointment(
        self,
        appointment_id: str,
        rejection_reason: Optional[str] = None
    ) -> Optional[Appointment]:
        """Doctor rejects appointment."""
        appointment = await self.appointment_repo.update(
            appointment_id,
            status=AppointmentStatus.CANCELLED,
            notes=rejection_reason
        )
        await self.session.commit()
        return appointment

    async def reschedule_appointment(
        self,
        appointment_id: str,
        new_date: datetime,
        reason: Optional[str] = None
    ) -> Optional[Appointment]:
        """Request appointment reschedule."""
        appointment = await self.appointment_repo.update(
            appointment_id,
            requested_reschedule_date=new_date,
            reschedule_reason=reason
        )
        await self.session.commit()
        return appointment

    async def complete_appointment(
        self,
        appointment_id: str,
        notes: Optional[str] = None,
        next_appointment_date: Optional[datetime] = None
    ) -> Optional[Appointment]:
        """Mark appointment as completed."""
        appointment = await self.appointment_repo.update(
            appointment_id,
            status=AppointmentStatus.COMPLETED,
            completed_date=datetime.utcnow(),
            notes=notes,
            next_appointment_date=next_appointment_date
        )
        
        # Create timeline event
        if appointment:
            event = TimelineEvent(
                id=str(uuid.uuid4()),
                patient_id=appointment.patient_id,
                title=f"Appointment with {appointment.doctor_name}",
                event_date=appointment.appointment_date.date(),
                event_year=appointment.appointment_date.year,
                event_month=appointment.appointment_date.month,
                event_type="appointment",
                related_appointment_id=appointment.id,
                created_by=appointment.patient_id
            )
            await self.timeline_repo.create(event)

        await self.session.commit()
        return appointment

    async def get_upcoming_appointments(
        self,
        patient_id: str,
        days: int = 30
    ) -> List[Appointment]:
        """Get upcoming appointments."""
        return await self.appointment_repo.get_upcoming(patient_id, days)


# ============================================================================
# TIMELINE SERVICE
# ============================================================================

class TimelineService:
    """Business logic for timeline management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.timeline_repo = TimelineRepository(session)

    async def get_patient_timeline(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[TimelineEventResponse], int]:
        """Get patient timeline."""
        events, total = await self.timeline_repo.get_by_patient_id(
            patient_id, skip, limit
        )
        
        event_responses = [
            TimelineEventResponse.model_validate(event)
            for event in events
        ]
        
        return event_responses, total

    async def get_timeline_by_year(
        self,
        patient_id: str
    ) -> List[TimelineListResponse]:
        """Get timeline grouped by year."""
        years = await self.timeline_repo.get_years(patient_id)
        
        timeline_data = []
        for year in years:
            events = await self.timeline_repo.get_by_year(patient_id, year)
            event_responses = [
                TimelineEventResponse.model_validate(event)
                for event in events
            ]
            timeline_data.append(
                TimelineListResponse(year=year, events=event_responses)
            )
        
        return timeline_data

    async def create_event(
        self,
        patient_id: str,
        title: str,
        event_date: date,
        **kwargs
    ) -> TimelineEvent:
        """Create timeline event."""
        event = TimelineEvent(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            title=title,
            event_date=event_date,
            event_year=event_date.year,
            event_month=event_date.month,
            created_by=patient_id,
            **kwargs
        )
        event = await self.timeline_repo.create(event)
        await self.session.commit()
        return event


# ============================================================================
# FAMILY ACCESS SERVICE
# ============================================================================

class FamilyAccessService:
    """Business logic for family access control."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.family_repo = FamilyAccessRepository(session)
        self.patient_repo = PatientRepository(session)

    async def request_family_access(
        self,
        patient_id: str,
        family_member_email: str,
        family_member_name: str,
        family_member_user_id: str,
        relationship: str,
        permission_level: str = "view_only",
        **kwargs
    ) -> FamilyAccess:
        """Request family member access (patient initiated)."""
        access = FamilyAccess(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            family_member_user_id=family_member_user_id,
            family_member_email=family_member_email,
            family_member_name=family_member_name,
            relationship=relationship,
            permission_level=permission_level,
            status=AccessStatus.PENDING,
            created_by=patient_id,
            **kwargs
        )
        access = await self.family_repo.create(access)
        await self.session.commit()
        return access

    async def approve_family_access(
        self,
        access_id: str,
        approved_by_id: str
    ) -> Optional[FamilyAccess]:
        """Approve family member access."""
        access = await self.family_repo.update(
            access_id,
            status=AccessStatus.APPROVED,
            approved_at=datetime.utcnow(),
            approved_by=approved_by_id
        )
        await self.session.commit()
        return access

    async def reject_family_access(
        self,
        access_id: str,
        rejection_reason: Optional[str] = None
    ) -> Optional[FamilyAccess]:
        """Reject family member access."""
        access = await self.family_repo.update(
            access_id,
            status=AccessStatus.REJECTED,
            rejected_at=datetime.utcnow(),
            rejection_reason=rejection_reason
        )
        await self.session.commit()
        return access

    async def revoke_family_access(
        self,
        access_id: str
    ) -> Optional[FamilyAccess]:
        """Revoke existing family access."""
        access = await self.family_repo.update(
            access_id,
            status=AccessStatus.REVOKED,
            revoked_at=datetime.utcnow()
        )
        await self.session.commit()
        return access

    async def get_approved_family_members(
        self,
        patient_id: str
    ) -> List[FamilyAccess]:
        """Get approved family members."""
        return await self.family_repo.get_approved_members(patient_id)

    async def get_pending_requests(
        self,
        patient_id: str
    ) -> List[FamilyAccess]:
        """Get pending family access requests."""
        return await self.family_repo.get_pending_requests(patient_id)


# ============================================================================
# VAULT SERVICE
# ============================================================================

class VaultService:
    """Business logic for vault storage management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.vault_repo = VaultFileRepository(session)

    async def create_vault_file(
        self,
        patient_id: str,
        original_filename: str,
        file_type: str,
        file_size_bytes: int,
        storage_path: str,
        encryption_key_version: str,
        **kwargs
    ) -> VaultFile:
        """Create vault file record."""
        file = VaultFile(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            original_filename=original_filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            storage_path=storage_path,
            encryption_key_version=encryption_key_version,
            upload_date=datetime.utcnow(),
            created_by=patient_id,
            **kwargs
        )
        file = await self.vault_repo.create(file)
        await self.session.commit()
        return file

    async def get_vault_stats(self, patient_id: str) -> Dict[str, Any]:
        """Get vault statistics."""
        stats = await self.vault_repo.get_vault_stats(patient_id)
        return {
            **stats,
            "total_size_mb": round(stats["total_size_bytes"] / (1024 * 1024), 2),
            "usage_percent": 0  # Implement if max storage is defined
        }

    async def get_vault_files(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20,
        file_type: Optional[str] = None,
        category: Optional[str] = None
    ) -> Tuple[List[VaultFile], int]:
        """Get vault files."""
        return await self.vault_repo.get_by_patient_id(
            patient_id, skip, limit, file_type, category
        )

    async def mark_for_ocr(self, file_id: str) -> Optional[VaultFile]:
        """Mark file for OCR processing."""
        return await self.vault_repo.update(
            file_id,
            extraction_status="pending"
        )

    async def update_ocr_status(
        self,
        file_id: str,
        status: str,
        extracted_text: Optional[str] = None
    ) -> Optional[VaultFile]:
        """Update OCR processing status."""
        updates = {
            "extraction_status": status,
            "extraction_date": datetime.utcnow() if status == "completed" else None
        }
        if status == "completed":
            updates["ocr_processed"] = True
            updates["ocr_text"] = extracted_text
        
        return await self.vault_repo.update(file_id, **updates)


# ============================================================================
# WEARABLE SERVICE
# ============================================================================

class WearableService:
    """Business logic for wearable metrics."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.wearable_repo = WearableMetricRepository(session)

    async def create_metric(
        self,
        patient_id: str,
        metric_type: str,
        metric_date: date,
        metric_timestamp: datetime,
        value: float,
        unit: str,
        **kwargs
    ) -> WearableMetric:
        """Create wearable metric."""
        metric = WearableMetric(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            metric_type=metric_type,
            metric_date=metric_date,
            metric_timestamp=metric_timestamp,
            value=value,
            unit=unit,
            created_by=patient_id,
            **kwargs
        )
        metric = await self.wearable_repo.create(metric)
        await self.session.commit()
        return metric

    async def batch_create_metrics(
        self,
        patient_id: str,
        metrics: List[Dict[str, Any]]
    ) -> List[WearableMetric]:
        """Create multiple metrics at once."""
        created_metrics = []
        for metric_data in metrics:
            metric = await self.create_metric(
                patient_id=patient_id,
                **metric_data
            )
            created_metrics.append(metric)
        
        await self.session.commit()
        return created_metrics

    async def get_patient_metrics(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 100,
        metric_type: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Tuple[List[WearableMetric], int]:
        """Get patient wearable metrics."""
        return await self.wearable_repo.get_by_patient_id(
            patient_id, skip, limit, metric_type, from_date, to_date
        )

    async def get_metric_types(self, patient_id: str) -> List[str]:
        """Get available metric types."""
        return await self.wearable_repo.get_metric_types(patient_id)

    async def get_recent_metrics(
        self,
        patient_id: str,
        metric_type: str,
        days: int = 30
    ) -> List[WearableMetric]:
        """Get recent metrics of specific type."""
        return await self.wearable_repo.get_latest_by_type(
            patient_id, metric_type, days
        )
