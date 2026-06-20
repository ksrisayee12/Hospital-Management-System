"""
Complaint Management System + Complaint Intelligence.

Priority classification uses a two-tier approach:
  1. Keyword/category-based classifier (always active) — fast, explainable,
     zero GPU dependency.
  2. MiniLM semantic embedding classifier (optional, feature-flagged via
     ENABLE_SEMANTIC_COMPLAINT_CLASSIFIER in core/config.py).

Blend strategy: if both classifiers are active and disagree, escalate to
the HIGHER of the two priorities. NEVER silently downgrade — false negatives
on priority are worse than false positives in healthcare governance.
"""

import logging

from sqlalchemy.orm import Session

from module4.backend.core.config import settings
from module4.backend.core.ids import parse_uuid_or_none
from module4.backend.models.complaint import Complaint, ComplaintCategory, ComplaintPriority, ComplaintStatus
from module4.backend.trust_engine.engine import penalize_for_complaint

logger = logging.getLogger(__name__)

# Categories that are inherently more severe, regardless of keywords.
_HIGH_SEVERITY_CATEGORIES = {
    ComplaintCategory.UNAUTHORIZED_ACCESS,
    ComplaintCategory.PRIVACY_ISSUE,
}

_CRITICAL_KEYWORDS = {"death", "died", "overdose", "wrong patient", "allergic reaction"}
_HIGH_KEYWORDS = {"wrong medication", "wrong prescription", "leaked", "unauthorized", "without consent"}


def classify_priority(category: ComplaintCategory, description: str) -> ComplaintPriority:
    """
    Classify complaint priority.

    When ENABLE_SEMANTIC_COMPLAINT_CLASSIFIER is False (default):
      Uses keyword/category rules only.

    When ENABLE_SEMANTIC_COMPLAINT_CLASSIFIER is True:
      Runs both classifiers and takes the HIGHER of the two priorities
      (escalation rule — never silently downgrade).

    Args:
        category:    Complaint category enum.
        description: Free-text description from the patient.

    Returns:
        ComplaintPriority enum value.
    """
    keyword_priority = _classify_keyword(category, description)

    if not settings.ENABLE_SEMANTIC_COMPLAINT_CLASSIFIER:
        return keyword_priority

    # Semantic classifier is enabled — import lazily so torch is not loaded
    # unless the feature flag is on.
    try:
        from module4.backend.complaints.semantic_classifier import blend_priorities, classify_priority_semantic
        semantic_priority = classify_priority_semantic(description)

        if keyword_priority != semantic_priority:
            logger.info(
                f"Classifier disagreement: keyword={keyword_priority.value} "
                f"semantic={semantic_priority.value} — escalating to higher."
            )

        return blend_priorities(keyword_priority, semantic_priority)
    except ImportError:
        logger.warning(
            "sentence-transformers not installed; falling back to keyword classifier. "
            "Install it or set ENABLE_SEMANTIC_COMPLAINT_CLASSIFIER=false."
        )
        return keyword_priority


def _classify_keyword(category: ComplaintCategory, description: str) -> ComplaintPriority:
    """
    Keyword and category-based priority classifier (always active).

    Args:
        category:    Complaint category enum.
        description: Free-text description.

    Returns:
        ComplaintPriority enum value.
    """
    text = description.lower()

    if any(kw in text for kw in _CRITICAL_KEYWORDS):
        return ComplaintPriority.CRITICAL

    if category in _HIGH_SEVERITY_CATEGORIES or any(kw in text for kw in _HIGH_KEYWORDS):
        return ComplaintPriority.HIGH

    if category == ComplaintCategory.MEDICAL_ERROR:
        return ComplaintPriority.MEDIUM

    return ComplaintPriority.LOW


def create_complaint(
    db: Session,
    patient_id: str,
    doctor_id: str,
    category: ComplaintCategory,
    description: str,
    hospital_id: str | None = None,
) -> Complaint:
    """
    Create a complaint and immediately apply a trust score penalty to the
    named doctor.

    Priority is set automatically by the classifier pipeline (keyword +
    optional semantic). Admins can still override the status later, but
    the initial trust penalty signal is permanent.

    Args:
        db:          SQLAlchemy session.
        patient_id:  Patient filing the complaint (must match JWT sub).
        doctor_id:   Doctor being complained about.
        category:    Category enum for the complaint.
        description: Free-text description.
        hospital_id: Optional hospital context.

    Returns:
        Persisted Complaint row.
    """
    priority = classify_priority(category, description)

    complaint = Complaint(
        patient_id=patient_id,
        doctor_id=doctor_id,
        hospital_id=hospital_id,
        category=category,
        description=description,
        status=ComplaintStatus.OPEN,
        priority=priority,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Filing a complaint dings the doctor's trust score immediately;
    # admins can still dismiss it later, but the initial signal counts.
    penalize_for_complaint(db, doctor_id, hospital_id)

    return complaint


def list_complaints(
    db: Session,
    status: ComplaintStatus | None = None,
    hospital_id: str | None = None,
    doctor_id: str | None = None,
) -> list[Complaint]:
    """
    List complaints with optional filters, ordered by priority then date.

    Args:
        db:          SQLAlchemy session.
        status:      Optional status filter.
        hospital_id: Optional hospital filter.
        doctor_id:   Optional doctor filter.

    Returns:
        List of Complaint rows: CRITICAL first, then HIGH, MEDIUM, LOW;
        newest first within each tier.
    """
    query = db.query(Complaint)
    if status:
        query = query.filter(Complaint.status == status)
    if hospital_id:
        query = query.filter(Complaint.hospital_id == hospital_id)
    if doctor_id:
        query = query.filter(Complaint.doctor_id == doctor_id)
    # Priority queue: CRITICAL first, then HIGH, MEDIUM, LOW; newest first within tier.
    priority_order = {
        ComplaintPriority.CRITICAL: 0,
        ComplaintPriority.HIGH: 1,
        ComplaintPriority.MEDIUM: 2,
        ComplaintPriority.LOW: 3,
    }
    results = query.order_by(Complaint.created_at.desc()).all()
    results.sort(key=lambda c: priority_order.get(c.priority, 4))
    return results


def update_complaint_status(
    db: Session,
    complaint_id: str,
    status: ComplaintStatus,
    admin_notes: str | None = None,
) -> Complaint | None:
    """
    Update a complaint's status and optional admin notes.

    Args:
        db:           SQLAlchemy session.
        complaint_id: UUID string of the complaint.
        status:       New status value.
        admin_notes:  Optional notes from the reviewing admin.

    Returns:
        Updated Complaint row, or None if not found / invalid ID.
    """
    parsed_id = parse_uuid_or_none(complaint_id)
    if parsed_id is None:
        return None

    complaint = db.query(Complaint).filter(Complaint.complaint_id == parsed_id).first()
    if not complaint:
        return None
    complaint.status = status
    if admin_notes:
        complaint.admin_notes = admin_notes
    db.commit()
    db.refresh(complaint)
    return complaint
