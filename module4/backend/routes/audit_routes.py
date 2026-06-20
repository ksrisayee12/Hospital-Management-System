"""
Audit log routes.

Access policy:
  - GET /audit : admin/super_admin; admin is hospital-scoped (JWT hospital_id wins).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from module4.backend.audit.service import get_recent_logs
from module4.backend.core.auth import CurrentUser, require_admin
from module4.backend.core.database import get_db
from module4.backend.schemas.audit import AuditLogOut
from module4.backend.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=PaginatedResponse[AuditLogOut])
def get_audit_logs(
    limit: int = Query(50, le=200, ge=1),
    offset: int = Query(0, ge=0),
    user_id: str | None = None,
    action: str | None = None,
    hospital_id: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
):
    """
    Return paginated audit logs with optional filters.

    Admin role: hospital_id from JWT always wins — client-supplied
    hospital_id query param is ignored.
    Super-admin: unscoped; may filter freely.
    """
    effective_hospital_id = hospital_id
    if user.role == "admin":
        effective_hospital_id = user.hospital_id

    total, items = get_recent_logs(
        db,
        limit=limit,
        offset=offset,
        user_id=user_id,
        action=action,
        hospital_id=effective_hospital_id,
    )
    return PaginatedResponse(total=total, items=items, limit=limit, offset=offset)
