"""
API routes for healthcare vault backend.
Includes endpoints for all features: patients, medical records, appointments, timeline, family, vault, wearable.
"""

from typing import Optional
from datetime import date, datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body, status, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import (
    PatientCreateRequest, PatientUpdateRequest, PatientResponse,
    MedicalRecordCreateRequest, MedicalRecordUpdateRequest, MedicalRecordResponse,
    AppointmentCreateRequest, AppointmentUpdateRequest, AppointmentStatusUpdate,
    AppointmentRescheduleRequest, AppointmentResponse,
    TimelineEventResponse, TimelineListResponse,
    FamilyAccessCreateRequest, FamilyAccessUpdateRequest, FamilyAccessApprovalRequest,
    FamilyAccessResponse, FamilyDashboardResponse,
    VaultFileCreateRequest, VaultFileResponse, VaultStorageStatsResponse,
    WearableMetricCreateRequest, WearableMetricResponse, WearableBatchUploadRequest,
    WearableMetricsStatsResponse, DashboardResponse,
    PaginationParams, PaginatedResponse, SuccessResponse, ErrorResponse,
    create_paginated_response
)
from app.services import (
    PatientService, DashboardService, MedicalRecordService,
    AppointmentService, TimelineService, FamilyAccessService,
    VaultService, WearableService
)
from app.dependencies import get_db, get_current_user
from app.utils.exceptions import (
    PatientNotFound, MedicalRecordNotFound, AppointmentNotFound,
    UnauthorizedAccess, InvalidOperation
)


# ============================================================================
# PATIENT ROUTES
# ============================================================================

router_patient = APIRouter(prefix="/api/v1/patients", tags=["Patients"])


@router_patient.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    request: PatientCreateRequest,
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new patient profile."""
    service = PatientService(session)
    
    # Check if patient already exists
    existing = await service.get_patient_by_user_id(request.user_id)
    if existing:
        raise HTTPException(status_code=400, detail="Patient already exists")
    
    patient = await service.create_patient(**request.model_dump())
    return PatientResponse.model_validate(patient)


@router_patient.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str = Path(..., description="Patient ID"),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get patient profile."""
    # TODO: Verify authorization - patient can access own, providers with consent
    service = PatientService(session)
    patient = await service.get_patient(patient_id)
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return PatientResponse.model_validate(patient)


@router_patient.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str = Path(...),
    request: PatientUpdateRequest = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update patient information."""
    service = PatientService(session)
    
    patient = await service.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Verify authorization
    if current_user.get("sub") != patient.user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    updated = await service.update_patient(patient_id, **request.model_dump(exclude_unset=True))
    return PatientResponse.model_validate(updated)


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

router_dashboard = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router_dashboard.get("/{patient_id}", response_model=DashboardResponse)
async def get_dashboard(
    patient_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get patient dashboard overview."""
    service = DashboardService(session)
    dashboard = await service.get_dashboard(patient_id)
    
    if not dashboard:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return dashboard


# ============================================================================
# MEDICAL RECORDS ROUTES
# ============================================================================

router_medical = APIRouter(prefix="/api/v1/patients/{patient_id}/medical-records", tags=["Medical Records"])


@router_medical.post("", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_medical_record(
    patient_id: str = Path(...),
    request: MedicalRecordCreateRequest = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create medical record."""
    service = MedicalRecordService(session)
    
    record = await service.create_medical_record(
        patient_id=patient_id,
        **request.model_dump()
    )
    return MedicalRecordResponse.model_validate(record)


@router_medical.get("", response_model=PaginatedResponse)
async def get_medical_records(
    patient_id: str = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    record_type: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get patient medical records."""
    service = MedicalRecordService(session)
    skip = (page - 1) * page_size
    
    records, total = await service.get_patient_medical_records(
        patient_id, skip, page_size, record_type, from_date, to_date
    )
    
    response_items = [MedicalRecordResponse.model_validate(r) for r in records]
    return create_paginated_response(response_items, page, page_size, total)


@router_medical.get("/{record_id}", response_model=MedicalRecordResponse)
async def get_medical_record(
    patient_id: str = Path(...),
    record_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific medical record."""
    service = MedicalRecordService(session)
    record = await service.get_medical_record(record_id)
    
    if not record or record.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Record not found")
    
    return MedicalRecordResponse.model_validate(record)


@router_medical.put("/{record_id}", response_model=MedicalRecordResponse)
async def update_medical_record(
    patient_id: str = Path(...),
    record_id: str = Path(...),
    request: MedicalRecordUpdateRequest = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update medical record."""
    service = MedicalRecordService(session)
    record = await service.get_medical_record(record_id)
    
    if not record or record.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Record not found")
    
    updated = await service.update_medical_record(record_id, **request.model_dump(exclude_unset=True))
    return MedicalRecordResponse.model_validate(updated)


@router_medical.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medical_record(
    patient_id: str = Path(...),
    record_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete medical record."""
    service = MedicalRecordService(session)
    record = await service.get_medical_record(record_id)
    
    if not record or record.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Record not found")
    
    await service.medical_repo.delete(record_id)
    await session.commit()


@router_medical.get("/critical", response_model=list[MedicalRecordResponse])
async def get_critical_records(
    patient_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get critical medical records."""
    service = MedicalRecordService(session)
    records = await service.get_critical_records(patient_id)
    
    return [MedicalRecordResponse.model_validate(r) for r in records]


# ============================================================================
# APPOINTMENTS ROUTES
# ============================================================================

router_appointment = APIRouter(prefix="/api/v1/patients/{patient_id}/appointments", tags=["Appointments"])


@router_appointment.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def request_appointment(
    patient_id: str = Path(...),
    request: AppointmentCreateRequest = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Request appointment from doctor."""
    service = AppointmentService(session)
    
    appointment = await service.request_appointment(
        patient_id=patient_id,
        **request.model_dump()
    )
    return AppointmentResponse.model_validate(appointment)


@router_appointment.get("", response_model=PaginatedResponse)
async def get_appointments(
    patient_id: str = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get patient appointments."""
    service = AppointmentService(session)
    skip = (page - 1) * page_size
    
    appointments, total = await service.appointment_repo.get_by_patient_id(
        patient_id, skip, page_size, status, from_date, to_date
    )
    
    response_items = [AppointmentResponse.model_validate(a) for a in appointments]
    return create_paginated_response(response_items, page, page_size, total)


@router_appointment.get("/upcoming", response_model=list[AppointmentResponse])
async def get_upcoming_appointments(
    patient_id: str = Path(...),
    days: int = Query(30, ge=1),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming appointments."""
    service = AppointmentService(session)
    appointments = await service.get_upcoming_appointments(patient_id, days)
    
    return [AppointmentResponse.model_validate(a) for a in appointments]


@router_appointment.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    patient_id: str = Path(...),
    appointment_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific appointment."""
    appointment = await session.get(Appointment, appointment_id)
    
    if not appointment or appointment.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return AppointmentResponse.model_validate(appointment)


@router_appointment.put("/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    patient_id: str = Path(...),
    appointment_id: str = Path(...),
    request: AppointmentStatusUpdate = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update appointment status."""
    service = AppointmentService(session)
    
    appointment = await service.appointment_repo.get_by_id(appointment_id)
    if not appointment or appointment.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    # Handle different status transitions
    if request.status == "completed":
        updated = await service.complete_appointment(
            appointment_id,
            request.notes,
            request.next_appointment_date
        )
    elif request.status == "approved":
        updated = await service.approve_appointment(appointment_id, current_user.get("sub"))
    elif request.status == "cancelled":
        updated = await service.reject_appointment(appointment_id, request.notes)
    else:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    return AppointmentResponse.model_validate(updated)


@router_appointment.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    patient_id: str = Path(...),
    appointment_id: str = Path(...),
    request: AppointmentRescheduleRequest = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Request appointment reschedule."""
    service = AppointmentService(session)
    
    appointment = await service.appointment_repo.get_by_id(appointment_id)
    if not appointment or appointment.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    updated = await service.reschedule_appointment(
        appointment_id,
        request.requested_reschedule_date,
        request.reschedule_reason
    )
    return AppointmentResponse.model_validate(updated)


# ============================================================================
# TIMELINE ROUTES
# ============================================================================

router_timeline = APIRouter(prefix="/api/v1/patients/{patient_id}/timeline", tags=["Timeline"])


@router_timeline.get("", response_model=PaginatedResponse)
async def get_timeline(
    patient_id: str = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get patient timeline."""
    service = TimelineService(session)
    skip = (page - 1) * page_size
    
    events, total = await service.get_patient_timeline(patient_id, skip, page_size)
    return create_paginated_response(events, page, page_size, total)


@router_timeline.get("/by-year", response_model=list[TimelineListResponse])
async def get_timeline_by_year(
    patient_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get timeline grouped by year."""
    service = TimelineService(session)
    return await service.get_timeline_by_year(patient_id)


# ============================================================================
# FAMILY ACCESS ROUTES
# ============================================================================

router_family = APIRouter(prefix="/api/v1/patients/{patient_id}/family", tags=["Family Access"])


@router_family.post("/invite", response_model=FamilyAccessResponse, status_code=status.HTTP_201_CREATED)
async def invite_family_member(
    patient_id: str = Path(...),
    request: FamilyAccessCreateRequest = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Invite family member to access records."""
    service = FamilyAccessService(session)
    patient_service = PatientService(session)
    
    family_member = await patient_service.get_patient_by_email(request.family_member_email)
    family_member_id = family_member.user_id if family_member else f"pending_{request.family_member_email}"
    
    access = await service.request_family_access(
        patient_id=patient_id,
        family_member_user_id=family_member_id,
        **request.model_dump()
    )
    return FamilyAccessResponse.model_validate(access)

@router_family.get("/{access_id}/dashboard", response_model=DashboardResponse)
async def get_family_dashboard(
    patient_id: str = Path(...),
    access_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard for a linked patient."""
    service = FamilyAccessService(session)
    access = await service.family_repo.get_by_id(access_id)
    
    if not access or access.patient_id != patient_id or access.status != "approved":
        raise HTTPException(status_code=403, detail="Not authorized to view this patient's dashboard")
        
    dashboard_service = DashboardService(session)
    dashboard = await dashboard_service.get_dashboard(patient_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
        
    return dashboard


@router_family.get("", response_model=PaginatedResponse)
async def get_family_members(
    patient_id: str = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get family access records."""
    service = FamilyAccessService(session)
    
    access_records, total = await service.family_repo.get_by_patient_id(
        patient_id, (page - 1) * page_size, page_size, status
    )
    
    response_items = [FamilyAccessResponse.model_validate(a) for a in access_records]
    return create_paginated_response(response_items, page, page_size, total)


@router_family.put("/{access_id}/approve", response_model=FamilyAccessResponse)
async def approve_family_access(
    patient_id: str = Path(...),
    access_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve family member access."""
    service = FamilyAccessService(session)
    
    access = await service.family_repo.get_by_id(access_id)
    if not access or access.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    approved = await service.approve_family_access(access_id, current_user.get("sub"))
    return FamilyAccessResponse.model_validate(approved)


@router_family.put("/{access_id}/reject", response_model=FamilyAccessResponse)
async def reject_family_access(
    patient_id: str = Path(...),
    access_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Reject family member access."""
    service = FamilyAccessService(session)
    
    access = await service.family_repo.get_by_id(access_id)
    if not access or access.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    rejected = await service.reject_family_access(access_id)
    return FamilyAccessResponse.model_validate(rejected)


@router_family.delete("/{access_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_family_access(
    patient_id: str = Path(...),
    access_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Revoke family member access."""
    service = FamilyAccessService(session)
    
    access = await service.family_repo.get_by_id(access_id)
    if not access or access.patient_id != patient_id:
        raise HTTPException(status_code=404, detail="Access record not found")
    
    await service.revoke_family_access(access_id)


# ============================================================================
# VAULT ROUTES
# ============================================================================

router_vault = APIRouter(prefix="/api/v1/patients/{patient_id}/vault", tags=["Vault Storage"])


@router_vault.post("/upload", response_model=VaultFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_vault_file(
    patient_id: str = Path(...),
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_shared_with_providers: bool = Form(False),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload file to health vault."""
    service = VaultService(session)
    content = await file.read()
    
    saved_file = await service.upload_and_encrypt_file(
        patient_id=patient_id,
        file_name=file.filename,
        content=content,
        file_type=file.content_type or "application/octet-stream",
        category=category,
        description=description,
        is_shared_with_providers=is_shared_with_providers
    )
    return VaultFileResponse.model_validate(saved_file)

@router_vault.get("/{file_id}/download")
async def download_vault_file(
    patient_id: str = Path(...),
    file_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Download decrypted file from health vault."""
    service = VaultService(session)
    file_record, decrypted_content = await service.download_and_decrypt_file(patient_id, file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    return Response(content=decrypted_content, media_type=file_record.mime_type or "application/octet-stream")

@router_vault.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vault_file(
    patient_id: str = Path(...),
    file_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete file from health vault."""
    service = VaultService(session)
    success = await service.delete_file(patient_id, file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")


@router_vault.get("", response_model=PaginatedResponse)
async def get_vault_files(
    patient_id: str = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    file_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get vault files."""
    service = VaultService(session)
    skip = (page - 1) * page_size
    
    files, total = await service.get_vault_files(
        patient_id, skip, page_size, file_type, category
    )
    
    response_items = [VaultFileResponse.model_validate(f) for f in files]
    return create_paginated_response(response_items, page, page_size, total)


@router_vault.get("/stats", response_model=VaultStorageStatsResponse)
async def get_vault_stats(
    patient_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get vault storage statistics."""
    service = VaultService(session)
    stats = await service.get_vault_stats(patient_id)
    
    return VaultStorageStatsResponse(
        patient_id=patient_id,
        max_size_mb=500,
        **stats
    )


# ============================================================================
# WEARABLE METRICS ROUTES
# ============================================================================

router_wearable = APIRouter(prefix="/api/v1/patients/{patient_id}/wearable", tags=["Wearable Metrics"])


@router_wearable.post("", response_model=WearableMetricResponse, status_code=status.HTTP_201_CREATED)
async def create_wearable_metric(
    patient_id: str = Path(...),
    request: WearableMetricCreateRequest = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create wearable metric."""
    service = WearableService(session)
    
    metric = await service.create_metric(
        patient_id=patient_id,
        **request.model_dump()
    )
    return WearableMetricResponse.model_validate(metric)


@router_wearable.post("/batch", response_model=list[WearableMetricResponse], status_code=status.HTTP_201_CREATED)
async def batch_upload_wearable(
    patient_id: str = Path(...),
    request: WearableBatchUploadRequest = Body(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Batch upload wearable metrics."""
    service = WearableService(session)
    
    metrics = await service.batch_create_metrics(
        patient_id,
        [m.model_dump() for m in request.metrics]
    )
    return [WearableMetricResponse.model_validate(m) for m in metrics]


@router_wearable.get("", response_model=PaginatedResponse)
async def get_wearable_metrics(
    patient_id: str = Path(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    metric_type: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get wearable metrics."""
    service = WearableService(session)
    skip = (page - 1) * page_size
    
    metrics, total = await service.get_patient_metrics(
        patient_id, skip, page_size, metric_type, from_date, to_date
    )
    
    response_items = [WearableMetricResponse.model_validate(m) for m in metrics]
    return create_paginated_response(response_items, page, page_size, total)


@router_wearable.get("/types", response_model=list[str])
async def get_metric_types(
    patient_id: str = Path(...),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get available metric types."""
    service = WearableService(session)
    return await service.get_metric_types(patient_id)


@router_wearable.get("/recent/{metric_type}", response_model=list[WearableMetricResponse])
async def get_recent_metrics(
    patient_id: str = Path(...),
    metric_type: str = Path(...),
    days: int = Query(30, ge=1),
    session: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get recent metrics of specific type."""
    service = WearableService(session)
    metrics = await service.get_recent_metrics(patient_id, metric_type, days)
    
    return [WearableMetricResponse.model_validate(m) for m in metrics]


# ============================================================================
# ROUTE AGGREGATION
# ============================================================================

def include_healthcare_routes(app):
    """Include all healthcare routes in the FastAPI app."""
    app.include_router(router_patient)
    app.include_router(router_dashboard)
    app.include_router(router_medical)
    app.include_router(router_appointment)
    app.include_router(router_timeline)
    app.include_router(router_family)
    app.include_router(router_vault)
    app.include_router(router_wearable)
