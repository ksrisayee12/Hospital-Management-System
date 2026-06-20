"""
Tests for emergency override routes — CRUD, role checks, doctor self-only.
"""

import uuid

import pytest

from module4.backend.models.emergency_override import EmergencyOverride, OverrideStatus
from module4.backend.tests.conftest import auth


VALID_PAYLOAD = {
    "doctor_id": "doctor-001",
    "patient_id": "patient-001",
    "reason": "Emergency surgery required.",
    "urgency": "HIGH",
    "hospital_id": "hospital-A",
}


class TestEmergencyRoutes:
    def test_doctor_can_request_override_for_self(self, client, doctor_headers):
        resp = client.post("/api/v1/emergency", json=VALID_PAYLOAD, headers=doctor_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["doctor_id"] == "doctor-001"
        assert data["status"] == "PENDING"

    def test_doctor_cannot_request_override_for_another_doctor(self, client):
        # doctor-002 tries to submit as doctor-001
        headers = auth("doctor-002", "doctor")
        resp = client.post("/api/v1/emergency", json=VALID_PAYLOAD, headers=headers)
        assert resp.status_code == 403

    def test_patient_cannot_request_override(self, client, patient_headers):
        resp = client.post("/api/v1/emergency", json=VALID_PAYLOAD, headers=patient_headers)
        assert resp.status_code == 403

    def test_admin_can_list_overrides(self, client, doctor_headers, admin_headers):
        client.post("/api/v1/emergency", json=VALID_PAYLOAD, headers=doctor_headers)
        resp = client.get("/api/v1/emergency", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 1

    def test_doctor_cannot_list_overrides(self, client, doctor_headers):
        resp = client.get("/api/v1/emergency", headers=doctor_headers)
        assert resp.status_code == 403

    def test_admin_can_approve_override(self, client, doctor_headers, admin_headers):
        create = client.post("/api/v1/emergency", json=VALID_PAYLOAD, headers=doctor_headers)
        request_id = create.json()["request_id"]

        resp = client.post(
            f"/api/v1/emergency/{request_id}/approve",
            json={"approve": True, "review_notes": "Approved.", "access_window_hours": 12},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "APPROVED"

    def test_admin_can_reject_override(self, client, doctor_headers, admin_headers):
        create = client.post("/api/v1/emergency", json=VALID_PAYLOAD, headers=doctor_headers)
        request_id = create.json()["request_id"]

        resp = client.post(
            f"/api/v1/emergency/{request_id}/approve",
            json={"approve": False, "review_notes": "Not justified."},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "REJECTED"

    def test_invalid_request_id_returns_404(self, client, admin_headers):
        resp = client.post(
            f"/api/v1/emergency/not-a-uuid/approve",
            json={"approve": True},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_approve_nonexistent_override_returns_404(self, client, admin_headers):
        fake_id = uuid.uuid4()
        resp = client.post(
            f"/api/v1/emergency/{fake_id}/approve",
            json={"approve": True},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_override_approval_logs_critical_action(self, client, db_session, doctor_headers, admin_headers):
        """Approval must produce a ledger entry (EMERGENCY_OVERRIDE_APPROVED is critical)."""
        from module4.backend.models.ledger_event import LedgerEvent

        create = client.post("/api/v1/emergency", json=VALID_PAYLOAD, headers=doctor_headers)
        request_id = create.json()["request_id"]
        client.post(
            f"/api/v1/emergency/{request_id}/approve",
            json={"approve": True},
            headers=admin_headers,
        )

        events = db_session.query(LedgerEvent).filter_by(event_type="EMERGENCY_OVERRIDE_APPROVED").all()
        assert len(events) >= 1

    def test_pagination_on_emergency(self, client, admin_headers):
        # Create several override requests with different doctor tokens
        for i in range(3):
            headers = auth(f"doctor-{i}", "doctor")
            client.post("/api/v1/emergency", json={
                "doctor_id": f"doctor-{i}",
                "patient_id": "patient-001",
                "reason": "Emergency",
                "urgency": "HIGH",
            }, headers=headers)

        resp = client.get("/api/v1/emergency?limit=2", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["limit"] == 2
