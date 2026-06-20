"""
Tests for fraud_detection/detector.py — threshold just-under and just-over,
and Bug 4 fix (json.dumps evidence).
"""

import json
import uuid
from datetime import datetime, timedelta

import pytest

from module4.backend.core.config import settings
from module4.backend.fraud_detection.detector import (
    detect_abnormal_downloads,
    detect_excessive_views,
    detect_override_abuse,
)
from module4.backend.models.audit_log import AuditLog
from module4.backend.models.emergency_override import EmergencyOverride, OverrideStatus
from module4.backend.models.security_alert import AlertType, SecurityAlert


def _insert_view_logs(db_session, user_id: str, count: int, minutes_ago: int = 30):
    """Insert VIEW_REPORT audit log entries."""
    ts = datetime.utcnow() - timedelta(minutes=minutes_ago)
    for _ in range(count):
        db_session.add(AuditLog(
            user_id=user_id,
            role="doctor",
            action="VIEW_REPORT",
            resource="patient-X",
            timestamp=ts,
        ))
    db_session.commit()


def _insert_download_logs(db_session, user_id: str, count: int, minutes_ago: int = 2):
    """Insert DOWNLOAD_REPORT audit log entries."""
    ts = datetime.utcnow() - timedelta(minutes=minutes_ago)
    for _ in range(count):
        db_session.add(AuditLog(
            user_id=user_id,
            role="doctor",
            action="DOWNLOAD_REPORT",
            resource="report-Y",
            timestamp=ts,
        ))
    db_session.commit()


def _insert_overrides(db_session, doctor_id: str, count: int, days_ago: int = 1):
    """Insert EmergencyOverride rows."""
    ts = datetime.utcnow() - timedelta(days=days_ago)
    for _ in range(count):
        db_session.add(EmergencyOverride(
            request_id=uuid.uuid4(),
            doctor_id=doctor_id,
            patient_id="patient-A",
            reason="Emergency",
            status=OverrideStatus.PENDING,
            requested_at=ts,
        ))
    db_session.commit()


# ---------------------------------------------------------------------------
# EXCESSIVE_VIEWS — just-under and just-over threshold
# ---------------------------------------------------------------------------

def test_excessive_views_just_under_threshold_no_alert(db_session):
    count = settings.FRAUD_VIEW_COUNT_THRESHOLD - 1
    _insert_view_logs(db_session, "doc-views-low", count)
    alert = detect_excessive_views(db_session, "doc-views-low")
    assert alert is None


def test_excessive_views_at_threshold_triggers_alert(db_session):
    count = settings.FRAUD_VIEW_COUNT_THRESHOLD
    _insert_view_logs(db_session, "doc-views-high", count)
    alert = detect_excessive_views(db_session, "doc-views-high")
    assert alert is not None
    assert alert.alert_type == AlertType.EXCESSIVE_VIEWS
    assert alert.risk_score > 0


def test_excessive_views_above_threshold_triggers_alert(db_session):
    count = settings.FRAUD_VIEW_COUNT_THRESHOLD + 5
    _insert_view_logs(db_session, "doc-views-over", count)
    alert = detect_excessive_views(db_session, "doc-views-over")
    assert alert is not None


# ---------------------------------------------------------------------------
# ABNORMAL_DOWNLOAD — just-under and just-over threshold
# ---------------------------------------------------------------------------

def test_abnormal_downloads_just_under_threshold_no_alert(db_session):
    count = settings.FRAUD_DOWNLOAD_COUNT_THRESHOLD - 1
    _insert_download_logs(db_session, "doc-dl-low", count)
    alert = detect_abnormal_downloads(db_session, "doc-dl-low")
    assert alert is None


def test_abnormal_downloads_at_threshold_triggers_alert(db_session):
    count = settings.FRAUD_DOWNLOAD_COUNT_THRESHOLD
    _insert_download_logs(db_session, "doc-dl-high", count)
    alert = detect_abnormal_downloads(db_session, "doc-dl-high")
    assert alert is not None
    assert alert.alert_type == AlertType.ABNORMAL_DOWNLOAD


# ---------------------------------------------------------------------------
# OVERRIDE_ABUSE — just-under and just-over threshold
# ---------------------------------------------------------------------------

def test_override_abuse_just_under_threshold_no_alert(db_session):
    count = settings.FRAUD_OVERRIDE_WEEKLY_THRESHOLD - 1
    _insert_overrides(db_session, "doc-ovr-low", count)
    alert = detect_override_abuse(db_session, "doc-ovr-low")
    assert alert is None


def test_override_abuse_at_threshold_triggers_alert(db_session):
    count = settings.FRAUD_OVERRIDE_WEEKLY_THRESHOLD
    _insert_overrides(db_session, "doc-ovr-high", count)
    alert = detect_override_abuse(db_session, "doc-ovr-high")
    assert alert is not None
    assert alert.alert_type == AlertType.OVERRIDE_ABUSE


# ---------------------------------------------------------------------------
# Bug 4 fix: evidence_json must be valid JSON (not Python repr)
# ---------------------------------------------------------------------------

def test_evidence_json_is_valid_json(db_session):
    """
    Bug 4 fix: _create_alert() was using str(evidence) which produces
    Python repr, not valid JSON. Verify the stored string is parseable.
    """
    count = settings.FRAUD_DOWNLOAD_COUNT_THRESHOLD
    _insert_download_logs(db_session, "doc-json-check", count)
    alert = detect_abnormal_downloads(db_session, "doc-json-check")
    assert alert is not None

    # Must not raise — if it was str(dict) this would throw JSONDecodeError
    parsed = json.loads(alert.evidence_json)
    assert isinstance(parsed, dict)
    assert "count" in parsed


def test_risk_score_capped_at_100(db_session):
    """Risk score must never exceed 100 even for extreme counts."""
    _insert_view_logs(db_session, "doc-extreme", 1000)
    alert = detect_excessive_views(db_session, "doc-extreme")
    if alert:
        assert alert.risk_score <= 100.0
