"""Run before the live demo to pre-populate realistic data."""
import os, sys, uuid

# Default to SQLite for local demo to avoid Postgres dependency
os.environ.setdefault("DATABASE_URL", "sqlite:///./dev.db")
os.environ.setdefault("JWT_SECRET_KEY", "CHANGE_ME_DEV_SECRET")

sys.path.insert(0, r"C:\Users\SRISAYEE\Desktop\Sai\Hackathon\Vortexa\module4")

from datetime import datetime, timedelta
from module4.backend.core.database import SessionLocal, engine, Base
from module4.backend.models.audit_log import AuditLog
from module4.backend.models.complaint import Complaint, ComplaintCategory, ComplaintPriority, ComplaintStatus
from module4.backend.trust_engine.engine import get_or_create_trust_score, penalize_for_complaint

import module4.backend.models as models
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# 1. Create a CRITICAL complaint
c = Complaint(
    complaint_id=uuid.uuid4(),
    patient_id="patient-001", doctor_id="doctor-001",
    hospital_id="hospital-A",
    category=ComplaintCategory.MEDICAL_ERROR,
    description="Patient died after wrong medication administered despite documented allergy.",
    status=ComplaintStatus.OPEN, priority=ComplaintPriority.CRITICAL,
)
db.add(c)
db.commit()
penalize_for_complaint(db, "doctor-001", "hospital-A")

# 2. Simulate suspicious behaviour: 15 rapid view-reports
for _ in range(15):
    db.add(AuditLog(
        user_id="doctor-001", role="doctor",
        action="VIEW_REPORT", resource="patient-001",
        hospital_id="hospital-A",
        timestamp=datetime.utcnow() - timedelta(minutes=10)
    ))

# 3. Give doctor-002 a LOW complaint history (for contrast)
for _ in range(2):
    db.add(AuditLog(
        user_id="doctor-002", role="doctor",
        action="VIEW_REPORT", resource="patient-002",
        hospital_id="hospital-A",
        timestamp=datetime.utcnow() - timedelta(hours=5)
    ))

db.commit()
print("Demo data seeded. Ready to present!")
db.close()
