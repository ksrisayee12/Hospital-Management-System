"""
IsolationForest-based anomaly scorer for fraud detection.

This module implements the ML upgrade path that was stubbed in
detector.py's trailing comment block. It runs ALONGSIDE the existing
rule-based detectors — both scores are produced, and any disagreement
is logged explicitly for explainability (judges / admins should be able
to see WHY someone was flagged, not just a number).

Feature vector per user (computed from audit_logs):
  [views_per_hour, downloads_per_hour, overrides_per_week, off_hours_access_ratio]

Model lifecycle:
  - Trained manually via fraud_detection/training/train_isolation_forest.py
    (intended to run nightly or on-demand by a super_admin).
  - Serialized with joblib to fraud_detection/training/isolation_forest.pkl
  - Loaded lazily at first score request; if no model file exists, returns None
    gracefully so the rule-based detectors still run unaffected.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from module4.backend.models.audit_log import AuditLog
from module4.backend.models.emergency_override import EmergencyOverride

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "training" / "isolation_forest.pkl"

# Loaded once per process (lazy)
_model = None
_model_loaded = False


def _load_model():
    """
    Lazily load the serialized IsolationForest model.

    Returns the model if the pkl file exists, else None.
    Does NOT raise — callers should treat None as "model not available yet".
    """
    global _model, _model_loaded
    if _model_loaded:
        return _model
    _model_loaded = True
    if not MODEL_PATH.exists():
        logger.info(json.dumps({
            "action": "ML_MODEL_LOAD",
            "outcome": "not_found",
            "path": str(MODEL_PATH),
        }))
        _model = None
        return None
    try:
        import joblib  # noqa: PLC0415
        _model = joblib.load(MODEL_PATH)
        logger.info(json.dumps({
            "action": "ML_MODEL_LOAD",
            "outcome": "loaded",
            "path": str(MODEL_PATH),
        }))
    except Exception as exc:  # noqa: BLE001
        logger.warning(json.dumps({
            "action": "ML_MODEL_LOAD",
            "outcome": "error",
            "error": str(exc),
        }))
        _model = None
    return _model


def _off_hours_ratio(rows: list) -> float:
    """
    Fraction of audit log timestamps that fall outside 08:00–20:00 local time.
    A high ratio is a fraud signal (accessing records at 3 AM repeatedly).
    """
    if not rows:
        return 0.0
    off_hours = sum(
        1 for ts in rows if ts.hour < 8 or ts.hour >= 20
    )
    return off_hours / len(rows)


def compute_user_features(db: Session, user_id: str) -> dict[str, float]:
    """
    Compute the feature vector for the IsolationForest model.

    Features:
      - views_per_hour:          VIEW_REPORT actions in the last 24h / 24
      - downloads_per_hour:      DOWNLOAD_REPORT actions in the last 24h / 24
      - overrides_per_week:      EmergencyOverride requests in the last 7d
      - off_hours_access_ratio:  fraction of all actions in last 24h outside 08-20

    Args:
        db:      SQLAlchemy session.
        user_id: User to compute features for.

    Returns:
        Dict with feature names → float values.
    """
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    views = (
        db.query(func.count(AuditLog.event_id))
        .filter(
            AuditLog.user_id == user_id,
            AuditLog.action == "VIEW_REPORT",
            AuditLog.timestamp >= day_ago,
        )
        .scalar() or 0
    )

    downloads = (
        db.query(func.count(AuditLog.event_id))
        .filter(
            AuditLog.user_id == user_id,
            AuditLog.action == "DOWNLOAD_REPORT",
            AuditLog.timestamp >= day_ago,
        )
        .scalar() or 0
    )

    overrides = (
        db.query(func.count(EmergencyOverride.request_id))
        .filter(
            EmergencyOverride.doctor_id == user_id,
            EmergencyOverride.requested_at >= week_ago,
        )
        .scalar() or 0
    )

    # For off-hours ratio, fetch all timestamps in last 24h
    timestamps = (
        db.query(AuditLog.timestamp)
        .filter(
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= day_ago,
        )
        .all()
    )
    off_ratio = _off_hours_ratio([row[0] for row in timestamps])

    return {
        "views_per_hour": views / 24.0,
        "downloads_per_hour": downloads / 24.0,
        "overrides_per_week": float(overrides),
        "off_hours_access_ratio": off_ratio,
    }


def score_user_with_model(features: dict[str, float]) -> float | None:
    """
    Run the IsolationForest model and return an anomaly score.

    Returns:
        float in range roughly [-0.5, 0.5]:
          - More negative → more anomalous (potential fraud).
          - None if the model hasn't been trained yet.

    The score is the raw decision_function() output from sklearn's
    IsolationForest. Normalize to 0-100 for display:
      display_score = (1 - score) * 50  (0 = normal, 100 = very anomalous)
    """
    model = _load_model()
    if model is None:
        return None

    try:
        import numpy as np  # noqa: PLC0415
        feature_order = ["views_per_hour", "downloads_per_hour", "overrides_per_week", "off_hours_access_ratio"]
        vec = np.array([[features[f] for f in feature_order]])
        score = float(model.decision_function(vec)[0])
        return score
    except Exception as exc:  # noqa: BLE001
        logger.warning(json.dumps({
            "action": "ML_SCORE",
            "outcome": "error",
            "error": str(exc),
        }))
        return None


def get_fraud_explanation(
    db: Session,
    user_id: str,
) -> dict[str, Any]:
    """
    Produce a combined rule-based + ML explanation for a given user.

    Used by the GET /fraud/explain/{user_id} endpoint (super_admin only).

    Returns:
        Dict with:
          - features:        The raw feature vector.
          - isolation_score: Raw ML score (None if model not available).
          - isolation_display_score: Normalized 0-100 score (None if unavailable).
          - rule_flags:      List of rule-based detector names that fired.
          - ml_anomaly:      True if ML score indicates anomaly (< 0).
          - disagreement:    True if rule and ML disagree.
          - explanation:     Human-readable summary.
    """
    from module4.backend.fraud_detection.detector import (  # noqa: PLC0415
        detect_abnormal_downloads,
        detect_excessive_views,
        detect_override_abuse,
    )

    features = compute_user_features(db, user_id)
    iso_score = score_user_with_model(features)

    # Run rule detectors in read-only fashion — we DON'T want to create
    # new alerts here, just check whether thresholds are breached.
    rule_flags = []
    from module4.backend.core.config import settings  # noqa: PLC0415
    from datetime import timedelta  # noqa: PLC0415

    # Replicate threshold checks without DB writes
    if features["views_per_hour"] * 24 >= settings.FRAUD_VIEW_COUNT_THRESHOLD:
        rule_flags.append("EXCESSIVE_VIEWS")
    if features["downloads_per_hour"] * 24 >= settings.FRAUD_DOWNLOAD_COUNT_THRESHOLD:
        rule_flags.append("ABNORMAL_DOWNLOAD")
    if features["overrides_per_week"] >= settings.FRAUD_OVERRIDE_WEEKLY_THRESHOLD:
        rule_flags.append("OVERRIDE_ABUSE")

    rule_fired = len(rule_flags) > 0
    ml_anomaly = (iso_score is not None) and (iso_score < 0)

    # Disagreement logging
    if iso_score is not None and rule_fired != ml_anomaly:
        logger.warning(json.dumps({
            "action": "FRAUD_DETECTOR_DISAGREEMENT",
            "user_id": user_id,
            "rule_fired": rule_fired,
            "ml_anomaly": ml_anomaly,
            "rule_flags": rule_flags,
            "isolation_score": iso_score,
        }))

    display_score = None
    if iso_score is not None:
        display_score = round(min(100.0, max(0.0, (1 - iso_score) * 50)), 2)

    if not rule_fired and not ml_anomaly:
        explanation = "No anomalies detected by rule-based or ML detectors."
    elif rule_fired and ml_anomaly:
        explanation = f"BOTH rule-based ({rule_flags}) and ML detectors flagged this user as anomalous."
    elif rule_fired:
        explanation = f"Rule-based detectors flagged: {rule_flags}. ML model did not flag (score={iso_score})."
    else:
        explanation = f"ML model flagged as anomalous (score={iso_score}). Rule-based thresholds not yet breached."

    return {
        "user_id": user_id,
        "features": features,
        "isolation_score": iso_score,
        "isolation_display_score": display_score,
        "rule_flags": rule_flags,
        "ml_anomaly": ml_anomaly,
        "disagreement": (iso_score is not None) and (rule_fired != ml_anomaly),
        "explanation": explanation,
    }
