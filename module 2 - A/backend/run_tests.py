import subprocess
import time
import sys

print("Starting server on port 8005...")
server_process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8005"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

time.sleep(10)  # Wait for server to initialize DB and start

print("Running tests...")
test_process = subprocess.run([sys.executable, "test_api.py"], capture_output=True, text=True)

print("--- TEST SCRIPT STDOUT ---")
print(test_process.stdout)
print("--- TEST SCRIPT STDERR ---")
print(test_process.stderr)

server_process.terminate()

print("--- SERVER LOGS ---")
for line in server_process.stdout:
    print(line, end="")
