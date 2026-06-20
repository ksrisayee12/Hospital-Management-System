"""
Core patient services — existing business logic migrated to app package.
"""

import uuid
from datetime import datetime, date, timedelta
import os
import base64
from app.utils.encryption import EncryptionService
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

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


class PatientService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.patient_repo = PatientRepository(session)

    async def create_patient(self, user_id: str, email: str, first_name: str, last_name: str, **kwargs) -> Patient:
        patient = Patient(
            id=str(uuid.uuid4()), user_id=user_id, email=email,
            first_name=first_name, last_name=last_name,
            created_by=user_id, vault_initialized=True, **kwargs
        )
        patient = await self.patient_repo.create(patient)
        await self.session.commit()
        return patient

    async def get_patient(self, patient_id: str) -> Optional[Patient]:
        return await self.patient_repo.get_by_id(patient_id)

    async def get_patient_by_email(self, email: str) -> Optional[Patient]:
        return await self.patient_repo.get_by_email(email)

    async def get_patient_by_user_id(self, user_id: str) -> Optional[Patient]:
        return await self.patient_repo.get_by_user_id(user_id)

    async def update_patient(self, patient_id: str, **updates) -> Optional[Patient]:
        if "height_cm" in updates or "weight_kg" in updates:
            patient = await self.patient_repo.get_by_id(patient_id)
            height_cm = updates.get("height_cm", patient.height_cm)
            weight_kg = updates.get("weight_kg", patient.weight_kg)
            if height_cm and weight_kg:
                updates["bmi"] = round(weight_kg / (height_cm / 100) ** 2, 2)
        patient = await self.patient_repo.update(patient_id, **updates)
        await self.session.commit()
        return patient


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.patient_repo = PatientRepository(session)
        self.medical_repo = MedicalRecordRepository(session)
        self.appointment_repo = AppointmentRepository(session)

    async def get_dashboard(self, patient_id: str) -> Optional[DashboardResponse]:
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            return None
        medical_records, _ = await self.medical_repo.get_by_patient_id(patient_id, limit=1000)
        appointments, _ = await self.appointment_repo.get_by_patient_id(patient_id, limit=1000)
        record_counts = await self.medical_repo.count_by_type(patient_id)
        upcoming = await self.appointment_repo.get_upcoming(patient_id)

        upcoming_dtos = [
            DashboardUpcomingAppointment(
                id=apt.id, doctor_name=apt.doctor_name,
                specialty=apt.doctor_specialty, appointment_date=apt.appointment_date,
                visit_type=apt.visit_type
            ) for apt in upcoming
        ]

        active_doctor_id = active_doctor_name = None
        if appointments:
            latest = sorted(appointments, key=lambda x: x.appointment_date, reverse=True)[0]
            active_doctor_id = latest.doctor_id
            active_doctor_name = latest.doctor_name

        health_status = DashboardHealthStatus(
            total_conditions=len([r for r in medical_records if r.diagnosis]),
            critical_conditions=len([r for r in medical_records if r.is_critical]),
            medications_active=record_counts.get("prescription", 0),
            allergies=record_counts.get("allergy", 0),
            last_checkup=max([r.record_date for r in medical_records], default=None)
        )

        return DashboardResponse(
            patient_id=patient_id,
            welcome_message=f"Welcome back, {patient.first_name}!",
            reports_count=sum(record_counts.get(t, 0) for t in ["lab_report", "mri_report", "ct_scan_report"]),
            prescriptions_count=record_counts.get("prescription", 0),
            appointments_count=len(appointments),
            allergies_count=record_counts.get("allergy", 0),
            health_status=health_status,
            upcoming_appointments=upcoming_dtos[:5],
            next_appointment=upcoming_dtos[0] if upcoming_dtos else None,
            active_doctor_id=active_doctor_id,
            active_doctor_name=active_doctor_name
        )


class MedicalRecordService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.medical_repo = MedicalRecordRepository(session)
        self.timeline_repo = TimelineRepository(session)

    async def create_medical_record(self, patient_id: str, record_type: str, title: str,
                                    record_date: date, provider_name: str, **kwargs) -> MedicalRecord:
        record = MedicalRecord(
            id=str(uuid.uuid4()), patient_id=patient_id, record_type=record_type,
            title=title, record_date=record_date, provider_name=provider_name,
            created_by=patient_id, **kwargs
        )
        record = await self.medical_repo.create(record)
        if record.diagnosis or record.is_critical:
            await self._create_timeline_event(record)
        await self.session.commit()
        return record

    async def update_medical_record(self, record_id: str, **updates) -> Optional[MedicalRecord]:
        record = await self.medical_repo.update(record_id, **updates)
        await self.session.commit()
        return record

    async def get_medical_record(self, record_id: str) -> Optional[MedicalRecord]:
        return await self.medical_repo.get_by_id(record_id)

    async def get_patient_medical_records(self, patient_id: str, skip: int = 0, limit: int = 20,
                                          record_type: Optional[str] = None,
                                          from_date: Optional[date] = None,
                                          to_date: Optional[date] = None) -> Tuple[List[MedicalRecord], int]:
        return await self.medical_repo.get_by_patient_id(patient_id, skip, limit, record_type, from_date, to_date)

    async def get_critical_records(self, patient_id: str) -> List[MedicalRecord]:
        return await self.medical_repo.get_critical_records(patient_id)

    async def _create_timeline_event(self, record: MedicalRecord):
        event = TimelineEvent(
            id=str(uuid.uuid4()), patient_id=record.patient_id,
            title=record.title, description=record.diagnosis,
            event_date=record.record_date, event_year=record.record_date.year,
            event_month=record.record_date.month, event_type=record.record_type,
            severity="critical" if record.is_critical else "medium",
            related_medical_record_id=record.id, created_by=record.patient_id
        )
        await self.timeline_repo.create(event)


class AppointmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.appointment_repo = AppointmentRepository(session)
        self.timeline_repo = TimelineRepository(session)

    def _send_notification(self, patient_id: str, message: str):
        # Stub for future Email/SMS/Push notification system
        logger.info(f"[NOTIFICATION to Patient {patient_id}]: {message}")

    async def request_appointment(self, patient_id: str, doctor_id: str, doctor_name: str,
                                  title: str, appointment_date: datetime, **kwargs) -> Appointment:
        appointment = Appointment(
            id=str(uuid.uuid4()), patient_id=patient_id, doctor_id=doctor_id,
            doctor_name=doctor_name, title=title, appointment_date=appointment_date,
            status=AppointmentStatus.REQUESTED, created_by=patient_id, **kwargs
        )
        appointment = await self.appointment_repo.create(appointment)
        await self.session.commit()
        self._send_notification(patient_id, f"Appointment requested with {doctor_name} on {appointment_date}")
        return appointment

    async def approve_appointment(self, appointment_id: str, approved_by_id: str) -> Optional[Appointment]:
        appt = await self.appointment_repo.update(appointment_id, status=AppointmentStatus.APPROVED)
        await self.session.commit()
        if appt:
            self._send_notification(appt.patient_id, f"Your appointment with {appt.doctor_name} has been approved.")
        return appt

    async def reject_appointment(self, appointment_id: str, reason: Optional[str] = None) -> Optional[Appointment]:
        appt = await self.appointment_repo.update(appointment_id, status=AppointmentStatus.CANCELLED, notes=reason)
        await self.session.commit()
        if appt:
            self._send_notification(appt.patient_id, f"Your appointment with {appt.doctor_name} was rejected. Reason: {reason}")
        return appt

    async def reschedule_appointment(self, appointment_id: str, new_date: datetime, reason: Optional[str] = None) -> Optional[Appointment]:
        appt = await self.appointment_repo.update(appointment_id, requested_reschedule_date=new_date, reschedule_reason=reason)
        await self.session.commit()
        if appt:
            self._send_notification(appt.patient_id, f"Your appointment with {appt.doctor_name} requires rescheduling.")
        return appt

    async def complete_appointment(self, appointment_id: str, notes: Optional[str] = None,
                                   next_appointment_date: Optional[datetime] = None) -> Optional[Appointment]:
        appointment = await self.appointment_repo.update(
            appointment_id, status=AppointmentStatus.COMPLETED,
            completed_date=datetime.utcnow(), notes=notes, next_appointment_date=next_appointment_date
        )
        if appointment:
            event = TimelineEvent(
                id=str(uuid.uuid4()), patient_id=appointment.patient_id,
                title=f"Appointment with {appointment.doctor_name}",
                event_date=appointment.appointment_date.date(),
                event_year=appointment.appointment_date.year,
                event_month=appointment.appointment_date.month,
                event_type="appointment", related_appointment_id=appointment.id,
                created_by=appointment.patient_id
            )
            await self.timeline_repo.create(event)
        await self.session.commit()
        return appointment

    async def get_upcoming_appointments(self, patient_id: str, days: int = 30) -> List[Appointment]:
        return await self.appointment_repo.get_upcoming(patient_id, days)


class TimelineService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.timeline_repo = TimelineRepository(session)

    async def get_patient_timeline(self, patient_id: str, skip: int = 0, limit: int = 100) -> Tuple[List[TimelineEventResponse], int]:
        events, total = await self.timeline_repo.get_by_patient_id(patient_id, skip, limit)
        return [TimelineEventResponse.model_validate(e) for e in events], total

    async def get_timeline_by_year(self, patient_id: str) -> List[TimelineListResponse]:
        years = await self.timeline_repo.get_years(patient_id)
        result = []
        for year in years:
            events = await self.timeline_repo.get_by_year(patient_id, year)
            result.append(TimelineListResponse(
                year=year,
                events=[TimelineEventResponse.model_validate(e) for e in events]
            ))
        return result

    async def create_event(self, patient_id: str, title: str, event_date: date, **kwargs) -> TimelineEvent:
        event = TimelineEvent(
            id=str(uuid.uuid4()), patient_id=patient_id, title=title,
            event_date=event_date, event_year=event_date.year, event_month=event_date.month,
            created_by=patient_id, **kwargs
        )
        event = await self.timeline_repo.create(event)
        await self.session.commit()
        return event


class FamilyAccessService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.family_repo = FamilyAccessRepository(session)
        self.patient_repo = PatientRepository(session)

    async def request_family_access(self, patient_id: str, family_member_email: str,
                                    family_member_name: str, family_member_user_id: str,
                                    relationship: str, permission_level: str = "view_only", **kwargs) -> FamilyAccess:
        access = FamilyAccess(
            id=str(uuid.uuid4()), patient_id=patient_id,
            family_member_user_id=family_member_user_id,
            family_member_email=family_member_email, family_member_name=family_member_name,
            relationship=relationship, permission_level=permission_level,
            status=AccessStatus.PENDING, created_by=patient_id, **kwargs
        )
        access = await self.family_repo.create(access)
        await self.session.commit()
        return access

    async def approve_family_access(self, access_id: str, approved_by_id: str) -> Optional[FamilyAccess]:
        access = await self.family_repo.update(access_id, status=AccessStatus.APPROVED,
                                               approved_at=datetime.utcnow(), approved_by=approved_by_id)
        await self.session.commit()
        return access

    async def reject_family_access(self, access_id: str, reason: Optional[str] = None) -> Optional[FamilyAccess]:
        access = await self.family_repo.update(access_id, status=AccessStatus.REJECTED,
                                               rejected_at=datetime.utcnow(), rejection_reason=reason)
        await self.session.commit()
        return access

    async def revoke_family_access(self, access_id: str) -> Optional[FamilyAccess]:
        access = await self.family_repo.update(access_id, status=AccessStatus.REVOKED, revoked_at=datetime.utcnow())
        await self.session.commit()
        return access

    async def get_approved_family_members(self, patient_id: str) -> List[FamilyAccess]:
        return await self.family_repo.get_approved_members(patient_id)

    async def get_pending_requests(self, patient_id: str) -> List[FamilyAccess]:
        return await self.family_repo.get_pending_requests(patient_id)


class VaultService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.vault_repo = VaultFileRepository(session)
        from app.repositories import PatientRepository
        self.patient_repo = PatientRepository(session)

    async def create_vault_file(self, patient_id: str, original_filename: str, file_type: str,
                                file_size_bytes: int, storage_path: str, encryption_key_version: str, **kwargs) -> VaultFile:
        file = VaultFile(
            id=str(uuid.uuid4()), patient_id=patient_id, original_filename=original_filename,
            file_type=file_type, file_size_bytes=file_size_bytes, storage_path=storage_path,
            encryption_key_version=encryption_key_version, upload_date=datetime.utcnow(),
            created_by=patient_id, **kwargs
        )
        file = await self.vault_repo.create(file)
        await self.session.commit()
        return file

    async def upload_and_encrypt_file(self, patient_id: str, file_name: str, content: bytes, file_type: str, category: Optional[str] = None, description: Optional[str] = None, is_shared_with_providers: bool = False) -> VaultFile:
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient.vault_encryption_key_id:
            import secrets
            patient.vault_encryption_key_id = secrets.token_hex(16)
            await self.session.commit()
            
        encrypted_data = EncryptionService.encrypt(base64.b64encode(content).decode('utf-8'), patient.vault_encryption_key_id)
        
        storage_dir = f"vault_storage/{patient_id}"
        os.makedirs(storage_dir, exist_ok=True)
        file_id = str(uuid.uuid4())
        storage_path = os.path.join(storage_dir, file_id)
        
        with open(storage_path, "w") as f:
            f.write(encrypted_data)
            
        file = VaultFile(
            id=file_id, patient_id=patient_id, original_filename=file_name,
            file_type=file_type, file_size_bytes=len(content), storage_path=storage_path,
            encryption_key_version="v1", upload_date=datetime.utcnow(),
            created_by=patient_id, category=category, description=description,
            is_shared_with_providers=is_shared_with_providers
        )
        file = await self.vault_repo.create(file)
        await self.session.commit()
        return file

    async def download_and_decrypt_file(self, patient_id: str, file_id: str) -> Tuple[Optional[VaultFile], Optional[bytes]]:
        file_record = await self.vault_repo.get_by_id(file_id)
        if not file_record or file_record.patient_id != patient_id:
            return None, None
            
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient or not patient.vault_encryption_key_id:
            return None, None
            
        if not os.path.exists(file_record.storage_path):
            return None, None
            
        with open(file_record.storage_path, "r") as f:
            encrypted_data = f.read()
            
        decrypted_b64 = EncryptionService.decrypt(encrypted_data, patient.vault_encryption_key_id)
        decrypted_content = base64.b64decode(decrypted_b64)
        return file_record, decrypted_content

    async def delete_file(self, patient_id: str, file_id: str) -> bool:
        file_record = await self.vault_repo.get_by_id(file_id)
        if not file_record or file_record.patient_id != patient_id:
            return False
            
        if os.path.exists(file_record.storage_path):
            os.remove(file_record.storage_path)
            
        await self.vault_repo.delete(file_id)
        await self.session.commit()
        return True

    async def get_vault_stats(self, patient_id: str) -> Dict[str, Any]:
        stats = await self.vault_repo.get_vault_stats(patient_id)
        return {**stats, "total_size_mb": round(stats["total_size_bytes"] / (1024 * 1024), 2), "usage_percent": 0}

    async def get_vault_files(self, patient_id: str, skip: int = 0, limit: int = 20,
                              file_type: Optional[str] = None, category: Optional[str] = None) -> Tuple[List[VaultFile], int]:
        return await self.vault_repo.get_by_patient_id(patient_id, skip, limit, file_type, category)

    async def mark_for_ocr(self, file_id: str) -> Optional[VaultFile]:
        return await self.vault_repo.update(file_id, extraction_status="pending")

    async def update_ocr_status(self, file_id: str, status: str, extracted_text: Optional[str] = None) -> Optional[VaultFile]:
        updates: Dict[str, Any] = {"extraction_status": status}
        if status == "completed":
            updates.update({"ocr_processed": True, "ocr_text": extracted_text, "extraction_date": datetime.utcnow()})
        return await self.vault_repo.update(file_id, **updates)


class WearableService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.wearable_repo = WearableMetricRepository(session)

    async def create_metric(self, patient_id: str, metric_type: str, metric_date: date,
                            metric_timestamp: datetime, value: float, unit: str, **kwargs) -> WearableMetric:
        metric = WearableMetric(
            id=str(uuid.uuid4()), patient_id=patient_id, metric_type=metric_type,
            metric_date=metric_date, metric_timestamp=metric_timestamp,
            value=value, unit=unit, created_by=patient_id, **kwargs
        )
        metric = await self.wearable_repo.create(metric)
        await self.session.commit()
        return metric

    async def batch_create_metrics(self, patient_id: str, metrics: List[Dict[str, Any]]) -> List[WearableMetric]:
        created = []
        for m in metrics:
            metric = WearableMetric(id=str(uuid.uuid4()), patient_id=patient_id, created_by=patient_id, **m)
            metric = await self.wearable_repo.create(metric)
            created.append(metric)
        await self.session.commit()
        return created

    async def get_patient_metrics(self, patient_id: str, skip: int = 0, limit: int = 100,
                                  metric_type: Optional[str] = None,
                                  from_date: Optional[date] = None, to_date: Optional[date] = None) -> Tuple[List[WearableMetric], int]:
        return await self.wearable_repo.get_by_patient_id(patient_id, skip, limit, metric_type, from_date, to_date)

    async def get_metric_types(self, patient_id: str) -> List[str]:
        return await self.wearable_repo.get_metric_types(patient_id)

    async def get_recent_metrics(self, patient_id: str, metric_type: str, days: int = 30) -> List[WearableMetric]:
        return await self.wearable_repo.get_latest_by_type(patient_id, metric_type, days)
