"""
Repository layer — all existing repos + new repos for Module 2 models.
Follows BaseRepository[T] pattern, fully async.
"""

from typing import List, Optional, Any, Dict, TypeVar, Generic
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload

from app.models import (
    Patient, MedicalRecord, Appointment, TimelineEvent,
    FamilyAccess, VaultFile, WearableMetric,
    Prescription, PrescriptionSafety, WearableGoal,
    HealthInsight, RAGIndexStatus, RecordAccessLog,
    RAGIndexStatusEnum, RiskLevel
)

T = TypeVar('T')


# ============================================================================
# BASE REPOSITORY
# ============================================================================

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type):
        self.session = session
        self.model = model

    async def get_by_id(self, id: str) -> Optional[T]:
        stmt = select(self.model).where(
            and_(self.model.id == id, self.model.is_deleted == False)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 20) -> tuple:
        count_stmt = select(func.count()).select_from(self.model).where(self.model.is_deleted == False)
        total = (await self.session.execute(count_stmt)).scalar()
        stmt = select(self.model).where(self.model.is_deleted == False).order_by(
            desc(self.model.created_at)
        ).offset(skip).limit(limit)
        items = (await self.session.execute(stmt)).scalars().all()
        return items, total

    async def create(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, id: str, **kwargs) -> Optional[T]:
        obj = await self.get_by_id(id)
        if not obj:
            return None
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        obj.updated_at = datetime.utcnow()
        await self.session.flush()
        return obj

    async def delete(self, id: str) -> bool:
        obj = await self.get_by_id(id)
        if not obj:
            return False
        obj.is_deleted = True
        obj.updated_at = datetime.utcnow()
        await self.session.flush()
        return True


# ============================================================================
# PATIENT REPOSITORY
# ============================================================================

class PatientRepository(BaseRepository[Patient]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Patient)

    async def get_by_email(self, email: str) -> Optional[Patient]:
        stmt = select(Patient).where(and_(Patient.email == email, Patient.is_deleted == False))
        return (await self.session.execute(stmt)).scalars().first()

    async def get_by_user_id(self, user_id: str) -> Optional[Patient]:
        stmt = select(Patient).where(and_(Patient.user_id == user_id, Patient.is_deleted == False))
        return (await self.session.execute(stmt)).scalars().first()

    async def get_with_records(self, patient_id: str) -> Optional[Patient]:
        stmt = select(Patient).where(
            and_(Patient.id == patient_id, Patient.is_deleted == False)
        ).options(
            selectinload(Patient.medical_records),
            selectinload(Patient.appointments),
            selectinload(Patient.family_accesses)
        )
        return (await self.session.execute(stmt)).scalars().first()


# ============================================================================
# MEDICAL RECORD REPOSITORY
# ============================================================================

class MedicalRecordRepository(BaseRepository[MedicalRecord]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, MedicalRecord)

    async def get_by_patient_id(
        self, patient_id: str, skip: int = 0, limit: int = 20,
        record_type: Optional[str] = None,
        from_date: Optional[date] = None, to_date: Optional[date] = None,
        include_archived: bool = False
    ) -> tuple:
        conditions = [MedicalRecord.patient_id == patient_id, MedicalRecord.is_deleted == False]
        if not include_archived:
            conditions.append(MedicalRecord.is_archived == False)
        if record_type:
            conditions.append(MedicalRecord.record_type == record_type)
        if from_date:
            conditions.append(MedicalRecord.record_date >= from_date)
        if to_date:
            conditions.append(MedicalRecord.record_date <= to_date)

        total = (await self.session.execute(
            select(func.count()).select_from(MedicalRecord).where(and_(*conditions))
        )).scalar()
        items = (await self.session.execute(
            select(MedicalRecord).where(and_(*conditions)).order_by(
                desc(MedicalRecord.record_date)
            ).offset(skip).limit(limit)
        )).scalars().all()
        return items, total

    async def get_critical_records(self, patient_id: str, limit: int = 10) -> List[MedicalRecord]:
        stmt = select(MedicalRecord).where(
            and_(MedicalRecord.patient_id == patient_id, MedicalRecord.is_critical == True,
                 MedicalRecord.is_deleted == False)
        ).order_by(desc(MedicalRecord.record_date)).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()

    async def count_by_type(self, patient_id: str) -> Dict[str, int]:
        stmt = select(
            MedicalRecord.record_type, func.count(MedicalRecord.id)
        ).where(
            and_(MedicalRecord.patient_id == patient_id, MedicalRecord.is_deleted == False)
        ).group_by(MedicalRecord.record_type)
        return dict((await self.session.execute(stmt)).all())

    async def get_by_provider(self, patient_id: str, provider_id: str) -> List[MedicalRecord]:
        stmt = select(MedicalRecord).where(
            and_(MedicalRecord.patient_id == patient_id,
                 MedicalRecord.provider_id == provider_id,
                 MedicalRecord.is_deleted == False)
        ).order_by(desc(MedicalRecord.record_date))
        return (await self.session.execute(stmt)).scalars().all()


# ============================================================================
# APPOINTMENT REPOSITORY
# ============================================================================

class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Appointment)

    async def get_by_patient_id(
        self, patient_id: str, skip: int = 0, limit: int = 20,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None, to_date: Optional[datetime] = None
    ) -> tuple:
        conditions = [Appointment.patient_id == patient_id, Appointment.is_deleted == False]
        if status:
            conditions.append(Appointment.status == status)
        if from_date:
            conditions.append(Appointment.appointment_date >= from_date)
        if to_date:
            conditions.append(Appointment.appointment_date <= to_date)

        total = (await self.session.execute(
            select(func.count()).select_from(Appointment).where(and_(*conditions))
        )).scalar()
        items = (await self.session.execute(
            select(Appointment).where(and_(*conditions)).order_by(
                Appointment.appointment_date
            ).offset(skip).limit(limit)
        )).scalars().all()
        return items, total

    async def get_upcoming(self, patient_id: str, days: int = 30) -> List[Appointment]:
        now = datetime.utcnow()
        future = now + timedelta(days=days)
        stmt = select(Appointment).where(
            and_(
                Appointment.patient_id == patient_id,
                Appointment.appointment_date >= now,
                Appointment.appointment_date <= future,
                Appointment.status.in_(["pending", "approved"]),
                Appointment.is_deleted == False
            )
        ).order_by(Appointment.appointment_date)
        return (await self.session.execute(stmt)).scalars().all()

    async def count_by_status(self, patient_id: str) -> Dict[str, int]:
        stmt = select(
            Appointment.status, func.count(Appointment.id)
        ).where(
            and_(Appointment.patient_id == patient_id, Appointment.is_deleted == False)
        ).group_by(Appointment.status)
        return dict((await self.session.execute(stmt)).all())

    async def get_by_doctor(self, patient_id: str, doctor_id: str) -> List[Appointment]:
        stmt = select(Appointment).where(
            and_(Appointment.patient_id == patient_id,
                 Appointment.doctor_id == doctor_id,
                 Appointment.is_deleted == False)
        ).order_by(desc(Appointment.appointment_date))
        return (await self.session.execute(stmt)).scalars().all()


# ============================================================================
# TIMELINE REPOSITORY
# ============================================================================

class TimelineRepository(BaseRepository[TimelineEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TimelineEvent)

    async def get_by_patient_id(self, patient_id: str, skip: int = 0, limit: int = 100) -> tuple:
        conditions = [TimelineEvent.patient_id == patient_id, TimelineEvent.is_deleted == False]
        total = (await self.session.execute(
            select(func.count()).select_from(TimelineEvent).where(and_(*conditions))
        )).scalar()
        items = (await self.session.execute(
            select(TimelineEvent).where(and_(*conditions)).order_by(
                desc(TimelineEvent.event_date)
            ).offset(skip).limit(limit)
        )).scalars().all()
        return items, total

    async def get_by_year(self, patient_id: str, year: int) -> List[TimelineEvent]:
        stmt = select(TimelineEvent).where(
            and_(TimelineEvent.patient_id == patient_id,
                 TimelineEvent.event_year == year,
                 TimelineEvent.is_deleted == False)
        ).order_by(TimelineEvent.event_date)
        return (await self.session.execute(stmt)).scalars().all()

    async def get_years(self, patient_id: str) -> List[int]:
        stmt = select(TimelineEvent.event_year).where(
            and_(TimelineEvent.patient_id == patient_id, TimelineEvent.is_deleted == False)
        ).distinct().order_by(desc(TimelineEvent.event_year))
        return (await self.session.execute(stmt)).scalars().all()


# ============================================================================
# FAMILY ACCESS REPOSITORY
# ============================================================================

class FamilyAccessRepository(BaseRepository[FamilyAccess]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FamilyAccess)

    async def get_by_patient_id(
        self, patient_id: str, skip: int = 0, limit: int = 20, status: Optional[str] = None
    ) -> tuple:
        conditions = [FamilyAccess.patient_id == patient_id, FamilyAccess.is_deleted == False]
        if status:
            conditions.append(FamilyAccess.status == status)
        total = (await self.session.execute(
            select(func.count()).select_from(FamilyAccess).where(and_(*conditions))
        )).scalar()
        items = (await self.session.execute(
            select(FamilyAccess).where(and_(*conditions)).order_by(
                desc(FamilyAccess.requested_at)
            ).offset(skip).limit(limit)
        )).scalars().all()
        return items, total

    async def get_approved_members(self, patient_id: str) -> List[FamilyAccess]:
        stmt = select(FamilyAccess).where(
            and_(FamilyAccess.patient_id == patient_id,
                 FamilyAccess.status == "approved",
                 FamilyAccess.is_deleted == False)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def get_by_family_member(self, patient_id: str, family_member_user_id: str) -> Optional[FamilyAccess]:
        stmt = select(FamilyAccess).where(
            and_(FamilyAccess.patient_id == patient_id,
                 FamilyAccess.family_member_user_id == family_member_user_id,
                 FamilyAccess.is_deleted == False)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def get_pending_requests(self, patient_id: str) -> List[FamilyAccess]:
        stmt = select(FamilyAccess).where(
            and_(FamilyAccess.patient_id == patient_id,
                 FamilyAccess.status == "pending",
                 FamilyAccess.is_deleted == False)
        ).order_by(desc(FamilyAccess.requested_at))
        return (await self.session.execute(stmt)).scalars().all()


# ============================================================================
# VAULT FILE REPOSITORY
# ============================================================================

class VaultFileRepository(BaseRepository[VaultFile]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, VaultFile)

    async def get_by_patient_id(
        self, patient_id: str, skip: int = 0, limit: int = 20,
        file_type: Optional[str] = None, category: Optional[str] = None
    ) -> tuple:
        conditions = [VaultFile.patient_id == patient_id, VaultFile.is_deleted == False]
        if file_type:
            conditions.append(VaultFile.file_type == file_type)
        if category:
            conditions.append(VaultFile.category == category)
        total = (await self.session.execute(
            select(func.count()).select_from(VaultFile).where(and_(*conditions))
        )).scalar()
        items = (await self.session.execute(
            select(VaultFile).where(and_(*conditions)).order_by(
                desc(VaultFile.upload_date)
            ).offset(skip).limit(limit)
        )).scalars().all()
        return items, total

    async def get_vault_stats(self, patient_id: str) -> Dict[str, Any]:
        files, _ = await self.get_by_patient_id(patient_id, limit=1000)
        total_size = sum(f.file_size_bytes for f in files)
        files_by_type: Dict[str, int] = {}
        files_by_category: Dict[str, int] = {}
        ocr_processed = sum(1 for f in files if f.ocr_processed)
        ocr_pending = sum(1 for f in files if f.extraction_status == "pending")
        for f in files:
            files_by_type[f.file_type] = files_by_type.get(f.file_type, 0) + 1
            key = f.category or "uncategorized"
            files_by_category[key] = files_by_category.get(key, 0) + 1
        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "files_by_type": files_by_type,
            "files_by_category": files_by_category,
            "ocr_processed_count": ocr_processed,
            "ocr_pending_count": ocr_pending,
        }


# ============================================================================
# WEARABLE METRIC REPOSITORY
# ============================================================================

class WearableMetricRepository(BaseRepository[WearableMetric]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WearableMetric)

    async def get_by_patient_id(
        self, patient_id: str, skip: int = 0, limit: int = 100,
        metric_type: Optional[str] = None,
        from_date: Optional[date] = None, to_date: Optional[date] = None
    ) -> tuple:
        conditions = [WearableMetric.patient_id == patient_id, WearableMetric.is_deleted == False]
        if metric_type:
            conditions.append(WearableMetric.metric_type == metric_type)
        if from_date:
            conditions.append(WearableMetric.metric_date >= from_date)
        if to_date:
            conditions.append(WearableMetric.metric_date <= to_date)
        total = (await self.session.execute(
            select(func.count()).select_from(WearableMetric).where(and_(*conditions))
        )).scalar()
        items = (await self.session.execute(
            select(WearableMetric).where(and_(*conditions)).order_by(
                desc(WearableMetric.metric_date)
            ).offset(skip).limit(limit)
        )).scalars().all()
        return items, total

    async def get_latest_by_type(self, patient_id: str, metric_type: str, days: int = 30) -> List[WearableMetric]:
        from_dt = datetime.utcnow() - timedelta(days=days)
        stmt = select(WearableMetric).where(
            and_(WearableMetric.patient_id == patient_id,
                 WearableMetric.metric_type == metric_type,
                 WearableMetric.metric_date >= from_dt.date(),
                 WearableMetric.is_deleted == False)
        ).order_by(WearableMetric.metric_timestamp)
        return (await self.session.execute(stmt)).scalars().all()

    async def get_metric_types(self, patient_id: str) -> List[str]:
        stmt = select(WearableMetric.metric_type).where(
            and_(WearableMetric.patient_id == patient_id, WearableMetric.is_deleted == False)
        ).distinct()
        return (await self.session.execute(stmt)).scalars().all()

    async def get_all_for_patient_period(
        self, patient_id: str, days: int = 90
    ) -> List[WearableMetric]:
        from_dt = datetime.utcnow() - timedelta(days=days)
        stmt = select(WearableMetric).where(
            and_(WearableMetric.patient_id == patient_id,
                 WearableMetric.metric_date >= from_dt.date(),
                 WearableMetric.is_deleted == False)
        ).order_by(WearableMetric.metric_timestamp)
        return (await self.session.execute(stmt)).scalars().all()


# ============================================================================
# PRESCRIPTION REPOSITORY (NEW)
# ============================================================================

class PrescriptionRepository(BaseRepository[Prescription]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Prescription)

    async def get_by_patient_id(
        self, patient_id: str, skip: int = 0, limit: int = 20,
        is_active: Optional[bool] = None
    ) -> tuple:
        conditions = [Prescription.patient_id == patient_id, Prescription.is_deleted == False]
        if is_active is not None:
            conditions.append(Prescription.is_active == is_active)
        total = (await self.session.execute(
            select(func.count()).select_from(Prescription).where(and_(*conditions))
        )).scalar()
        items = (await self.session.execute(
            select(Prescription).where(and_(*conditions)).order_by(
                desc(Prescription.prescription_date)
            ).offset(skip).limit(limit)
        )).scalars().all()
        return items, total

    async def get_active_prescriptions(self, patient_id: str) -> List[Prescription]:
        stmt = select(Prescription).where(
            and_(Prescription.patient_id == patient_id,
                 Prescription.is_active == True,
                 Prescription.is_deleted == False)
        )
        return (await self.session.execute(stmt)).scalars().all()


# ============================================================================
# PRESCRIPTION SAFETY REPOSITORY (NEW)
# ============================================================================

class PrescriptionSafetyRepository(BaseRepository[PrescriptionSafety]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, PrescriptionSafety)

    async def get_by_patient_id(
        self, patient_id: str, risk_level: Optional[str] = None, limit: int = 50
    ) -> List[PrescriptionSafety]:
        conditions = [PrescriptionSafety.patient_id == patient_id, PrescriptionSafety.is_deleted == False]
        if risk_level:
            conditions.append(PrescriptionSafety.risk_level == risk_level)
        stmt = select(PrescriptionSafety).where(and_(*conditions)).order_by(
            desc(PrescriptionSafety.analyzed_at)
        ).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()

    async def get_by_prescription(self, prescription_id: str) -> Optional[PrescriptionSafety]:
        stmt = select(PrescriptionSafety).where(
            and_(PrescriptionSafety.prescription_id == prescription_id,
                 PrescriptionSafety.is_deleted == False)
        ).order_by(desc(PrescriptionSafety.analyzed_at))
        return (await self.session.execute(stmt)).scalars().first()

    async def count_high_risk(self, patient_id: str) -> int:
        stmt = select(func.count()).select_from(PrescriptionSafety).where(
            and_(PrescriptionSafety.patient_id == patient_id,
                 PrescriptionSafety.risk_level.in_(["HIGH", "CRITICAL"]),
                 PrescriptionSafety.is_deleted == False)
        )
        return (await self.session.execute(stmt)).scalar()


# ============================================================================
# WEARABLE GOAL REPOSITORY (NEW)
# ============================================================================

class WearableGoalRepository(BaseRepository[WearableGoal]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WearableGoal)

    async def get_by_patient_id(self, patient_id: str) -> List[WearableGoal]:
        stmt = select(WearableGoal).where(
            and_(WearableGoal.patient_id == patient_id,
                 WearableGoal.is_active == True,
                 WearableGoal.is_deleted == False)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def get_by_metric_type(self, patient_id: str, metric_type: str) -> Optional[WearableGoal]:
        stmt = select(WearableGoal).where(
            and_(WearableGoal.patient_id == patient_id,
                 WearableGoal.metric_type == metric_type,
                 WearableGoal.is_deleted == False)
        )
        return (await self.session.execute(stmt)).scalars().first()


# ============================================================================
# HEALTH INSIGHT REPOSITORY (NEW)
# ============================================================================

class HealthInsightRepository(BaseRepository[HealthInsight]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, HealthInsight)

    async def get_by_patient_id(self, patient_id: str, limit: int = 10) -> List[HealthInsight]:
        stmt = select(HealthInsight).where(
            and_(HealthInsight.patient_id == patient_id, HealthInsight.is_deleted == False)
        ).order_by(desc(HealthInsight.generated_at)).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()

    async def get_unread_count(self, patient_id: str) -> int:
        stmt = select(func.count()).select_from(HealthInsight).where(
            and_(HealthInsight.patient_id == patient_id,
                 HealthInsight.is_read == False,
                 HealthInsight.is_deleted == False)
        )
        return (await self.session.execute(stmt)).scalar()

    async def get_latest(self, patient_id: str) -> Optional[HealthInsight]:
        stmt = select(HealthInsight).where(
            and_(HealthInsight.patient_id == patient_id, HealthInsight.is_deleted == False)
        ).order_by(desc(HealthInsight.generated_at))
        return (await self.session.execute(stmt)).scalars().first()


# ============================================================================
# RAG INDEX STATUS REPOSITORY (NEW)
# ============================================================================

class RAGIndexStatusRepository(BaseRepository[RAGIndexStatus]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RAGIndexStatus)

    async def get_by_record(self, patient_id: str, record_id: str, record_type: str) -> Optional[RAGIndexStatus]:
        stmt = select(RAGIndexStatus).where(
            and_(RAGIndexStatus.patient_id == patient_id,
                 RAGIndexStatus.record_id == record_id,
                 RAGIndexStatus.record_type == record_type,
                 RAGIndexStatus.is_deleted == False)
        )
        return (await self.session.execute(stmt)).scalars().first()

    async def get_pending(self, patient_id: str) -> List[RAGIndexStatus]:
        stmt = select(RAGIndexStatus).where(
            and_(RAGIndexStatus.patient_id == patient_id,
                 RAGIndexStatus.status == RAGIndexStatusEnum.PENDING,
                 RAGIndexStatus.is_deleted == False)
        )
        return (await self.session.execute(stmt)).scalars().all()


# ============================================================================
# RECORD ACCESS LOG REPOSITORY (NEW) — Immutable, no soft-delete
# ============================================================================

class RecordAccessLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, log: RecordAccessLog) -> RecordAccessLog:
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_by_record(self, record_id: str, limit: int = 50) -> List[RecordAccessLog]:
        stmt = select(RecordAccessLog).where(
            RecordAccessLog.record_id == record_id
        ).order_by(desc(RecordAccessLog.accessed_at)).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()

    async def get_by_patient(self, patient_id: str, limit: int = 100) -> List[RecordAccessLog]:
        stmt = select(RecordAccessLog).where(
            RecordAccessLog.patient_id == patient_id
        ).order_by(desc(RecordAccessLog.accessed_at)).limit(limit)
        return (await self.session.execute(stmt)).scalars().all()
