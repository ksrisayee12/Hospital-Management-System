"""
Audit Intelligence System — write path.

Every action in the platform (from any module) should call
`record_action()`. Critical actions (consent, override, prescription
signing) ALSO get mirrored into the immutable ledger via
`record_critical_event()`.

Operational logging (separate from the DB audit_logs table) is emitted
as structured JSON on every write for debugging the platform itself.
Each log line includes: timestamp, action, user_id, and outcome.
"""

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from module4.backend.blockchain.ledger import append_event
from module4.backend.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# Actions that MUST also be written to the immutable ledger.
# BUG FIX: added EMERGENCY_OVERRIDE_REQUESTED and SECURITY_ALERT_RAISED —
# both are governance-critical events that must be tamper-evident.
CRITICAL_ACTIONS = {
    "CONSENT_APPROVED",
    "CONSENT_REVOKED",
    "EMERGENCY_OVERRIDE_REQUESTED",   # FIX: was missing, now ledger-mirrored
    "EMERGENCY_OVERRIDE_APPROVED",
    "EMERGENCY_OVERRIDE_REJECTED",
    "PRESCRIPTION_SIGNED",
    "COMPLAINT_CREATED",
    "SECURITY_ALERT_RAISED",          # FIX: was missing, now ledger-mirrored
}


def record_action(
    db: Session,
    user_id: str,
    role: str,
    action: str,
    resource: str | None = None,
    hospital_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """
    Write a row to audit_logs (always), and to the immutable ledger if
    the action is in CRITICAL_ACTIONS.

    Args:
        db:          SQLAlchemy session.
        user_id:     Actor performing the action (JWT sub).
        role:        Actor's role (doctor / patient / admin / super_admin).
        action:      Action string (e.g. "CONSENT_APPROVED").
        resource:    Optional resource identifier (patient_id, report_id, etc.).
        hospital_id: Optional hospital context.
        metadata:    Optional free-form extra context (JSON-serialized).

    Returns:
        The persisted AuditLog row.
    """
    log = AuditLog(
        user_id=user_id,
        role=role,
        action=action,
        resource=resource,
        hospital_id=hospital_id,
        metadata_json=json.dumps(metadata or {}, default=str),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    is_critical = action in CRITICAL_ACTIONS
    logger.info(
        json.dumps({
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "action": action,
            "user_id": user_id,
            "role": role,
            "resource": resource,
            "hospital_id": hospital_id,
            "critical": is_critical,
            "outcome": "recorded",
        })
    )

    if is_critical:
        try:
            append_event(
                db,
                event_type=action,
                event_payload={
                    "user_id": user_id,
                    "role": role,
                    "action": action,
                    "resource": resource,
                    "hospital_id": hospital_id,
                    "metadata": metadata or {},
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(
                json.dumps({
                    "action": action,
                    "user_id": user_id,
                    "outcome": "ledger_mirror_failed",
                    "error": str(exc),
                })
            )
            raise

    return log


def get_recent_logs(
    db: Session,
    limit: int = 100,
    offset: int = 0,
    user_id: str | None = None,
    action: str | None = None,
    hospital_id: str | None = None,
) -> tuple[int, list[AuditLog]]:
    """
    Fetch audit logs with optional filters.

    Args:
        db:          SQLAlchemy session.
        limit:       Max rows to return (caller enforces max=200).
        offset:      Rows to skip for pagination.
        user_id:     Optional filter by actor.
        action:      Optional filter by action string.
        hospital_id: Optional filter by hospital.

    Returns:
        Tuple of (total_count, items).
    """
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if hospital_id:
        query = query.filter(AuditLog.hospital_id == hospital_id)

    query = query.order_by(AuditLog.timestamp.desc())
    total = query.count()
    items = query.offset(offset).limit(limit).all()
    return total, items
