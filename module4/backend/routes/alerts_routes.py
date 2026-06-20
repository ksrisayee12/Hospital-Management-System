"""
Security Alerts routes.

Access policy:
  - GET  /alerts      : admin/super_admin; admin is hospital-scoped.
  - PATCH /alerts/{id}: admin/super_admin; no extra hospital check needed
                        (alert was already created scoped to hospital).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from module4.backend.core.auth import CurrentUser, require_admin
from module4.backend.core.database import get_db
from module4.backend.core.ids import parse_uuid_or_none
from module4.backend.models.security_alert import AlertStatus, SecurityAlert
from module4.backend.schemas.alert import SecurityAlertOut, SecurityAlertUpdateStatus
from module4.backend.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/alerts", tags=["Security Alerts"])


@router.get("", response_model=PaginatedResponse[SecurityAlertOut])
def get_alerts(
    status: AlertStatus | None = None,
    hospital_id: str | None = None,
    limit: int = Query(50, le=200, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
):
    """
    Return paginated security alerts with optional filters.

    Admin role: hospital_id from JWT always wins.
    Super-admin: unscoped; may filter freely.
    """
    query = db.query(SecurityAlert)

    effective_hospital_id = hospital_id
    if user.role == "admin":
        effective_hospital_id = user.hospital_id

    if status:
        query = query.filter(SecurityAlert.status == status)
    if effective_hospital_id:
        query = query.filter(SecurityAlert.hospital_id == effective_hospital_id)

    query = query.order_by(SecurityAlert.risk_score.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return PaginatedResponse(total=total, items=items, limit=limit, offset=offset)


@router.patch("/{alert_id}", response_model=SecurityAlertOut)
def update_alert_status(
    alert_id: str,
    payload: SecurityAlertUpdateStatus,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
):
    """
    Update an alert's triage status (DISMISS, REVIEW, or ESCALATE).

    Admin role can update alerts from their own hospital only.
    """
    parsed_id = parse_uuid_or_none(alert_id)
    if parsed_id is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert = db.query(SecurityAlert).filter(SecurityAlert.alert_id == parsed_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Hospital admins must not touch alerts from other hospitals
    if user.role == "admin" and alert.hospital_id != user.hospital_id:
        raise HTTPException(
            status_code=403,
            detail="You may only manage alerts from your own hospital.",
        )

    alert.status = payload.status
    db.commit()
    db.refresh(alert)
    return alert
