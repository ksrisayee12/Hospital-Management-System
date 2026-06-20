"""
Repository layer for data access patterns.
Implements CRUD operations and common queries.
"""

from typing import List, Optional, Any, Dict, TypeVar, Generic
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.models import (
    Patient, MedicalRecord, Appointment, TimelineEvent, 
    FamilyAccess, VaultFile, WearableMetric
)

T = TypeVar('T')


# ============================================================================
# BASE REPOSITORY
# ============================================================================

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID."""
        stmt = select(self.model).where(
            and_(
                self.model.id == id,
                self.model.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        order_by: Optional[str] = None
    ) -> tuple[List[T], int]:
        """Get all entities with pagination."""
        # Count total
        count_stmt = select(func.count()).select_from(self.model).where(
            self.model.is_deleted == False
        )
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get items
        stmt = select(self.model).where(self.model.is_deleted == False)
        
        if order_by:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(desc(self.model.created_at))
        
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        return items, total

    async def create(self, obj: T) -> T:
        """Create new entity."""
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def update(self, id: str, **kwargs) -> Optional[T]:
        """Update entity."""
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
        """Soft delete entity."""
        obj = await self.get_by_id(id)
        if not obj:
            return False
        
        obj.is_deleted = True
        obj.updated_at = datetime.utcnow()
        await self.session.flush()
        return True

    async def hard_delete(self, id: str) -> bool:
        """Hard delete entity (permanent)."""
        stmt = select(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        obj = result.scalars().first()
        
        if not obj:
            return False
        
        await self.session.delete(obj)
        await self.session.flush()
        return True


# ============================================================================
# PATIENT REPOSITORY
# ============================================================================

class PatientRepository(BaseRepository[Patient]):
    """Repository for patient operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Patient)

    async def get_by_email(self, email: str) -> Optional[Patient]:
        """Get patient by email."""
        stmt = select(self.model).where(
            and_(
                self.model.email == email,
                self.model.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_user_id(self, user_id: str) -> Optional[Patient]:
        """Get patient by authentication user ID."""
        stmt = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_with_records(self, patient_id: str) -> Optional[Patient]:
        """Get patient with eagerly loaded relationships."""
        stmt = select(self.model).where(
            and_(
                self.model.id == patient_id,
                self.model.is_deleted == False
            )
        ).options(
            selectinload(self.model.medical_records),
            selectinload(self.model.appointments),
            selectinload(self.model.family_accesses)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()


# ============================================================================
# MEDICAL RECORD REPOSITORY
# ============================================================================

class MedicalRecordRepository(BaseRepository[MedicalRecord]):
    """Repository for medical records."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, MedicalRecord)

    async def get_by_patient_id(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20,
        record_type: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> tuple[List[MedicalRecord], int]:
        """Get medical records for a patient with filters."""
        conditions = [
            self.model.patient_id == patient_id,
            self.model.is_deleted == False
        ]
        
        if record_type:
            conditions.append(self.model.record_type == record_type)
        
        if from_date:
            conditions.append(self.model.record_date >= from_date)
        
        if to_date:
            conditions.append(self.model.record_date <= to_date)

        # Count
        count_stmt = select(func.count()).select_from(self.model).where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get records
        stmt = select(self.model).where(and_(*conditions)).order_by(
            desc(self.model.record_date)
        ).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        return items, total

    async def get_critical_records(
        self,
        patient_id: str,
        limit: int = 10
    ) -> List[MedicalRecord]:
        """Get critical medical records for a patient."""
        stmt = select(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.is_critical == True,
                self.model.is_deleted == False
            )
        ).order_by(desc(self.model.record_date)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_provider(
        self,
        patient_id: str,
        provider_id: str
    ) -> List[MedicalRecord]:
        """Get records from specific provider."""
        stmt = select(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.provider_id == provider_id,
                self.model.is_deleted == False
            )
        ).order_by(desc(self.model.record_date))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_type(self, patient_id: str) -> Dict[str, int]:
        """Count records by type."""
        stmt = select(
            self.model.record_type,
            func.count(self.model.id)
        ).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.is_deleted == False
            )
        ).group_by(self.model.record_type)
        result = await self.session.execute(stmt)
        return dict(result.all())


# ============================================================================
# APPOINTMENT REPOSITORY
# ============================================================================

class AppointmentRepository(BaseRepository[Appointment]):
    """Repository for appointments."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Appointment)

    async def get_by_patient_id(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> tuple[List[Appointment], int]:
        """Get appointments for patient."""
        conditions = [
            self.model.patient_id == patient_id,
            self.model.is_deleted == False
        ]
        
        if status:
            conditions.append(self.model.status == status)
        
        if from_date:
            conditions.append(self.model.appointment_date >= from_date)
        
        if to_date:
            conditions.append(self.model.appointment_date <= to_date)

        # Count
        count_stmt = select(func.count()).select_from(self.model).where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        # Get items
        stmt = select(self.model).where(and_(*conditions)).order_by(
            self.model.appointment_date
        ).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        return items, total

    async def get_upcoming(
        self,
        patient_id: str,
        days: int = 30
    ) -> List[Appointment]:
        """Get upcoming appointments."""
        now = datetime.utcnow()
        future = now + timedelta(days=days)
        
        stmt = select(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.appointment_date >= now,
                self.model.appointment_date <= future,
                self.model.status.in_(["pending", "approved"]),
                self.model.is_deleted == False
            )
        ).order_by(self.model.appointment_date)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_doctor(
        self,
        patient_id: str,
        doctor_id: str
    ) -> List[Appointment]:
        """Get appointments with specific doctor."""
        stmt = select(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.doctor_id == doctor_id,
                self.model.is_deleted == False
            )
        ).order_by(desc(self.model.appointment_date))
        result = await self.session.execute(stmt)
        return result.scalars().all()


# ============================================================================
# TIMELINE REPOSITORY
# ============================================================================

class TimelineRepository(BaseRepository[TimelineEvent]):
    """Repository for timeline events."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, TimelineEvent)

    async def get_by_patient_id(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[TimelineEvent], int]:
        """Get timeline events for patient."""
        count_stmt = select(func.count()).select_from(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.is_deleted == False
            )
        )
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        stmt = select(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.is_deleted == False
            )
        ).order_by(desc(self.model.event_date)).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        return items, total

    async def get_by_year(
        self,
        patient_id: str,
        year: int
    ) -> List[TimelineEvent]:
        """Get events for specific year."""
        stmt = select(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.event_year == year,
                self.model.is_deleted == False
            )
        ).order_by(self.model.event_date)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_years(self, patient_id: str) -> List[int]:
        """Get all years with events."""
        stmt = select(self.model.event_year).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.is_deleted == False
            )
        ).distinct().order_by(desc(self.model.event_year))
        result = await self.session.execute(stmt)
        return result.scalars().all()


# ============================================================================
# FAMILY ACCESS REPOSITORY
# ============================================================================

class FamilyAccessRepository(BaseRepository[FamilyAccess]):
    """Repository for family access management."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, FamilyAccess)

    async def get_by_patient_id(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None
    ) -> tuple[List[FamilyAccess], int]:
        """Get family access records for patient."""
        conditions = [
            self.model.patient_id == patient_id,
            self.model.is_deleted == False
        ]
        
        if status:
            conditions.append(self.model.status == status)

        count_stmt = select(func.count()).select_from(self.model).where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        stmt = select(self.model).where(and_(*conditions)).order_by(
            desc(self.model.requested_at)
        ).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        return items, total

    async def get_approved_members(self, patient_id: str) -> List[FamilyAccess]:
        """Get approved family members."""
        stmt = select(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.status == "approved",
                self.model.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_family_member(
        self,
        patient_id: str,
        family_member_user_id: str
    ) -> Optional[FamilyAccess]:
        """Get specific family member access."""
        stmt = select(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.family_member_user_id == family_member_user_id,
                self.model.is_deleted == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_pending_requests(self, patient_id: str) -> List[FamilyAccess]:
        """Get pending family access requests."""
        stmt = select(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.status == "pending",
                self.model.is_deleted == False
            )
        ).order_by(desc(self.model.requested_at))
        result = await self.session.execute(stmt)
        return result.scalars().all()


# ============================================================================
# VAULT FILE REPOSITORY
# ============================================================================

class VaultFileRepository(BaseRepository[VaultFile]):
    """Repository for vault file operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, VaultFile)

    async def get_by_patient_id(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20,
        file_type: Optional[str] = None,
        category: Optional[str] = None
    ) -> tuple[List[VaultFile], int]:
        """Get vault files for patient."""
        conditions = [
            self.model.patient_id == patient_id,
            self.model.is_deleted == False
        ]
        
        if file_type:
            conditions.append(self.model.file_type == file_type)
        
        if category:
            conditions.append(self.model.category == category)

        count_stmt = select(func.count()).select_from(self.model).where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        stmt = select(self.model).where(and_(*conditions)).order_by(
            desc(self.model.upload_date)
        ).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        return items, total

    async def get_vault_stats(self, patient_id: str) -> Dict[str, Any]:
        """Get vault statistics."""
        files = await self.get_by_patient_id(patient_id, limit=1000)
        
        total_files = len(files[0])
        total_size = sum(f.file_size_bytes for f in files[0])
        
        files_by_type = {}
        files_by_category = {}
        ocr_processed = 0
        ocr_pending = 0
        
        for f in files[0]:
            files_by_type[f.file_type] = files_by_type.get(f.file_type, 0) + 1
            files_by_category[f.category or "uncategorized"] = files_by_category.get(
                f.category or "uncategorized", 0
            ) + 1
            
            if f.ocr_processed:
                ocr_processed += 1
            elif f.extraction_status == "pending":
                ocr_pending += 1
        
        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "files_by_type": files_by_type,
            "files_by_category": files_by_category,
            "ocr_processed_count": ocr_processed,
            "ocr_pending_count": ocr_pending
        }


# ============================================================================
# WEARABLE METRICS REPOSITORY
# ============================================================================

class WearableMetricRepository(BaseRepository[WearableMetric]):
    """Repository for wearable metrics."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, WearableMetric)

    async def get_by_patient_id(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 100,
        metric_type: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> tuple[List[WearableMetric], int]:
        """Get wearable metrics for patient."""
        conditions = [
            self.model.patient_id == patient_id,
            self.model.is_deleted == False
        ]
        
        if metric_type:
            conditions.append(self.model.metric_type == metric_type)
        
        if from_date:
            conditions.append(self.model.metric_date >= from_date)
        
        if to_date:
            conditions.append(self.model.metric_date <= to_date)

        count_stmt = select(func.count()).select_from(self.model).where(and_(*conditions))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar()

        stmt = select(self.model).where(and_(*conditions)).order_by(
            desc(self.model.metric_date)
        ).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        items = result.scalars().all()
        
        return items, total

    async def get_latest_by_type(
        self,
        patient_id: str,
        metric_type: str,
        days: int = 30
    ) -> List[WearableMetric]:
        """Get latest metrics of specific type."""
        from_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(self.model).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.metric_type == metric_type,
                self.model.metric_date >= from_date.date(),
                self.model.is_deleted == False
            )
        ).order_by(self.model.metric_timestamp)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_metric_types(self, patient_id: str) -> List[str]:
        """Get available metric types for patient."""
        stmt = select(self.model.metric_type).where(
            and_(
                self.model.patient_id == patient_id,
                self.model.is_deleted == False
            )
        ).distinct()
        result = await self.session.execute(stmt)
        return result.scalars().all()
