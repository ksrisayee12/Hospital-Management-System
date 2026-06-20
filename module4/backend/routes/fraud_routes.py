"""
Fraud explain endpoint.

Access policy: super_admin only.
Returns combined rule-based flags AND IsolationForest anomaly score for
a given user — so a judge or admin can see WHY someone was flagged.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from module4.backend.core.auth import CurrentUser, require_super_admin
from module4.backend.core.database import get_db
from module4.backend.fraud_detection.ml_detector import get_fraud_explanation

router = APIRouter(prefix="/fraud", tags=["Fraud Intelligence"])


@router.get("/explain/{user_id}")
def explain_fraud(
    user_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_super_admin),
):
    """
    Return a full fraud explanation for a user.

    Response includes:
    - features: raw feature vector (views_per_hour, downloads_per_hour,
                overrides_per_week, off_hours_access_ratio)
    - rule_flags: list of rule-based detectors that would fire
    - isolation_score: IsolationForest raw score (None if not trained)
    - isolation_display_score: normalized 0-100 (None if not trained)
    - ml_anomaly: True if ML considers user anomalous
    - disagreement: True if rule and ML disagree (worth investigating)
    - explanation: human-readable summary explaining the signals

    Super-admin only. Suitable for live judge demo.
    """
    return get_fraud_explanation(db, user_id)
