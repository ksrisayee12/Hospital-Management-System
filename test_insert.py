import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

payload = {
    "doctor_code": "DOC001",
    "patient_id": "PAT001",
    "medicine_name": "Amoxicillin",
    "dosage": "500mg",
    "frequency": "Twice a day",
    "duration": "7 days",
    "ai_status": "SAFE",
    "doctor_confirmed": True
}

try:
    res = supabase.table("prescriptions").insert(payload).execute()
    print("Insert success:", res.data)
except Exception as e:
    print("Error inserting into prescriptions:", str(e))
