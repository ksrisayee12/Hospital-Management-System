"""
IsolationForest training script — run manually, NOT in the request path.

Intended cadence: nightly or on-demand by a super_admin after the system
has accumulated sufficient audit_log volume (recommended: ≥ 500 audit log
rows covering a representative mix of normal and suspicious activity).

Usage:
    cd module4/
    python -m fraud_detection.training.train_isolation_forest

This will:
  1. Connect to the database specified in DATABASE_URL (or .env)
  2. Query audit_logs and emergency_overrides to build feature vectors
     for every distinct user_id seen in the last 30 days
  3. Train an IsolationForest(contamination=0.05, random_state=42)
  4. Serialize the model to fraud_detection/training/isolation_forest.pkl

After retraining, restart the FastAPI app (or call importlib.reload on
ml_detector) so the new model is picked up. The model file is small
(<1 MB) and safe to deploy alongside the app image.

WARNING: Do NOT run this script while the app is handling high traffic —
the feature query is a full table scan. Run it during off-peak hours or
on a read replica.
"""

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure module4 root is on sys.path when running as a script
_ROOT = Path(__file__).resolve().parents[3]  # module4/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

OUTPUT_PATH = Path(__file__).parent / "isolation_forest.pkl"
LOOKBACK_DAYS = 30
CONTAMINATION = 0.05  # expected fraction of anomalous users
RANDOM_STATE = 42


def build_feature_matrix(db):
    """
    Compute the feature vector for every distinct user seen in the last
    LOOKBACK_DAYS days.

    Feature vector: [views_per_hour, downloads_per_hour, overrides_per_week,
                     off_hours_access_ratio]

    Returns:
        (user_ids, feature_matrix) where feature_matrix is a list of lists.
    """
    from datetime import datetime, timedelta

    from sqlalchemy import func

    from module4.backend.models.audit_log import AuditLog
    from module4.backend.models.emergency_override import EmergencyOverride

    cutoff = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)

    # Distinct users active in the window
    user_ids = [
        row[0]
        for row in db.query(AuditLog.user_id)
        .filter(AuditLog.timestamp >= cutoff)
        .distinct()
        .all()
    ]

    if not user_ids:
        logger.warning("No users found in audit_logs for the training window. Aborting.")
        return [], []

    features = []
    for uid in user_ids:
        day_ago = datetime.utcnow() - timedelta(hours=24)
        week_ago = datetime.utcnow() - timedelta(days=7)

        views = (
            db.query(func.count(AuditLog.event_id))
            .filter(AuditLog.user_id == uid, AuditLog.action == "VIEW_REPORT", AuditLog.timestamp >= day_ago)
            .scalar() or 0
        )
        downloads = (
            db.query(func.count(AuditLog.event_id))
            .filter(AuditLog.user_id == uid, AuditLog.action == "DOWNLOAD_REPORT", AuditLog.timestamp >= day_ago)
            .scalar() or 0
        )
        overrides = (
            db.query(func.count(EmergencyOverride.request_id))
            .filter(EmergencyOverride.doctor_id == uid, EmergencyOverride.requested_at >= week_ago)
            .scalar() or 0
        )
        timestamps = (
            db.query(AuditLog.timestamp)
            .filter(AuditLog.user_id == uid, AuditLog.timestamp >= day_ago)
            .all()
        )
        off = sum(1 for (ts,) in timestamps if ts.hour < 8 or ts.hour >= 20)
        off_ratio = off / len(timestamps) if timestamps else 0.0

        features.append([views / 24.0, downloads / 24.0, float(overrides), off_ratio])

    return user_ids, features


def train_and_save(db):
    """Train IsolationForest and serialize to OUTPUT_PATH."""
    import numpy as np
    from sklearn.ensemble import IsolationForest
    import joblib

    logger.info("Building feature matrix...")
    user_ids, feature_matrix = build_feature_matrix(db)

    if not user_ids:
        return

    X = np.array(feature_matrix)
    logger.info(f"Training on {len(user_ids)} users, {X.shape[1]} features...")

    model = IsolationForest(contamination=CONTAMINATION, random_state=RANDOM_STATE)
    model.fit(X)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, OUTPUT_PATH)
    logger.info(json.dumps({
        "action": "ISOLATION_FOREST_TRAINED",
        "users": len(user_ids),
        "contamination": CONTAMINATION,
        "output": str(OUTPUT_PATH),
        "outcome": "saved",
    }))


if __name__ == "__main__":
    from module4.backend.core.database import SessionLocal

    db = SessionLocal()
    try:
        train_and_save(db)
    finally:
        db.close()
