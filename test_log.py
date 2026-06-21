import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

try:
    res = supabase.table("doctor_activity_logs").insert({
        "doctor_code": "DOC001",
        "patient_id": "PAT001",
        "action": "TEST",
        "details": "Test insert"
    }).execute()
    print("Log Insert success:", res.data)
except Exception as e:
    print("Error inserting into doctor_activity_logs:", str(e))
