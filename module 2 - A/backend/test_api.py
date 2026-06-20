import jwt
import requests
import time

# Create a valid JWT
SECRET = "dev-secret-key-change-in-production"
token = jwt.encode({
    "sub": "test_user_1",
    "email": "test@example.com",
    "patient_id": "test_patient_1",
    "roles": ["patient"]
}, SECRET, algorithm="HS256")

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

base_url = "http://127.0.0.1:8000/api/v1"

def print_result(name, resp):
    print(f"\n--- {name} ---")
    print(f"Status: {resp.status_code}")
    try:
        print(resp.json())
    except:
        print(resp.text)

import uuid
unique_suffix = str(uuid.uuid4())[:8]

# 1. Create Patient
patient_data = {
    "user_id": f"test_user_{unique_suffix}",
    "email": f"test_{unique_suffix}@example.com",
    "first_name": "Test",
    "last_name": "User",
    "vault_initialized": True
}
resp = requests.post(f"{base_url}/patients", json=patient_data, headers=headers)
print_result("CREATE PATIENT", resp)
patient_id = resp.json().get("id") if resp.status_code == 201 else "test_patient_1"

# Regenerate token with the actual patient ID so AI endpoints work
token = jwt.encode({
    "sub": f"test_user_{unique_suffix}",
    "email": f"test_{unique_suffix}@example.com",
    "patient_id": patient_id,
    "roles": ["patient"]
}, SECRET, algorithm="HS256")
headers["Authorization"] = f"Bearer {token}"
headers_upload = {"Authorization": f"Bearer {token}"}

# 2. Upload file to Vault (with form data)
form_data = {
    "category": "prescription",
    "description": "Test prescription"
}
# Create a dummy image file
with open("test_prescription.jpg", "wb") as f:
    f.write(b"dummy image data")

files = {
    "file": ("test_prescription.jpg", open("test_prescription.jpg", "rb"), "image/jpeg")
}
headers_upload = {"Authorization": f"Bearer {token}"} # no content-type for multipart
resp = requests.post(f"{base_url}/patients/{patient_id}/vault/upload", files=files, data=form_data, headers=headers_upload)
print_result("VAULT UPLOAD", resp)
vault_file_id = resp.json().get("id")

# 3. Vault Download
resp = requests.get(f"{base_url}/patients/{patient_id}/vault/{vault_file_id}/download", headers=headers)
print("\n--- VAULT DOWNLOAD ---")
print(f"Status: {resp.status_code}, Content: {resp.text}")

# 4. Family Invite
family_data = {
    "family_member_email": "fam@example.com",
    "family_member_name": "Fam User",
    "relationship": "parent",
    "permission_level": "view_only"
}
resp = requests.post(f"{base_url}/patients/{patient_id}/family/invite", json=family_data, headers=headers)
print_result("FAMILY INVITE", resp)
access_id = resp.json().get("id")

# 5. Get Dashboard
resp = requests.get(f"{base_url}/dashboard/{patient_id}", headers=headers)
print_result("GET DASHBOARD", resp)

# 6. Create Prescription
prescription_data = {
    "medicine_name": "Lisinopril",
    "dosage": "10mg",
    "frequency": "Once daily",
    "duration": "30 days"
}
resp = requests.post(f"{base_url}/patient/prescriptions", json=prescription_data, headers=headers)
print_result("CREATE PRESCRIPTION", resp)
prescription_id = resp.json().get("id") if resp.status_code in (200, 201) else "mock_id"

# 7. Analyze Prescription Safety
resp = requests.get(f"{base_url}/patient/safety/{prescription_id}", headers=headers)
print_result("SAFETY ANALYSIS", resp)
