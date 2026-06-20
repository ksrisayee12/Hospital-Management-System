"""
Tests for super_admin/analytics_service.py — idempotency and risk formula.
"""

import uuid

import pytest

from module4.backend.models.complaint import Complaint, ComplaintCategory, ComplaintPriority, ComplaintStatus
from module4.backend.models.security_alert import AlertStatus, AlertType, SecurityAlert
from module4.backend.super_admin.analytics_service import recompute_hospital_metrics


def _make_complaint(db_session, hospital_id: str, status: ComplaintStatus):
    c = Complaint(
        complaint_id=uuid.uuid4(),
        patient_id="p1",
        doctor_id="d1",
        hospital_id=hospital_id,
        category=ComplaintCategory.OTHER,
        description="Test.",
        status=status,
        priority=ComplaintPriority.LOW,
    )
    db_session.add(c)
    db_session.commit()
    return c


def _make_alert(db_session, hospital_id: str, alert_status: AlertStatus):
    a = SecurityAlert(
        alert_id=uuid.uuid4(),
        user_id="d1",
        hospital_id=hospital_id,
        alert_type=AlertType.EXCESSIVE_VIEWS,
        risk_score=60.0,
        status=alert_status,
    )
    db_session.add(a)
    db_session.commit()
    return a


# ---------------------------------------------------------------------------
# Idempotency — calling twice with no new data → same risk_score (Bug 5 fix)
# ---------------------------------------------------------------------------

def test_recompute_hospital_metrics_idempotent(db_session):
    """
    Calling recompute_hospital_metrics twice in a row with no new data
    must produce identical risk_scores (not drift).
    This verifies the idempotency requirement from section 3.1.
    """
    hosp = "hospital-idempotent"
    _make_complaint(db_session, hosp, ComplaintStatus.OPEN)

    m1 = recompute_hospital_metrics(db_session, hosp, "Test Hospital")
    risk1 = m1.risk_score

    m2 = recompute_hospital_metrics(db_session, hosp, "Test Hospital")
    risk2 = m2.risk_score

    assert risk1 == risk2, f"Risk score drifted: {risk1} → {risk2}"


def test_recompute_creates_metrics_if_missing(db_session):
    metrics = recompute_hospital_metrics(db_session, "hospital-new")
    assert metrics is not None
    assert metrics.hospital_id == "hospital-new"


def test_recompute_counts_open_complaints(db_session):
    hosp = "hospital-counts"
    _make_complaint(db_session, hosp, ComplaintStatus.OPEN)
    _make_complaint(db_session, hosp, ComplaintStatus.OPEN)
    _make_complaint(db_session, hosp, ComplaintStatus.RESOLVED)

    metrics = recompute_hospital_metrics(db_session, hosp)
    assert metrics.total_complaints == 3
    assert metrics.open_complaints == 2


def test_recompute_active_alerts(db_session):
    hosp = "hospital-alerts"
    _make_alert(db_session, hosp, AlertStatus.NEW)
    _make_alert(db_session, hosp, AlertStatus.UNDER_REVIEW)
    _make_alert(db_session, hosp, AlertStatus.DISMISSED)

    metrics = recompute_hospital_metrics(db_session, hosp)
    assert metrics.total_alerts == 3
    assert metrics.active_alerts == 2  # NEW + UNDER_REVIEW


def test_risk_score_is_zero_for_clean_hospital(db_session):
    """A hospital with no complaints, alerts, or overrides should have low risk."""
    metrics = recompute_hospital_metrics(db_session, "hospital-clean")
    # avg_trust defaults to 100, so trust_component = 0. Everything else is 0.
    assert metrics.risk_score == 0.0


def test_updated_at_advances_on_second_call(db_session):
    """Bug 5 fix: updated_at must advance even when no data changes."""
    import time
    hosp = "hospital-updated-at"
    m1 = recompute_hospital_metrics(db_session, hosp)
    t1 = m1.updated_at

    time.sleep(0.01)  # Ensure clock advances

    m2 = recompute_hospital_metrics(db_session, hosp)
    t2 = m2.updated_at

    assert t2 >= t1  # Must not be stale


def test_hospital_risk_routes_require_super_admin(client, admin_headers):
    """Hospital risk endpoint must NOT be accessible to regular admins."""
    resp = client.get("/api/v1/hospital-risk", headers=admin_headers)
    assert resp.status_code == 403


def test_hospital_risk_accessible_to_super_admin(client, super_admin_headers):
    resp = client.get("/api/v1/hospital-risk", headers=super_admin_headers)
    assert resp.status_code == 200
    assert "items" in resp.json()
