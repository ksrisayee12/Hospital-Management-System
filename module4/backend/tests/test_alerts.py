"""
Tests for security alerts — CRUD, hospital scoping, role checks.
"""

import uuid

import pytest

from module4.backend.models.security_alert import AlertStatus, AlertType, SecurityAlert
from module4.backend.tests.conftest import auth


def _seed_alert(db_session, hospital_id: str, status: AlertStatus = AlertStatus.NEW) -> SecurityAlert:
    alert = SecurityAlert(
        alert_id=uuid.uuid4(),
        user_id="doctor-X",
        hospital_id=hospital_id,
        alert_type=AlertType.EXCESSIVE_VIEWS,
        risk_score=75.0,
        status=status,
    )
    db_session.add(alert)
    db_session.commit()
    return alert


class TestAlertsRoutes:
    def test_admin_can_list_own_hospital_alerts(self, client, db_session, admin_headers):
        _seed_alert(db_session, "hospital-A")
        resp = client.get("/api/v1/alerts", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    def test_patient_cannot_list_alerts(self, client, patient_headers):
        resp = client.get("/api/v1/alerts", headers=patient_headers)
        assert resp.status_code == 403

    def test_doctor_cannot_list_alerts(self, client, doctor_headers):
        resp = client.get("/api/v1/alerts", headers=doctor_headers)
        assert resp.status_code == 403

    def test_admin_can_update_own_hospital_alert(self, client, db_session):
        alert = _seed_alert(db_session, "hospital-A")
        headers = auth("admin-A", "admin", "hospital-A")
        resp = client.patch(
            f"/api/v1/alerts/{alert.alert_id}",
            json={"status": "DISMISSED"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "DISMISSED"

    def test_admin_cannot_update_other_hospital_alert(self, client, db_session):
        """Admin from hospital-A must NOT update hospital-B's alerts."""
        alert = _seed_alert(db_session, "hospital-B")
        headers = auth("admin-A", "admin", "hospital-A")
        resp = client.patch(
            f"/api/v1/alerts/{alert.alert_id}",
            json={"status": "ESCALATED"},
            headers=headers,
        )
        assert resp.status_code == 403

    def test_malformed_alert_id_returns_404(self, client, admin_headers):
        resp = client.patch(
            "/api/v1/alerts/not-a-uuid",
            json={"status": "DISMISSED"},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_missing_alert_returns_404(self, client, admin_headers):
        fake_id = uuid.uuid4()
        resp = client.patch(
            f"/api/v1/alerts/{fake_id}",
            json={"status": "DISMISSED"},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_pagination_on_alerts(self, client, db_session, admin_headers):
        for _ in range(5):
            _seed_alert(db_session, "hospital-A")

        resp = client.get("/api/v1/alerts?limit=3&offset=0", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 3
        assert data["total"] >= 3
