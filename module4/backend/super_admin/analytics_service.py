"""
Hospital Security Analytics (Super Admin view).

Computes a 0-100 hospital risk score from complaints, alerts,
overrides, and average doctor trust score. Weighted, explainable
formula — easy to defend to judges, no black-box ML needed here.

BUG FIX: recompute_hospital_metrics() now forces updated_at = utcnow()
on every call so the field advances even when underlying counts haven't
changed (SQLAlchemy's onupdate only fires when a tracked column changes).
This ensures idempotency (same data → same risk_score) while still
accurately reflecting the last-computed timestamp.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from module4.backend.models.complaint import Complaint, ComplaintStatus
from module4.backend.models.emergency_override import EmergencyOverride
from module4.backend.models.hospital_metrics import HospitalMetrics
from module4.backend.models.security_alert import AlertStatus, SecurityAlert
from module4.backend.trust_engine.engine import get_hospital_average_trust_score

# Weights sum to 100; tune as needed for your demo narrative.
WEIGHT_COMPLAINTS = 0.30
WEIGHT_ALERTS = 0.30
WEIGHT_OVERRIDES = 0.15
WEIGHT_TRUST = 0.25


def _normalize(value: int, cap: int) -> float:
    """Scale a raw count to 0-100, capped at `cap`."""
    return min(100.0, (value / cap) * 100) if cap else 0.0


def recompute_hospital_metrics(db: Session, hospital_id: str, hospital_name: str | None = None) -> HospitalMetrics:
    """
    Recompute and persist hospital risk metrics.

    Idempotent: calling twice with identical underlying data produces the
    same risk_score both times. updated_at is explicitly set on every call
    so it always reflects the most recent computation timestamp.

    Args:
        db:            SQLAlchemy session.
        hospital_id:   Hospital to compute for.
        hospital_name: Optional human-readable name (only stored if provided).

    Returns:
        Updated HospitalMetrics row.
    """
    metrics = db.query(HospitalMetrics).filter(HospitalMetrics.hospital_id == hospital_id).first()
    if not metrics:
        metrics = HospitalMetrics(hospital_id=hospital_id, hospital_name=hospital_name)
        db.add(metrics)

    total_complaints = db.query(Complaint).filter(Complaint.hospital_id == hospital_id).count()
    open_complaints = (
        db.query(Complaint)
        .filter(Complaint.hospital_id == hospital_id, Complaint.status == ComplaintStatus.OPEN)
        .count()
    )
    total_alerts = db.query(SecurityAlert).filter(SecurityAlert.hospital_id == hospital_id).count()
    active_alerts = (
        db.query(SecurityAlert)
        .filter(
            SecurityAlert.hospital_id == hospital_id,
            SecurityAlert.status.in_([AlertStatus.NEW, AlertStatus.UNDER_REVIEW]),
        )
        .count()
    )
    total_overrides = db.query(EmergencyOverride).filter(EmergencyOverride.hospital_id == hospital_id).count()
    avg_trust = get_hospital_average_trust_score(db, hospital_id)

    metrics.total_complaints = total_complaints
    metrics.open_complaints = open_complaints
    metrics.total_alerts = total_alerts
    metrics.active_alerts = active_alerts
    metrics.total_overrides = total_overrides
    metrics.avg_trust_score = avg_trust

    # Explainable weighted risk score (caps chosen as "reasonably bad" thresholds).
    complaints_component = _normalize(open_complaints, cap=10)
    alerts_component = _normalize(active_alerts, cap=10)
    overrides_component = _normalize(total_overrides, cap=20)
    trust_component = max(0.0, 100 - avg_trust)  # lower trust → higher risk

    risk_score = (
        complaints_component * WEIGHT_COMPLAINTS
        + alerts_component * WEIGHT_ALERTS
        + overrides_component * WEIGHT_OVERRIDES
        + trust_component * WEIGHT_TRUST
    )

    metrics.risk_score = round(risk_score, 2)

    # BUG FIX: explicitly set updated_at so it advances even when no
    # data columns changed. SQLAlchemy's onupdate= only fires when
    # SQLAlchemy detects a dirty column; if all counts are identical,
    # the row is considered unchanged and updated_at would be stale.
    metrics.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(metrics)
    return metrics


def get_all_hospital_metrics(db: Session) -> list[HospitalMetrics]:
    """Return all hospital metrics rows, ordered by risk score descending."""
    return db.query(HospitalMetrics).order_by(HospitalMetrics.risk_score.desc()).all()


def get_hospital_metrics(db: Session, hospital_id: str) -> HospitalMetrics | None:
    """Return metrics for a single hospital, or None if not yet computed."""
    return db.query(HospitalMetrics).filter(HospitalMetrics.hospital_id == hospital_id).first()
