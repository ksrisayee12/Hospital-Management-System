# fraud_seed.py — run to simulate suspicious behaviour
import os, sys
os.environ.setdefault("DATABASE_URL", "sqlite:///./dev.db")
os.environ.setdefault("JWT_SECRET_KEY", "CHANGE_ME_DEV_SECRET")

sys.path.insert(0, r"C:\Users\SRISAYEE\Desktop\Sai\Hackathon\Vortexa\module4")
from datetime import datetime, timedelta
from module4.backend.core.database import SessionLocal, engine, Base
from module4.backend.models.audit_log import AuditLog

import module4.backend.models as models
Base.metadata.create_all(bind=engine)

db = SessionLocal()
for _ in range(15):
    db.add(AuditLog(
        user_id="doctor-001", role="doctor",
        action="VIEW_REPORT", resource="patient-001",
        hospital_id="hospital-A",
        timestamp=datetime.utcnow() - timedelta(minutes=10)
    ))
db.commit()
print("Seeded 15 VIEW_REPORT logs for doctor-001")
