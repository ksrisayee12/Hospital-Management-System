"""
Trust Score Engine.

Every doctor starts at 100. Score decreases on:
  - Complaints filed against them
  - Security alerts raised against them
  - Confirmed emergency override misuse

This module also rolls doctor scores up into hospital-level averages
for the Super Admin's Hospital Risk Analytics view.

Score is clamped to [TRUST_SCORE_MIN, TRUST_SCORE_DEFAULT] (default: [0, 100])
and can never go below 0 or above 100 regardless of how many penalties
are applied.
"""

import json
import logging

from sqlalchemy.orm import Session

from module4.backend.core.config import settings
from module4.backend.models.trust_score import RiskLevel, TrustScore, score_to_risk_level

logger = logging.getLogger(__name__)


def get_or_create_trust_score(db: Session, doctor_id: str, hospital_id: str | None = None) -> TrustScore:
    """
    Return the trust score for a doctor, creating a default 100-point
    record if none exists yet.

    Args:
        db:          SQLAlchemy session.
        doctor_id:   Doctor's user_id.
        hospital_id: Hospital context (only used when creating a new record).

    Returns:
        TrustScore row.
    """
    record = db.query(TrustScore).filter(TrustScore.doctor_id == doctor_id).first()
    if record:
        return record

    record = TrustScore(
        doctor_id=doctor_id,
        hospital_id=hospital_id,
        score=settings.TRUST_SCORE_DEFAULT,
        risk_level=RiskLevel.LOW,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(
        json.dumps({
            "action": "TRUST_SCORE_CREATED",
            "user_id": doctor_id,
            "hospital_id": hospital_id,
            "score": settings.TRUST_SCORE_DEFAULT,
            "outcome": "created",
        })
    )
    return record


def _apply_penalty(db: Session, doctor_id: str, penalty: int, hospital_id: str | None = None) -> TrustScore:
    """
    Deduct `penalty` points from a doctor's trust score, clamping the
    result to [TRUST_SCORE_MIN, TRUST_SCORE_DEFAULT] so the score never
    goes negative or above the maximum.

    Args:
        db:          SQLAlchemy session.
        doctor_id:   Doctor receiving the penalty.
        penalty:     Points to deduct (positive integer).
        hospital_id: Hospital context (used on record creation only).

    Returns:
        Updated TrustScore row.
    """
    record = get_or_create_trust_score(db, doctor_id, hospital_id)
    old_score = record.score
    new_score = max(settings.TRUST_SCORE_MIN, record.score - penalty)
    record.score = new_score
    record.risk_level = score_to_risk_level(new_score)
    db.commit()
    db.refresh(record)

    logger.info(
        json.dumps({
            "action": "TRUST_SCORE_PENALTY",
            "user_id": doctor_id,
            "penalty": penalty,
            "old_score": old_score,
            "new_score": new_score,
            "risk_level": record.risk_level.value,
            "outcome": "applied",
        })
    )
    return record


def penalize_for_complaint(db: Session, doctor_id: str, hospital_id: str | None = None) -> TrustScore:
    """Apply TRUST_SCORE_COMPLAINT_PENALTY (default: -5) for a filed complaint."""
    return _apply_penalty(db, doctor_id, settings.TRUST_SCORE_COMPLAINT_PENALTY, hospital_id)


def penalize_for_alert(db: Session, doctor_id: str, hospital_id: str | None = None) -> TrustScore:
    """Apply TRUST_SCORE_ALERT_PENALTY (default: -3) for a security alert raised."""
    return _apply_penalty(db, doctor_id, settings.TRUST_SCORE_ALERT_PENALTY, hospital_id)


def penalize_for_override_misuse(db: Session, doctor_id: str, hospital_id: str | None = None) -> TrustScore:
    """Apply TRUST_SCORE_OVERRIDE_MISUSE_PENALTY (default: -10) for confirmed override abuse."""
    return _apply_penalty(db, doctor_id, settings.TRUST_SCORE_OVERRIDE_MISUSE_PENALTY, hospital_id)


def get_hospital_average_trust_score(db: Session, hospital_id: str) -> float:
    """
    Return the average trust score for all doctors at a hospital.

    Returns TRUST_SCORE_DEFAULT (100) if no doctors are registered yet,
    so a hospital with no doctors doesn't appear artificially risky.

    Args:
        db:          SQLAlchemy session.
        hospital_id: Hospital to aggregate.

    Returns:
        Average score as a float.
    """
    records = db.query(TrustScore).filter(TrustScore.hospital_id == hospital_id).all()
    if not records:
        return float(settings.TRUST_SCORE_DEFAULT)
    return sum(r.score for r in records) / len(records)
