"""
Trust Score Engine routes.

Access policy:
  - GET /trust-score/{doctor_id}  : doctor only; doctor_id MUST match JWT sub.
  - GET /trust-score              : admin/super_admin; admin is hospital-scoped.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from module4.backend.core.auth import CurrentUser, require_admin, require_doctor
from module4.backend.core.database import get_db
from module4.backend.schemas.pagination import PaginatedResponse
from module4.backend.schemas.trust_and_metrics import TrustScoreOut
from module4.backend.trust_engine.engine import get_or_create_trust_score

router = APIRouter(prefix="/trust-score", tags=["Trust Score Engine"])


@router.get("/{doctor_id}", response_model=TrustScoreOut)
def get_trust_score(
    doctor_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_doctor),
):
    """
    Return the trust score for a specific doctor.

    Security: a doctor may only view their OWN score (doctor_id must equal JWT sub).
    """
    # BUG FIX: doctors must only see their own score
    if doctor_id != user.user_id:
        raise HTTPException(
            status_code=403,
            detail="You may only view your own trust score.",
        )
    return get_or_create_trust_score(db, doctor_id)


@router.get("", response_model=PaginatedResponse[TrustScoreOut])
def get_all_trust_scores_for_hospital(
    hospital_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
):
    """
    List trust scores for all doctors.

    Admin role: scoped to their own hospital_id from JWT (client-supplied
    hospital_id is ignored — the JWT hospital_id always wins).
    Super-admin: unscoped, may optionally filter by hospital_id query param.
    """
    from module4.backend.models.trust_score import TrustScore  # local import to keep router lean

    limit = min(limit, 200)
    effective_hospital_id = hospital_id
    if user.role == "admin":
        effective_hospital_id = user.hospital_id

    query = db.query(TrustScore)
    if effective_hospital_id:
        query = query.filter(TrustScore.hospital_id == effective_hospital_id)

    total = query.count()
    items = query.order_by(TrustScore.score.asc()).offset(offset).limit(limit).all()
    return PaginatedResponse(total=total, items=items, limit=limit, offset=offset)
