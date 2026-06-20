"""
Token generator for live demo.
Run: python token_gen.py
Copy the tokens into your demo terminal.
"""
from datetime import datetime, timedelta
from jose import jwt

SECRET = "CHANGE_ME_DEV_SECRET"  # change to match JWT_SECRET_KEY in .env

def make(user_id, role, hospital_id=None):
    p = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=8),
    }
    if hospital_id:
        p["hospital_id"] = hospital_id
    return jwt.encode(p, SECRET, algorithm="HS256")

print("=== COPY THESE INTO YOUR DEMO TERMINAL ===\n")
print("PATIENT TOKEN (patient-001):")
print(make("patient-001", "patient"))

print("\nDOCTOR TOKEN (doctor-001, hospital-A):")
print(make("doctor-001", "doctor", "hospital-A"))

print("\nADMIN TOKEN (admin-001, hospital-A):")
print(make("admin-001", "admin", "hospital-A"))

print("\nSUPER ADMIN TOKEN (superadmin-001):")
print(make("superadmin-001", "super_admin"))

print("\n=== SET THEM IN POWERSHELL ===")
print('$PATIENT = "Bearer ' + make("patient-001", "patient") + '"')
print('$DOCTOR  = "Bearer ' + make("doctor-001", "doctor", "hospital-A") + '"')
print('$ADMIN   = "Bearer ' + make("admin-001", "admin", "hospital-A") + '"')
print('$SADMIN  = "Bearer ' + make("superadmin-001", "super_admin") + '"')
