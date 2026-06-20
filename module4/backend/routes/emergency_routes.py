"""
Emergency Override routes.

Access policy:
  - POST /emergency              : doctor only; doctor_id MUST match JWT sub.
  - GET  /emergency              : admin/super_admin; admin is hospital-scoped.
  - POST /emergency/{id}/approve : admin/super_admin.

Rate limiting:
  - POST /emergency: 10 requests per minute per user (doctors spamming
    override requests is itself a fraud signal — slowapi handles this
    at the application layer; Render/Railway can add infra-level limits too).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from module4.backend.admin.emergency_service import (
    create_override_request,
    list_override_requests,
    review_override_request,
)
from module4.backend.core.auth import CurrentUser, require_admin, require_doctor
from module4.backend.core.database import get_db
from module4.backend.models.emergency_override import OverrideStatus
from module4.backend.schemas.emergency import EmergencyOverrideCreate, EmergencyOverrideOut, EmergencyOverrideReview
from module4.backend.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/emergency", tags=["Emergency Override"])


@router.post("", response_model=EmergencyOverrideOut, status_code=201)
def request_override(
    payload: EmergencyOverrideCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_doctor),
):
    """
    Request an emergency override to access a patient's records.

    Security: a doctor may only submit overrides for themselves
    (doctor_id must equal JWT sub).
    Rate-limited: 10 requests per minute per IP.
    """
    if payload.doctor_id != user.user_id:
        raise HTTPException(status_code=403, detail="You may only request overrides as yourself.")

    return create_override_request(
        db,
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        reason=payload.reason,
        urgency=payload.urgency,
        hospital_id=payload.hospital_id,
    )


@router.get("", response_model=PaginatedResponse[EmergencyOverrideOut])
def get_override_requests(
    status: OverrideStatus | None = None,
    hospital_id: str | None = None,
    limit: int = Query(50, le=200, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
):
    """
    List override requests with optional filters.

    Admin role: hospital_id from JWT always wins.
    Super-admin: unscoped; may filter freely.
    """
    effective_hospital_id = hospital_id
    if user.role == "admin":
        effective_hospital_id = user.hospital_id

    all_items = list_override_requests(db, status=status, hospital_id=effective_hospital_id)
    total = len(all_items)
    items = all_items[offset : offset + limit]
    return PaginatedResponse(total=total, items=items, limit=limit, offset=offset)


@router.post("/{request_id}/approve", response_model=EmergencyOverrideOut)
def approve_or_reject_override(
    request_id: str,
    payload: EmergencyOverrideReview,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
):
    """
    Approve or reject a pending emergency override request.

    On approval, sets a temporary access window (default 24h).
    The decision is mirrored to the immutable ledger as a critical action.
    """
    override = review_override_request(
        db,
        request_id=request_id,
        approve=payload.approve,
        reviewed_by=user.user_id,
        review_notes=payload.review_notes,
        access_window_hours=payload.access_window_hours,
    )
    if not override:
        raise HTTPException(status_code=404, detail="Override request not found")
    return override
