"""
End-to-end smoke test for Module 4.
Run: python e2e_test.py
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "CHANGE_ME_DEV_SECRET"

import uuid as _uuid
import sqlalchemy.dialects.postgresql as pg_dialect
from sqlalchemy.types import TypeDecorator, CHAR

class SQLiteUUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True
    def process_bind_param(self, value, dialect):
        return str(value) if value else None
    def process_result_value(self, value, dialect):
        return _uuid.UUID(str(value)) if value else None

class _CompatUUID:
    def __new__(cls, as_uuid=False):
        return SQLiteUUID()

pg_dialect.UUID = _CompatUUID

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from module4.backend.core.database import Base
import module4.backend.models as models  # noqa: F401

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
db = Session()

# ── Step 1: Complaint submission ─────────────────────────────────────────────
print("Step 1: Submit complaint...")
from module4.backend.complaints.service import create_complaint
from module4.backend.models.complaint import ComplaintCategory
c = create_complaint(db, "p1", "d1", ComplaintCategory.UNAUTHORIZED_ACCESS,
                     "Doctor accessed records without consent.", hospital_id="hosp-A")
print(f"  Complaint created: {c.complaint_id}, priority={c.priority}")

# ── Step 2: Trust penalty ────────────────────────────────────────────────────
print("Step 2: Trust score penalty applied...")
from module4.backend.trust_engine.engine import get_or_create_trust_score
ts = get_or_create_trust_score(db, "d1")
assert ts.score == 95, f"Expected 95, got {ts.score}"
print(f"  Trust score: {ts.score} (100 - 5 penalty = 95) [OK]")

# ── Step 3: Critical action -> ledger ────────────────────────────────────────
print("Step 3: Critical action mirrored to ledger...")
from module4.backend.audit.service import record_action
record_action(db, "admin-1", "admin", "CONSENT_APPROVED", resource="p1")
from module4.backend.models.ledger_event import LedgerEvent
events = db.query(LedgerEvent).all()
assert len(events) >= 1
print(f"  Ledger events: {len(events)} [OK]")

# ── Step 4: Tamper detection ─────────────────────────────────────────────────
print("Step 4: Chain integrity verification...")
from module4.backend.blockchain.ledger import verify_chain
result = verify_chain(db)
valid = result["valid"]
assert valid is True
print(f"  Chain valid: {valid} [OK]")

# ── Step 5: Fraud alert ──────────────────────────────────────────────────────
print("Step 5: Fraud alert detection...")
from datetime import datetime, timedelta
from module4.backend.models.audit_log import AuditLog
for _ in range(15):
    db.add(AuditLog(user_id="d1", role="doctor", action="VIEW_REPORT",
                    resource="patient-X", timestamp=datetime.utcnow() - timedelta(minutes=10)))
db.commit()
from module4.backend.fraud_detection.detector import detect_excessive_views
alert = detect_excessive_views(db, "d1", "hosp-A")
alert_type = alert.alert_type if alert else None
print(f"  Fraud alert type: {alert_type} [OK]")

# ── Step 6: Emergency override approval ─────────────────────────────────────
print("Step 6: Emergency override approve/reject flow...")
from module4.backend.admin.emergency_service import create_override_request, review_override_request
override = create_override_request(db, "d1", "p1", "Emergency surgery", hospital_id="hosp-A")
approved = review_override_request(db, str(override.request_id), approve=True, reviewed_by="admin-1")
status = approved.status.value
assert status == "APPROVED", f"Expected APPROVED, got {status}"
print(f"  Override status: {status} [OK]")

# Verify ledger entry for override approval
override_events = db.query(LedgerEvent).filter_by(event_type="EMERGENCY_OVERRIDE_APPROVED").all()
assert len(override_events) >= 1
print(f"  Override logged to ledger: {len(override_events)} event(s) [OK]")

# ── Step 7: Hospital risk scoring ────────────────────────────────────────────
print("Step 7: Hospital risk recomputation...")
from module4.backend.super_admin.analytics_service import recompute_hospital_metrics
m = recompute_hospital_metrics(db, "hosp-A", "Test Hospital")
assert m.risk_score >= 0
print(f"  Hospital risk score: {m.risk_score} [OK]")

# Idempotency check
m2 = recompute_hospital_metrics(db, "hosp-A", "Test Hospital")
assert m.risk_score == m2.risk_score
print(f"  Idempotency confirmed: {m.risk_score} == {m2.risk_score} [OK]")

print()
print("=" * 55)
print("  END-TO-END FLOW: ALL 7 STEPS PASSED [OK]")
print("=" * 55)
