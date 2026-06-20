import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

tables = ["doctor_patients", "appointments", "doctor_activity_logs", "doctors"]

for t in tables:
    try:
        res = supabase.table(t).select("*").limit(5).execute()
        print(f"Table {t} data:", res.data)
    except Exception as e:
        print(f"Error reading {t}:", str(e))
