"""
Tests for audit/service.py — write path and CRITICAL_ACTIONS ledger mirroring.
"""

import pytest

from module4.backend.audit.service import CRITICAL_ACTIONS, record_action, get_recent_logs
from module4.backend.blockchain.ledger import verify_chain
from module4.backend.models.ledger_event import LedgerEvent


def test_record_action_writes_to_audit_log(db_session):
    log = record_action(db_session, "doctor-1", "doctor", "VIEW_REPORT", resource="patient-A")
    assert log.event_id is not None
    assert log.user_id == "doctor-1"
    assert log.action == "VIEW_REPORT"


def test_non_critical_action_not_mirrored_to_ledger(db_session):
    """Non-critical actions (e.g. VIEW_REPORT) must NOT appear in ledger_events."""
    assert "VIEW_REPORT" not in CRITICAL_ACTIONS
    record_action(db_session, "doctor-1", "doctor", "VIEW_REPORT")
    events = db_session.query(LedgerEvent).all()
    assert len(events) == 0


def test_critical_action_is_mirrored_to_ledger(db_session):
    """Every CRITICAL_ACTIONS string must also produce a ledger_event row."""
    for action in sorted(CRITICAL_ACTIONS):
        record_action(db_session, "user-x", "admin", action)

    events = db_session.query(LedgerEvent).all()
    assert len(events) == len(CRITICAL_ACTIONS)


def test_emergency_override_requested_in_critical_actions():
    """Bug 3 fix: EMERGENCY_OVERRIDE_REQUESTED must be in CRITICAL_ACTIONS."""
    assert "EMERGENCY_OVERRIDE_REQUESTED" in CRITICAL_ACTIONS


def test_security_alert_raised_in_critical_actions():
    """Bug 3 fix: SECURITY_ALERT_RAISED must be in CRITICAL_ACTIONS."""
    assert "SECURITY_ALERT_RAISED" in CRITICAL_ACTIONS


def test_get_recent_logs_returns_total_and_items(db_session):
    for i in range(5):
        record_action(db_session, f"user-{i}", "doctor", "VIEW_REPORT")

    total, items = get_recent_logs(db_session, limit=3, offset=0)
    assert total == 5
    assert len(items) == 3


def test_get_recent_logs_pagination(db_session):
    for i in range(10):
        record_action(db_session, "user-1", "doctor", "VIEW_REPORT")

    total, page1 = get_recent_logs(db_session, limit=4, offset=0)
    _, page2 = get_recent_logs(db_session, limit=4, offset=4)

    assert total == 10
    assert len(page1) == 4
    assert len(page2) == 4
    # Pages must not overlap
    ids1 = {r.event_id for r in page1}
    ids2 = {r.event_id for r in page2}
    assert ids1.isdisjoint(ids2)


def test_get_recent_logs_hospital_filter(db_session):
    record_action(db_session, "user-1", "admin", "VIEW_REPORT", hospital_id="hospital-A")
    record_action(db_session, "user-2", "admin", "VIEW_REPORT", hospital_id="hospital-B")

    total, items = get_recent_logs(db_session, hospital_id="hospital-A")
    assert total == 1
    assert items[0].hospital_id == "hospital-A"


def test_audit_ledger_chain_intact_after_multiple_critical_actions(db_session):
    """After writing several critical actions, verify_chain must pass."""
    for action in ["CONSENT_APPROVED", "EMERGENCY_OVERRIDE_APPROVED", "COMPLAINT_CREATED"]:
        record_action(db_session, "user-1", "admin", action)

    result = verify_chain(db_session)
    assert result["valid"] is True


def test_audit_route_requires_admin(client, patient_headers):
    """Patients must NOT access audit logs."""
    resp = client.get("/api/v1/audit", headers=patient_headers)
    assert resp.status_code == 403


def test_audit_route_accessible_to_admin(client, admin_headers):
    resp = client.get("/api/v1/audit", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
