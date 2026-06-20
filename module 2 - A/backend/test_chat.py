import jwt
import requests
import uuid

SECRET = "dev-secret-key-change-in-production"

# Generate patient token
patient_id = "test_patient_1"
token = jwt.encode({
    "sub": f"test_user_1",
    "email": "test@example.com",
    "patient_id": patient_id,
    "roles": ["patient"]
}, SECRET, algorithm="HS256")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Test Patient Chat (Attempting to get raw reports)
print("--- PATIENT CHAT TEST ---")
patient_chat_url = f"http://127.0.0.1:8000/api/v1/patient/{patient_id}/chat"
payload = {
    "question": "What are the exact raw values and doctor notes in my blood report?",
    "top_k": 5
}
resp = requests.post(patient_chat_url, json=payload, headers=headers)
print("Patient Response:", resp.status_code)
if resp.status_code == 200:
    print(resp.json().get("answer"))
else:
    print(resp.text)

# Generate doctor token
doctor_token = jwt.encode({
    "sub": f"test_doctor_1",
    "email": "doctor@example.com",
    "roles": ["doctor"]
}, SECRET, algorithm="HS256")

doctor_headers = {
    "Authorization": f"Bearer {doctor_token}",
    "Content-Type": "application/json"
}

# 2. Test Doctor Chat (Attempting to get comprehensive summary)
print("\n--- DOCTOR CHAT TEST ---")
doctor_chat_url = f"http://127.0.0.1:8000/api/v1/doctor/patients/{patient_id}/chat"
payload = {
    "question": "Summarize the patient's entire medical history and any raw laboratory findings.",
    "top_k": 10
}
resp = requests.post(doctor_chat_url, json=payload, headers=doctor_headers)
print("Doctor Response:", resp.status_code)
if resp.status_code == 200:
    print(resp.json().get("answer"))
else:
    print(resp.text)
