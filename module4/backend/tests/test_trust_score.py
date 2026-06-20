"""
Tests for trust_engine/engine.py — floor/ceiling clamping, penalties,
and self-only access check via the API.
"""

import pytest

from module4.backend.core.config import settings
from module4.backend.models.trust_score import RiskLevel
from module4.backend.trust_engine.engine import (
    get_or_create_trust_score,
    penalize_for_alert,
    penalize_for_complaint,
    penalize_for_override_misuse,
)
from module4.backend.tests.conftest import auth


# ---------------------------------------------------------------------------
# Trust score floor — the key safety property
# ---------------------------------------------------------------------------

def test_trust_score_floors_at_zero_after_50_complaints(db_session):
    """
    Hammer a doctor with 50 complaints (each deducts TRUST_SCORE_COMPLAINT_PENALTY).
    The score MUST floor at TRUST_SCORE_MIN (0), never go negative.
    This is the exact test demanded by the prompt.
    """
    doctor_id = "doctor-floor-test"
    for _ in range(50):
        penalize_for_complaint(db_session, doctor_id, "hospital-X")

    record = get_or_create_trust_score(db_session, doctor_id)
    assert record.score == settings.TRUST_SCORE_MIN, (
        f"Score went to {record.score} instead of flooring at {settings.TRUST_SCORE_MIN}"
    )
    assert record.score >= 0, "Score went negative — floor not applied"


def test_trust_score_starts_at_default(db_session):
    record = get_or_create_trust_score(db_session, "new-doctor", "hospital-A")
    assert record.score == settings.TRUST_SCORE_DEFAULT  # 100
    assert record.risk_level == RiskLevel.LOW


def test_complaint_penalty_reduces_score(db_session):
    doc = "doctor-penalty"
    before = get_or_create_trust_score(db_session, doc).score
    penalize_for_complaint(db_session, doc)
    after = get_or_create_trust_score(db_session, doc).score
    assert after == before - settings.TRUST_SCORE_COMPLAINT_PENALTY


def test_alert_penalty_reduces_score(db_session):
    doc = "doctor-alert-penalty"
    get_or_create_trust_score(db_session, doc)
    penalize_for_alert(db_session, doc)
    record = get_or_create_trust_score(db_session, doc)
    assert record.score == settings.TRUST_SCORE_DEFAULT - settings.TRUST_SCORE_ALERT_PENALTY


def test_override_misuse_penalty_reduces_score(db_session):
    doc = "doctor-override-penalty"
    get_or_create_trust_score(db_session, doc)
    penalize_for_override_misuse(db_session, doc)
    record = get_or_create_trust_score(db_session, doc)
    assert record.score == settings.TRUST_SCORE_DEFAULT - settings.TRUST_SCORE_OVERRIDE_MISUSE_PENALTY


def test_risk_level_transitions(db_session):
    """Risk level must update correctly as score drops through thresholds."""
    doc = "doctor-levels"
    # Start at 100 → LOW
    record = get_or_create_trust_score(db_session, doc)
    assert record.risk_level == RiskLevel.LOW

    # Drive score to 75 (MODERATE: 60-79)
    # Each complaint = -5 points. 5 complaints = -25 → 75
    for _ in range(5):
        penalize_for_complaint(db_session, doc)
    record = get_or_create_trust_score(db_session, doc)
    assert record.score == 75
    assert record.risk_level == RiskLevel.MODERATE

    # Drive to 50 → HIGH (40-59)
    for _ in range(5):
        penalize_for_complaint(db_session, doc)
    record = get_or_create_trust_score(db_session, doc)
    assert record.score == 50
    assert record.risk_level == RiskLevel.HIGH

    # Drive to 30 → CRITICAL (0-39)
    for _ in range(4):
        penalize_for_complaint(db_session, doc)
    record = get_or_create_trust_score(db_session, doc)
    assert record.score == 30
    assert record.risk_level == RiskLevel.CRITICAL


# ---------------------------------------------------------------------------
# API-level: doctor self-only check (Bug 1 fix verification)
# ---------------------------------------------------------------------------

def test_doctor_cannot_view_other_doctors_trust_score(client):
    """
    A doctor must NOT be able to fetch another doctor's trust score.
    The endpoint must return 403 Forbidden.
    (This is Bug 1 from the correctness audit.)
    """
    headers = auth("doctor-001", "doctor")
    # doctor-001 tries to view doctor-002's score
    resp = client.get("/api/v1/trust-score/doctor-002", headers=headers)
    assert resp.status_code == 403


def test_doctor_can_view_own_trust_score(client, db_session):
    """A doctor CAN view their own trust score."""
    # Pre-create the record
    get_or_create_trust_score(db_session, "doctor-self")
    db_session.commit()

    headers = auth("doctor-self", "doctor")
    resp = client.get("/api/v1/trust-score/doctor-self", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["doctor_id"] == "doctor-self"


def test_patient_cannot_access_trust_score(client):
    """A patient must NOT access the trust score endpoint (wrong role)."""
    headers = auth("patient-001", "patient")
    resp = client.get("/api/v1/trust-score/doctor-001", headers=headers)
    assert resp.status_code == 403


def test_admin_can_list_trust_scores(client, admin_headers):
    """Admin can access the list endpoint (returns paginated response)."""
    resp = client.get("/api/v1/trust-score", headers=admin_headers)
    assert resp.status_code == 200
    assert "items" in resp.json()
    assert "total" in resp.json()
