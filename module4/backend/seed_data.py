import os
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from module4.backend.core.config import settings
from module4.backend.models.audit_log import AuditLog
from module4.backend.models.ledger_event import LedgerEvent
from module4.backend.models.security_alert import SecurityAlert, AlertStatus
from module4.backend.models.complaint import Complaint, ComplaintPriority, ComplaintStatus
from module4.backend.models.emergency_override import EmergencyOverride, OverrideStatus
from module4.backend.models.trust_score import TrustScore
from module4.backend.models.hospital_metrics import HospitalMetrics

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed():
    db = SessionLocal()
    
    # 1. Hospitals and Doctors
    hospitals = ["HOSP-123", "HOSP-456", "HOSP-789"]
    doctors = [f"doctor-{i}" for i in range(1, 11)]

    print("Cleaning up old data...")
    db.query(LedgerEvent).delete()
    db.query(AuditLog).delete()
    db.query(SecurityAlert).delete()
    db.query(Complaint).delete()
    db.query(EmergencyOverride).delete()
    db.query(TrustScore).delete()
    db.query(HospitalMetrics).delete()
    db.commit()

    print("Seeding Trust Scores...")
    for doc in doctors:
        score = random.randint(40, 100)
        risk = "LOW" if score >= 80 else "MODERATE" if score >= 60 else "HIGH" if score >= 40 else "CRITICAL"
        ts = TrustScore(
            doctor_id=doc,
            hospital_id=random.choice(hospitals),
            score=score,
            risk_level=risk
        )
        db.add(ts)
    
    print("Seeding Alerts...")
    alert_types = ["REPEATED_ACCESS", "ABNORMAL_DOWNLOAD", "EXCESSIVE_VIEWS", "OVERRIDE_ABUSE", "OTHER_ANOMALY"]
    for i in range(15):
        doc = random.choice(doctors)
        status = random.choice([AlertStatus.NEW, AlertStatus.DISMISSED, AlertStatus.UNDER_REVIEW, AlertStatus.ESCALATED])
        alert = SecurityAlert(
            user_id=doc,
            hospital_id=random.choice(hospitals),
            alert_type=random.choice(alert_types),
            risk_score=random.randint(40, 95),
            status=status,
            description=f"Suspicious activity detected for {doc}",
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5))
        )
        db.add(alert)
        
    print("Seeding Complaints...")
    for i in range(10):
        doc = random.choice(doctors)
        status = random.choice([ComplaintStatus.OPEN, ComplaintStatus.UNDER_REVIEW, ComplaintStatus.RESOLVED])
        comp = Complaint(
            patient_id=f"patient-{random.randint(1, 100)}",
            doctor_id=doc,
            hospital_id=random.choice(hospitals),
            category="UNAUTHORIZED_ACCESS" if random.random() > 0.5 else "PRIVACY_ISSUE",
            description=f"Patient noticed unusual access by {doc}.",
            priority=ComplaintPriority.HIGH if random.random() > 0.7 else ComplaintPriority.MEDIUM,
            status=status,
            created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 5))
        )
        db.add(comp)
        
    print("Seeding Overrides...")
    for i in range(8):
        doc = random.choice(doctors)
        status = random.choice([OverrideStatus.PENDING, OverrideStatus.APPROVED, OverrideStatus.REJECTED])
        ov = EmergencyOverride(
            doctor_id=doc,
            patient_id=f"patient-{random.randint(1, 100)}",
            hospital_id=random.choice(hospitals),
            reason="Patient in ER, needs immediate history.",
            urgency="CRITICAL",
            status=status,
            requested_at=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48))
        )
        db.add(ov)
        
    db.commit()

    print("Seeding Hospital Metrics...")
    for hosp in hospitals:
        metrics = HospitalMetrics(
            hospital_id=hosp,
            risk_score=random.uniform(20.0, 80.0),
            avg_trust_score=random.uniform(60.0, 95.0),
            open_complaints=random.randint(0, 5),
            active_alerts=random.randint(0, 8),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(metrics)
    db.commit()

    print("Seeding Ledger Events...")
    import hashlib
    prev_hash = "GENESIS"
    for i in range(1, 21):
        evt_type = random.choice(["SECURITY_ALERT_RAISED", "COMPLAINT_CREATED", "TRUST_SCORE_UPDATED", "EMERGENCY_OVERRIDE_APPROVED"])
        doc = random.choice(doctors)
        summary = f"{evt_type} for {doc}"
        
        event_data = f"{i}|{evt_type}|{summary}|{doc}|{prev_hash}"
        curr_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        le = LedgerEvent(
            sequence_number=i,
            event_type=evt_type,
            event_data=event_data,
            previous_hash=prev_hash,
            current_hash=curr_hash,
            timestamp=datetime.now(timezone.utc) - timedelta(hours=20-i)
        )
        db.add(le)
        prev_hash = curr_hash

    db.commit()
    db.close()
    print("Seeding complete!")

if __name__ == "__main__":
    seed()
