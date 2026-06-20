import urllib.request
import json
try:
    print(urllib.request.urlopen('http://localhost:5000/api/doctor/DOC001/dashboard').read().decode('utf-8'))
except Exception as e:
    print(str(e))
