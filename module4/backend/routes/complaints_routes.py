"""
Complaints routes.

Access policy:
  - POST /complaints       : patient only; patient_id MUST match JWT sub.
  - GET  /complaints       : admin/super_admin; admin is hospital-scoped.
  - PATCH /complaints/{id} : admin/super_admin; admin MUST only touch complaints
                             from their own hospital.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from module4.backend.complaints.service import create_complaint, list_complaints, update_complaint_status
from module4.backend.core.auth import CurrentUser, require_admin, require_patient
from module4.backend.core.database import get_db
from module4.backend.models.complaint import ComplaintStatus
from module4.backend.schemas.complaint import ComplaintCreate, ComplaintOut, ComplaintUpdateStatus
from module4.backend.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("", response_model=ComplaintOut, status_code=201)
def submit_complaint(
    payload: ComplaintCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_patient),
):
    """
    File a complaint against a doctor.

    Security: a patient may only file complaints on their own behalf
    (patient_id in the payload must match the JWT sub claim).
    Rate-limited: 5 requests per minute per IP.
    """
    if payload.patient_id != user.user_id:
        raise HTTPException(status_code=403, detail="You may only file complaints as yourself.")

    complaint = create_complaint(
        db,
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        category=payload.category,
        description=payload.description,
        hospital_id=payload.hospital_id,
    )
    return complaint


@router.get("", response_model=PaginatedResponse[ComplaintOut])
def get_complaints(
    status: ComplaintStatus | None = None,
    hospital_id: str | None = None,
    doctor_id: str | None = None,
    limit: int = Query(50, le=200, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
):
    """
    List complaints with optional filters.

    Admin role: hospital_id from JWT always wins — client-supplied hospital_id is ignored.
    Super-admin: unscoped; may filter freely.
    """
    effective_hospital_id = hospital_id
    if user.role == "admin":
        effective_hospital_id = user.hospital_id

    all_items = list_complaints(
        db, status=status, hospital_id=effective_hospital_id, doctor_id=doctor_id
    )
    total = len(all_items)
    items = all_items[offset : offset + limit]
    return PaginatedResponse(total=total, items=items, limit=limit, offset=offset)


@router.patch("/{complaint_id}", response_model=ComplaintOut)
def update_complaint(
    complaint_id: str,
    payload: ComplaintUpdateStatus,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
):
    """
    Update complaint status and/or admin notes.

    Security (BUG FIX): an admin may only update complaints from their own
    hospital. Super-admin is unscoped.
    """
    complaint = update_complaint_status(db, complaint_id, payload.status, payload.admin_notes)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # BUG FIX: hospital admin must not touch another hospital's complaints
    if user.role == "admin" and complaint.hospital_id != user.hospital_id:
        raise HTTPException(
            status_code=403,
            detail="You may only manage complaints from your own hospital.",
        )

    return complaint
