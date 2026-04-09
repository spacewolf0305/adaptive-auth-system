"""Quick test script for the Adaptive Auth SaaS API."""
import sqlite3
import requests

# Get the API key from database
conn = sqlite3.connect("auth.db")
c = conn.cursor()
c.execute("SELECT key FROM api_keys WHERE is_active=1 LIMIT 1")
row = c.fetchone()
conn.close()

if not row:
    print("❌ No API keys found. Please sign up first at http://localhost:5000/signup")
    exit(1)

API_KEY = row[0]
BASE = "http://localhost:5000"

print(f"🔑 Using API key: {API_KEY[:20]}...{API_KEY[-6:]}")
print()

# Test 1: Safe login
print("=" * 50)
print("TEST 1: Safe login from India")
print("=" * 50)
r = requests.post(f"{BASE}/api/v1/assess", headers={"X-API-Key": API_KEY}, json={
    "country": "India",
    "device_type": "desktop",
    "hour_of_day": 14,
    "threat_score": 10,
    "distance_from_last_login": 50,
})
data = r.json()
print(f"  Risk Score : {data['risk_score']}")
print(f"  Action     : {data['action']}")
print(f"  Reasons    : {data.get('reasons', [])}")
print(f"  Request ID : {data.get('request_id')}")
print(f"  Usage      : {data.get('usage')}")
print()

# Test 2: Suspicious login
print("=" * 50)
print("TEST 2: Suspicious login from North Korea")
print("=" * 50)
r = requests.post(f"{BASE}/api/v1/assess", headers={"X-API-Key": API_KEY}, json={
    "country": "North Korea",
    "device_type": "iot_device",
    "hour_of_day": 3,
    "prev_login_success": 0,
    "threat_score": 92,
    "distance_from_last_login": 8000,
})
data = r.json()
print(f"  Risk Score : {data['risk_score']}")
print(f"  Action     : {data['action']}")
print(f"  Reasons    : {data.get('reasons', [])}")
print(f"  Request ID : {data.get('request_id')}")
print(f"  Usage      : {data.get('usage')}")
print()

# Test 3: No API key
print("=" * 50)
print("TEST 3: Request without API key")
print("=" * 50)
r = requests.post(f"{BASE}/api/v1/assess", json={"country": "India"})
print(f"  Status   : {r.status_code}")
print(f"  Response : {r.json()}")
print()

print("✅ All tests complete!")
