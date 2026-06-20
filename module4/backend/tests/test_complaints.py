"""
Tests for complaints — CRUD, role checks, priority classification, and
hospital scoping (Bug 2 fix verification).
"""

import pytest

from module4.backend.complaints.service import classify_priority, _classify_keyword, create_complaint
from module4.backend.models.complaint import ComplaintCategory, ComplaintPriority, ComplaintStatus
from module4.backend.tests.conftest import auth


# ---------------------------------------------------------------------------
# Priority classifier — every category × keyword combination
# ---------------------------------------------------------------------------

class TestKeywordClassifier:
    def test_critical_keyword_death(self):
        p = _classify_keyword(ComplaintCategory.OTHER, "The patient died after the procedure.")
        assert p == ComplaintPriority.CRITICAL

    def test_critical_keyword_overdose(self):
        p = _classify_keyword(ComplaintCategory.OTHER, "This was an overdose situation.")
        assert p == ComplaintPriority.CRITICAL

    def test_critical_keyword_wrong_patient(self):
        p = _classify_keyword(ComplaintCategory.MEDICAL_ERROR, "Records mixed up — wrong patient given surgery.")
        assert p == ComplaintPriority.CRITICAL

    def test_critical_keyword_allergic_reaction(self):
        p = _classify_keyword(ComplaintCategory.OTHER, "Severe allergic reaction occurred.")
        assert p == ComplaintPriority.CRITICAL

    def test_high_keyword_wrong_medication(self):
        p = _classify_keyword(ComplaintCategory.OTHER, "Doctor gave wrong medication.")
        assert p == ComplaintPriority.HIGH

    def test_high_keyword_without_consent(self):
        p = _classify_keyword(ComplaintCategory.OTHER, "Records accessed without consent.")
        assert p == ComplaintPriority.HIGH

    def test_high_keyword_leaked(self):
        p = _classify_keyword(ComplaintCategory.OTHER, "My data was leaked to another party.")
        assert p == ComplaintPriority.HIGH

    def test_high_category_unauthorized_access(self):
        p = _classify_keyword(ComplaintCategory.UNAUTHORIZED_ACCESS, "Someone accessed my records.")
        assert p == ComplaintPriority.HIGH

    def test_high_category_privacy_issue(self):
        p = _classify_keyword(ComplaintCategory.PRIVACY_ISSUE, "Doctor shared my data.")
        assert p == ComplaintPriority.HIGH

    def test_medium_category_medical_error(self):
        p = _classify_keyword(ComplaintCategory.MEDICAL_ERROR, "Incorrect diagnosis was made.")
        assert p == ComplaintPriority.MEDIUM

    def test_low_other_category(self):
        p = _classify_keyword(ComplaintCategory.OTHER, "Doctor was rude during appointment.")
        assert p == ComplaintPriority.LOW

    def test_low_behavioral_issue(self):
        p = _classify_keyword(ComplaintCategory.BEHAVIORAL_ISSUE, "Doctor did not explain side effects.")
        assert p == ComplaintPriority.LOW

    def test_critical_overrides_category(self):
        """CRITICAL keyword must override even a LOW-severity category."""
        p = _classify_keyword(ComplaintCategory.OTHER, "Patient died — this is serious.")
        assert p == ComplaintPriority.CRITICAL


# ---------------------------------------------------------------------------
# Complaint CRUD — API routes
# ---------------------------------------------------------------------------

class TestComplaintRoutes:
    def test_patient_can_submit_own_complaint(self, client, patient_headers):
        payload = {
            "patient_id": "patient-001",
            "doctor_id": "doctor-001",
            "category": "BEHAVIORAL_ISSUE",
            "description": "The doctor was rude.",
        }
        resp = client.post("/api/v1/complaints", json=payload, headers=patient_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["patient_id"] == "patient-001"
        assert data["status"] == "OPEN"
        assert data["priority"] is not None

    def test_patient_cannot_file_as_another_patient(self, client, patient_headers):
        payload = {
            "patient_id": "patient-DIFFERENT",
            "doctor_id": "doctor-001",
            "category": "OTHER",
            "description": "Some complaint.",
        }
        resp = client.post("/api/v1/complaints", json=payload, headers=patient_headers)
        assert resp.status_code == 403

    def test_doctor_cannot_submit_complaint(self, client, doctor_headers):
        payload = {
            "patient_id": "patient-001",
            "doctor_id": "doctor-002",
            "category": "OTHER",
            "description": "Filing complaint.",
        }
        resp = client.post("/api/v1/complaints", json=payload, headers=doctor_headers)
        assert resp.status_code == 403

    def test_admin_can_list_complaints(self, client, patient_headers, admin_headers):
        # Create a complaint first
        client.post("/api/v1/complaints", json={
            "patient_id": "patient-001",
            "doctor_id": "doctor-001",
            "category": "OTHER",
            "description": "Test complaint.",
        }, headers=patient_headers)

        resp = client.get("/api/v1/complaints", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_patient_cannot_list_complaints(self, client, patient_headers):
        resp = client.get("/api/v1/complaints", headers=patient_headers)
        assert resp.status_code == 403

    def test_pagination_params(self, client, patient_headers, admin_headers):
        # Create 3 complaints
        for i in range(3):
            headers = auth(f"patient-{i}", "patient")
            client.post("/api/v1/complaints", json={
                "patient_id": f"patient-{i}",
                "doctor_id": "doctor-001",
                "category": "OTHER",
                "description": f"Complaint {i}.",
            }, headers=headers)

        resp = client.get("/api/v1/complaints?limit=2&offset=0", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["limit"] == 2

    def test_admin_cannot_patch_other_hospital_complaint(self, client, db_session):
        """
        Bug 2 fix: admin from hospital-A must NOT be able to PATCH a complaint
        that belongs to hospital-B.
        """
        # Create complaint for hospital-B directly in DB
        from module4.backend.models.complaint import Complaint, ComplaintCategory, ComplaintPriority, ComplaintStatus
        import uuid
        complaint = Complaint(
            complaint_id=uuid.uuid4(),
            patient_id="p1",
            doctor_id="d1",
            hospital_id="hospital-B",  # Different hospital!
            category=ComplaintCategory.OTHER,
            description="Other hospital complaint.",
            status=ComplaintStatus.OPEN,
            priority=ComplaintPriority.LOW,
        )
        db_session.add(complaint)
        db_session.commit()

        admin_a_headers = auth("admin-A", "admin", "hospital-A")
        resp = client.patch(
            f"/api/v1/complaints/{complaint.complaint_id}",
            json={"status": "RESOLVED"},
            headers=admin_a_headers,
        )
        assert resp.status_code == 403

    def test_super_admin_can_patch_any_complaint(self, client, db_session, super_admin_headers):
        """Super-admin is unscoped and can update any hospital's complaints."""
        from module4.backend.models.complaint import Complaint, ComplaintCategory, ComplaintPriority, ComplaintStatus
        import uuid
        complaint = Complaint(
            complaint_id=uuid.uuid4(),
            patient_id="p2",
            doctor_id="d2",
            hospital_id="hospital-Z",
            category=ComplaintCategory.OTHER,
            description="Cross-hospital complaint.",
            status=ComplaintStatus.OPEN,
            priority=ComplaintPriority.LOW,
        )
        db_session.add(complaint)
        db_session.commit()

        resp = client.patch(
            f"/api/v1/complaints/{complaint.complaint_id}",
            json={"status": "RESOLVED", "admin_notes": "Closed by super admin."},
            headers=super_admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "RESOLVED"
