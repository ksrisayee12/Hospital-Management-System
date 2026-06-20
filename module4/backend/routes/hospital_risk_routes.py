"""
Hospital Risk Analytics routes.

Access policy: super_admin only (unscoped, cross-hospital view).
Admins must NOT access this endpoint — it reveals other hospitals' data.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from module4.backend.core.auth import CurrentUser, require_super_admin
from module4.backend.core.database import get_db
from module4.backend.schemas.pagination import PaginatedResponse
from module4.backend.schemas.trust_and_metrics import HospitalMetricsOut
from module4.backend.super_admin.analytics_service import (
    get_all_hospital_metrics,
    get_hospital_metrics,
    recompute_hospital_metrics,
)

router = APIRouter(prefix="/hospital-risk", tags=["Hospital Security Analytics"])


@router.get("", response_model=PaginatedResponse[HospitalMetricsOut])
def get_all_risk_scores(
    limit: int = Query(50, le=200, ge=1),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_super_admin),
):
    """
    Return paginated hospital risk scores ordered by risk descending.

    Super-admin only — returns cross-hospital data.
    """
    all_items = get_all_hospital_metrics(db)
    total = len(all_items)
    items = all_items[offset : offset + limit]
    return PaginatedResponse(total=total, items=items, limit=limit, offset=offset)


@router.get("/{hospital_id}", response_model=HospitalMetricsOut)
def get_risk_score(
    hospital_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_super_admin),
):
    """Return the current risk metrics for a single hospital."""
    metrics = get_hospital_metrics(db, hospital_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="No metrics found for this hospital yet")
    return metrics


@router.post("/{hospital_id}/recompute", response_model=HospitalMetricsOut)
def recompute_risk_score(
    hospital_id: str,
    hospital_name: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_super_admin),
):
    """
    Recompute risk metrics for a hospital from current DB state.

    Idempotent: calling twice with no new data produces the same risk_score.
    """
    return recompute_hospital_metrics(db, hospital_id, hospital_name)
