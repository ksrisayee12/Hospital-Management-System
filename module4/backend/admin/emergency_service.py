"""
Emergency Override Management.

Doctor requests emergency access -> Admin reviews -> Approve/Reject.
Approved overrides get a temporary access window and are logged to
the immutable ledger (critical action).
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from module4.backend.audit.service import record_action
from module4.backend.core.ids import parse_uuid_or_none
from module4.backend.fraud_detection.detector import detect_override_abuse
from module4.backend.models.emergency_override import EmergencyOverride, OverrideStatus

DEFAULT_ACCESS_WINDOW_HOURS = 24


def create_override_request(
    db: Session,
    doctor_id: str,
    patient_id: str,
    reason: str,
    urgency: str = "HIGH",
    hospital_id: str | None = None,
) -> EmergencyOverride:
    override = EmergencyOverride(
        doctor_id=doctor_id,
        patient_id=patient_id,
        hospital_id=hospital_id,
        reason=reason,
        urgency=urgency,
        status=OverrideStatus.PENDING,
    )
    db.add(override)
    db.commit()
    db.refresh(override)

    record_action(
        db,
        user_id=doctor_id,
        role="doctor",
        action="EMERGENCY_OVERRIDE_REQUESTED",
        resource=patient_id,
        hospital_id=hospital_id,
        metadata={"reason": reason, "urgency": urgency, "request_id": str(override.request_id)},
    )

    # Check for override abuse pattern at request time so admins see the
    # flag before they even approve/reject.
    detect_override_abuse(db, doctor_id, hospital_id)

    return override


def list_override_requests(
    db: Session,
    status: OverrideStatus | None = None,
    hospital_id: str | None = None,
):
    query = db.query(EmergencyOverride)
    if status:
        query = query.filter(EmergencyOverride.status == status)
    if hospital_id:
        query = query.filter(EmergencyOverride.hospital_id == hospital_id)
    return query.order_by(EmergencyOverride.requested_at.desc()).all()


def review_override_request(
    db: Session,
    request_id: str,
    approve: bool,
    reviewed_by: str,
    review_notes: str | None = None,
    access_window_hours: int = DEFAULT_ACCESS_WINDOW_HOURS,
) -> EmergencyOverride | None:
    parsed_id = parse_uuid_or_none(request_id)
    if parsed_id is None:
        return None

    override = db.query(EmergencyOverride).filter(EmergencyOverride.request_id == parsed_id).first()
    if not override:
        return None

    override.status = OverrideStatus.APPROVED if approve else OverrideStatus.REJECTED
    override.reviewed_by = reviewed_by
    override.review_notes = review_notes
    override.reviewed_at = datetime.utcnow()

    if approve:
        override.access_expires_at = datetime.utcnow() + timedelta(hours=access_window_hours)

    db.commit()
    db.refresh(override)

    record_action(
        db,
        user_id=reviewed_by,
        role="admin",
        action="EMERGENCY_OVERRIDE_APPROVED" if approve else "EMERGENCY_OVERRIDE_REJECTED",
        resource=override.patient_id,
        hospital_id=override.hospital_id,
        metadata={
            "request_id": str(override.request_id),
            "doctor_id": override.doctor_id,
            "review_notes": review_notes,
        },
    )

    return override
