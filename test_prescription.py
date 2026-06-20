import urllib.request
import urllib.error
import json

req = urllib.request.Request(
    'http://localhost:5000/api/prescription/create',
    method='POST',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({
        'doctor_code': 'DOC001',
        'patient_id': 'PAT001',
        'medicine_name': 'Amoxicillin',
        'dosage': '500mg',
        'frequency': 'Twice a day',
        'duration': '7 days'
    }).encode('utf-8')
)

try:
    res = urllib.request.urlopen(req)
    print(res.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(e.read().decode('utf-8'))
